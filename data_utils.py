import os
import threading
import time

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

from config import CACHE_TTL_SECONDS, HISTORY_PERIOD, TICKERS

_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
_CACHE_FILE = os.path.join(_CACHE_DIR, "price_data.pkl")

_cache = {"data": None, "ts": 0.0}
_lock = threading.Lock()

# Set by fetch_price_data on every call so the UI can show data freshness /
# whether we're currently showing stale disk-cached data (e.g. offline).
status = {"as_of": None, "fetched_at": None, "stale": False, "error": None}


def _load_disk_cache() -> pd.DataFrame | None:
    if not os.path.exists(_CACHE_FILE):
        return None
    try:
        df = pd.read_pickle(_CACHE_FILE)
        return df if not df.empty else None
    except Exception:
        return None


def _save_disk_cache(df: pd.DataFrame) -> None:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    df.to_pickle(_CACHE_FILE)


def _set_status(df: pd.DataFrame, stale: bool, error: str | None = None) -> None:
    status["as_of"] = df.index[-1] if not df.empty else None
    status["fetched_at"] = pd.Timestamp.now()
    status["stale"] = stale
    status["error"] = error


def fetch_price_data(force: bool = False) -> pd.DataFrame:
    """Total-return daily close prices for all configured tickers.

    The fetch uses auto_adjust=True, which back-adjusts every close for
    splits and dividends - so each column is a total return index and
    pct_change() on it is the full daily total return (price + dividends
    reinvested). All downstream return / covariance / correlation math
    therefore operates on total returns, not price-only returns.

    Layered caching so the dashboard opens fast and survives flaky/no
    internet:
    1. In-process cache, reused for CACHE_TTL_SECONDS (covers bursts of
       callback triggers within one running session).
    2. On-disk cache (cache/price_data.pkl), reused across app restarts
       while still within CACHE_TTL_SECONDS of when it was written.
    3. Yahoo Finance network fetch, written back to both caches on success.
    4. If the network fetch fails, fall back to the on-disk cache no matter
       how old it is, so the dashboard still renders (marked stale).
    """
    with _lock:
        now = time.time()
        if not force and _cache["data"] is not None and now - _cache["ts"] < CACHE_TTL_SECONDS:
            return _cache["data"]

        if not force and os.path.exists(_CACHE_FILE):
            age = now - os.path.getmtime(_CACHE_FILE)
            if age < CACHE_TTL_SECONDS:
                disk_df = _load_disk_cache()
                if disk_df is not None:
                    _cache["data"] = disk_df
                    _cache["ts"] = now
                    _set_status(disk_df, stale=False)
                    return disk_df

        try:
            symbols = list(TICKERS.values())
            raw = yf.download(
                symbols,
                period=HISTORY_PERIOD,
                interval="1d",
                auto_adjust=True,  # dividend/split-adjusted closes -> total return
                actions=False,
                progress=False,
                group_by="ticker",
                threads=True,
            )

            closes = {}
            for label, sym in TICKERS.items():
                try:
                    if isinstance(raw.columns, pd.MultiIndex):
                        series = raw[sym]["Close"]
                    else:
                        # yfinance collapses to a flat frame when only one
                        # symbol was requested.
                        series = raw["Close"]
                    closes[label] = series.dropna()
                except (KeyError, IndexError):
                    continue

            df = pd.DataFrame(closes).sort_index()
            df = df.dropna(how="all")

            if df.empty:
                raise RuntimeError("No price data returned from Yahoo Finance.")

            _save_disk_cache(df)
            _cache["data"] = df
            _cache["ts"] = now
            _set_status(df, stale=False)
            return df

        except Exception as e:
            disk_df = _load_disk_cache()
            if disk_df is not None:
                _cache["data"] = disk_df
                _cache["ts"] = now
                _set_status(disk_df, stale=True, error=str(e))
                return disk_df
            _set_status(pd.DataFrame(), stale=True, error=str(e))
            raise RuntimeError(
                f"{e} (no on-disk cache available yet to fall back to)"
            ) from e


def _return_since(series: pd.Series, cutoff: pd.Timestamp) -> float:
    """% return from the last observation before `cutoff` to the latest one.

    Using the prior close (not the first close on/after cutoff) is what
    makes this match the conventional MTD/QTD definition.
    """
    series = series.dropna()
    prior = series[series.index < cutoff]
    after = series[series.index >= cutoff]
    if len(after) == 0:
        return np.nan
    base = prior.iloc[-1] if len(prior) > 0 else after.iloc[0]
    if base == 0 or pd.isna(base):
        return np.nan
    return (after.iloc[-1] / base - 1) * 100


