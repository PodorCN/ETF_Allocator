import numpy as np
import pandas as pd

from attribution.portfolios import BENCHMARK_WEIGHTS, benchmark_returns
from data.registry import get_data
from manager_selection.implement import slot_returns
from port_con.config import CALIBRATION_END
from port_con.portfolio import METHODS, final_weights, l1_weights

# Daily backtest of the port_con weights.
# Run from the repo root: python -m backtest.backtest [start]
#
# - Weights set at the close of a rebalance date earn returns from the next day.
# - Between rebalances the target weights are held (daily rebalanced), the same
#   simplification the attribution uses.
# - Returns are what we actually earn: managers (manager_selection) included.
# - Whatever the weights don't sum to earns the 3-month T-bill (leverage pays it).
# - Trading cost: COST_BPS per unit of one-way turnover, charged when new weights take effect.

COST_BPS = 5


def backtest(weights: pd.DataFrame, managers: bool = True) -> pd.DataFrame:
    """Daily gross return, net return (after trading cost) and turnover of `weights`.
    managers=False: every slot earns its passive ETF's return."""
    returns = slot_returns() if managers else get_data("prices").pct_change(fill_method=None)
    index = returns.index
    cash = benchmark_returns(index)["Cash"].fillna(0)

    held = weights.reindex(index.union(weights.index)).ffill().reindex(index).shift(1)
    held = held.loc[held.notna().any(axis=1)]
    rets = returns.loc[held.index, held.columns].fillna(0)
    gross = (held * rets).sum(axis=1) + (1 - held.sum(axis=1)) * cash.loc[held.index]

    turnover = weights.diff().abs().sum(axis=1).iloc[1:] / 2
    turnover = turnover.reindex(index.union(turnover.index)).shift(1).reindex(held.index).fillna(0)
    return pd.DataFrame({"gross": gross, "net": gross - turnover * COST_BPS / 1e4, "turnover": turnover})


def benchmark(index: pd.DatetimeIndex) -> pd.Series:
    """Daily return of the 70/20/10 benchmark (attribution.portfolios)."""
    bench = benchmark_returns(get_data("prices").index)
    return sum(bench[seg] * w for seg, w in BENCHMARK_WEIGHTS.items()).reindex(index)


def stats(r: pd.Series, bench: pd.Series, cash: pd.Series, turnover: pd.Series | None = None) -> dict:
    """Annualized performance numbers of daily returns `r`."""
    years = len(r) / 252
    growth = (1 + r).cumprod()
    active = r - bench
    out = {
        "Total return": growth.iloc[-1] - 1,
        "Ann. return": growth.iloc[-1] ** (1 / years) - 1,
        "Ann. vol": r.std() * np.sqrt(252),
        "Sharpe": (r - cash).mean() / r.std() * np.sqrt(252),
        "Max drawdown": (growth / growth.cummax() - 1).min(),
        "Tracking error": active.std() * np.sqrt(252),
        "Info ratio": active.mean() / active.std() * np.sqrt(252) if active.std() > 0 else np.nan,
    }
    if turnover is not None:
        out["Turnover / yr"] = turnover.sum() / years
    return out


def run(start: str) -> dict:
    """Backtest every port_con method from `start`: daily returns, weights and stats."""
    # First rebalance a week before `start` so weights are in place on `start`.
    first = (pd.Timestamp(start) - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    results = {m: backtest(final_weights(m, first)).loc[start:] for m in METHODS}
    index = next(iter(results.values())).index
    bench = benchmark(index)
    cash = benchmark_returns(index)["Cash"].fillna(0)

    def table(dates: pd.DatetimeIndex) -> pd.DataFrame:
        b, c = bench.loc[dates], cash.loc[dates]
        rows = {"Benchmark 70/20/10": stats(b, b, c)}
        for m, res in results.items():
            r = res.loc[dates]
            rows[f"{m} (gross)"] = stats(r["gross"], b, c, r["turnover"])
            rows[f"{m} (net {COST_BPS}bp)"] = stats(r["net"], b, c, r["turnover"])
        return pd.DataFrame(rows).T

    # In sample: before CALIBRATION_END, the data the tilt parameters were calibrated on.
    split = pd.Timestamp(CALIBRATION_END)
    periods = {"In sample": index[index < split], "Out of sample": index[index >= split]}
    return {
        "returns": pd.DataFrame({**{m: res["net"] for m, res in results.items()}, "benchmark": bench}),
        "gross": pd.DataFrame({m: res["gross"] for m, res in results.items()}),
        "sleeves": {m: l1_weights(m, first).loc[start:] for m in METHODS},
        "weights": {m: final_weights(m, first).loc[start:] for m in METHODS},
        "stats": table(index),
        "period_stats": {p: table(dates) for p, dates in periods.items() if len(dates) > 20},
    }


if __name__ == "__main__":
    import sys
    start = sys.argv[1] if len(sys.argv) > 1 else (pd.Timestamp.today() - pd.DateOffset(years=3)).strftime("%Y-%m-%d")
    res = run(start)
    pd.set_option("display.width", 200)
    print(res["stats"].round(4))
