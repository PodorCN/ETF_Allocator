from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Brinson-Fachler performance attribution. Pure calculation: no data loading,
# so any portfolio can be attributed. Build the inputs somewhere else (see
# attribution/portfolios.py) and call attribute():
#
#   from attribution import attribute
#   att = attribute(weights, returns, segments, bench_weights, bench_returns)
#   att.summary("2025-01-01", "2025-12-31")["total"]


def attribute(
    weights: pd.DataFrame,
    returns: pd.DataFrame,
    segments: dict[str, str],
    bench_weights: dict[str, float] | pd.DataFrame,
    bench_returns: pd.DataFrame,
    name: str = "Portfolio",
    benchmark_name: str = "Benchmark",
    lag: int = 1,
    actual_returns: pd.DataFrame | None = None,
    leverage_returns: pd.DataFrame | None = None,
) -> "Attribution":
    """Daily Brinson-Fachler attribution of a portfolio of assets grouped into segments.

    weights        dates x assets. Target weights as decided on each date (e.g.
                   month-end rebalances); forward-filled onto the return dates
                   and applied `lag` trading days later, so a weight set at the
                   close of day d earns returns from d + lag. Weights may sum to
                   anything: model cash / leverage as its own asset.
    returns        dates x assets, daily simple returns. Defines the calendar.
    segments       asset -> segment (e.g. "ZXLK" -> "Equity"). Every weighted
                   asset needs one.
    bench_weights  segment -> constant weight, or dates x segments (same lag
                   convention as `weights`). Missing segments get weight 0.
    bench_returns  dates x segments, daily simple returns. A segment without a
                   column (e.g. cash the benchmark doesn't hold) uses the
                   portfolio's own segment return, so it only has an
                   allocation effect.
    actual_returns dates x assets, the returns actually earned when an asset
                   is implemented by a manager instead of the asset itself
                   (default: `returns`). Brinson effects use `returns`; the
                   difference is a fourth effect, Manager = w * (actual - returns).
    leverage_returns dates x assets, the part of (actual - returns) that comes
                   from a manager's leverage. Shown as its own effect,
                   Manager leverage = w * leverage_returns, and taken out of Manager.

    Starts on the first date where every weighted asset has a return.
    """
    assets = list(weights.columns)
    missing = [a for a in assets if a not in segments]
    if missing:
        raise ValueError(f"No segment for assets: {missing}")
    seg_names = list(dict.fromkeys(segments[a] for a in assets))

    index = returns.index
    wm = _hold(weights, index, lag)
    rm = returns.reindex(columns=assets)
    if isinstance(bench_weights, pd.DataFrame):
        wb = _hold(bench_weights, index, lag).reindex(columns=seg_names).fillna(0.0)
    else:
        wb = pd.DataFrame({s: float(bench_weights.get(s, 0.0)) for s in seg_names}, index=index)

    # Keep dates from the first one where weights are known and every
    # weighted asset has a return.
    has_weights = wm.notna().any(axis=1)
    complete = ~((wm.fillna(0) != 0) & rm.isna()).any(axis=1)
    ok = (has_weights & complete)[lambda s: s].index
    if ok.empty:
        raise ValueError("No dates with both weights and returns")
    valid = (index >= ok[0]) & has_weights
    wm, rm, wb = wm.loc[valid].fillna(0.0), rm.loc[valid].fillna(0.0), wb.loc[valid]
    ra = rm if actual_returns is None else actual_returns.reindex(index=wm.index, columns=assets).fillna(rm)
    rl = rm * 0 if leverage_returns is None else leverage_returns.reindex(index=wm.index, columns=assets).fillna(0.0)

    groups = pd.Series(segments).reindex(assets)
    wp = wm.T.groupby(groups).sum().T.reindex(columns=seg_names)
    contrib = (wm * rm).T.groupby(groups).sum().T.reindex(columns=seg_names)
    rb = bench_returns.reindex(index=wm.index, columns=seg_names)
    # Segment return = weighted average of its assets; where the portfolio
    # holds none of the segment, use the benchmark return (no effect).
    rp = (contrib / wp.where(wp != 0)).fillna(rb)
    rb = rb.fillna(rp)
    if rb.isna().any().any():
        bad = rb.columns[rb.isna().any()].tolist()
        raise ValueError(f"Benchmark returns missing for segments {bad} inside the attribution window")

    return Attribution(name=name, benchmark_name=benchmark_name, segments=seg_names,
                       asset_segment=groups.to_dict(), asset_weights=wm, asset_returns=rm,
                       asset_manager=wm * (ra - rm - rl), asset_leverage=wm * rl, wp=wp, rp=rp, wb=wb, rb=rb)


