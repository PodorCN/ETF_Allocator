import pandas as pd

# All functions take daily close prices (one column per ETF) and return a
# raw signal of the same shape. Positive = more attractive.


def rate_sensitivity(prices: pd.DataFrame, ten_year: pd.Series, beta_window: int = 756, n: int = 63) -> pd.DataFrame:
    """Sector beta to 10-year yield changes x the yield change over `n` days.

    Favors sectors that benefit from the current rate move (e.g. financials
    when yields rise, utilities / real estate when yields fall). A simple
    stand-in for "macro change x sector sensitivity" until PMI data is added.

    Reference: Chen, N., Roll, R. & Ross, S. (1986). Economic Forces and the
    Stock Market. Journal of Business, 59(3), 383-403.
    """
    ten_year = ten_year.reindex(prices.index, method="ffill")
    rets = prices.pct_change()
    dy = ten_year.diff()
    beta = rets.rolling(beta_window).cov(dy).div(dy.rolling(beta_window).var(), axis=0)
    return beta.mul(ten_year - ten_year.shift(n), axis=0)
