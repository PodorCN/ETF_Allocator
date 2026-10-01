import json
import os

import numpy as np
import pandas as pd

from backtest.html import page
from data.registry import get_data
from port_con.calibrate import HORIZON, rank_corr, weekly_dates
from port_con.config import CALIBRATION_END, EQUITY, L1_SIGNALS, L2_SIGNALS
from port_con.l1 import get_l1_signals
from port_con.l2 import get_l2_signals

# Signal tearsheet: each signal's own backtest, in sample (before
# CALIBRATION_END, used to calibrate) vs out of sample (after). Split the
# same way as the calibration: a date is in sample only if its forward return
# window ends before CALIBRATION_END (see _periods).
# Run from the repo root: python -m backtest.signal_tearsheet
#
# Per signal, on weekly dates:
#   IC        rank correlation with the next HORIZON days' return
#             L1 (time series): signal vs equity basket minus bond basket, signed by
#             the signal's side, so > 0 always means the signal helped
#             L2 (cross section): across sectors on each date
#   Quantiles average next-HORIZON-day return by signal bucket
#             L1: quintiles of the signal over time; L2: thirds of the sectors each week,
#             return in excess of the sector average
#   Curve     L1: timing, hold clip(signal / 2, -1, 1) of equity minus bonds for a week
#             L2: long the top third of sectors, short the bottom third, for a week
# t-stats account for overlapping forward returns (HORIZON days sampled weekly).

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "signals.html")
NW_LAGS = 4  # Newey-West lags ~ HORIZON / 5 trading days
WEEK = 5  # trading days a weekly curve return spans


def _newey_west_t(x: pd.Series) -> float:
    """t-stat of the mean of `x`, with Newey-West standard errors."""
    x = x.dropna()
    n = len(x)
    if n < 10:
        return np.nan
    e = (x - x.mean()).values
    var = (e @ e) / n
    for k in range(1, NW_LAGS + 1):
        var += 2 * (1 - k / (NW_LAGS + 1)) * (e[k:] @ e[:-k]) / n
    return x.mean() / np.sqrt(var / n)


def _corr_t(ic: float, n: int) -> float:
    """t-stat of a correlation over n overlapping weekly samples (effective n = n / overlap)."""
    n_eff = n / (HORIZON / 5)
    return ic * np.sqrt(max(n_eff - 2, 1)) / np.sqrt(max(1 - ic * ic, 1e-9))


def _ann(weekly: pd.Series) -> float:
    weekly = weekly.dropna()
    return (1 + weekly).prod() ** (52 / len(weekly)) - 1 if len(weekly) else np.nan


def _periods(index: pd.DatetimeIndex, horizon: int = HORIZON) -> dict[str, pd.DatetimeIndex]:
    """In sample: dates whose forward `horizon`-trading-day window ends before
    CALIBRATION_END (the rule port_con.calibrate uses). Out of sample: from
    CALIBRATION_END. Dates whose window straddles the split are in neither."""
    split = pd.Timestamp(CALIBRATION_END)
    trading = get_data("prices").index
    last_ok = trading[trading < split][-horizon - 1]
    return {"is": index[index <= last_ok], "oos": index[index >= split]}


def _series(s: pd.Series, digits: int = 5) -> list:
    return [None if pd.isna(v) else round(float(v), digits) for v in s]


def _dates(index) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in index]


def _all_weeks(start) -> pd.DatetimeIndex:
    """Last trading day of every week from `start` (including weeks without a full forward window)."""
    index = get_data("prices").index
    weeks = pd.DatetimeIndex(pd.Series(index, index=index).groupby(index.to_period("W")).last())
    return weeks[weeks >= start]


def _next_week(prices, dates: pd.DatetimeIndex):
    """Return from each weekly date to the next one."""
    p = prices.reindex(dates)
    return p.shift(-1) / p - 1


