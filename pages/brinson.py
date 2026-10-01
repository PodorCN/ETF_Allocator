from functools import cache

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dash_table, dcc, html

from attribution.brinson import Attribution
from attribution.portfolios import PORTFOLIOS
from data.results import cached
from pages.common import (
    DOWN, EMPTY_FIG, MUTED, SERIES, TABLE_STYLE, UP, base_layout, bps, card, kpi, kpi_value, pct, signed_style,
)

# Portfolio Backtest > Brinson attribution tab. Display only: renders whichever
# Attribution objects PORTFOLIOS in attribution/portfolios.py returns. The
# calculation lives in attribution.brinson.

EFFECT_COLORS = dict(zip(["Allocation", "Selection", "Interaction", "Manager", "Manager leverage"], SERIES))
# Benchmarked segments on the weights chart, in order (others are drawn in gray).
SEGMENT_COLORS = SERIES[5:] + SERIES[:5]

PERIODS = ["MTD", "QTD", "YTD", "1Y", "3Y", "5Y", "10Y", "Inception"]
DEFAULT_PERIOD = "1Y"

@cache
def get_attribution(portfolio: str) -> Attribution:
    """Saved by precompute.py."""
    return cached(f"brinson_{portfolio}", PORTFOLIOS[portfolio])


def period_start(period: str, first: pd.Timestamp, last: pd.Timestamp) -> pd.Timestamp:
    """First date included in `period` ending at `last` (returns are close-to-close)."""
    anchors = {
        "MTD": last.to_period("M").start_time,
        "QTD": last.to_period("Q").start_time,
        "YTD": last.to_period("Y").start_time,
        "1Y": last - pd.DateOffset(years=1) + pd.Timedelta(days=1),
        "3Y": last - pd.DateOffset(years=3) + pd.Timedelta(days=1),
        "5Y": last - pd.DateOffset(years=5) + pd.Timedelta(days=1),
        "10Y": last - pd.DateOffset(years=10) + pd.Timedelta(days=1),
    }
    return max(anchors.get(period, first), first)


EFFECT_COLS = ["Allocation", "Selection", "Interaction", "Manager", "Manager leverage", "Total"]


