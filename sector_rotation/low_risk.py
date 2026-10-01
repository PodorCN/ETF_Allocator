import pandas as pd

# Low-risk sector signals. Take daily close prices (one column per ETF) and
# return a raw signal of the same shape. Positive = more attractive.


def beta(rets: pd.DataFrame, market: pd.Series, window: int = 756) -> pd.DataFrame:
    """Rolling beta of each column of `rets` to `market` (at least half a window of data)."""
    return rets.rolling(window, min_periods=window // 2).cov(market).div(
        market.rolling(window, min_periods=window // 2).var(), axis=0)


def low_beta(prices: pd.DataFrame, equity: pd.Series) -> pd.DataFrame:
    """Negative 3-year beta to the equity basket.

    Reference: Frazzini & Pedersen (2014), Betting Against Beta, JFE.
    """
    rets = prices.pct_change(fill_method=None)
    return -beta(rets, equity.reindex(prices.index).pct_change(fill_method=None))
