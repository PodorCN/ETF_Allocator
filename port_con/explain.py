from functools import cache

import numpy as np
import pandas as pd

from data.registry import get_data
from manager_selection.config import MANAGERS
from port_con import te_budget
from port_con.config import (
    BASELINE_WEIGHTS, L1_ON, L1_SIGNALS, L1_TE_BUDGET, L1_TE_WEIGHTS, L2_ON, L2_SIGNALS, L2_TE_BUDGET, METHOD, SLEEVES,
)
from port_con.l1 import get_l1_signals, get_l1_values
from port_con.l2 import get_l2_signals, get_l2_values
from port_con.portfolio import METHODS, apply_l2, explain_l1, get_baseline, get_cov, rebalance_dates

# Everything that goes into the portfolio on one rebalance date: raw inputs,
# raw and normalized signals, L1 / L2 values and the weights after each step.
# Used by the Snapshot page (pages/snapshot.py).
# Run from the repo root: python -m port_con.explain [date] [method]


@cache
def _raw_signal(layer: str, name: str) -> pd.Series | pd.DataFrame:
    """A signal before normalization (the function's own output)."""
    cfg = L1_SIGNALS[layer][name] if layer != "l2" else L2_SIGNALS[name]
    return cfg["func"](**{arg: get_data(d) for arg, d in cfg["data"].items()})


def _asof(x: pd.Series | pd.DataFrame, date: pd.Timestamp):
    """Last value on or before `date`."""
    return x.loc[:date].iloc[-1] if not x.loc[:date].empty else None


def _input_text(cfg: dict, date: pd.Timestamp) -> str:
    """Raw inputs of one signal on `date`: the value of each series input
    (inputs with one column per asset are described, not listed)."""
    parts = []
    for arg, name in cfg["data"].items():
        data = get_data(name)
        if isinstance(data, pd.DataFrame):
            parts.append(f"{arg} = {name} ({data.shape[1]} assets)")
        else:
            v = _asof(data, date)
            parts.append(f"{arg} = {name}: {v:,.4g}" if v is not None else f"{arg} = {name}: -")
    return "; ".join(parts)


def rebalance_date(date) -> pd.Timestamp:
    """The rebalance date used for `date`: the last one on or before it."""
    dates = rebalance_dates()
    before = dates[dates <= pd.Timestamp(date)]
    return before[-1] if len(before) else dates[0]


