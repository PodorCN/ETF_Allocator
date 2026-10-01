import pandas as pd

from data.registry import get_data
from manager_selection.config import MANAGERS

# Turns port_con's slot weights into what we actually hold, and gives the
# returns actually earned in each slot (used for the manager effects in attribution).
# Run from the repo root: python -m manager_selection.implement


def _returns(name: str, index: pd.DatetimeIndex) -> pd.DataFrame:
    return get_data(name).reindex(index).pct_change(fill_method=None)


def slot_returns() -> pd.DataFrame:
    """Daily return earned in each slot: the manager's where it has one, else the slot's own."""
    returns = get_data("prices").pct_change(fill_method=None)
    managers = _returns("manager_prices", returns.index)
    return returns.assign(**{slot: managers[slot].fillna(returns[slot]) for slot in MANAGERS})


def leverage_returns() -> pd.DataFrame:
    """Daily part of each slot's return that comes from the manager's leverage:
    (leverage - 1) x (unlevered return - cash), on days the manager is held. 0 elsewhere."""
    returns = get_data("prices").pct_change(fill_method=None)
    managers = _returns("manager_prices", returns.index)
    unlevered = _returns("manager_unlevered_prices", returns.index)
    cash = (get_data("us3m") / 100 / 252).reindex(returns.index).ffill().shift(1)
    out = pd.DataFrame(0.0, index=returns.index, columns=returns.columns)
    for slot, m in MANAGERS.items():
        lev = (m["leverage"] - 1) * unlevered[slot].sub(cash)
        out[slot] = lev.where(managers[slot].notna(), 0.0).fillna(0.0)
    return out


def holdings(weights: pd.DataFrame) -> pd.DataFrame:
    """Slot weights -> weights per instrument we actually buy (manager symbol
    replaces the slot on dates the manager has a price)."""
    live = get_data("manager_prices").reindex(weights.index, method="ffill").notna()
    out = weights.copy()
    for slot, m in MANAGERS.items():
        out[m["symbol"]] = weights[slot].where(live[slot], 0.0)
        out[slot] = weights[slot].where(~live[slot], 0.0)
    return out.loc[:, (out != 0).any()]


if __name__ == "__main__":
    from port_con.portfolio import final_weights
    print(holdings(final_weights()).tail(1).T.round(3))
