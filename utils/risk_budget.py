import numpy as np


def risk_contributions(w, cov) -> np.ndarray:
    """Fraction of portfolio variance contributed by each asset (sums to 1)."""
    w, cov = np.asarray(w, float), np.asarray(cov, float)
    mrc = cov @ w
    return w * mrc / (w @ mrc)


def risk_budget_weights(cov, budget, n_iter: int = 1000, tol: float = 1e-10) -> np.ndarray:
    """Long-only weights (summing to 1) whose risk contributions match `budget`.

    Cyclical coordinate descent: Griveau-Billion, Richard & Roncalli (2013),
    A Fast Algorithm for Computing High-Dimensional Risk Parity Portfolios.
    """
    cov = np.asarray(cov, float)
    b = np.asarray(budget, float)
    b = b / b.sum()
    var = np.diag(cov)
    w = 1 / np.sqrt(var)
    w /= w.sum()
    for _ in range(n_iter):
        w_old = w.copy()
        for i in range(len(w)):
            vol = np.sqrt(w @ cov @ w)
            c = cov[i] @ w - var[i] * w[i]
            w[i] = (-c + np.sqrt(c * c + 4 * var[i] * b[i] * vol)) / (2 * var[i])
        if np.abs(w - w_old).max() < tol:
            break
    return w / w.sum()