def body() -> list:
    """Tab content."""
    return [
        dbc.Row([
            dbc.Col(html.Div(id="att-subtitle", className="kpi-delta"), width="auto"),
            dbc.Col(html.Span(id="att-status-pill", className="status-pill"), width="auto", className="ms-auto"),
        ], align="center", className="mb-3"),

        dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(dbc.Row([
            dbc.Col(dcc.Dropdown(id="att-portfolio", options=list(PORTFOLIOS), value=next(iter(PORTFOLIOS)),
                                 clearable=False, persistence=True, persistence_type="memory"),
                    xs=12, lg=3),
            dbc.Col(dbc.RadioItems(id="att-period", options=[{"label": p, "value": p} for p in PERIODS], value=DEFAULT_PERIOD,
                                   inline=True, className="btn-group period-btns", inputClassName="btn-check",
                                   labelClassName="btn btn-outline-secondary btn-sm",
                                   labelCheckedClassName="active"), width="auto"),
            dbc.Col(dcc.DatePickerRange(id="att-date-range", display_format="YYYY-MM-DD", clearable=True,
                                        start_date_placeholder_text="Custom start", end_date_placeholder_text="Custom end"),
                    width="auto"),
            dbc.Col(html.Div(id="att-range-label", className="kpi-delta"), width="auto", className="ms-auto"),
        ], align="center", className="g-3")), className="section-card"))),

        dbc.Row([
            kpi("Portfolio", "att-k-port", "att-k-port-sub"),
            kpi("Benchmark", "att-k-bench", "att-k-bench-sub"),
            kpi("Active", "att-k-active", "att-k-active-sub"),
            kpi("Allocation", "att-k-alloc", "att-k-alloc-sub"),
            kpi("Selection", "att-k-sel", "att-k-sel-sub"),
            kpi("Interaction", "att-k-inter", "att-k-inter-sub"),
            kpi("Manager", "att-k-mgr", "att-k-mgr-sub"),
            kpi("Manager leverage", "att-k-lev", "att-k-lev-sub"),
        ], className="g-3 mb-4"),

        dbc.Row([
            dbc.Col(card("Active Return Bridge", dcc.Graph(figure=EMPTY_FIG, id="att-waterfall", config={"displayModeBar": False})), lg=5),
            dbc.Col(card("Attribution by Segment", dash_table.DataTable(
                id="att-segment-table",
                columns=[{"name": "Segment", "id": "Segment"}]
                + [{"name": c, "id": c, "type": "numeric", "format": {"specifier": ".1%"}}
                   for c in ["Port Wt", "Bench Wt"]]
                + [{"name": c, "id": c, "type": "numeric", "format": {"specifier": "+.2%"}}
                   for c in ["Port Ret", "Bench Ret"] + EFFECT_COLS],
                style_data_conditional=signed_style(EFFECT_COLS)
                + [{"if": {"filter_query": '{Segment} = "Total"'}, "fontWeight": "700",
                    "backgroundColor": "var(--card-bg-alt)"}],
                **TABLE_STYLE,
            ), html.Div("Weights are period averages. A segment the benchmark doesn't hold "
                        "(e.g. cash / leverage) only has an allocation effect. Manager = weight x "
                        "(manager return - the slot's passive return), excluding the manager's leverage, which is "
                        "Manager leverage = weight x (leverage - 1) x (unlevered return - cash).",
                        className="kpi-delta mt-2", style={"textAlign": "left"})), lg=7),
        ], className="g-4 mb-4"),

        dbc.Row(dbc.Col(card("Cumulative Effects (linked)", dcc.Graph(figure=EMPTY_FIG, id="att-cumulative", config={"displayModeBar": False}))),
                className="mb-4"),

        dbc.Row(dbc.Col(card("Effects by Period", dcc.Graph(figure=EMPTY_FIG, id="att-periods", config={"displayModeBar": False}),
                             extra=dbc.RadioItems(id="att-freq", options=[{"label": "Monthly", "value": "M"},
                                                                      {"label": "Yearly", "value": "Y"}],
                                                  value="M", inline=True, className="btn-group period-btns",
                                                  inputClassName="btn-check",
                                                  labelClassName="btn btn-outline-secondary btn-sm",
                                                  labelCheckedClassName="active"))),
                className="mb-4"),

        dbc.Row([
            dbc.Col(card("Selection + Interaction by Asset", dcc.Graph(figure=EMPTY_FIG, id="att-asset-bars", config={"displayModeBar": False}),
                         html.Div("Each asset's share of its segment's selection + interaction: its excess return over "
                                  "the segment benchmark, times its weight in the portfolio.",
                                  className="kpi-delta mt-1", style={"textAlign": "left"})), lg=6),
            dbc.Col(card("Segment Weights vs Benchmark", dcc.Graph(figure=EMPTY_FIG, id="att-weights", config={"displayModeBar": False})), lg=6),
        ], className="g-4"),
    ]


