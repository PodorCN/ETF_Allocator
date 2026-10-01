import pandas as pd

from attribution.brinson import Attribution, attribute
from data.registry import get_data
from data.yahoo import get_adj_close
from manager_selection.config import MANAGERS
from manager_selection.implement import leverage_returns, slot_returns
from port_con.config import ALTERNATIVE, BONDS, EQUITY, SLEEVES
from port_con.portfolio import final_weights, l1_weights

# Inputs for attribution.brinson.attribute(): which portfolios to attribute
# and against what. The Brinson attribution tab (pages/brinson.py) shows every entry in PORTFOLIOS.
# Run from the repo root: python -m attribution.portfolios

# Benchmark: 70% S&P 500 + 20% fixed income + 10% alternative, in CAD,
# rebalanced daily (same split as the port_con baseline).
# - S&P 500: SPY converted to CAD (unhedged). Same construction as the
#   sector ETF signal prices (SPDR x USDCAD), so the equity selection effect
#   is pure sector/region tilt, not proxy noise. ZSP.TO is the traded
#   equivalent but only has history from 2012.
# - Fixed income: XBB.TO, iShares Core Canadian Universe Bond (FTSE Canada
#   Universe Bond Index), the standard broad CAD bond benchmark.
# - Alternative: equal weight of the ALTERNATIVE ETFs (HUG, XEC, XEU),
#   over the ones with a price that day.
BENCHMARK_WEIGHTS = {"Equity": 0.70, "Fixed Income": 0.20, "Alternative": 0.10}
BENCHMARK_EQUITY = "SPY"
BENCHMARK_BOND = "XBB.TO"
BENCHMARK_NAME = (f"70% S&P 500 ({BENCHMARK_EQUITY} in CAD) + 20% Canadian Universe Bond ({BENCHMARK_BOND})"
                  f" + 10% alternative (equal weight {', '.join(ALTERNATIVE)})")

# Leverage (weights not summing to 1) is funded / parked in cash earning the
# 3-month T-bill. USD rate used as a stand-in for CAD cash.
CASH = "Cash"
SEGMENTS = {**{a: "Equity" for a in EQUITY}, **{a: "Fixed Income" for a in BONDS},
            **{a: "Alternative" for a in ALTERNATIVE}, CASH: "Cash"}


def benchmark_returns(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Daily CAD returns of the benchmark segments, plus the cash rate."""
    usdcad = get_adj_close("CAD=X")
    spx = get_adj_close(BENCHMARK_EQUITY)
    spx = spx * usdcad.reindex(spx.index, method="ffill")
    bond = get_adj_close(BENCHMARK_BOND)
    alternative = get_data("prices")[ALTERNATIVE].reindex(index).pct_change(fill_method=None).mean(axis=1)
    return pd.DataFrame({
        "Equity": spx.reindex(index).ffill().pct_change(fill_method=None),
        "Fixed Income": bond.reindex(index).ffill().pct_change(fill_method=None),
        "Alternative": alternative,
        # Yesterday's annualized T-bill yield accrues today.
        "Cash": (get_data("us3m") / 100 / 252).reindex(index).ffill().shift(1),
    })


def attribute_vs_benchmark(weights: pd.DataFrame, name: str, managers: bool = False) -> Attribution:
    """Attribute month-end ETF weights (UNIVERSE labels) against the 70/20/10 benchmark.

    Whatever the weights don't sum to is held in cash (negative = leverage).
    managers=True: slots in manager_selection.config.MANAGERS earn the
    manager's return; the difference shows up as the Manager and Manager
    leverage effects.
    """
    prices = get_data("prices")
    bench = benchmark_returns(prices.index)
    weights = weights.assign(**{CASH: 1 - weights.sum(axis=1)})
    returns = prices.pct_change(fill_method=None).assign(**{CASH: bench["Cash"]})
    actual = slot_returns().assign(**{CASH: bench["Cash"]}) if managers else None
    leverage = leverage_returns() if managers else None
    return attribute(weights, returns, SEGMENTS, BENCHMARK_WEIGHTS, bench, name=name,
                     benchmark_name=BENCHMARK_NAME, actual_returns=actual, leverage_returns=leverage)


def strategy_with_managers(method: str = "te_budget") -> Attribution:
    """The full strategy built with `method`, implemented with the managers in MANAGERS."""
    names = ", ".join(f"{slot} -> {m['symbol']}" for slot, m in MANAGERS.items())
    return attribute_vs_benchmark(final_weights(method), f"Strategy ({method}) + managers ({names})", managers=True)


def strategy() -> Attribution:
    """The full strategy: L1 sleeve weights x L2 weights inside the equity sleeve."""
    return attribute_vs_benchmark(final_weights(), "Strategy (L1 + L2)")


def l1_only() -> Attribution:
    """L1 sleeve weights with equal weight inside each sleeve (no L2), to
    see what L2 adds."""
    prices = get_data("prices")
    l1 = l1_weights()
    rows = {}
    for date in l1.index:
        live = prices.loc[date].notna()
        row = {}
        for sleeve, assets in SLEEVES.items():
            held = [a for a in assets if live[a]]
            row.update({a: l1.at[date, sleeve] / len(held) for a in held})
        rows[date] = row
    columns = [a for assets in SLEEVES.values() for a in assets]
    weights = pd.DataFrame(rows).T.reindex(columns=columns).fillna(0.0)
    return attribute_vs_benchmark(weights, "L1 only (equal weight in sleeves)")


# Display name -> function returning an Attribution. The first entry is the
# page's default. Add any portfolio here to show it on the Brinson attribution tab.
PORTFOLIOS = {
    "Strategy + managers": strategy_with_managers,
    "Strategy (Black-Litterman) + managers": lambda: strategy_with_managers("black_litterman"),
    "Strategy (L1 + L2)": strategy,
    "L1 only": l1_only,
}


if __name__ == "__main__":
    for label, build in PORTFOLIOS.items():
        s = build().summary()
        print(label, {k: f"{v:+.2%}" for k, v in s["total"].items()})
