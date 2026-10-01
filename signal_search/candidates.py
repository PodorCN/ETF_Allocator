import numpy as np
import pandas as pd

from sector_rotation.low_risk import low_beta
from sector_rotation.momentum import ma_energy, residual_mom
from sector_rotation.momentum import mom_vol_adj as ind_mom_risk_adj

# Candidate signals, fixed before testing (research_notes/signal_search_protocol.md).
# Same contract as the live signals: data is passed in, a raw signal comes out.
# L1: one Series, high = favour equity over bonds.
# L2: dates x sectors, high = overweight.


# ---- L1: equity vs bonds ----

def eq_abs_mom(equity: pd.Series, three_month: pd.Series) -> pd.Series:
    """Equity 12-month return minus the 3-month T-bill yield (absolute momentum).

    References: Moskowitz, Ooi & Pedersen (2012), Time Series Momentum, JFE;
    Antonacci (2013), Absolute Momentum: A Simple Rule-Based Strategy.
    """
    rf = three_month.reindex(equity.index, method="ffill") / 100
    return (equity / equity.shift(252) - 1) - rf


def eq_trend(equity: pd.Series) -> pd.Series:
    """Equity price relative to its 210-day (10-month) moving average.

    Reference: Faber (2007), A Quantitative Approach to Tactical Asset Allocation.
    """
    return equity / equity.rolling(210).mean() - 1


def eq_bond_mom(equity: pd.Series, bonds: pd.Series) -> pd.Series:
    """Equity 12-month return minus bond 12-month return (cross-asset momentum).

    Reference: Asness, Moskowitz & Pedersen (2013), Value and Momentum Everywhere, JF.
    """
    bonds = bonds.reindex(equity.index, method="ffill")
    return (equity / equity.shift(252) - 1) - (bonds / bonds.shift(252) - 1)


def vrp(equity: pd.Series, vix: pd.Series) -> pd.Series:
    """Variance risk premium: implied variance (VIX^2) minus 21-day realized variance.

    Reference: Bollerslev, Tauchen & Zhou (2009), Expected Stock Returns and
    Variance Risk Premia, RFS.
    """
    realized = equity.pct_change().rolling(21).var() * 252
    implied = (vix.reindex(equity.index, method="ffill") / 100) ** 2
    return implied - realized


def low_realized_vol(equity: pd.Series) -> pd.Series:
    """Negative 21-day realized volatility of equity (volatility-managed exposure).

    Reference: Moreira & Muir (2017), Volatility-Managed Portfolios, JF.
    """
    return -equity.pct_change().rolling(21).std() * np.sqrt(252)


def credit_spread_level(spread: pd.Series) -> pd.Series:
    """Baa minus 10-year Treasury yield: a high default spread means a high
    expected equity premium.

    References: Keim & Stambaugh (1986), Predicting Returns in the Stock and
    Bond Markets, JFE; Fama & French (1989), Business Conditions and Expected
    Returns on Stocks and Bonds, JFE.
    """
    return spread


def credit_spread_change(spread: pd.Series) -> pd.Series:
    """Negative 63-day change of the Baa spread (widening = risk-off).

    Reference: Gilchrist & Zakrajsek (2012), Credit Spreads and Business Cycle
    Fluctuations, AER.
    """
    daily = spread.asfreq("D").ffill()
    return -(daily - daily.shift(91))


def claims_change(claims: pd.Series) -> pd.Series:
    """Negative year-on-year change of 4-week average initial jobless claims
    (rising claims lead recessions).

    Reference: Neftci (1982), Optimal Prediction of Cyclical Downturns, JEDC.
    """
    avg = claims.rolling(4).mean()
    return -(avg / avg.shift(52) - 1)


def halloween(equity: pd.Series) -> pd.Series:
    """+1 from November to April, -1 from May to October ("Sell in May").

    Reference: Bouman & Jacobsen (2002), The Halloween Indicator, AER.
    """
    month = equity.index.month
    return pd.Series(np.where((month >= 11) | (month <= 4), 1.0, -1.0), index=equity.index)


# ---- L2: sector rotation ----

def ind_mom_6m(prices: pd.DataFrame) -> pd.DataFrame:
    """6-month return. Reference: Moskowitz & Grinblatt (1999), Do Industries
    Explain Momentum?, JF."""
    return prices / prices.shift(126) - 1


def ind_mom_1m(prices: pd.DataFrame) -> pd.DataFrame:
    """1-month return (industry, unlike single stocks, continues short term).
    Reference: Moskowitz & Grinblatt (1999), JF."""
    return prices / prices.shift(21) - 1


def low_vol(prices: pd.DataFrame) -> pd.DataFrame:
    """Negative 1-year volatility.

    Reference: Baker, Bradley & Wurgler (2011), Benchmarks as Limits to
    Arbitrage: Understanding the Low-Volatility Anomaly, FAJ.
    """
    return -prices.pct_change(fill_method=None).rolling(252, min_periods=200).std()


