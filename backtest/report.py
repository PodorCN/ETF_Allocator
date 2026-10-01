import json
import os

import pandas as pd

from attribution.signal_attribution import summary as signal_summary
from backtest.backtest import COST_BPS, run
from backtest.html import page
from port_con.config import BASELINE_WEIGHTS, REBALANCE

# Writes the backtest as a standalone HTML page with charts (plotly.js from CDN).
# Run from the repo root: python -m backtest.report [start]

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "backtest.html")

LABELS = {"black_litterman": "Black-Litterman", "te_budget": "TE budget", "benchmark": "Benchmark 70/20/10"}
SLEEVE_LABELS = {"equity": "Equity", "fixed_income": "Fixed income", "alternative": "Alternative"}
# Signal attribution components -> group shown on the cumulative chart.
def component_group(component: str) -> str:
    if component.startswith("L1"):
        return "L1 signals"
    if component.startswith("L2"):
        return "L2 signals"
    if component in ("Sizing (leverage)", "Interaction"):
        return "Sizing + interaction"
    return component


GROUPS = ["Baseline vs benchmark", "L1 signals", "L2 signals", "Sizing + interaction", "Manager", "Manager leverage",
          "Trading cost"]

STAT_FORMATS = {
    "Total return": "pct", "Ann. return": "pct", "Ann. vol": "pct", "Sharpe": "num",
    "Max drawdown": "pct", "Tracking error": "pct", "Info ratio": "num", "Turnover / yr": "pct0",
}


def _series(s: pd.Series, digits: int = 5) -> list:
    return [None if pd.isna(v) else round(float(v), digits) for v in s]


def build_data(start: str) -> dict:
    res = run(start)
    r = res["returns"]
    growth = (1 + r).cumprod()
    # Start every line at 1 the day before the first return.
    growth = pd.concat([pd.DataFrame(1.0, index=[r.index[0] - pd.Timedelta(days=1)], columns=r.columns), growth])
    drawdown = growth / growth.cummax() - 1
    active = growth[["black_litterman", "te_budget"]].sub(growth["benchmark"], axis=0)

    stats = res["stats"]
    rows = []
    for name, row in stats.iterrows():
        for key, label in LABELS.items():
            name = name.replace(key, label)
        rows.append({"name": name, **{k: (None if pd.isna(v) else float(v)) for k, v in row.items()}})

    return {
        "start": r.index[0].strftime("%Y-%m-%d"),
        "end": r.index[-1].strftime("%Y-%m-%d"),
        "rebalance": {"W": "weekly", "M": "monthly"}[REBALANCE],
        "cost_bps": COST_BPS,
        "labels": LABELS,
        "sleeve_labels": SLEEVE_LABELS,
        "baseline": BASELINE_WEIGHTS,
        "dates": [d.strftime("%Y-%m-%d") for d in growth.index],
        "growth": {c: _series(growth[c]) for c in growth},
        "drawdown": {c: _series(drawdown[c]) for c in drawdown},
        "active": {c: _series(active[c]) for c in active},
        "sleeves": {
            m: {"dates": [d.strftime("%Y-%m-%d") for d in df.index],
                **{s: _series(df[s], 4) for s in SLEEVE_LABELS}}
            for m, df in res["sleeves"].items()
        },
        "stats": rows,
        "stat_formats": STAT_FORMATS,
        "attr": _attribution_data(start),
    }


def _attribution_data(start: str) -> dict:
    s = signal_summary(start)
    table = s["table"]
    components = [c for c in table.index if c != "Total active"]
    cumulative = {}
    for m, res in s["results"].items():
        grouped = res["daily"].T.groupby(component_group).sum().T[GROUPS].cumsum()
        cumulative[m] = {"dates": [d.strftime("%Y-%m-%d") for d in grouped.index],
                         **{g: _series(grouped[g]) for g in GROUPS}}
    ic = s["ic"].reindex(components)
    return {
        "components": components,
        "groups": GROUPS,
        "contrib": {m: _series(table.loc[components, m]) for m in table.columns},
        "total": {m: float(table.loc["Total active", m]) for m in table.columns},
        "ic_before": _series(ic["IC before"], 3),
        "ic_window": _series(ic["IC in window"], 3),
        "cumulative": cumulative,
    }