def snapshot(date, method: str = METHOD) -> dict:
    date = rebalance_date(date)
    m = METHODS[method]

    # L1 signals
    l1_sig = get_l1_signals()
    l1_values = get_l1_values().loc[date]
    l1_rows = []
    for layer, sigs in L1_SIGNALS.items():
        for name, cfg in sigs.items():
            z = l1_sig.loc[date, name]
            side = 1 if cfg["side"] == "equity" else -1
            l1_rows.append({
                "Layer": layer.upper(), "Signal": name, "Side": cfg["side"], "Inputs": _input_text(cfg, date),
                "Raw": _asof(_raw_signal(layer, name), date), "Z": z, "Weight": cfg["weight"],
                "Contribution": z * cfg["weight"] * side if L1_ON else 0.0,
            })

    # Sleeves (L1 steps)
    cov = get_cov(date)
    baseline = get_baseline(date, cov.index)
    mix = pd.DataFrame(baseline).T.fillna(0)[cov.index]
    steps = explain_l1(l1_values, mix @ cov @ mix.T, m)
    sleeves = pd.DataFrame({
        "Baseline": steps["baseline"], "Tilted": steps["tilted"], "Sized": steps["sized"], "Final": steps["final"],
    })

    # L2 per sector
    l2_sig = get_l2_signals()
    l2_values = get_l2_values().loc[date]
    eq = baseline["equity"].index
    inside_eq = apply_l2(l2_values, baseline["equity"], cov.loc[eq, eq], m)
    l2 = pd.DataFrame(index=list(SLEEVES["equity"]))
    for name in L2_SIGNALS:
        l2[f"{name} raw"] = _asof(_raw_signal("l2", name), date)
        l2[f"{name} z"] = l2_sig[name].loc[date]
    l2["L2 value"] = l2_values
    l2["Baseline in equity"] = baseline["equity"]
    l2["Tilted in equity"] = inside_eq

    # Final weights per ETF, and last week's
    inside = {**baseline, "equity": inside_eq}
    base_w = pd.concat([baseline[s] * BASELINE_WEIGHTS[s] for s in SLEEVES])
    final = pd.concat([inside[s] * steps["final"][s] for s in SLEEVES])
    dates = rebalance_dates()
    prev_date = dates[dates < date][-1] if (dates < date).any() else None
    prev = _final_weights(prev_date, method) if prev_date is not None else pd.Series(dtype=float)
    live = get_data("manager_prices").loc[:date]
    held = {slot: m_["symbol"] if slot in live and live[slot].notna().any() else slot for slot, m_ in MANAGERS.items()}
    weights = pd.DataFrame({
        "Sleeve": {a: s for s, assets in SLEEVES.items() for a in assets},
        "Holding": {a: held.get(a, a) for a in base_w.index.union(final.index)},
        "Baseline": base_w, "Final": final,
    }).reindex([a for assets in SLEEVES.values() for a in assets])
    weights["Active"] = weights["Final"] - weights["Baseline"].fillna(0)
    weights["Last week"] = prev.reindex(weights.index)
    weights["Change"] = weights["Final"].fillna(0) - weights["Last week"].fillna(0)

    return {
        "date": date, "prev_date": prev_date, "method": method,
        "l1_signals": pd.DataFrame(l1_rows), "l1_values": l1_values,
        "sleeves": sleeves, "vol": {k: steps[k] for k in ["baseline_vol", "tilted_vol", "target_vol", "raw_leverage", "leverage"]},
        "l2": l2, "weights": weights,
        "te": _te_breakdown(date, cov, baseline, steps, inside_eq, l1_values, l2_values, method),
    }


