from functools import cache

import numpy as np
import pandas as pd

from data.registry import get_data
from port_con import black_litterman, te_budget
from port_con.config import (
    BASELINE_WEIGHTS, COV_WINDOW, EQUITY, GAMMA, LEVERAGE_BOUNDS, MAX_DEV, METHOD, REBALANCE, SLEEVES,
    SP500_SECTORS,
)
from port_con.l1 import get_l1_values
from port_con.l2 import get_l2_values

# Run from the repo root: python -m port_con.portfolio
#
# Builds the portfolio on each rebalance date (config REBALANCE) in 4 steps:
#
#   Step 0  Baseline  70% equity (S&P 500 sector weights), 20% fixed income,
#                     10% alternative (equal weight inside those two)
#   Step 1  L1        SAA + TAA values tilt the sleeve weights (equity / FI / alt),
#                     then size (leverage) and cap
#   Step 2  L2        L2 values tilt the sector weights inside equity
#   Step 3  Combine   sleeve weight x weight inside the sleeve = weight per ETF
#
# The tilt in steps 1 and 2 is done by one of two methods (config METHOD):
#   black_litterman  port_con/black_litterman.py
#   te_budget        port_con/te_budget.py (no leverage step)
# All give the baseline back when all values are 0.

METHODS = {"black_litterman": black_litterman, "te_budget": te_budget}


def vol(w: pd.Series, cov: pd.DataFrame) -> float:
    return float(np.sqrt(w @ cov @ w))


@cache
def _returns() -> pd.DataFrame:
    return get_data("prices").pct_change(fill_method=None)


def rebalance_dates(start=None) -> pd.DatetimeIndex:
    """Last trading day of each week ("W") or month ("M"), from `start`."""
    index = get_data("prices").index
    dates = pd.Series(index, index=index).groupby(index.to_period(REBALANCE)).last()
    return pd.DatetimeIndex(dates[dates >= pd.Timestamp(start)] if start else dates)


