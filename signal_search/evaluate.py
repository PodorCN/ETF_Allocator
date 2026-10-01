import sys

import numpy as np
import pandas as pd

from backtest.signal_tearsheet import _corr_t, _newey_west_t, _row_rank_corr
from data.registry import get_data
from port_con.calibrate import HORIZON, rank_corr, weekly_dates
from port_con.config import CALIBRATION_END, EQUITY
from signal_search import candidates as c
from utils.data_utils import cross_sectional_zscore, normalize_signal

# Runs the pre-registered signal search (research_notes/signal_search_protocol.md).
# Run from the repo root, one stage at a time:
#   python -m signal_search.evaluate select [round]     筛选段: every candidate
#   python -m signal_search.evaluate validate [round]   验证段: only the ones that passed select
# round = 1 (default) or 2.
# The test period is not reported here: after the signals are chosen, it is
# looked at once through the Signal Backtest and Portfolio Backtest pages.

SELECT_END = "2018-01-01"
VALIDATE_END = CALIBRATION_END
L1_T, L2_T = 1.5, 2.0          # select: minimum t-stat
L2_VALIDATE_T = 1.0            # validate: minimum t-stat for L2 (L1 only needs IC > 0)
MAX_CORR = 0.7
PRETEST_T = {1: None, 2: 3.0}  # round 2: t over select + validate (multiple testing)

L1 = {
    "eq_abs_mom": (c.eq_abs_mom, {"equity": "equity_basket", "three_month": "us3m"}, "taa"),
    "eq_trend": (c.eq_trend, {"equity": "equity_basket"}, "taa"),
    "eq_bond_mom": (c.eq_bond_mom, {"equity": "equity_basket", "bonds": "bond_basket"}, "taa"),
    "vrp": (c.vrp, {"equity": "equity_basket", "vix": "vix"}, "taa"),
    "low_realized_vol": (c.low_realized_vol, {"equity": "equity_basket"}, "taa"),
    "credit_spread_level": (c.credit_spread_level, {"spread": "baa_spread"}, "saa"),
    "credit_spread_change": (c.credit_spread_change, {"spread": "baa_spread"}, "taa"),
    "claims_change": (c.claims_change, {"claims": "jobless_claims"}, "saa"),
    "halloween": (c.halloween, {"equity": "equity_basket"}, "saa"),
}
L2 = {
    "ind_mom_6m": (c.ind_mom_6m, {"prices": "equity_prices"}),
    "ind_mom_1m": (c.ind_mom_1m, {"prices": "equity_prices"}),
    "ind_mom_risk_adj": (c.ind_mom_risk_adj, {"prices": "equity_prices"}),
    "residual_mom": (c.residual_mom, {"prices": "equity_prices", "equity": "equity_basket"}),
    "low_beta": (c.low_beta, {"prices": "equity_prices", "equity": "equity_basket"}),
    "low_vol": (c.low_vol, {"prices": "equity_prices"}),
    "seasonality": (c.seasonality, {"prices": "equity_prices"}),
}
L1_R2 = {
    "eq_mom_13612w": (c.eq_mom_13612w, {"equity": "equity_basket"}, "taa"),
    "canary": (c.canary, {"canaries": "canary_prices"}, "taa"),
    "gem_multi": (c.gem_multi, {"equity": "equity_basket", "bonds": "bond_basket"}, "taa"),
    "absorption_shift": (c.absorption_shift, {"prices": "equity_prices"}, "taa"),
    "low_turbulence": (c.low_turbulence, {"prices": "prices"}, "taa"),
}
L2_R2 = {
    "ind_mom_13612w": (c.ind_mom_13612w, {"prices": "equity_prices"}),
    "protective_mom": (c.protective_mom, {"prices": "equity_prices"}),
    "ma_energy": (c.ma_energy, {"prices": "equity_prices"}),
}
ROUNDS = {1: (L1, L2), 2: (L1_R2, L2_R2)}


def _periods(dates: pd.DatetimeIndex) -> dict[str, pd.DatetimeIndex]:
    """Weekly dates whose forward HORIZON-day window lies entirely inside each period."""
    trading = get_data("prices").index
    pos = trading.get_indexer(dates)
    window_end = trading[np.minimum(pos + HORIZON, len(trading) - 1)]
    sel, val = pd.Timestamp(SELECT_END), pd.Timestamp(VALIDATE_END)
    return {"select": dates[window_end < sel],
            "validate": dates[(dates >= sel) & (window_end < val)]}


