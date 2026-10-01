from functools import cache

import pandas as pd

from data.fred import get_fred
from data.sp500 import get_sp500_sector_weights
from data.universe import get_signal_prices
from data.yahoo import get_adj_close
from manager_selection.config import MANAGERS
from port_con.config import BONDS, EQUITY, HY, IG

# Data name -> function that loads it. Signals in port_con/config.py ask for
# data by these names.


def _basket(labels: list[str]) -> pd.Series:
    """Equal-weight, daily-rebalanced index of `labels`. Assets join once they have prices."""
    rets = get_signal_prices()[labels].pct_change(fill_method=None).mean(axis=1)
    return (1 + rets.dropna()).cumprod()


DATA = {
    "prices": lambda: get_signal_prices(),                  # all UNIVERSE assets
    "equity_prices": lambda: get_signal_prices()[EQUITY],   # equity assets, one column each
    "equity_basket": lambda: _basket(EQUITY),
    "bond_basket": lambda: _basket(BONDS),
    "hy": lambda: get_signal_prices()[HY],
    "ig": lambda: get_signal_prices()[IG],
    "us10y": lambda: get_adj_close("^TNX"),                 # US 10-year yield, %
    "us3m": lambda: get_adj_close("^IRX"),                  # US 3-month T-bill yield, %
    "canary_prices": lambda: pd.DataFrame({t: get_adj_close(t) for t in ["EEM", "AGG"]}),  # DAA canary assets, USD
    "vix": lambda: get_adj_close("^VIX"),                   # VIX index, % (annualized vol)
    "baa_spread": lambda: get_fred("BAA10Y", lag_days=1),   # Moody's Baa yield minus 10-year Treasury, %
    "jobless_claims": lambda: get_fred("ICSA", lag_days=7), # weekly initial claims, published the next Thursday
    "sp500_sector_weights": get_sp500_sector_weights,       # GICS sector -> current S&P 500 weight
    "manager_prices": lambda: pd.DataFrame({slot: get_adj_close(m["symbol"]) for slot, m in MANAGERS.items()}),
    "manager_unlevered_prices": lambda: pd.DataFrame({slot: get_adj_close(m["unlevered"]) for slot, m in MANAGERS.items()}),
}


@cache
def get_data(name: str):
    """Load a dataset by name (each one is loaded once per run)."""
    return DATA[name]()