def _hold(weights: pd.DataFrame, index: pd.DatetimeIndex, lag: int) -> pd.DataFrame:
    """Forward-fill target weights onto `index`, then lag them."""
    return weights.reindex(index.union(weights.index)).ffill().reindex(index).shift(lag)


def carino_factors(port: pd.Series, bench: pd.Series) -> pd.Series:
    """Per-period Carino (1999) scaling so daily effects sum to the
    geometric-compounded active return over the whole window."""
    R, B = (1 + port).prod() - 1, (1 + bench).prod() - 1
    k = (np.log1p(R) - np.log1p(B)) / (R - B) if abs(R - B) > 1e-12 else 1 / (1 + R)
    diff = port - bench
    kt = pd.Series(np.where(diff.abs() > 1e-12,
                            (np.log1p(port) - np.log1p(bench)) / diff.where(diff.abs() > 1e-12, 1),
                            1 / (1 + port)), index=port.index)
    return kt / k


@dataclass
class Attribution:
    """Daily single-period attribution. Frames are dates x segments, except
    asset_weights / asset_returns / asset_manager (dates x assets, weights
    already lagged). asset_manager / asset_leverage are each asset's manager
    and manager-leverage effects."""

    name: str
    benchmark_name: str
    segments: list[str]
    asset_segment: dict[str, str]
    asset_weights: pd.DataFrame
    asset_returns: pd.DataFrame
    asset_manager: pd.DataFrame
    asset_leverage: pd.DataFrame
    wp: pd.DataFrame
    rp: pd.DataFrame
    wb: pd.DataFrame
    rb: pd.DataFrame
    port: pd.Series = field(init=False)
    bench: pd.Series = field(init=False)
    alloc: pd.DataFrame = field(init=False)
    sel: pd.DataFrame = field(init=False)
    inter: pd.DataFrame = field(init=False)
    mgr: pd.DataFrame = field(init=False)
    lev: pd.DataFrame = field(init=False)

    def __post_init__(self):
        groups = pd.Series(self.asset_segment).reindex(self.asset_manager.columns)
        self.mgr = self.asset_manager.T.groupby(groups).sum().T.reindex(columns=self.segments)
        self.lev = self.asset_leverage.T.groupby(groups).sum().T.reindex(columns=self.segments)
        self.port = (self.wp * self.rp).sum(axis=1) + self.mgr.sum(axis=1) + self.lev.sum(axis=1)
        self.bench = (self.wb * self.rb).sum(axis=1)
        # Brinson-Fachler: allocation is measured against the total benchmark
        # return, so overweighting a segment that beats the benchmark is positive.
        self.alloc = (self.wp - self.wb).mul(self.rb.sub(self.bench, axis=0))
        self.sel = self.wb * (self.rp - self.rb)
        self.inter = (self.wp - self.wb) * (self.rp - self.rb)

    @property
    def dates(self) -> pd.DatetimeIndex:
        return self.port.index

    def summary(self, start=None, end=None, freq: str = "M") -> dict:
        """Linked attribution over [start, end]. Empty dict if no dates in range.

        total       portfolio / benchmark / active return and the five effects
                    (allocation, selection, interaction, manager, manager leverage)
        segments    per segment: average weights, compounded returns, effects
        assets      per asset: its share of its segment's selection + interaction
                    (weight x excess return over the segment benchmark); they
                    sum to the segment's selection + interaction
        cumulative  linked cumulative effects over time
        periods     effects per calendar period (`freq`: "M" or "Y"), each
                    period linked on its own, plus active return
        """
        sl = slice(start, end)
        port, bench = self.port.loc[sl], self.bench.loc[sl]
        if port.empty:
            return {}
        f = carino_factors(port, bench)
        alloc = self.alloc.loc[sl].mul(f, axis=0)
        sel = self.sel.loc[sl].mul(f, axis=0)
        inter = self.inter.loc[sl].mul(f, axis=0)
        mgr = self.mgr.loc[sl].mul(f, axis=0)
        lev = self.lev.loc[sl].mul(f, axis=0)

        R, B = (1 + port).prod() - 1, (1 + bench).prod() - 1
        total = {
            "Portfolio": R, "Benchmark": B, "Active": R - B,
            "Allocation": alloc.sum().sum(), "Selection": sel.sum().sum(), "Interaction": inter.sum().sum(),
            "Manager": mgr.sum().sum(), "Manager leverage": lev.sum().sum(),
        }

        segments = pd.DataFrame({
            "Port Wt": self.wp.loc[sl].mean(),
            "Bench Wt": self.wb.loc[sl].mean(),
            "Port Ret": (1 + self.rp.loc[sl]).prod() - 1,
            "Bench Ret": (1 + self.rb.loc[sl]).prod() - 1,
            "Allocation": alloc.sum(),
            "Selection": sel.sum(),
            "Interaction": inter.sum(),
            "Manager": mgr.sum(),
            "Manager leverage": lev.sum(),
        }).loc[self.segments]
        segments["Total"] = segments[["Allocation", "Selection", "Interaction", "Manager", "Manager leverage"]].sum(axis=1)

        # A segment's sel + inter = wp * (rp - rb) = sum over its assets of w_k * (r_k - rb).
        wm, rm = self.asset_weights.loc[sl], self.asset_returns.loc[sl]
        seg_of = pd.Series(self.asset_segment)
        rb_asset = self.rb.loc[sl, seg_of.values].set_axis(seg_of.index, axis=1)
        held = wm.columns[(wm != 0).any()]
        assets = pd.DataFrame({
            "Segment": seg_of[held],
            "Avg Wt": wm[held].mean(),
            "Contribution": (wm[held] * (rm[held] - rb_asset[held])).mul(f, axis=0).sum(),
            "Return": (1 + rm[held].where(wm[held] != 0, 0)).prod() - 1,  # while held
            "Manager": self.asset_manager.loc[sl, held].mul(f, axis=0).sum(),
            "Manager leverage": self.asset_leverage.loc[sl, held].mul(f, axis=0).sum(),
        }).rename_axis("Asset").reset_index()

        cumulative = pd.DataFrame({
            "Allocation": alloc.sum(axis=1).cumsum(),
            "Selection": sel.sum(axis=1).cumsum(),
            "Interaction": inter.sum(axis=1).cumsum(),
            "Manager": mgr.sum(axis=1).cumsum(),
            "Manager leverage": lev.sum(axis=1).cumsum(),
        })
        cumulative["Active"] = cumulative.sum(axis=1)

        rows = []
        for p, idx in port.groupby(port.index.to_period(freq)).groups.items():
            fp = carino_factors(port.loc[idx], bench.loc[idx])
            rows.append({
                "Period": p.to_timestamp(),
                "Active": (1 + port.loc[idx]).prod() - (1 + bench.loc[idx]).prod(),
                "Allocation": self.alloc.loc[idx].sum(axis=1).mul(fp).sum(),
                "Selection": self.sel.loc[idx].sum(axis=1).mul(fp).sum(),
                "Interaction": self.inter.loc[idx].sum(axis=1).mul(fp).sum(),
                "Manager": self.mgr.loc[idx].sum(axis=1).mul(fp).sum(),
                "Manager leverage": self.lev.loc[idx].sum(axis=1).mul(fp).sum(),
            })
        periods = pd.DataFrame(rows).set_index("Period")

        return {"total": total, "segments": segments, "assets": assets,
                "cumulative": cumulative, "periods": periods}
