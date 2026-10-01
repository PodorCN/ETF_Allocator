import numpy as np
import pandas as pd

from port_con.config import BASELINE_WEIGHTS, L1_TE_BUDGET, L1_TE_WEIGHTS, L2_MAX_TILT, L2_TE_BUDGET, MAX_DEV

# Run from the repo root: python -m port_con.te_budget   (TE used vs budget, latest date)
#
# TE budget: turn L1 / L2 values into weights (used by port_con.portfolio).
# The budget is how far each layer may move away from the baseline (tracking
# error, share of the whole portfolio); the signals decide direction and size.
#   1. raw tilt = score / active vol (volatile assets get smaller tilts for the same score)
#   2. scale the tilt so its tracking error = budget x signal strength (strength <= 1,
#      so the full budget is used only when the signal is strong)
#   3. caps: tilts sum to 0, weights stay >= 0 and within the max tilt of baseline
# A score of 0 gives the baseline back. No leverage: portfolio.explain_l1 skips
# its sizing step for this method (LEVERAGE = False).
#
# References:
# - Grinold, R. & Kahn, R. (2000). Active Portfolio Management, 2nd ed.
#   (optimal active weight ~ score / active volatility when bets are independent).
# - Amundi (2020). Risk budgeting and trade sizing: why they matter to multi-asset.

LEVERAGE = False


def te(active: pd.Series, cov: pd.DataFrame) -> float:
    """Tracking error of active weights (annualized, same units as cov)."""
    return float(np.sqrt(active @ cov @ active))


def fit_to_budget(raw: pd.Series, cov: pd.DataFrame, target: float,
                  lower: pd.Series, upper: pd.Series) -> pd.Series:
    """Scale `raw` (sums to 0) to tracking error `target`, then keep each tilt
    within [lower, upper] and the sum at 0. Caps can only lower the TE."""
    size = te(raw, cov)
    if target <= 0 or size == 0:
        return raw * 0.0
    a = raw * target / size
    for _ in range(50):
        a = a.clip(lower, upper)
        residual = a.sum()
        free = (a > lower + 1e-12) & (a < upper - 1e-12)
        if abs(residual) < 1e-12 or not free.any():
            break
        a[free] -= residual / free.sum()
    return a * min(1.0, target / te(a, cov)) if te(a, cov) > 0 else a


def tilt_l1(base: pd.Series, cov: pd.DataFrame, l1: pd.Series,
            budget: float = L1_TE_BUDGET) -> pd.Series:
    """Sleeve weights (sum to 1). One bet: move weight from fixed income to equity
    (score > 0) or back (score < 0); the alternative sleeve keeps its weight."""
    score = sum(l1[layer] * w for layer, w in L1_TE_WEIGHTS.items())
    bet = pd.Series(0.0, index=base.index)
    bet[["equity", "fixed_income"]] = [1.0, -1.0]
    strength = float(np.clip(score, -1, 1))
    lower = pd.Series(-MAX_DEV, index=base.index).clip(lower=-base)
    upper = pd.Series(MAX_DEV, index=base.index)
    move = strength * budget / te(bet, cov)
    move = min(move, upper["equity"], -lower["fixed_income"]) if move > 0 else \
        max(move, lower["equity"], -upper["fixed_income"])
    return base + bet * move


def active_vol(base: pd.Series, cov: pd.DataFrame) -> pd.Series:
    """Volatility of each asset's return minus the `base` portfolio's return."""
    return np.sqrt(np.diag(cov) - 2 * (cov @ base) + base @ cov @ base)


def l2_raw(base: pd.Series, cov: pd.DataFrame, scores: pd.Series) -> pd.Series:
    """Step 1 of L2: score / active vol, demeaned so the tilts sum to 0."""
    raw = scores[base.index] / active_vol(base, cov)
    return raw - raw.mean()


def l2_target(scores: pd.Series, budget: float = L2_TE_BUDGET) -> float:
    """Step 2 of L2: TE target inside equity = budget x strength / equity sleeve weight.
    Strength = spread of the scores across sectors, at most 1."""
    strength = min(float(scores.std()), 1.0) if len(scores) > 1 else 0.0
    return budget * strength / BASELINE_WEIGHTS["equity"]


def tilt_l2(base: pd.Series, cov: pd.DataFrame, l2: pd.Series,
            budget: float = L2_TE_BUDGET) -> pd.Series:
    """Sector weights inside equity (sum to 1). Budget and caps are shares of the
    whole portfolio, so inside equity they are divided by the equity sleeve weight."""
    scores = l2[base.index]
    cap = L2_MAX_TILT / BASELINE_WEIGHTS["equity"]
    lower = pd.Series(-cap, index=base.index).clip(lower=-base)
    upper = pd.Series(cap, index=base.index)
    return base + fit_to_budget(l2_raw(base, cov, scores), cov, l2_target(scores, budget), lower, upper)


def l2_pieces(base: pd.Series, cov: pd.DataFrame, l2: pd.Series, parts: dict[str, pd.Series],
              budget: float = L2_TE_BUDGET) -> dict[str, pd.Series]:
    """Split the L2 tilt inside equity (before caps) into one piece per signal.
    `parts` are each signal's share of the L2 value (they sum to `l2`); the tilt
    before caps is linear in the scores, so the pieces add up to it."""
    scores = l2[base.index]
    size = te(l2_raw(base, cov, scores), cov)
    scale = l2_target(scores, budget) / size if size > 0 else 0.0
    return {name: l2_raw(base, cov, p) * scale for name, p in parts.items()}


def report(date=None, method: str = "te_budget") -> pd.DataFrame:
    """Tracking error vs baseline on `date` (default: latest), per layer and per asset."""
    from port_con.l1 import get_l1_values
    from port_con.l2 import get_l2_values
    from port_con.portfolio import METHODS, build_portfolio, get_baseline, get_cov, rebalance_dates
    from port_con.config import SLEEVES

    dates = rebalance_dates()
    date = dates[dates <= pd.Timestamp(date)][-1] if date else dates[-1]
    cov = get_cov(date)
    inside = get_baseline(date, cov.index)
    base = pd.concat([inside[s] * BASELINE_WEIGHTS[s] for s in SLEEVES])
    sleeves, weights = build_portfolio(date, get_l1_values().loc[date], get_l2_values().loc[date], METHODS[method])
    l1_only = pd.concat([inside[s] * sleeves[s] for s in SLEEVES])
    c = cov.loc[base.index, base.index]

    active = weights.reindex(base.index).fillna(0) - base
    total = te(active, c)
    by_asset = pd.DataFrame({"baseline": base, "weight": weights.reindex(base.index).fillna(0), "active": active,
                             "TE share": active * (c @ active) / total**2 if total > 0 else 0.0})
    print(f"{date.date()}  method {method}")
    print(f"  L1 TE {te(l1_only - base, c):.2%} (budget {L1_TE_BUDGET:.2%})   "
          f"L2 TE {te(weights.reindex(base.index).fillna(0) - l1_only, c):.2%} (budget {L2_TE_BUDGET:.2%})   "
          f"total {total:.2%}")
    return by_asset


if __name__ == "__main__":
    print((report() * 100).round(2))
