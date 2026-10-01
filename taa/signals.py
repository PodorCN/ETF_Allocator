import pandas as pd

# Fast signals for L1 (equity vs bonds). Normalize with
# utils.data_utils.normalize_signal before use.


def equity_credit_appetite(hy: pd.Series, ig: pd.Series, n: int = 63) -> pd.Series:
    """Equity signal: HY return minus IG return over `n` days.

    HY beating IG means credit spreads are tightening (risk-on), which is
    good for equities. Both legs are credit, so rate moves mostly cancel.

    Reference: Gilchrist, S. & Zakrajsek, E. (2012). Credit Spreads and
    Business Cycle Fluctuations. American Economic Review, 102(4), 1692-1720.
    """
    return (hy / hy.shift(n) - 1) - (ig / ig.shift(n) - 1)


def bond_tsmom(bonds: pd.Series) -> pd.Series:
    """Bond signal: 12-month return of the bond portfolio (time-series momentum).

    Reference: Moskowitz, T., Ooi, Y. & Pedersen, L. (2012). Time Series
    Momentum. Journal of Financial Economics, 104(2), 228-250.
    """
    return bonds / bonds.shift(252) - 1