def _mtd_qtd_anchors(last_date: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    month_start = pd.Timestamp(year=last_date.year, month=last_date.month, day=1)
    quarter_month = (last_date.month - 1) // 3 * 3 + 1
    quarter_start = pd.Timestamp(year=last_date.year, month=quarter_month, day=1)
    return month_start, quarter_start


def compute_summary_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Per-ETF table: last close, daily / MTD / QTD % return."""
    if df.empty:
        return pd.DataFrame(columns=["ETF", "Last Close", "Daily %", "MTD %", "QTD %"])

    last_date = df.index[-1]
    month_start, quarter_start = _mtd_qtd_anchors(last_date)

    rows = []
    for col in df.columns:
        series = df[col].dropna()
        if series.empty:
            continue
        daily = (
            (series.iloc[-1] / series.iloc[-2] - 1) * 100
            if len(series) >= 2
            else np.nan
        )
        rows.append(
            {
                "ETF": col,
                "Last Close": round(float(series.iloc[-1]), 2),
                "Daily %": round(daily, 2) if not np.isnan(daily) else np.nan,
                "MTD %": round(_return_since(series, month_start), 2),
                "QTD %": round(_return_since(series, quarter_start), 2),
            }
        )
    return pd.DataFrame(rows)


def compute_portfolio_series(df: pd.DataFrame, weights: dict) -> tuple[pd.Series, pd.Series]:
    """Daily portfolio return series + cumulative index (starts at 1.0).

    Assumes weights are held constant (rebalanced daily). Assets without
    data on a given day (e.g. ETFs listed later than the window start -
    the BMO SPDR sector suite only exists since Feb 2025) are excluded
    that day and the remaining weights renormalised to 1, so the portfolio
    stays fully invested instead of silently dragging a cash position
    during an asset's listing gap.
    """
    rets = df.pct_change()
    w = pd.Series(weights, dtype=float).reindex(df.columns).fillna(0.0)
    has_data = rets.notna() & w.gt(0)
    w_effective = has_data.mul(w, axis=1).sum(axis=1)
    raw = rets.mul(w, axis=1).sum(axis=1, min_count=1)
    port_ret = raw / w_effective.where(w_effective > 0)
    port_ret = port_ret.fillna(0.0)
    port_index = (1 + port_ret).cumprod()
    return port_ret, port_index


def compute_portfolio_summary(df: pd.DataFrame, weights: dict) -> tuple[dict, pd.Series]:
    port_ret, port_index = compute_portfolio_series(df, weights)
    if port_index.empty:
        return {"Daily %": np.nan, "MTD %": np.nan, "QTD %": np.nan}, port_index

    last_date = df.index[-1]
    month_start, quarter_start = _mtd_qtd_anchors(last_date)

    daily = port_ret.iloc[-1] * 100 if len(port_ret) else np.nan
    summary = {
        "Daily %": daily,
        "MTD %": _return_since(port_index, month_start),
        "QTD %": _return_since(port_index, quarter_start),
    }
    return summary, port_index


def compute_correlation(df: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """Pairwise correlation of daily returns over the trailing `lookback` days."""
    rets = df.pct_change().dropna(how="all").tail(lookback)
    return rets.corr()


def compute_covariance(
    df: pd.DataFrame,
    lookback: int = 252,
    halflife: float = 63,
    annualized: bool = True,
) -> pd.DataFrame:
    """Covariance matrix of daily total returns with exponential decay.

    RiskMetrics-style EWMA weighting: each observation's weight is
    (1/2)^(age / halflife), where `age` counts trading days back from the
    most recent one. Older returns matter less, so the estimate tracks
    regime shifts faster than an equal-weighted covariance.

    Estimation is pairwise: each (i, j) entry uses the observations where
    both assets have returns, with weights renormalised on that subsample.
    This keeps the matrix well-defined when assets have different listing
    dates (e.g. the BMO SPDR sector ETFs launched Feb 2025) or an isolated
    missing day.

    Args:
        df: price (total return index) DataFrame, one column per asset.
        lookback: trailing window of daily returns to use.
        halflife: decay half-life in trading days.
        annualized: scale by 252 to get annualised covariances.

    Returns:
        DataFrame covariance matrix (asset order preserved).
    """
    rets = df.pct_change().dropna(how="all").tail(lookback)
    labels = list(rets.columns)
    x = rets.to_numpy(dtype=float)

    age = np.arange(len(rets) - 1, -1, -1, dtype=float)
    w_full = 0.5 ** (age / halflife)

    k = len(labels)
    valid = ~np.isnan(x)
    cov = np.full((k, k), np.nan)
    for j in range(k):
        for l in range(j, k):
            mask = valid[:, j] & valid[:, l]
            if not mask.any():
                continue
            w = w_full[mask]
            w /= w.sum()
            a = x[mask, j]
            b = x[mask, l]
            ma = float(w @ a)
            mb = float(w @ b)
            cov[j, l] = cov[l, j] = float(w @ ((a - ma) * (b - mb)))

    if annualized:
        cov *= 252.0

    return pd.DataFrame(cov, index=labels, columns=labels)


def _solve_max_sharpe(
    mu_vec: np.ndarray,
    sigma: np.ndarray,
    labels: list,
    risk_free: float,
) -> pd.Series:
    """Long-only, fully-invested max-Sharpe weights for given mu / Sigma.

    Falls back to inverse-variance weights if the solver does not converge.
    """
    n = len(labels)

    def neg_sharpe(w: np.ndarray) -> float:
        ret = float(w @ mu_vec)
        vol = float(np.sqrt(max(w @ sigma @ w, 1e-12)))
        return -(ret - risk_free) / vol

    result = minimize(
        neg_sharpe,
        x0=np.full(n, 1.0 / n),
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
        options={"maxiter": 500, "ftol": 1e-9},
    )

    if result.success and np.isfinite(result.x).all():
        weights = np.clip(result.x, 0.0, None)
    else:
        var = np.diag(sigma).copy()
        weights = np.where(var > 0, 1.0 / var, 0.0)
    weights /= weights.sum()

    return pd.Series(weights, index=labels)


def optimize_max_sharpe(
    df: pd.DataFrame,
    risk_free: float = 0.02,
    lookback: int = 252,
    halflife: float = 63,
) -> pd.Series | None:
    """Long-only max-Sharpe portfolio weights from trailing total returns.

    Expected returns are the annualised mean of each asset's daily total
    returns over the trailing `lookback` days (each asset uses whatever
    history it has in that window). The covariance matrix is the
    exponential-decay EWMA estimate from `compute_covariance`, which
    handles the differing listing dates pairwise.
    """
    rets = df.pct_change().dropna(how="all").tail(lookback)
    labels = list(rets.columns)
    if len(labels) < 2 or len(rets) < 20:
        return None

    # Per-asset annualised expected return, ignoring missing observations.
    mu = rets.mean() * 252.0
    cov = compute_covariance(df, lookback=lookback, halflife=halflife)
    sigma = cov.loc[labels, labels].to_numpy()

    return _solve_max_sharpe(mu.loc[labels].to_numpy(), sigma, labels, risk_free)


def compute_target_portfolio(
    df: pd.DataFrame,
    risk_free: float = 0.02,
    est_months: int = 38,
    skip_months: int = 2,
    halflife: float = 126,
) -> pd.Series | None:
    """Target portfolio: max Sharpe on a rolling window that lags the present.

    Estimation uses daily total returns from (T - `est_months` months) to
    (T - `skip_months` months) - i.e. the most recent `skip_months` months
    are excluded so the strategy is not fitted on the freshest noise.
    Within the window every observation carries an exponential weight
    (half-life `halflife` trading days, newest counts most): the weighted
    mean feeds expected returns and the EWMA covariance (via
    `compute_covariance`) feeds risk. The window rolls forward on every
    refresh because it is always anchored to the latest available date.

    Assets with too little history inside the window (<20 observations)
    are dropped rather than optimised blind.
    """
    last = df.index[-1]
    start = last - pd.DateOffset(months=est_months)
    cutoff = last - pd.DateOffset(months=skip_months)
    est = df[(df.index >= start) & (df.index <= cutoff)]
    rets_all = est.pct_change().dropna(how="all")
    if len(rets_all) < 20:
        return None

    labels = [c for c in rets_all.columns if rets_all[c].notna().sum() >= 20]
    if len(labels) < 2:
        return None
    rets = rets_all[labels]

    age = np.arange(len(rets) - 1, -1, -1, dtype=float)
    w_obs = 0.5 ** (age / halflife)

    x = rets.to_numpy(dtype=float)
    valid = ~np.isnan(x)
    mass = valid.T @ w_obs
    with np.errstate(invalid="ignore", divide="ignore"):
        mu_daily = np.where(mass > 0, np.nan_to_num(x).T @ w_obs / np.where(mass > 0, mass, 1.0), 0.0)
    mu = mu_daily * 252.0

    cov = compute_covariance(est, lookback=len(est) + 1, halflife=halflife)
    sigma = cov.loc[labels, labels].to_numpy()
    if not np.isfinite(sigma).all():
        sigma = np.nan_to_num(sigma, nan=0.0)

    return _solve_max_sharpe(mu, sigma, labels, risk_free)
