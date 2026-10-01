import numpy as np
import pandas as pd

from data.registry import get_data
from port_con import black_litterman
from port_con.config import BASELINE_WEIGHTS, CALIBRATION_END, EQUITY, L1_SIGNALS, L2_SIGNALS
from port_con.l1 import get_l1_signals, get_l1_values
from port_con.l2 import get_l2_signals, get_l2_values
from port_con.portfolio import get_baseline, get_cov

# Calibrates the tilt parameters from the signals' IC, using only data
# before `end` (so a backtest after `end` is out of sample).
# Run from the repo root: python -m port_con.calibrate
#
# 1. IC = rank correlation of a signal with the next HORIZON days' return,
#    sampled weekly.
#    L1: SAA value / TAA value vs equity basket minus bond basket return.
#    L2: L2 value vs sector returns, across sectors on each date, averaged.
# 2. Black-Litterman IC parameters = the measured ICs (negative -> 0, no view).
#
# Paste the printed values into port_con/config.py.

HORIZON = 21  # trading days of forward return


def rank_corr(a: pd.Series, b: pd.Series) -> float:
    """Spearman rank correlation (without scipy)."""
    return a.rank().corr(b.rank())


def forward_return(prices: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    return prices.shift(-HORIZON) / prices - 1


def weekly_dates(index: pd.DatetimeIndex, start=None, end=None) -> pd.DatetimeIndex:
    """Last trading day of each week from `start` whose forward return window
    ends before `end` (default: the end of the data)."""
    before_end = index[index < pd.Timestamp(end)] if end else index
    last_ok = before_end[-HORIZON - 1]
    dates = pd.Series(index, index=index).groupby(index.to_period("W")).last()
    dates = dates[dates <= last_ok]
    return pd.DatetimeIndex(dates[dates >= pd.Timestamp(start)] if start else dates)


def weekly_before(index: pd.DatetimeIndex, end) -> pd.DatetimeIndex:
    return weekly_dates(index, end=end)


def _cross_sectional_ic(signal: pd.DataFrame, fwd: pd.DataFrame, dates: pd.DatetimeIndex) -> float:
    """Average across dates of the rank correlation across assets."""
    ics = []
    for date in dates:
        df = pd.DataFrame({"signal": signal.loc[date], "fwd": fwd.loc[date]}).dropna()
        if len(df) >= 5 and df["signal"].std() > 0:
            ics.append(rank_corr(df["signal"], df["fwd"]))
    return float(np.mean(ics)) if ics else np.nan


def signal_ics(start=None, end=None) -> pd.Series:
    """IC of every single L1 and L2 signal on weekly dates in [start, end).
    L1 signals are signed by their side, so > 0 always means the signal helped."""
    index = get_data("prices").index
    dates = weekly_dates(index, start, end)
    out = {}

    l1 = get_l1_signals()
    fwd = forward_return(get_data("equity_basket")) - forward_return(get_data("bond_basket"))
    for layer, sigs in L1_SIGNALS.items():
        for name, cfg in sigs.items():
            side = 1 if cfg["side"] == "equity" else -1
            df = pd.DataFrame({"signal": l1.loc[dates, name] * side, "fwd": fwd.reindex(dates)}).dropna()
            df = df[df["signal"] != 0]
            out[f"L1 {layer.upper()}: {name}"] = rank_corr(df["signal"], df["fwd"])

    l2 = get_l2_signals()
    fwd2 = forward_return(get_data("prices")[EQUITY])
    for name in L2_SIGNALS:
        out[f"L2: {name}"] = _cross_sectional_ic(l2[name], fwd2, dates)
    return pd.Series(out)


def l1_ic(end) -> dict[str, float]:
    values = get_l1_values()
    fwd = forward_return(get_data("equity_basket")) - forward_return(get_data("bond_basket"))
    dates = weekly_before(values.index, end)
    out = {}
    for layer in ["saa", "taa"]:
        df = pd.DataFrame({"signal": values.loc[dates, layer], "fwd": fwd.reindex(dates)}).dropna()
        df = df[df["signal"] != 0]  # before the signal has history
        out[layer] = rank_corr(df["signal"], df["fwd"])
    return out


def l2_ic(end) -> float:
    values = get_l2_values()
    fwd = forward_return(get_data("prices")[EQUITY])
    return _cross_sectional_ic(values, fwd, weekly_before(values.index, end))


def calibrate(end) -> dict[str, float]:
    ic1, ic2 = l1_ic(end), l2_ic(end)
    bl = {"BL_IC_SAA": max(ic1["saa"], 0.0), "BL_IC_TAA": max(ic1["taa"], 0.0), "BL_IC_L2": max(ic2, 0.0)}
    return {"IC_SAA": ic1["saa"], "IC_TAA": ic1["taa"], "IC_L2": ic2, **bl}


if __name__ == "__main__":
    import sys
    end = sys.argv[1] if len(sys.argv) > 1 else CALIBRATION_END
    print(f"Calibrating on data before {end}")
    for k, v in calibrate(end).items():
        print(f"{k} = {v:.4f}")
