import pandas as pd

# Slow signals for L1 (equity vs bonds). Signals only compute; the data is
# passed in by port_con (see port_con/config.py).


def equity_value(equity: pd.Series) -> pd.Series:
    """Equity value: negative 5-year return (long-term reversal).

    Equity that has run up a lot over 5 years is "expensive". Price-only
    proxy for value that works across asset classes.

    Reference: Asness, C., Moskowitz, T. & Pedersen, L. (2013). Value and
    Momentum Everywhere. Journal of Finance, 68(3), 929-985.
    """
    return -(equity / equity.shift(1260) - 1)


def bond_term_spread(ten_year: pd.Series, three_month: pd.Series) -> pd.Series:
    """Bond signal: 10-year yield minus 3-month T-bill yield (in %).

    A steeper curve predicts higher bond excess returns.

    References:
    - Fama, E. & Bliss, R. (1987). The Information in Long-Maturity Forward
      Rates. American Economic Review, 77(4), 680-692.
    - Campbell, J. & Shiller, R. (1991). Yield Spreads and Interest Rate
      Movements: A Bird's Eye View. Review of Economic Studies, 58(3), 495-514.
    """
    return (ten_year - three_month).dropna().rename("term_spread")
