import pandas as pd

from sector_rotation.low_risk import beta

# All functions take daily close prices (one column per ETF) and return a
# raw signal of the same shape. Normalize with utils.data_utils.normalize_signal.


def mom_12_1(prices: pd.DataFrame) -> pd.DataFrame:
    """12-month return, skipping the most recent month."""
    return prices.shift(21) / prices.shift(252) - 1


def mom_multi(prices: pd.DataFrame) -> pd.DataFrame:
    """Average of 1, 3, 6 and 12-month returns."""
    return sum(prices / prices.shift(n) - 1 for n in [21, 63, 126, 252]) / 4


def mom_ma(prices: pd.DataFrame, window: int = 200) -> pd.DataFrame:
    """Price relative to its moving average."""
    return prices / prices.rolling(window).mean() - 1


def mom_ewma(prices: pd.DataFrame, fast: int = 20, slow: int = 100) -> pd.DataFrame:
    """Fast minus slow EWMA, scaled by recent price volatility."""
    vol = prices.pct_change().rolling(63).std() * prices
    return (prices.ewm(span=fast).mean() - prices.ewm(span=slow).mean()) / vol


def mom_vol_adj(prices: pd.DataFrame) -> pd.DataFrame:
    """12-month return divided by 12-month annualized volatility.
    Reference: Barroso & Santa-Clara (2015), Momentum Has Its Moments, JFE (risk scaling)."""
    vol = prices.pct_change(fill_method=None).rolling(252).std() * 252 ** 0.5
    return (prices / prices.shift(252) - 1) / vol


def credit_vs_equity(hy: pd.Series, equity: pd.Series, n: int = 63) -> pd.Series:
    """HY return minus equity return over `n` days.

    Negative = credit is not confirming the equity move (risk appetite
    fading), a caution signal for equities. HY is a risk asset, so buying HY
    reflects risk-on / reaching for yield, not a lack of confidence in stocks.

    Note: the credit/equity divergence signal itself is mostly practitioner
    evidence; backtest before relying on it.

    References:
    - Becker, B. & Ivashina, V. (2015). Reaching for Yield in the Bond Market.
      Journal of Finance, 70(5), 1863-1902.
    - Frazzini, A. & Lamont, O. (2008). Dumb Money: Mutual Fund Flows and the
      Cross-Section of Stock Returns. Journal of Financial Economics, 88(2), 299-322.
    - Jostova, G., Nikolova, S., Philipov, A. & Stahel, C. (2013). Momentum in
      Corporate Bond Returns. Review of Financial Studies, 26(7), 1649-1693.
    """
    return (hy / hy.shift(n) - 1) - (equity / equity.shift(n) - 1)


def residual_mom(prices: pd.DataFrame, equity: pd.Series) -> pd.DataFrame:
    """12-1 month sum of residual returns vs the equity basket, over their volatility.

    Reference: Blitz, Huij & Martens (2011), Residual Momentum, JEF.
    """
    rets = prices.pct_change(fill_method=None)
    market = equity.reindex(prices.index).pct_change(fill_method=None)
    resid = rets - beta(rets, market).shift(1).mul(market, axis=0)
    window = resid.rolling(231, min_periods=200)
    return (window.sum() / window.std()).shift(21)


def ma_energy(prices: pd.DataFrame) -> pd.DataFrame:
    """Average distance from the 20/50/100/200-day moving averages, over 63-day volatility.

    Source: github.com/garroshub/Quant_Sector_Rotation_Strategy (practitioner).
    """
    dist = sum(prices / prices.rolling(n).mean() - 1 for n in [20, 50, 100, 200]) / 4
    return dist / prices.pct_change(fill_method=None).rolling(63).std()