BODY = """<main>
  <h1>Backtest: last 3 years</h1>
  <p class="sub" id="sub"></p>

  <section class="card">
    <h2>Growth of 1 (after trading costs)</h2>
    <p>Both methods vs the 70/20/10 benchmark.</p>
    <div class="chart" id="growth"></div>
  </section>

  <section class="card">
    <h2>Performance</h2>
    <p>Annualized from daily returns. Sharpe uses the 3-month T-bill; tracking error and info ratio are vs the benchmark.</p>
    <div class="table-wrap"><table id="stats"></table></div>
  </section>

  <div class="grid2">
    <section class="card">
      <h2>Active return vs benchmark</h2>
      <p>Cumulative, growth of 1 minus the benchmark's.</p>
      <div class="chart" id="active"></div>
    </section>
    <section class="card">
      <h2>Drawdown</h2>
      <p>Fall from the previous peak.</p>
      <div class="chart" id="drawdown"></div>
    </section>
  </div>

  <div class="grid2">
    <section class="card">
      <h2>Sleeve weights: Black-Litterman</h2>
      <p>Dotted: baseline. Weights include leverage.</p>
      <div class="chart" id="sleeves_bl"></div>
    </section>
    <section class="card">
      <h2>Sleeve weights: TE budget</h2>
      <p>Dotted: baseline. Weights include leverage.</p>
      <div class="chart" id="sleeves_te"></div>
    </section>
  </div>

  <h1 style="margin-top:32px">Signal attribution</h1>
  <p class="sub">Where the active return vs the benchmark came from. Each signal: the portfolio rebuilt with only
  that signal on, minus the portfolio with every signal off. Carino-linked, so the rows add up to the total
  active return.</p>

  <section class="card">
    <h2>Contribution by component</h2>
    <p>Cumulative over the window, net of trading cost, with managers.</p>
    <div class="chart" id="attr_bars" style="height:520px"></div>
  </section>

  <section class="card">
    <h2>Cumulative contribution over time</h2>
    <p id="attr_line_sub"></p>
    <div id="attr_method" style="margin-bottom:6px"></div>
    <div class="chart" id="attr_line"></div>
  </section>

  <section class="card">
    <h2>Contribution and IC by signal</h2>
    <p>IC = rank correlation with the next 21 trading days' return (L1: equity minus bonds, signed so &gt; 0 helps;
    L2: across sectors). "Before" = data used for calibration; "in window" = this backtest period.</p>
    <div class="table-wrap"><table id="attr_table"></table></div>
  </section>

  <ul class="notes" id="notes"></ul>
</main>

"""