def get_cov(date: pd.Timestamp) -> pd.DataFrame:
    """Annualized covariance of daily returns over the last COV_WINDOW days, for
    assets with at least half a window of history."""
    rets = _returns().loc[:date].tail(COV_WINDOW)
    rets = rets.loc[:, rets.count() >= COV_WINDOW // 2].dropna()
    return rets.cov() * 252


# ---- Step 0: baseline ----

def get_baseline(date: pd.Timestamp, assets: pd.Index) -> dict[str, pd.Series]:
    """Baseline weights inside each sleeve (each sums to 1), using only `assets`.

    Equity: S&P 500 sector weights. Yahoo only has today's weights, so they are
    rolled back to `date` with each sector's price change since then.
    """
    prices = get_data("prices")
    sector_w = pd.Series(get_data("sp500_sector_weights")).rename(SP500_SECTORS)
    equity = sector_w * prices.loc[date, EQUITY] / prices[EQUITY].iloc[-1]

    inside = {
        "equity": equity,
        "fixed_income": pd.Series(1.0, index=SLEEVES["fixed_income"]),
        "alternative": pd.Series(1.0, index=SLEEVES["alternative"]),
    }
    inside = {s: w[w.index.isin(assets)].dropna() for s, w in inside.items()}
    return {s: w / w.sum() for s, w in inside.items()}


# ---- Step 1: L1 ----

def apply_l1(l1: pd.Series, sleeve_cov: pd.DataFrame, method) -> pd.Series:
    """Sleeve weights after L1, including leverage (see explain_l1)."""
    return explain_l1(l1, sleeve_cov, method)["final"]


def explain_l1(l1: pd.Series, sleeve_cov: pd.DataFrame, method) -> dict:
    """Every step of L1, for inspection. "final" is what apply_l1 returns.

    1. Tilt: the method turns the SAA / TAA values into sleeve weights (sum to 1).
    2. Size: target vol = baseline vol * (1 + GAMMA * avg L1 signal),
       leverage = target vol / tilted vol, within LEVERAGE_BOUNDS.
       Skipped (leverage 1) for methods with LEVERAGE = False.
    3. Cap: each sleeve within +/- MAX_DEV of its baseline weight.
    """
    base = pd.Series(BASELINE_WEIGHTS)
    w = method.tilt_l1(base, sleeve_cov, l1)

    target_vol = vol(base, sleeve_cov) * (1 + GAMMA * l1["avg_signal"])
    raw_leverage = target_vol / vol(w, sleeve_cov)
    leverage = np.clip(raw_leverage, *LEVERAGE_BOUNDS) if getattr(method, "LEVERAGE", True) else 1.0

    return {
        "baseline": base, "tilted": w, "baseline_vol": vol(base, sleeve_cov), "tilted_vol": vol(w, sleeve_cov),
        "target_vol": target_vol, "raw_leverage": raw_leverage, "leverage": leverage,
        "sized": w * leverage, "final": (w * leverage).clip(base - MAX_DEV, base + MAX_DEV),
    }


# ---- Step 2: L2 ----

def apply_l2(l2: pd.Series, equity_base: pd.Series, equity_cov: pd.DataFrame, method) -> pd.Series:
    """Sector weights inside equity (sum to 1): the method tilts the baseline by the L2 values."""
    return method.tilt_l2(equity_base, equity_cov, l2)


# ---- Step 3: combine, every rebalance date ----

def build_portfolio(date: pd.Timestamp, l1: pd.Series, l2: pd.Series, method) -> tuple[pd.Series, pd.Series] | None:
    """(sleeve weights, weight per ETF) on `date`. None if a sleeve has no assets with enough history."""
    cov = get_cov(date)
    baseline = get_baseline(date, cov.index)
    if any(w.empty for w in baseline.values()):
        return None

    # Sleeve covariance: each sleeve is its baseline mix of assets.
    mix = pd.DataFrame(baseline).T.fillna(0)[cov.index]
    sleeve_cov = mix @ cov @ mix.T

    sleeves = apply_l1(l1, sleeve_cov, method)
    eq = baseline["equity"].index
    inside = {**baseline, "equity": apply_l2(l2, baseline["equity"], cov.loc[eq, eq], method)}
    weights = pd.concat([inside[s] * sleeves[s] for s in SLEEVES])
    return sleeves, weights


@cache
def run(method: str = METHOD, start=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """History on each rebalance date from `start`: (sleeve weights + leverage + L1 values, weight per ETF)."""
    return build_history(method, start, get_l1_values(), get_l2_values())


def build_history(method: str, start, l1_values: pd.DataFrame, l2_values: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Like run(), with given L1 / L2 values (used by the signal attribution)."""
    sleeve_rows, weight_rows = {}, {}
    for date in rebalance_dates(start):
        result = build_portfolio(date, l1_values.loc[date], l2_values.loc[date], METHODS[method])
        if result is None:
            continue
        sleeves, weights = result
        sleeve_rows[date] = {**sleeves, "leverage": sleeves.sum(), **l1_values.loc[date, ["saa", "taa"]]}
        weight_rows[date] = weights

    columns = [a for assets in SLEEVES.values() for a in assets]
    return pd.DataFrame(sleeve_rows).T, pd.DataFrame(weight_rows).T.reindex(columns=columns).fillna(0)


def l1_weights(method: str = METHOD, start=None) -> pd.DataFrame:
    """Sleeve weights (equity / fixed_income / alternative), leverage, SAA and TAA values per rebalance date."""
    return run(method, start)[0]


def final_weights(method: str = METHOD, start=None) -> pd.DataFrame:
    """Weight per ETF on each rebalance date. Sums to the leverage."""
    return run(method, start)[1]


if __name__ == "__main__":
    for m in METHODS:
        print(f"== {m}")
        print(l1_weights(m).tail(3).round(3))
        fw = final_weights(m)
        print(fw.tail(1).T.round(3), f"sum: {fw.iloc[-1].sum():.3f}", sep="\n")
