import os
import threading
import time

import numpy as np
import pandas as pd
import yfinance as yf

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
        # A cache written for a different ticker list is useless.
        return df if not df.empty and set(df.columns) == set(TICKERS) else None
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
    """Daily close prices for all configured tickers, one column per label.

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
                auto_adjust=True,
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

    Assumes weights are held constant (rebalanced daily) - the standard
    simplification for an interactive "what if" allocator, as opposed to
    a strict buy-and-hold drift simulation.
    """
    rets = df.pct_change()
    w = pd.Series(weights, dtype=float).reindex(df.columns).fillna(0.0)
    port_ret = (rets * w).sum(axis=1, min_count=1)
    port_index = (1 + port_ret.fillna(0)).cumprod()
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
