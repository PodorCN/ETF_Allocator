import pandas as pd

# All functions take daily close prices (one column per ETF) and return a
# raw signal of the same shape. Positive = more attractive.


def high_52w(prices: pd.DataFrame) -> pd.DataFrame:
    """Price divided by its 52-week high.

    Investors anchor on the 52-week high and under-react to news near it,
    so assets close to their high tend to keep outperforming.

    Reference: George, T. & Hwang, C. (2004). The 52-Week High and Momentum
    Investing. Journal of Finance, 59(5), 2145-2176.
    """
    return prices / prices.rolling(252).max()
