import sys

import numpy as np
import pandas as pd

from attribution.portfolios import benchmark_returns
from backtest.backtest import backtest, stats
from data.registry import get_data
from port_con.config import BASELINE_WEIGHTS, CALIBRATION_END, EQUITY, SLEEVES
from port_con.portfolio import get_baseline
from signal_search.candidates import _mom_13612w

# Round 3 of the signal search: trend signals as a drawdown-control overlay
# (research_notes/signal_search_protocol.md). Run from the repo root:
#   python -m signal_search.drawdown pretest   select + validate periods, picks the overlay by the rules
#   python -m signal_search.drawdown test      the test period, once, for the chosen overlay only

START = "2007-11-01"
SELECT_END = "2018-01-01"
RISK_OFF_EQUITY = 0.40          # equity weight when fully risk-off (baseline 0.70); the rest earns T-bills
MIN_MDD_GAIN = 0.02             # max drawdown at least 2 pp shallower than the base
MAX_SHARPE_LOSS = 0.05


def month_ends() -> pd.DatetimeIndex:
    index = get_data("prices").loc[START:].index
    return pd.DatetimeIndex(pd.Series(index, index=index).groupby(index.to_period("M")).last())


def base_weights(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """70/20/10 with S&P sector weights inside equity; the alternative 10% goes to
    fixed income until an alternative asset has prices."""
    prices = get_data("prices")
    rows = {}
    for date in dates:
        available = prices.loc[:date].tail(22).notna().all()
        inside = get_baseline(date, available.index[available])
        sleeves = dict(BASELINE_WEIGHTS)
        if inside["alternative"].empty:
            sleeves["fixed_income"] += sleeves.pop("alternative")
        rows[date] = pd.concat([inside[s] * w for s, w in sleeves.items()])
    return pd.DataFrame(rows).T.fillna(0)


# ---- Risk-off share on each month end (0 = baseline, 1 = equity cut to RISK_OFF_EQUITY) ----

def faber_sma10(dates: pd.DatetimeIndex) -> pd.Series:
    """Equity month-end close below its 10-month average. Faber (2007)."""
    monthly = get_data("equity_basket").groupby(get_data("equity_basket").index.to_period("M")).last()
    off = (monthly < monthly.rolling(10).mean()).astype(float)
    return pd.Series(off.reindex(dates.to_period("M")).values, index=dates)


def abs_mom(dates: pd.DatetimeIndex) -> pd.Series:
    """Equity 12-month return below the 3-month T-bill yield. Antonacci (2013)."""
    eq = get_data("equity_basket")
    rf = get_data("us3m").reindex(eq.index, method="ffill") / 100
    return ((eq / eq.shift(252) - 1) < rf).astype(float).reindex(dates)


def canary(dates: pd.DatetimeIndex) -> pd.Series:
    """Share of the canaries (EEM, AGG) with negative 13612W momentum. Keller & Keuning (2018)."""
    mom = _mom_13612w(get_data("canary_prices"))
    return (mom < 0).mean(axis=1).reindex(mom.index.union(dates)).ffill().reindex(dates)


OVERLAYS = {"faber_sma10": faber_sma10, "abs_mom": abs_mom, "canary": canary}


def overlay_weights(base: pd.DataFrame, risk_off: pd.Series) -> pd.DataFrame:
    eq = [c for c in base.columns if c in EQUITY]
    scale = 1 - risk_off * (1 - RISK_OFF_EQUITY / BASELINE_WEIGHTS["equity"])
    w = base.copy()
    w[eq] = w[eq].mul(scale, axis=0)
    return w


def periods(index: pd.DatetimeIndex) -> dict[str, pd.DatetimeIndex]:
    sel, val = pd.Timestamp(SELECT_END), pd.Timestamp(CALIBRATION_END)
    return {"select": index[index < sel], "validate": index[(index >= sel) & (index < val)],
            "test": index[index >= val]}


def run() -> tuple[dict[str, pd.DataFrame], dict[str, pd.Series]]:
    dates = month_ends()
    base = base_weights(dates)
    weights = {"base": base, **{n: overlay_weights(base, f(dates).fillna(0)) for n, f in OVERLAYS.items()}}
    results = {n: backtest(w, managers=False).loc[START:] for n, w in weights.items()}
    share = {n: f(dates) for n, f in OVERLAYS.items()}
    return results, share


def table(results: dict, dates: pd.DatetimeIndex) -> pd.DataFrame:
    cash = benchmark_returns(dates)["Cash"].fillna(0)
    base = results["base"]["net"].loc[dates]
    rows = {}
    for n, r in results.items():
        s = stats(r["net"].loc[dates], base, cash, r["turnover"].loc[dates])
        rows[n] = {k: s[k] for k in ["Ann. return", "Ann. vol", "Sharpe", "Max drawdown", "Turnover / yr"]}
        rows[n]["Calmar"] = s["Ann. return"] / -s["Max drawdown"]
    return pd.DataFrame(rows).T


def main(stage: str) -> None:
    pd.set_option("display.width", 200)
    results, share = run()
    p = periods(results["base"].index)
    tables = {k: table(results, p[k]) for k in ["select", "validate"]}

    passed = []
    for n in OVERLAYS:
        ok = all(t.loc[n, "Max drawdown"] - t.loc["base", "Max drawdown"] >= MIN_MDD_GAIN and
                 t.loc[n, "Sharpe"] >= t.loc["base", "Sharpe"] - MAX_SHARPE_LOSS for t in tables.values())
        if ok:
            passed.append(n)
    pretest = p["select"].union(p["validate"])
    chosen = max(passed, key=lambda n: table(results, pretest).loc[n, "Sharpe"]) if passed else None

    if stage == "pretest":
        for k, t in tables.items():
            print(f"=== {k} ({p[k][0].date()} to {p[k][-1].date()}) ===")
            print(t.round(3), "\n")
        print("Share of months risk-off (pre-test):",
              {n: round(float(s.loc[:CALIBRATION_END].mean()), 2) for n, s in share.items()})
        print(f"Passed: {passed or 'none'}. Chosen: {chosen or 'none'}")
    elif stage == "test":
        if chosen is None:
            print("No overlay passed; the test period is not looked at.")
            return
        print(f"=== test ({p['test'][0].date()} to {p['test'][-1].date()}), chosen: {chosen} ===")
        print(table({k: results[k] for k in ["base", chosen]}, p["test"]).round(3))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "pretest")