def _doc(func) -> str:
    return (func.__doc__ or "").strip().split("\n")[0]


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Rank correlation of two arrays without ties (fast, for rolling windows)."""
    return float(np.corrcoef(a.argsort().argsort(), b.argsort().argsort())[0, 1])


def _row_rank_corr(a: pd.DataFrame, b: pd.DataFrame, min_count: int = 5) -> pd.Series:
    """Rank correlation across columns, row by row, over the columns where both have a value."""
    mask = a.notna() & b.notna()
    ra, rb = a.where(mask).rank(axis=1), b.where(mask).rank(axis=1)
    ra, rb = ra.sub(ra.mean(axis=1), axis=0), rb.sub(rb.mean(axis=1), axis=0)
    denom = np.sqrt((ra ** 2).sum(axis=1) * (rb ** 2).sum(axis=1)).replace(0, np.nan)
    return ((ra * rb).sum(axis=1) / denom).where(mask.sum(axis=1) >= min_count)


def _thirds(z: pd.DataFrame) -> pd.DataFrame:
    """0 / 1 / 2 = bottom / middle / top third of each row by value (NaN where no value)."""
    ranks = z.rank(axis=1, method="first")
    return np.floor(3 * (ranks - 0.5).div(z.notna().sum(axis=1), axis=0))


# ---- L1: time-series signals ----

def l1_sheet(name: str, cfg: dict, layer: str) -> dict:
    ic_dates = weekly_dates(get_data("prices").index)
    side = 1 if cfg["side"] == "equity" else -1
    z = get_l1_signals()[name] * side
    eq, fi = get_data("equity_basket"), get_data("bond_basket")
    fwd = (eq.shift(-HORIZON) / eq - 1) - (fi.shift(-HORIZON) / fi - 1)

    df = pd.DataFrame({"z": z.reindex(ic_dates), "fwd": fwd.reindex(ic_dates)}).dropna()
    df = df[df["z"] != 0]  # before the signal has history

    zv, fv = df["z"].values, df["fwd"].values
    rolling = pd.Series([_spearman(zv[i - 52:i], fv[i - 52:i]) if i >= 52 else np.nan
                         for i in range(1, len(df) + 1)], index=df.index)
    yearly = df.groupby(df.index.year).apply(lambda g: rank_corr(g["z"], g["fwd"]) if len(g) > 10 else np.nan)

    quant = {}
    for p, dates in _periods(df.index).items():
        d = df.loc[dates]
        buckets = pd.qcut(d["z"].rank(method="first"), 5, labels=False)
        quant[p] = d.groupby(buckets)["fwd"].mean()

    weeks = _all_weeks(df.index[0])
    pos = (z.reindex(weeks) / 2).clip(-1, 1)
    weekly = (pos * (_next_week(eq, weeks) - _next_week(fi, weeks))).dropna()
    curve = (1 + weekly).cumprod()

    summary = {}
    for p, dates in _periods(df.index).items():
        d = df.loc[dates]
        ic = rank_corr(d["z"], d["fwd"])
        summary[p] = {
            "IC": ic, "t": _corr_t(ic, len(d)), "IC IR": None,
            "Hit rate": float((np.sign(d["z"]) == np.sign(d["fwd"])).mean()),
            "Curve ann.": _ann(weekly.loc[_periods(weekly.index, WEEK)[p]]),
            "Weeks": len(d),
        }
    zw = z.reindex(weeks)
    summary["autocorr"] = float(zw.corr(zw.shift(1)))

    return {
        "name": name, "layer": f"L1 {layer.upper()}", "kind": "ts", "desc": _doc(cfg["func"]),
        "ic_line": {"label": "Rolling 52-week IC", "dates": _dates(rolling.index), "values": _series(rolling, 4)},
        "yearly": {"years": [int(y) for y in yearly.index], "values": _series(yearly, 4)},
        "quantiles": {"labels": ["Q1 low", "Q2", "Q3", "Q4", "Q5 high"],
                      "is": _series(quant["is"]), "oos": _series(quant["oos"])},
        "curve": {"label": "Timing: equity minus bonds, sized by the signal",
                  "dates": _dates(curve.index), "values": _series(curve, 4)},
        "summary": summary,
        "_weekly_z": zw,
    }


# ---- L2: cross-sectional signals ----

def l2_sheet(name: str, cfg: dict) -> dict:
    ic_dates = weekly_dates(get_data("prices").index)
    prices = get_data("prices")[EQUITY]
    z = get_l2_signals()[name]
    fwd = prices.shift(-HORIZON) / prices - 1

    # Weekly IC and next-HORIZON-day excess return by third, all dates at once.
    zi, fi = z.reindex(ic_dates), fwd.reindex(ic_dates)
    mask = zi.notna() & fi.notna()
    ic = _row_rank_corr(zi, fi).dropna()
    thirds = _thirds(zi.where(mask))
    excess = fi.where(mask).sub(fi.where(mask).mean(axis=1), axis=0)
    q = pd.DataFrame({k: excess.where(thirds == k).mean(axis=1) for k in range(3)}).loc[ic.index]

    # Long-short: top third minus bottom third, held for a week.
    weeks = _all_weeks(ic.index[0])
    zw = z.reindex(weeks)
    nxt = _next_week(prices, weeks)
    thirds_w = _thirds(zw)
    ls = nxt.where(thirds_w == 2).mean(axis=1) - nxt.where(thirds_w == 0).mean(axis=1)
    weekly = ls.where(zw.notna().sum(axis=1) >= 5).dropna()
    curve = (1 + weekly).cumprod()

    summary = {}
    for p, dates in _periods(ic.index).items():
        x = ic.loc[dates]
        summary[p] = {
            "IC": float(x.mean()), "t": _newey_west_t(x), "IC IR": float(x.mean() / x.std()),
            "Hit rate": float((x > 0).mean()),
            "Curve ann.": _ann(weekly.loc[_periods(weekly.index, WEEK)[p]]),
            "Weeks": len(x),
        }
    summary["autocorr"] = float(_row_rank_corr(zw, zw.shift(1)).mean())

    return {
        "name": name, "layer": "L2", "kind": "cs", "desc": _doc(cfg["func"]),
        "ic_line": {"label": "Cumulative IC", "dates": _dates(ic.index), "values": _series(ic.cumsum(), 4)},
        "yearly": {"years": [int(y) for y in ic.index.year.unique()],
                   "values": _series(ic.groupby(ic.index.year).mean(), 4)},
        "quantiles": {"labels": ["Bottom third", "Middle third", "Top third"],
                      "is": _series(q.loc[_periods(q.index)["is"]].mean()),
                      "oos": _series(q.loc[_periods(q.index)["oos"]].mean())},
        "curve": {"label": "Long top third, short bottom third of sectors",
                  "dates": _dates(curve.index), "values": _series(curve, 4)},
        "summary": summary,
        "_weekly_z": zw,
    }


def _correlations(sheets: list[dict]) -> dict:
    """Signal correlation matrices, in sample and out of sample (L1: over time; L2: pooled sector-weeks)."""
    out = {}
    for kind in ["ts", "cs"]:
        group = [s for s in sheets if s["kind"] == kind]
        names = [s["name"] for s in group]
        if kind == "ts":
            frame = pd.DataFrame({s["name"]: s["_weekly_z"] for s in group}).replace(0, np.nan)
        else:
            frame = pd.DataFrame({s["name"]: s["_weekly_z"].stack() for s in group})
            frame.index = frame.index.get_level_values(0)
        mats = {p: frame.loc[frame.index.isin(dates)].corr().reindex(index=names, columns=names)
                for p, dates in _periods(frame.index.unique(), 0).items()}
        out[kind] = {"names": names, "is": mats["is"].round(3).values.tolist(),
                     "oos": mats["oos"].round(3).values.tolist()}
    return out


def build_data() -> dict:
    sheets = [l1_sheet(name, cfg, layer) for layer, sigs in L1_SIGNALS.items() for name, cfg in sigs.items()]
    sheets += [l2_sheet(name, cfg) for name, cfg in L2_SIGNALS.items()]
    corr = _correlations(sheets)
    for s in sheets:
        s.pop("_weekly_z")
    return {"split": CALIBRATION_END, "horizon": HORIZON, "sheets": sheets, "corr": corr}


BODY = """<main>
  <h1>Signal tearsheet</h1>
  <p class="sub" id="sub"></p>

  <section class="card">
    <h2>Summary: in sample vs out of sample</h2>
    <p>IC = rank correlation with the next <span class="h"></span> trading days' return. t-stats adjust for
    overlapping returns. IC IR = mean / std of weekly IC (L2 only). Hit rate: L1 = signal and return had the
    same sign; L2 = weeks with IC &gt; 0. Autocorr = signal this week vs last week (low = more turnover).
    Curve = the weekly strategy chart in each section, annualized.</p>
    <div class="table-wrap"><table id="summary"></table></div>
  </section>

  <div class="grid2">
    <section class="card">
      <h2>L1 signal correlation</h2>
      <p>Below the diagonal: in sample. Above: out of sample.</p>
      <div class="chart" id="corr_ts"></div>
    </section>
    <section class="card">
      <h2>L2 signal correlation</h2>
      <p>Below the diagonal: in sample. Above: out of sample. Pooled over sectors and weeks.</p>
      <div class="chart" id="corr_cs"></div>
    </section>
  </div>

  <div id="sheets"></div>
