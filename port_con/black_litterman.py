import numpy as np
import pandas as pd

from port_con.config import BL_DELTA, BL_IC_L2, BL_IC_SAA, BL_IC_TAA, BL_TAU

# Black-Litterman: turn L1 / L2 values into weights (used by port_con.portfolio).
#   1. prior: returns implied by the baseline, pi = delta * cov @ baseline
#   2. views from the signals: expected excess return = IC x volatility x score
#   3. posterior returns = prior blended with the views
#   4. weights = mean-variance optimum of the posterior, (delta * cov)^-1 @ mu
# A score of 0 gives the baseline back.
#
# View confidence follows He & Litterman (1999): Omega = tau * P @ cov @ P',
# i.e. each view is as uncertain as the prior, so tau cancels out.
#
# References:
# - Black, F. & Litterman, R. (1992). Global Portfolio Optimization.
#   Financial Analysts Journal, 48(5), 28-43.
# - He, G. & Litterman, R. (1999). The Intuition Behind Black-Litterman
#   Model Portfolios. Goldman Sachs Investment Management Research.
# - Grinold, R. & Kahn, R. (2000). Active Portfolio Management, 2nd ed.
#   (alpha = IC x volatility x score).


def implied_returns(base: pd.Series, cov: pd.DataFrame) -> pd.Series:
    """Step 1: expected returns that make `base` the optimal portfolio."""
    return BL_DELTA * cov @ base


def posterior_returns(pi: pd.Series, cov: pd.DataFrame, P: pd.DataFrame, Q: pd.Series) -> pd.Series:
    """Step 3: blend the prior `pi` with views P @ mu = Q."""
    S, P_, Q_, pi_ = BL_TAU * cov.to_numpy(), P.to_numpy(), Q.to_numpy(), pi.to_numpy()
    omega = np.diag(np.diag(P_ @ S @ P_.T))
    gain = S @ P_.T @ np.linalg.inv(P_ @ S @ P_.T + omega)
    return pd.Series(pi_ + gain @ (Q_ - P_ @ pi_), index=pi.index)


def optimal_weights(mu: pd.Series, cov: pd.DataFrame) -> pd.Series:
    """Step 4: unconstrained mean-variance weights."""
    return pd.Series(np.linalg.solve(BL_DELTA * cov, mu), index=mu.index)


def tilt_l1(base: pd.Series, cov: pd.DataFrame, l1: pd.Series,
            ic_saa: float = BL_IC_SAA, ic_taa: float = BL_IC_TAA) -> pd.Series:
    """Sleeve weights (sum to 1). One relative view: equity minus fixed income
    returns IC x vol x score more than implied, score from the SAA and TAA values."""
    pi = implied_returns(base, cov)
    P = pd.DataFrame(0.0, index=["equity_vs_fi"], columns=base.index)
    P.loc["equity_vs_fi", ["equity", "fixed_income"]] = [1.0, -1.0]
    view_vol = np.sqrt(P.iloc[0] @ cov @ P.iloc[0])
    Q = P @ pi + view_vol * (ic_saa * l1["saa"] + ic_taa * l1["taa"])
    return optimal_weights(posterior_returns(pi, cov, P, Q), cov)


def tilt_l2(base: pd.Series, cov: pd.DataFrame, l2: pd.Series, ic: float = BL_IC_L2) -> pd.Series:
    """Sector weights inside equity (sum to 1). One view per sector: IC x vol x L2 value.
    Long-only: negative weights are set to 0, then rescaled to sum to 1."""
    pi = implied_returns(base, cov)
    P = pd.DataFrame(np.eye(len(base)), index=base.index, columns=base.index)
    Q = pi + ic * np.sqrt(np.diag(cov)) * l2[base.index]
    w = optimal_weights(posterior_returns(pi, cov, P, Q), cov).clip(lower=0)
    return w / w.sum()