@callback(
    Output("att-subtitle", "children"),
    Output("att-status-pill", "children"), Output("att-status-pill", "className"), Output("att-range-label", "children"),
    Output("att-k-port", "children"), Output("att-k-bench", "children"), Output("att-k-active", "children"),
    Output("att-k-alloc", "children"), Output("att-k-sel", "children"), Output("att-k-inter", "children"),
    Output("att-k-mgr", "children"), Output("att-k-lev", "children"),
    Output("att-k-port-sub", "children"), Output("att-k-bench-sub", "children"), Output("att-k-active-sub", "children"),
    Output("att-k-alloc-sub", "children"), Output("att-k-sel-sub", "children"), Output("att-k-inter-sub", "children"),
    Output("att-k-mgr-sub", "children"), Output("att-k-lev-sub", "children"),
    Output("att-waterfall", "figure"), Output("att-segment-table", "data"), Output("att-cumulative", "figure"),
    Output("att-periods", "figure"), Output("att-asset-bars", "figure"), Output("att-weights", "figure"),
    Input("att-portfolio", "value"), Input("att-period", "value"), Input("att-date-range", "start_date"),
    Input("att-date-range", "end_date"), Input("att-freq", "value"),
)
def update(portfolio, period, custom_start, custom_end, freq):
    empty = EMPTY_FIG
    try:
        att = get_attribution(portfolio)
    except Exception as e:
        return ("", f"Data unavailable: {e}", "status-pill stale", "", *[kpi_value(float("nan"))] * 8,
                *[""] * 8, empty, [], empty, empty, empty, empty)

    subtitle = f"Brinson-Fachler · {att.name} vs {att.benchmark_name}"
    first, last = att.dates[0], att.dates[-1]
    if custom_start or custom_end:
        start = pd.Timestamp(custom_start) if custom_start else first
        end = pd.Timestamp(custom_end) if custom_end else last
        label = "Custom range"
    else:
        start, end, label = period_start(period, first, last), last, period
    s = att.summary(start, end, freq=freq)
    if not s:
        return (subtitle, "No data in range", "status-pill stale", "", *[kpi_value(float("nan"))] * 8,
                *[""] * 8, empty, [], empty, empty, empty, empty)

    t = s["total"]
    idx = s["cumulative"].index
    range_label = f"{label}: {idx[0]:%Y-%m-%d} → {idx[-1]:%Y-%m-%d} · {len(idx)} trading days"
    years = (idx[-1] - idx[0]).days / 365.25

    def ann(r):
        return f"{(1 + r) ** (1 / years) - 1:+.2%} ann." if years >= 1 else "cumulative"

    # Waterfall: benchmark -> effects -> portfolio.
    wf = go.Figure(go.Waterfall(
        x=["Benchmark", "Allocation", "Selection", "Interaction", "Manager", "Mgr leverage", "Portfolio"],
        measure=["absolute", "relative", "relative", "relative", "relative", "relative", "total"],
        y=[t["Benchmark"], t["Allocation"], t["Selection"], t["Interaction"], t["Manager"], t["Manager leverage"], 0],
        text=[pct(t["Benchmark"]), pct(t["Allocation"]), pct(t["Selection"]), pct(t["Interaction"]),
              pct(t["Manager"]), pct(t["Manager leverage"]), pct(t["Portfolio"])],
        textposition="outside", cliponaxis=False,
        increasing={"marker": {"color": UP}}, decreasing={"marker": {"color": DOWN}},
        totals={"marker": {"color": MUTED}},
        connector={"line": {"color": "rgba(255,255,255,0.2)", "width": 1}},
        hovertemplate="%{x}: %{text}<extra></extra>",
    ))
    base_layout(wf, showlegend=False, height=360)
    # Zoom the y-axis onto the bridge so small effects stay visible.
    levels = pd.Series([t["Benchmark"], t["Allocation"], t["Selection"], t["Interaction"], t["Manager"],
                        t["Manager leverage"]]).cumsum()
    lo, hi = min(levels.min(), t["Portfolio"]), max(levels.max(), t["Portfolio"])
    pad = max(hi - lo, 0.002) * 0.25
    wf.update_yaxes(tickformat=".1%", range=[lo - pad, hi + pad])

    seg = s["segments"].reset_index(names="Segment")
    total_row = {"Segment": "Total", "Port Wt": seg["Port Wt"].sum(), "Bench Wt": seg["Bench Wt"].sum(),
                 "Port Ret": t["Portfolio"], "Bench Ret": t["Benchmark"], "Allocation": t["Allocation"],
                 "Selection": t["Selection"], "Interaction": t["Interaction"], "Manager": t["Manager"],
                 "Manager leverage": t["Manager leverage"], "Total": t["Active"]}
    table = seg.to_dict("records") + [total_row]

    cum = go.Figure()
    for name, color in EFFECT_COLORS.items():
        cum.add_trace(go.Scatter(x=idx, y=s["cumulative"][name], name=name, mode="lines",
                                 line={"color": color, "width": 2}))
    cum.add_trace(go.Scatter(x=idx, y=s["cumulative"]["Active"], name="Active (total)", mode="lines",
                             line={"color": "#e7ebf3", "width": 2.5}))
    base_layout(cum, height=380, hovermode="x unified")
    cum.update_yaxes(tickformat=".1%")
    cum.update_traces(hovertemplate="%{fullData.name}: %{y:+.2%}<extra></extra>")

    per = s["periods"]
    if freq == "Y":
        per.index = per.index.year.astype(str)
    pf = go.Figure()
    for name, color in EFFECT_COLORS.items():
        pf.add_trace(go.Bar(x=per.index, y=per[name], name=name, marker={"color": color, "line": {"width": 0}},
                            hovertemplate=f"{name}: %{{y:+.2%}}<extra></extra>"))
    pf.add_trace(go.Scatter(x=per.index, y=per["Active"], name="Active", mode="markers",
                            marker={"color": "#e7ebf3", "size": 8, "symbol": "diamond",
                                    "line": {"color": "#131b2e", "width": 2}},
                            hovertemplate="Active: %{y:+.2%}<extra></extra>"))
    base_layout(pf, barmode="relative", bargap=0.25, height=340, hovermode="x unified")
    pf.update_yaxes(tickformat=".1%")
    if freq == "M":
        pf.update_xaxes(tickformat="%b %Y")
    else:
        pf.update_xaxes(type="category")

    # Assets in benchmarked segments (an unbenchmarked segment such as cash
    # only has an allocation effect, so its assets always contribute 0 here).
    benchmarked = [seg for seg in att.segments if (att.wb.loc[idx[0]:idx[-1], seg] != 0).any()]
    assets = s["assets"][s["assets"]["Segment"].isin(benchmarked)].sort_values("Contribution")
    eb = go.Figure(go.Bar(
        x=assets["Contribution"], y=assets["Asset"], orientation="h",
        marker={"color": [UP if v >= 0 else DOWN for v in assets["Contribution"]]},
        customdata=assets[["Segment", "Avg Wt", "Return"]], text=[bps(v) for v in assets["Contribution"]],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y} (%{customdata[0]})<br>Contribution: %{x:+.2%}<br>Avg weight: %{customdata[1]:.1%}"
                      "<br>Return while held: %{customdata[2]:+.2%}<extra></extra>",
    ))
    base_layout(eb, showlegend=False, height=520, margin={"t": 10, "l": 90, "r": 70, "b": 30})
    lo, hi = min(assets["Contribution"].min(), 0), max(assets["Contribution"].max(), 0)
    pad = (hi - lo) * 0.2  # room for the outside bp labels
    eb.update_xaxes(tickformat=".1%", gridcolor="rgba(255,255,255,0.06)", showgrid=True, range=[lo - pad, hi + pad])

    wp, wb = att.wp.loc[idx[0]:idx[-1]], att.wb.loc[idx[0]:idx[-1]]
    wt = go.Figure()
    for seg, color in zip(benchmarked, SEGMENT_COLORS):
        wt.add_trace(go.Scatter(x=wp.index, y=wp[seg], name=f"{seg} (portfolio)", mode="lines",
                                line={"color": color, "width": 2, "shape": "hv"}))
        wt.add_trace(go.Scatter(x=wp.index, y=wb[seg], name=f"{seg} (benchmark)",
                                mode="lines", line={"color": color, "width": 1.5, "dash": "dot"}))
    for seg in att.segments:
        if seg not in benchmarked:
            wt.add_trace(go.Scatter(x=wp.index, y=wp[seg], name=seg, mode="lines",
                                    line={"color": MUTED, "width": 1.5, "shape": "hv"}))
    base_layout(wt, height=520, hovermode="x unified")
    wt.update_yaxes(tickformat=".0%")
    wt.update_traces(hovertemplate="%{fullData.name}: %{y:.1%}<extra></extra>")

    subs = [ann(t["Portfolio"]), ann(t["Benchmark"]), bps(t["Active"]),
            bps(t["Allocation"]), bps(t["Selection"]), bps(t["Interaction"]), bps(t["Manager"]),
            bps(t["Manager leverage"])]
    return (
        subtitle, f"Data as of {last:%Y-%m-%d}", "status-pill", range_label,
        kpi_value(t["Portfolio"], neutral=True), kpi_value(t["Benchmark"], neutral=True), kpi_value(t["Active"]),
        kpi_value(t["Allocation"]), kpi_value(t["Selection"]), kpi_value(t["Interaction"]), kpi_value(t["Manager"]),
        kpi_value(t["Manager leverage"]),
        *subs, wf, table, cum, pf, eb, wt,
    )


@callback(Output("att-date-range", "start_date"), Output("att-date-range", "end_date"), Input("att-period", "value"),
              prevent_initial_call=True)
def clear_custom_range(_period):
    """Picking a preset period clears any custom date range."""
    return None, None

