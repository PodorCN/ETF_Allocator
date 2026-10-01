from functools import cache

import pandas as pd

from data.registry import get_data
from port_con.config import L1_ON, L1_SIGNALS, NORMALIZE_WINDOW
from utils.data_utils import normalize_signal

# Run from the repo root: python -m port_con.l1

_SIDE = {"equity": 1, "bond": -1}


@cache
def get_l1_signals() -> pd.DataFrame:
    """Every L1 signal in the config, normalized (missing = 0). One column per signal."""
    index = get_data("prices").index
    out = {}
    for layer, signals in L1_SIGNALS.items():                            # 1. which signals the config lists
        for name, cfg in signals.items():
            data = {arg: get_data(d) for arg, d in cfg["data"].items()}  # 2. get the data each one needs
            raw = cfg["func"](**data)                                    # 3. give the data to the signal
            raw = raw.reindex(raw.index.union(index)).ffill().reindex(index)  # line up trading calendars
            out[name] = normalize_signal(raw, window=NORMALIZE_WINDOW, center=cfg.get("center", True)).fillna(0)  # 4.
    return pd.DataFrame(out)


def get_l1_values(signals: pd.DataFrame | None = None, keep: list[str] | None = None) -> pd.DataFrame:
    """SAA value and TAA value on every date. > 0 = tilt to equity, < 0 = tilt to bonds.

    5. Each layer's value = sum of its signals x weight x side.
    Also returns avg_signal: the plain average of all L1 signals (each one
    positive = good for its own asset), used for the target vol in portfolio.py.
    keep: only these signals count towards SAA / TAA (the others count as 0);
    used by the signal attribution.
    """
    if signals is None:
        signals = get_l1_signals()
    values = pd.DataFrame(0.0, index=signals.index, columns=["saa", "taa"])
    if not L1_ON:
        return values.assign(avg_signal=0.0)
    for layer, sigs in L1_SIGNALS.items():
        for name, cfg in sigs.items():
            if keep is None or name in keep:
                values[layer] += signals[name] * cfg["weight"] * _SIDE[cfg["side"]]
    values["avg_signal"] = signals.mean(axis=1)
    return values


if __name__ == "__main__":
    print(get_l1_values().tail().round(2))