def _align(raw: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    index = get_data("prices").index
    return raw.reindex(raw.index.union(index)).ffill().reindex(index)


def l1_signals(cands: dict) -> dict[str, pd.Series]:
    """Normalized like port_con.l1 (expanding z-score, capped)."""
    return {name: normalize_signal(_align(func(**{a: get_data(d) for a, d in data.items()})))
            for name, (func, data, _) in cands.items()}


def l2_signals(cands: dict) -> dict[str, pd.DataFrame]:
    """Normalized like port_con.l2 (cross-sectional z-score)."""
    return {name: cross_sectional_zscore(func(**{a: get_data(d) for a, d in data.items()}).reindex(
        get_data("prices").index)) for name, (func, data) in cands.items()}


def l1_stats(z: pd.Series, dates: pd.DatetimeIndex) -> dict:
    eq, fi = get_data("equity_basket"), get_data("bond_basket")
    fwd = (eq.shift(-HORIZON) / eq - 1) - (fi.shift(-HORIZON) / fi - 1)
    df = pd.DataFrame({"z": z.reindex(dates), "fwd": fwd.reindex(dates)}).dropna()
    ic = rank_corr(df["z"], df["fwd"]) if len(df) > 20 else np.nan
    return {"IC": ic, "t": _corr_t(ic, len(df)), "weeks": len(df), "from": df.index[0].date() if len(df) else None}


def l2_stats(z: pd.DataFrame, dates: pd.DatetimeIndex) -> dict:
    prices = get_data("prices")[EQUITY]
    fwd = (prices.shift(-HORIZON) / prices - 1).reindex(dates)
    ic = _row_rank_corr(z.reindex(dates), fwd).dropna()
    return {"IC": ic.mean(), "t": _newey_west_t(ic), "weeks": len(ic), "from": ic.index[0].date() if len(ic) else None}


def _table(signals: dict, stats, dates: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame({name: stats(z, dates) for name, z in signals.items()}).T


def _dedupe(names: list[str], signals: dict, table: pd.DataFrame, dates: pd.DatetimeIndex, pooled: bool) -> list[str]:
    """Drop the lower-t signal of any pair correlated above MAX_CORR (on select dates)."""
    if pooled:
        frame = pd.DataFrame({n: signals[n].reindex(dates).stack() for n in names})
    else:
        frame = pd.DataFrame({n: signals[n].reindex(dates) for n in names})
    corr = frame.corr()
    keep = sorted(names, key=lambda n: -table.loc[n, "t"])
    out = []
    for n in keep:
        if all(abs(corr.loc[n, k]) <= MAX_CORR for k in out):
            out.append(n)
        else:
            print(f"  drop {n}: corr > {MAX_CORR} with {[k for k in out if abs(corr.loc[n, k]) > MAX_CORR]}")
    print(corr.round(2))
    return out


def main(stage: str, round_: int = 1) -> None:
    pd.set_option("display.width", 200)
    dates = _periods(weekly_dates(get_data("prices").index))
    c1, c2 = ROUNDS[round_]
    s1, s2 = l1_signals(c1), l2_signals(c2)

    t1 = _table(s1, l1_stats, dates["select"])
    t2 = _table(s2, l2_stats, dates["select"])
    t1["pass"] = (t1["IC"] > 0) & (t1["t"] >= L1_T)
    t2["pass"] = (t2["IC"] > 0) & (t2["t"] >= L2_T)
    pass1, pass2 = list(t1.index[t1["pass"]]), list(t2.index[t2["pass"]])

    if stage == "select":
        print(f"=== Select period (forward windows ending before {SELECT_END}) ===")
        print(f"L1 (pass: IC > 0 and t >= {L1_T})"); print(t1.round(3))
        print(f"\nL2 (pass: IC > 0 and t >= {L2_T})"); print(t2.round(3))
        return

    v1 = _table({n: s1[n] for n in pass1}, l1_stats, dates["validate"])
    v2 = _table({n: s2[n] for n in pass2}, l2_stats, dates["validate"])
    print(f"=== Validate period ({SELECT_END} to {VALIDATE_END}) ===")
    if len(v1):
        v1["pass"] = v1["IC"] > 0
        print("L1 (pass: IC > 0)"); print(v1.round(3))
    if len(v2):
        v2["pass"] = (v2["IC"] > 0) & (v2["t"] >= L2_VALIDATE_T)
        print(f"\nL2 (pass: IC > 0 and t >= {L2_VALIDATE_T})"); print(v2.round(3))
    keep1 = list(v1.index[v1["pass"]]) if len(v1) else []
    keep2 = list(v2.index[v2["pass"]]) if len(v2) else []

    hurdle = PRETEST_T[round_]
    if hurdle and (keep1 or keep2):
        pretest = dates["select"].union(dates["validate"])
        p1 = _table({n: s1[n] for n in keep1}, l1_stats, pretest)
        p2 = _table({n: s2[n] for n in keep2}, l2_stats, pretest)
        print(f"\n=== Multiple-testing hurdle: t >= {hurdle} over select + validate ===")
        for p in [p1, p2]:
            if len(p):
                p["pass"] = p["t"] >= hurdle
                print(p.round(3))
        keep1 = [n for n in keep1 if p1.loc[n, "pass"]]
        keep2 = [n for n in keep2 if p2.loc[n, "pass"]]

    print("\n=== Redundancy (select period z-scores) ===")
    final1 = _dedupe(keep1, s1, t1, dates["select"], pooled=False) if len(keep1) > 1 else keep1
    final2 = _dedupe(keep2, s2, t2, dates["select"], pooled=True) if len(keep2) > 1 else keep2
    print(f"\nChosen L1: {[(n, c1[n][2]) for n in final1] or 'none -> L1 off'}")
    print(f"Chosen L2: {final2 or 'none -> L2 off'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "select", int(sys.argv[2]) if len(sys.argv) > 2 else 1)
