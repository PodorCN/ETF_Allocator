import pandas as pd

# All functions take daily close prices (one column per ETF) and return a
# raw signal of the same shape. Positive = more attractive.


def long_term_reversal(prices: pd.DataFrame) -> pd.DataFrame:
    """Negative 5-year return: sectors that ran up the most are "expensive".

    Price-only value proxy; compare each sector with its own history.

    Reference: Asness, C., Moskowitz, T. & Pedersen, L. (2013). Value and
    Momentum Everywhere. Journal of Finance, 68(3), 929-985.
    """
    return -(prices / prices.shift(1260) - 1)