SCRIPT = """const METHODS = ["black_litterman", "te_budget"];
X_RANGE = [DATA.dates[0], DATA.dates[DATA.dates.length - 1]];

function endLabels(th, x, series) {
  // Direct label at the end of each line, in text ink (the line carries the color).
  return series.map(([y, text]) => ({
    x: x[x.length - 1], y: y[y.length - 1], text, xanchor: "left", xshift: 6, showarrow: false,
    font: { color: th.ink, size: 11 },
  }));
}

function render() {
  const th = THEMES[mode()];
  const x = DATA.dates;
  const color = { black_litterman: th.series[0], te_budget: th.series[1], benchmark: th.bench };

  // Growth of 1
  const g = ["black_litterman", "te_budget", "benchmark"].map(k =>
    line(x, DATA.growth[k], DATA.labels[k], color[k],
         { hovertemplate: DATA.labels[k] + ": %{y:.3f}<extra></extra>",
           line: { color: color[k], width: 2, dash: k === "benchmark" ? "dot" : "solid" } }));
  const gl = layout(th);
  gl.yaxis.tickformat = ".2f";
  Plotly.react("growth", g, gl, CONFIG);

  // Active return
  const a = METHODS.map(k => line(x, DATA.active[k], DATA.labels[k], color[k],
    { hovertemplate: DATA.labels[k] + ": %{y:+.2%}<extra></extra>" }));
  const al = layout(th, { margin: { t: 56, r: 56, b: 32, l: 52 } });
  al.yaxis.tickformat = "+.0%";
  al.shapes = [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 0, y1: 0, line: { color: th.axis, width: 1 } }];
  al.annotations = endLabels(th, x, METHODS.map(k => [DATA.active[k], pct(DATA.active[k][DATA.active[k].length - 1])]));
  Plotly.react("active", a, al, CONFIG);

  // Drawdown
  const d = ["black_litterman", "te_budget", "benchmark"].map(k =>
    line(x, DATA.drawdown[k], DATA.labels[k], color[k],
         { hovertemplate: DATA.labels[k] + ": %{y:.1%}<extra></extra>",
           line: { color: color[k], width: 2, dash: k === "benchmark" ? "dot" : "solid" } }));
  const dl = layout(th);
  dl.yaxis.tickformat = ".0%";
  Plotly.react("drawdown", d, dl, CONFIG);

  // Sleeve weights, same y-scale for both methods
  const sleeveColor = { equity: th.series[2], fixed_income: th.series[3], alternative: th.series[4] };
  const all = METHODS.flatMap(m => Object.keys(DATA.sleeve_labels).flatMap(s => DATA.sleeves[m][s]));
  const ymax = Math.ceil(Math.max(...all) * 10) / 10;
  [["black_litterman", "sleeves_bl"], ["te_budget", "sleeves_te"]].forEach(([m, id]) => {
    const sx = DATA.sleeves[m].dates;
    const traces = Object.entries(DATA.sleeve_labels).map(([s, label]) =>
      line(sx, DATA.sleeves[m][s], label, sleeveColor[s],
        { line: { color: sleeveColor[s], width: 2, shape: "hv" }, hovertemplate: label + ": %{y:.1%}<extra></extra>" }));
    const sl = layout(th);
    sl.yaxis.tickformat = ".0%";
    sl.yaxis.range = [0, ymax];
    sl.shapes = Object.keys(DATA.sleeve_labels).map(s => ({
      type: "line", xref: "paper", x0: 0, x1: 1, y0: DATA.baseline[s], y1: DATA.baseline[s],
      line: { color: th.muted, width: 1, dash: "dot" } }));
    Plotly.react(id, traces, sl, CONFIG);
  });

  renderAttribution(th, color);

  // Table
  const cols = Object.keys(DATA.stat_formats);
  const fmt = (v, f) => v == null ? "–" : f === "num" ? v.toFixed(2) : f === "pct0" ? (v * 100).toFixed(0) + "%" : pct(v);
  const keyColor = name => name.startsWith(DATA.labels.black_litterman) ? color.black_litterman
    : name.startsWith(DATA.labels.te_budget) ? color.te_budget : th.bench;
  document.getElementById("stats").innerHTML =
    "<thead><tr><th>Portfolio</th>" + cols.map(c => `<th>${c}</th>`).join("") + "</tr></thead><tbody>" +
    DATA.stats.map(r => `<tr><td><span class="key" style="background:${keyColor(r.name)}"></span>${r.name}</td>` +
      cols.map(c => `<td>${fmt(r[c], DATA.stat_formats[c])}</td>`).join("") + "</tr>").join("") + "</tbody>";
}

let attrMethod = "black_litterman";

function renderAttribution(th, color) {
  const A = DATA.attr;
  const comps = A.components.slice().reverse();  // first component on top
  const rev = arr => arr.slice().reverse();
  const bars = METHODS.map(m => ({
    type: "bar", orientation: "h", name: DATA.labels[m], y: comps, x: rev(A.contrib[m]),
    marker: { color: color[m], line: { width: 0 } }, width: 0.36,
    hovertemplate: "%{y}<br>" + DATA.labels[m] + ": %{x:+.2%}<extra></extra>",
  }));
  const bl = layout(th, { barmode: "group", bargap: 0.3, hovermode: "closest",
                          margin: { t: 56, r: 24, b: 32, l: 210 } });
  bl.xaxis = { tickformat: "+.0%", gridcolor: th.grid, zeroline: true, zerolinecolor: th.axis, zerolinewidth: 1 };
  bl.yaxis = { automargin: true, tickfont: { color: th.ink2 } };
  Plotly.react("attr_bars", bars, bl, CONFIG);

  // Method toggle + cumulative lines by group
  const tog = document.getElementById("attr_method");
  tog.className = "toggle";
  tog.innerHTML = METHODS.map(m =>
    `<button type="button" data-m="${m}" aria-pressed="${m === attrMethod}">${DATA.labels[m]}</button>`).join("");
  tog.querySelectorAll("button").forEach(b => b.onclick = () => { attrMethod = b.dataset.m; render(); });

  const groupColor = { "Baseline vs benchmark": th.bench, "L1 signals": th.series[2], "L2 signals": th.series[3],
                       "Sizing + interaction": th.series[4], "Manager": th.groupExtra[0],
                       "Manager leverage": th.groupExtra[1], "Trading cost": th.groupExtra[2] };
  const C = A.cumulative[attrMethod];
  const lines = A.groups.map(g => line(C.dates, C[g], g, groupColor[g],
    { hovertemplate: g + ": %{y:+.2%}<extra></extra>",
      line: { color: groupColor[g], width: 2, dash: g === "Baseline vs benchmark" ? "dot" : "solid" } }));
  const ll = layout(th);
  ll.xaxis.range = [C.dates[0], C.dates[C.dates.length - 1]];
  ll.yaxis.tickformat = "+.0%";
  ll.shapes = [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 0, y1: 0, line: { color: th.axis, width: 1 } }];
  Plotly.react("attr_line", lines, ll, CONFIG);
  document.getElementById("attr_line_sub").textContent =
    `${DATA.labels[attrMethod]}, grouped. Total active return: ${pct(A.total[attrMethod])}.`;

  // Table
  const f3 = v => v == null ? "–" : (v >= 0 ? "+" : "") + v.toFixed(3);
  document.getElementById("attr_table").innerHTML =
    "<thead><tr><th>Component</th>" + METHODS.map(m => `<th>${DATA.labels[m]}</th>`).join("") +
    "<th>IC before</th><th>IC in window</th></tr></thead><tbody>" +
    A.components.map((c, i) => `<tr><td>${c}</td>` + METHODS.map(m => `<td>${pct(A.contrib[m][i], 2)}</td>`).join("") +
      `<td>${f3(A.ic_before[i])}</td><td>${f3(A.ic_window[i])}</td></tr>`).join("") +
    `<tr><td><b>Total active</b></td>` + METHODS.map(m => `<td><b>${pct(A.total[m], 2)}</b></td>`).join("") +
    "<td></td><td></td></tr></tbody>";
}

document.getElementById("sub").textContent =
  `${DATA.start} to ${DATA.end} · ${DATA.rebalance} rebalance · parameters calibrated on data before the start · ` +
  `net of ${DATA.cost_bps} bp trading cost · managers included`;
document.getElementById("notes").innerHTML = [
  "Weights set at a rebalance close earn returns from the next day; target weights are held between rebalances.",
  "Weights not summing to 100% are funded by / earn the US 3-month T-bill.",
  "Sector signals use the US SPDR originals converted to CAD; XHY / XIG use HYG / LQD (CAD-hedged ETFs).",
  "Benchmark: 70% S&P 500 (SPY in CAD) + 20% XBB + 10% equal-weight HUG / XEC / XEU.",
].map(t => `<li>${t}</li>`).join("");

render();
watchTheme(render);
"""


def write_report(start: str) -> str:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page("ETF Allocator Backtest", BODY, SCRIPT, json.dumps(build_data(start))))
    return OUT


if __name__ == "__main__":
    import sys
    start = sys.argv[1] if len(sys.argv) > 1 else (pd.Timestamp.today() - pd.DateOffset(years=3)).strftime("%Y-%m-%d")
    print(write_report(start))