</main>"""

SCRIPT = """
const SPLIT = DATA.split;
const f2 = v => v == null || isNaN(v) ? "–" : (v >= 0 ? "+" : "") + v.toFixed(2);
const f3 = v => v == null || isNaN(v) ? "–" : (v >= 0 ? "+" : "") + v.toFixed(3);
const p0 = v => v == null || isNaN(v) ? "–" : (v * 100).toFixed(0) + "%";

function oosShade(th) {
  // Out-of-sample region: a light wash plus a hairline at the split.
  return [
    { type: "rect", xref: "x", yref: "paper", x0: SPLIT, x1: "2100-01-01", y0: 0, y1: 1,
      fillcolor: th.muted, opacity: 0.10, line: { width: 0 }, layer: "below" },
    { type: "line", xref: "x", yref: "paper", x0: SPLIT, x1: SPLIT, y0: 0, y1: 1, line: { color: th.muted, width: 1 } },
  ];
}

function oosLabel(th) {
  return [{ x: SPLIT, y: 1, xref: "x", yref: "paper", text: "out of sample", showarrow: false,
            xanchor: "left", yanchor: "top", xshift: 4, font: { color: th.ink2, size: 11 } }];
}

function small(th, extra = {}) {
  return layout(th, Object.assign({ margin: { t: 16, r: 12, b: 28, l: 48 }, showlegend: false }, extra));
}

