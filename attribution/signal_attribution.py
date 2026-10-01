import pandas as pd

from attribution.brinson import carino_factors
from backtest.backtest import backtest, benchmark
from manager_selection.implement import leverage_returns
from port_con.calibrate import signal_ics
from port_con.config import L1_SIGNALS, L2_SIGNALS
from port_con.l1 import get_l1_signals, get_l1_values
from port_con.l2 import get_l2_signals, get_l2_values
from port_con.portfolio import build_history

# Signal attribution: how much of the active return each signal added.
# Run from the repo root: python -m attribution.signal_attribution [start]
#
# The portfolio is rebuilt with one signal switched on at a time (all others
# off). A signal's contribution = that portfolio's return - the baseline
# portfolio's (all signals off). The rest of the active return is split into:
#   Baseline vs benchmark   baseline portfolio - benchmark (e.g. sector ETFs vs SPY)
#   Sizing                  leverage from the average L1 signal (GAMMA)
#   Interaction             signals together - sum of the signals one at a time
#   Manager                 holding the managers instead of the passive ETFs (region,
#                           stock picking, fees), excluding their leverage
#   Manager leverage        (leverage - 1) x (unlevered return - cash) of the managers
#   Trading cost
# Daily contributions are Carino-linked, so they add up to the compounded
# active return of the real (net, with managers) portfolio over the window.


def _weights(method: str, start: str, l1: pd.DataFrame, l2: pd.DataFrame) -> pd.DataFrame:
    first = (pd.Timestamp(start) - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    return build_history(method, first, l1, l2)[1]


def _returns(method: str, start: str, l1: pd.DataFrame, l2: pd.DataFrame, managers: bool = False) -> pd.DataFrame:
    return backtest(_weights(method, start, l1, l2), managers=managers).loc[start:]


def _leverage(weights: pd.DataFrame, index: pd.DatetimeIndex) -> pd.Series:
    """Daily return from the managers' leverage, with the weights held as in the backtest."""
    lev = leverage_returns()
    held = weights.reindex(lev.index.union(weights.index)).ffill().reindex(lev.index).shift(1)
    return (held * lev[weights.columns]).sum(axis=1).reindex(index)


def signal_attribution(method: str, start: str) -> dict:
    """Daily contribution of each component to the active return of `method` from `start`."""
    l1_sig, l2_sig = get_l1_signals(), get_l2_signals()
    l1_full, l2_full = get_l1_values(), get_l2_values()
    l1_off, l2_off = l1_full * 0, l2_full * 0

    base = _returns(method, start, l1_off, l2_off)["gross"]
    full = _returns(method, start, l1_full, l2_full)["gross"]
    real = _returns(method, start, l1_full, l2_full, managers=True)
    bench = benchmark(real.index)

    parts = {"Baseline vs benchmark": base - bench}
    for layer, sigs in L1_SIGNALS.items():
        for name in sigs:
            l1 = get_l1_values(l1_sig, keep=[name]).assign(avg_signal=0.0)
            parts[f"L1 {layer.upper()}: {name}"] = _returns(method, start, l1, l2_off)["gross"] - base
    for name in L2_SIGNALS:
        l2 = get_l2_values(l2_sig, keep=[name])
        parts[f"L2: {name}"] = _returns(method, start, l1_off, l2)["gross"] - base
    sizing = l1_off.assign(avg_signal=l1_full["avg_signal"])
    parts["Sizing (leverage)"] = _returns(method, start, sizing, l2_off)["gross"] - base
    signal_sum = sum(v for k, v in parts.items() if k != "Baseline vs benchmark")
    parts["Interaction"] = full - base - signal_sum
    lev = _leverage(_weights(method, start, l1_full, l2_full), real.index)
    parts["Manager"] = real["gross"] - full - lev
    parts["Manager leverage"] = lev
    parts["Trading cost"] = real["net"] - real["gross"]

    daily = pd.DataFrame(parts).mul(carino_factors(real["net"], bench), axis=0)
    return {
        "daily": daily,
        "total": daily.sum(),
        "active": (1 + real["net"]).prod() - (1 + bench).prod(),
    }


def summary(start: str, methods=("black_litterman", "te_budget")) -> dict:
    """Contribution table for each method plus the signals' IC before and during the window."""
    results = {m: signal_attribution(m, start) for m in methods}
    table = pd.DataFrame({m: r["total"] for m, r in results.items()})
    table.loc["Total active"] = [r["active"] for r in results.values()]
    ic = pd.DataFrame({
        "IC before": signal_ics(end=start),
        "IC in window": signal_ics(start=start),
    })
    return {"results": results, "table": table, "ic": ic}


if __name__ == "__main__":
    import sys
    start = sys.argv[1] if len(sys.argv) > 1 else (pd.Timestamp.today() - pd.DateOffset(years=3)).strftime("%Y-%m-%d")
    s = summary(start)
    pd.set_option("display.width", 200)
    print((s["table"] * 100).round(2).astype(str) + "%")
    print(s["ic"].round(3))