def seasonality(prices: pd.DataFrame, years: int = 10, min_years: int = 5) -> pd.DataFrame:
    """Average return of the coming calendar month (the month in the middle of the
    next 21 trading days) over the previous `years` years.

    References: Heston & Sadka (2008), Seasonality in the Cross-Section of Stock
    Returns, JFE; Keloharju, Linnainmaa & Nyberg (2016), Return Seasonalities, JF.
    """
    monthly = prices.resample("ME").last().pct_change(fill_method=None)
    by_month = {m: monthly[monthly.index.month == m] for m in range(1, 13)}
    target = prices.index + pd.Timedelta(days=15)
    out = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    for (year, month), dates in pd.Series(prices.index, index=prices.index).groupby(
            [target.year, target.month]):
        past = by_month[month]
        past = past[(past.index.year < year) & (past.index.year >= year - years)]
        avg = past.mean().where(past.count() >= min_years)
        out.loc[dates.values] = avg.values
    return out


# ---- Round 2: common GitHub TAA / sector rotation signals ----

def _mom_13612w(prices):
    """Keller's weighted momentum: 12*r1m + 4*r3m + 2*r6m + r12m."""
    return sum(w * (prices / prices.shift(n) - 1) for w, n in [(12, 21), (4, 63), (2, 126), (1, 252)])


def eq_mom_13612w(equity: pd.Series) -> pd.Series:
    """Equity 13612W momentum.

    Reference: Keller & Keuning (2017), Breadth Momentum and Vigilant Asset
    Allocation (VAA), SSRN 3002624.
    """
    return _mom_13612w(equity)


def canary(canaries: pd.DataFrame) -> pd.Series:
    """Number of canary assets (EEM, AGG) with positive 13612W momentum (0, 1 or 2).

    Reference: Keller & Keuning (2018), Breadth Momentum and the Canary
    Universe: Defensive Asset Allocation (DAA), SSRN 3212862.
    """
    mom = _mom_13612w(canaries)
    return (mom > 0).sum(axis=1).where(mom.notna().all(axis=1))


def gem_multi(equity: pd.Series, bonds: pd.Series) -> pd.Series:
    """Share of 6..12-month lookbacks where equity beat bonds (Diversified GEM).

    Reference: Antonacci (2014), Dual Momentum Investing, McGraw-Hill.
    """
    bonds = bonds.reindex(equity.index, method="ffill")
    wins = [((equity / equity.shift(21 * m)) > (bonds / bonds.shift(21 * m))).where(equity.shift(21 * m).notna())
            for m in range(6, 13)]
    return pd.concat(wins, axis=1).mean(axis=1, skipna=False)


def _absorption_ratio(rets: pd.DataFrame, n_pc: int = 2) -> float:
    eig = np.linalg.eigvalsh(rets.cov().values)
    return eig[-n_pc:].sum() / eig.sum()


def absorption_shift(prices: pd.DataFrame, window: int = 500) -> pd.Series:
    """Negative standardized shift of the absorption ratio: (15-day mean AR minus
    1-year mean AR) / 1-year std of AR. A rising AR = fragile market = risk-off.

    Reference: Kritzman, Li, Page & Rigobon (2011), Principal Components as a
    Measure of Systemic Risk, Journal of Portfolio Management.
    """
    rets = prices.pct_change(fill_method=None)
    dates = rets.index[window:]
    ar = pd.Series([_absorption_ratio(rets.iloc[i - window:i].dropna(axis=1, thresh=window // 2).dropna())
                    for i in range(window, len(rets))], index=dates)
    return -(ar.rolling(15).mean() - ar.rolling(252).mean()) / ar.rolling(252).std()


def low_turbulence(prices: pd.DataFrame, window: int = 756) -> pd.Series:
    """Negative 21-day average financial turbulence: the Mahalanobis distance of
    each day's returns from the past `window` days' mean and covariance.

    Reference: Kritzman & Li (2010), Skulls, Financial Turbulence, and Risk
    Management, Financial Analysts Journal.
    """
    rets = prices.pct_change(fill_method=None)
    out = pd.Series(np.nan, index=rets.index)
    for i in range(window, len(rets), 5):  # refit weekly; the distance uses each day's own returns
        past = rets.iloc[i - window:i].dropna(axis=1, thresh=window // 2).dropna()
        cols = past.columns
        mu, inv = past.mean().values, np.linalg.pinv(past.cov().values)
        block = rets.iloc[i:i + 5][cols].fillna(0).values - mu
        out.iloc[i:i + 5] = np.einsum("ij,jk,ik->i", block, inv, block) / len(cols)
    return -out.rolling(21).mean()


def ind_mom_13612w(prices: pd.DataFrame) -> pd.DataFrame:
    """Each sector's 13612W momentum. Reference: Keller & Keuning (2017), VAA."""
    return _mom_13612w(prices)


def protective_mom(prices: pd.DataFrame) -> pd.DataFrame:
    """Average 1/3/6/12-month return x (1 - 1-year correlation with the equal-weight sectors).

    Reference: Keller & Keuning (2016), Protective Asset Allocation /
    Generalized Protective Momentum, SSRN 2759734.
    """
    rets = prices.pct_change(fill_method=None)
    avg_ret = sum(prices / prices.shift(n) - 1 for n in [21, 63, 126, 252]) / 4
    corr = rets.rolling(252, min_periods=200).corr(rets.mean(axis=1))
    return avg_ret * (1 - corr)