function refLine(th, y) {
  return { type: "line", xref: "paper", x0: 0, x1: 1, y0: y, y1: y, line: { color: th.axis, width: 1 } };
}

function renderSheet(th, s, i) {
  const x0 = s.ic_line.dates[0], x1 = s.curve.dates[s.curve.dates.length - 1];

  const icl = small(th); icl.xaxis.range = [x0, x1];
  icl.shapes = [...oosShade(th), refLine(th, 0)];
  icl.annotations = oosLabel(th);
  Plotly.react(`ic_${i}`, [line(s.ic_line.dates, s.ic_line.values, s.ic_line.label, th.series[0],
    { hovertemplate: "%{x}<br>" + s.ic_line.label + ": %{y:.3f}<extra></extra>" })], icl, CONFIG);

  const ql = small(th, { barmode: "group", bargap: 0.35, hovermode: "closest", showlegend: true });
  ql.margin.t = 36;
  ql.xaxis = { type: "category", linecolor: th.axis, tickfont: { color: th.ink2 } };
  ql.yaxis.tickformat = ".1%"; ql.yaxis.zeroline = true; ql.yaxis.zerolinecolor = th.axis;
  const bar = (y, name, color) => ({ type: "bar", x: s.quantiles.labels, y, name, width: 0.3,
    marker: { color, line: { width: 0 } }, hovertemplate: name + " · %{x}: %{y:.2%}<extra></extra>" });
  Plotly.react(`q_${i}`, [bar(s.quantiles.is, "In sample", th.series[0]),
                          bar(s.quantiles.oos, "Out of sample", th.series[1])], ql, CONFIG);

  const cl = small(th); cl.xaxis.range = [x0, x1];
  cl.shapes = [...oosShade(th), refLine(th, 1)];
  cl.annotations = oosLabel(th);
  cl.yaxis.tickformat = ".2f";
  Plotly.react(`c_${i}`, [line(s.curve.dates, s.curve.values, "Growth of 1", th.series[0],
    { hovertemplate: "%{x}<br>Growth of 1: %{y:.3f}<extra></extra>" })], cl, CONFIG);

  const yl = small(th, { hovermode: "closest" });
  yl.xaxis = { type: "linear", dtick: 2, tickformat: "d", tickangle: 0, linecolor: th.axis, tickfont: { color: th.ink2 } };
  yl.yaxis.tickformat = ".2f"; yl.yaxis.zeroline = true; yl.yaxis.zerolinecolor = th.axis;
  const splitYear = parseInt(SPLIT.slice(0, 4));
  Plotly.react(`y_${i}`, [{ type: "bar", x: s.yearly.years, y: s.yearly.values, width: 0.6,
    marker: { color: s.yearly.years.map(y => y < splitYear ? th.series[0] : th.series[1]), line: { width: 0 } },
    hovertemplate: "%{x}: IC %{y:.3f}<extra></extra>" }], yl, CONFIG);
}

