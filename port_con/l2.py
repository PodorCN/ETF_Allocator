from functools import cache

import pandas as pd

from data.registry import get_data
from port_con.config import L2_ON, L2_SIGNALS, NORMALIZE_WINDOW
from utils.data_utils import cross_sectional_zscore, normalize_signal

# Run from the repo root: python -m port_con.l2


@cache
def get_l2_signals() -> dict[str, pd.DataFrame]:
    """Every L2 signal in the config, normalized: name -> dates x equity assets (NaN = no value)."""
    index = get_data("prices").index
    out = {}
    for name, cfg in L2_SIGNALS.items():                                 # 1. which signals the config lists
        data = {arg: get_data(d) for arg, d in cfg["data"].items()}      # 2. get the data each one needs
        raw = cfg["func"](**data).reindex(index)                         # 3. give the data to the signal
        if cfg["compare"] == "cross":                                    # 4. normalize
            out[name] = cross_sectional_zscore(raw)
        else:
            out[name] = normalize_signal(raw, window=NORMALIZE_WINDOW)
    return out


def get_l2_values(signals: dict[str, pd.DataFrame] | None = None, keep: list[str] | None = None) -> pd.DataFrame:
    """L2 value per equity asset on every date (dates x assets). > 0 = overweight.

    5. Weighted average of the signals available on each date; no signal = 0.
    keep: only these signals count in the numerator (the average still divides
    by all available weights); used by the signal attribution.
    """
    if signals is None:
        signals = get_l2_signals()
    if not L2_ON:
        return pd.DataFrame(0.0, index=get_data("prices").index, columns=next(iter(signals.values())).columns)
    total = 0
    weight_sum = 0
    for name, cfg in L2_SIGNALS.items():
        z = signals[name]
        if keep is None or name in keep:
            total = total + z.fillna(0) * cfg["weight"]
        weight_sum = weight_sum + z.notna() * cfg["weight"]
    return (total / weight_sum).fillna(0)


if __name__ == "__main__":
    print(get_l2_values().tail(1).T.round(2))
