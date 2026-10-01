import os

import pandas as pd

from config import CAD_HEDGED, SIGNAL_PROXY, UNIVERSE
from data.yahoo import get_adj_close

_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "signal_prices.pkl")


def get_signal_prices(force: bool = False) -> pd.DataFrame:
    """Daily close prices in CAD for signal calculation, one column per UNIVERSE label.

    Assets in SIGNAL_PROXY use the US original (longer history), converted
    from USD to CAD unless the traded ETF is CAD-hedged. Cached to
    cache/signal_prices.pkl; force=True re-downloads.
    """
    if not force and os.path.exists(_CACHE_FILE):
        return pd.read_pickle(_CACHE_FILE)

    usdcad = get_adj_close("CAD=X")
    prices = {}
    for label, sym in UNIVERSE.items():
        if label in CAD_HEDGED:
            prices[label] = get_adj_close(SIGNAL_PROXY[label])
        elif label in SIGNAL_PROXY:
            px = get_adj_close(SIGNAL_PROXY[label])
            prices[label] = px * usdcad.reindex(px.index, method="ffill")
        else:
            prices[label] = get_adj_close(sym)
    prices = pd.DataFrame(prices).ffill()

    os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
    prices.to_pickle(_CACHE_FILE)
    return prices