function renderCorr(th, id, C) {
  const n = C.names.length, z = [], text = [];
  for (let r = 0; r < n; r++) {
    z.push([]); text.push([]);
    for (let c = 0; c < n; c++) {
      const v = r === c ? null : (r > c ? C.is[r][c] : C.oos[r][c]);
      z[r].push(v); text[r].push(v == null ? "" : v.toFixed(2));
    }
  }
  const dark = mode() === "dark";
  const scale = [[0, dark ? "#e66767" : "#e34948"], [0.5, dark ? "#383835" : "#f0efec"], [1, dark ? "#3987e5" : "#2a78d6"]];
  const l = layout(th, { hovermode: "closest", margin: { t: 16, r: 16, b: 100, l: 160 } });
  l.xaxis = { tickangle: -30, tickfont: { color: th.ink2 }, showgrid: false };
  l.yaxis = { autorange: "reversed", tickfont: { color: th.ink2 }, showgrid: false };
  Plotly.react(id, [{ type: "heatmap", x: C.names, y: C.names, z, text, texttemplate: "%{text}",
    textfont: { color: th.ink }, zmin: -1, zmax: 1, xgap: 2, ygap: 2, colorscale: scale,
    colorbar: { thickness: 10, tickfont: { color: th.ink2 } },
    hovertemplate: "%{y} vs %{x}: %{z:.2f}<extra></extra>" }], l, CONFIG);
}

function render() {
  const th = THEMES[mode()];
  DATA.sheets.forEach((s, i) => renderSheet(th, s, i));
  renderCorr(th, "corr_ts", DATA.corr.ts);
  renderCorr(th, "corr_cs", DATA.corr.cs);
}

function buildPage() {
  document.getElementById("sub").textContent =
    `In sample: before ${SPLIT} (used to calibrate the parameters). Out of sample: ${SPLIT} onward. ` +
    `Weekly samples, ${DATA.horizon}-trading-day forward returns.`;
  document.querySelectorAll(".h").forEach(e => e.textContent = DATA.horizon);

  const cols = [["IC", f3], ["t", f2], ["IC IR", f2], ["Hit rate", p0], ["Curve ann.", v => pct(v, 1)]];
  let h = "<thead><tr><th rowspan='2'>Signal</th>" + cols.map(([c]) => `<th colspan="2">${c}</th>`).join("") +
          "<th rowspan='2'>Autocorr</th></tr><tr>" + cols.map(() => "<th>In</th><th>Out</th>").join("") + "</tr></thead><tbody>";
  DATA.sheets.forEach(s => {
    h += `<tr><td><a href="#sheet_${s.name}">${s.layer}: ${s.name}</a></td>` +
      cols.map(([c, f]) => `<td>${f(s.summary.is[c])}</td><td>${f(s.summary.oos[c])}</td>`).join("") +
      `<td>${f2(s.summary.autocorr)}</td></tr>`;
  });
  document.getElementById("summary").innerHTML = h + "</tbody>";

  document.getElementById("sheets").innerHTML = DATA.sheets.map((s, i) => `
    <section class="card" id="sheet_${s.name}">
      <h2>${s.layer}: ${s.name}</h2>
      <p>${s.desc}</p>
      <div class="grid2">
        <div><p><b>${s.ic_line.label}</b></p><div class="chart mini" id="ic_${i}"></div></div>
        <div><p><b>Average forward return by signal bucket</b>
          ${s.kind === "cs" ? "(vs sector average)" : "(equity minus bonds)"}</p><div class="chart mini" id="q_${i}"></div></div>
        <div><p><b>${s.curve.label}</b> (weekly)</p><div class="chart mini" id="c_${i}"></div></div>
        <div><p><b>IC by year</b> (blue in sample, orange out of sample)</p><div class="chart mini" id="y_${i}"></div></div>
      </div>
    </section>`).join("");
}

buildPage();
render();
watchTheme(render);
"""

EXTRA_CSS = """<style>
.chart.mini { height: 230px; }
th[colspan] { text-align: center; }
a { color: inherit; }
</style>"""


def write_report() -> str:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    html = page("Signal Tearsheet", EXTRA_CSS + BODY, SCRIPT, json.dumps(build_data()))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    return OUT


if __name__ == "__main__":
    print(write_report())