def _te_breakdown(date, cov, baseline, steps, inside_eq, l1_values, l2_values, method) -> dict:
    """Tracking error vs baseline on `date`: per layer, per signal and per asset.

    Contributions are Euler shares, active_i x (cov @ active)_i / TE, so they add
    up to the total TE. Per signal:
      L1: the sleeve move is split in proportion to each signal's part of the L1 score.
      L2: te_budget only. Its tilt before caps is linear in the scores, so it splits
          exactly into one piece per signal; "caps" is what the caps changed.
    """
    base_w = pd.concat([baseline[s] * BASELINE_WEIGHTS[s] for s in SLEEVES])
    assets = base_w.index
    c = cov.loc[assets, assets]
    eq = baseline["equity"].index
    move = steps["final"] - steps["baseline"]
    l1_active = pd.concat([baseline[s] * move[s] for s in SLEEVES]).reindex(assets)
    l2_active = ((inside_eq - baseline["equity"]) * steps["final"]["equity"]).reindex(assets).fillna(0)
    active = l1_active + l2_active
    total = te_budget.te(active, c)
    marginal = c @ active / total if total > 0 else active * 0.0

    def contrib(piece: pd.Series) -> float:
        return float(piece.reindex(assets).fillna(0) @ marginal)

    is_te = method == "te_budget"
    l1_sig = get_l1_signals()
    l1_parts = {}
    for layer, sigs in L1_SIGNALS.items():
        for name, cfg in sigs.items():
            side = 1 if cfg["side"] == "equity" else -1
            weight = L1_TE_WEIGHTS.get(layer, 0.0) if is_te else 1.0
            l1_parts[(layer.upper(), name)] = l1_sig.loc[date, name] * cfg["weight"] * side * weight if L1_ON else 0.0
    l1_score = sum(l1_parts.values())
    l2_scores = l2_values[eq]

    # Per layer
    layers = pd.DataFrame({
        "Score / strength": [float(np.clip(l1_score, -1, 1)) if is_te else np.nan,
                             min(float(l2_scores.std()), 1.0) if is_te else np.nan, np.nan],
        "Budget": [L1_TE_BUDGET, L2_TE_BUDGET, np.nan] if is_te else [np.nan] * 3,
        "TE alone": [te_budget.te(l1_active, c), te_budget.te(l2_active, c), total],
        "Contribution": [contrib(l1_active), contrib(l2_active), total],
    }, index=["L1 (stocks vs bonds)", "L2 (sectors)", "Total"])
    layers["Target"] = layers["Budget"] * layers["Score / strength"].abs()

    # Per signal (te_budget only: the other methods are not linear in the signals)
    rows = []
    if is_te:
        for (layer, name), part in l1_parts.items():
            piece = l1_active * (part / l1_score) if l1_score != 0 else l1_active * 0.0
            rows.append({"Layer": layer, "Signal": name, "Tilt": "equity" if part > 0 else "bonds" if part < 0 else "-",
                         "Contribution": contrib(piece)})
        sig = get_l2_signals()
        weight_sum = sum(sig[n].loc[date, eq].notna() * cfg["weight"] for n, cfg in L2_SIGNALS.items())
        parts = {n: (sig[n].loc[date, eq].fillna(0) * cfg["weight"] / weight_sum).fillna(0) if L2_ON else l2_scores * 0
                 for n, cfg in L2_SIGNALS.items()}
        pieces = te_budget.l2_pieces(baseline["equity"], cov.loc[eq, eq], l2_values, parts)
        pieces = {n: p * steps["final"]["equity"] for n, p in pieces.items()}
        for n, p in pieces.items():
            top = p.sort_values()
            tilt = f"+{top.index[-1]} / -{top.index[0]}" if top.abs().max() > 1e-6 else "-"
            rows.append({"Layer": "L2", "Signal": n, "Tilt": tilt, "Contribution": contrib(p)})
        rows.append({"Layer": "L2", "Signal": "caps", "Tilt": "sector cap / no shorting",
                     "Contribution": contrib(l2_active - sum(pieces.values()))})
    signals = pd.DataFrame(rows, columns=["Layer", "Signal", "Tilt", "Contribution"])
    signals["Share of TE"] = signals["Contribution"] / total if total > 0 else 0.0

    # Per asset
    per_asset = pd.DataFrame({
        "L2 value": l2_values.reindex(assets), "Active vol": te_budget.active_vol(base_w, c),
        "L1 active": l1_active, "L2 active": l2_active, "Active": active,
        "Contribution": active * marginal,
    })
    per_asset["Share of TE"] = per_asset["Contribution"] / total if total > 0 else 0.0
    return {"layers": layers, "signals": signals, "assets": per_asset, "total": total, "has_signals": is_te}


def _final_weights(date: pd.Timestamp, method: str) -> pd.Series:
    """Final weight per ETF on one rebalance date (same steps as port_con.portfolio.build_portfolio)."""
    from port_con.portfolio import build_portfolio
    result = build_portfolio(date, get_l1_values().loc[date], get_l2_values().loc[date], METHODS[method])
    return result[1] if result else pd.Series(dtype=float)


if __name__ == "__main__":
    import sys
    s = snapshot(sys.argv[1] if len(sys.argv) > 1 else pd.Timestamp.today(),
                 sys.argv[2] if len(sys.argv) > 2 else METHOD)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 60)
    print("Rebalance date:", s["date"].date(), "| previous:", s["prev_date"].date() if s["prev_date"] is not None else "-")
    print(s["l1_signals"].round(4).to_string(index=False))
    print(s["l1_values"].round(3).to_dict(), {k: round(float(v), 4) for k, v in s["vol"].items()})
    print(s["sleeves"].round(4))
    print(s["l2"].round(3).T)
    print(s["weights"].round(4))
    print(s["te"]["layers"].round(4))
    print(s["te"]["signals"].round(4).to_string(index=False))
    print(s["te"]["assets"].round(4))
