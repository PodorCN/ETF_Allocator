from functools import lru_cache

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dash_table, dcc, html

from attribution.signal_attribution import summary as signal_summary
from backtest.backtest import COST_BPS, run
from backtest.report import GROUPS, LABELS, SLEEVE_LABELS, component_group
from data.results import cached
from pages import brinson
from pages.common import (
    MUTED, SERIES, TABLE_STYLE, base_layout, card, controls, graph, note, num_cols, oos_shade, page_header,
    signed_style, toggle, zero_line,
)
from port_con.config import BACKTEST_START, BASELINE_WEIGHTS, CALIBRATION_END, REBALANCE

# Portfolio Backtest page (/backtest), three tabs:
#   Performance         both methods vs the benchmark from a start date (backtest/backtest.py),
#                       in sample (before CALIBRATION_END) vs out of sample
#   Brinson attribution allocation / selection / interaction / manager effects (pages/brinson.py)
#   Signal attribution  what each signal added (attribution/signal_attribution.py)
# Tabs are built when opened, so the slow signal attribution only runs on demand.

METHODS = ["black_litterman", "te_budget"]
COLOR = {"black_litterman": SERIES[0], "te_budget": SERIES[1], "benchmark": MUTED}
SLEEVE_COLOR = dict(zip(SLEEVE_LABELS, SERIES[2:5]))
GROUP_COLOR = {"Baseline vs benchmark": MUTED, **dict(zip(GROUPS[1:], SERIES[2:]))}
STAT_FORMATS = {"Total return": "+.1%", "Ann. return": "+.1%", "Ann. vol": ".1%", "Sharpe": ".2f",
                "Max drawdown": ".1%", "Tracking error": ".1%", "Info ratio": "+.2f", "Turnover / yr": ".0%"}
PERIODS = ["In sample", "Out of sample", "Full"]


@lru_cache(maxsize=8)
def performance(start: str) -> dict:
    """Saved by precompute.py for the default start."""
    return cached(f"performance_{start}", lambda: run(start))


@lru_cache(maxsize=8)
def attribution(start: str) -> dict:
    """Saved by precompute.py for the default start."""
    return cached(f"signal_attribution_{start}", lambda: signal_summary(start))


def layout() -> list:
    rebalance = {"W": "Weekly", "M": "Monthly"}[REBALANCE]
    return [
        page_header("Portfolio Backtest",
                    f"{rebalance} rebalance · net of {COST_BPS} bp trading cost · managers included · "
                    f"vs 70/20/10 benchmark", "/backtest"),
        dbc.Tabs(id="pb-tabs", active_tab="performance", className="mb-3", children=[
            dbc.Tab(label="Performance", tab_id="performance"),
            dbc.Tab(label="Brinson attribution", tab_id="brinson"),
            dbc.Tab(label="Signal attribution", tab_id="signals"),
        ]),
        html.Div(id="pb-content"),
    ]


def _start_picker(id_: str, date: str) -> dbc.Col:
    return dbc.Col([html.Span("Start ", className="kpi-delta me-2"),
                    dcc.DatePickerSingle(id=id_, date=date, display_format="YYYY-MM-DD")], width="auto")


def performance_body() -> list:
    return [
        controls(_start_picker("pb-start", BACKTEST_START),
                 dbc.Col(html.Div(f"Shaded: out of sample, from {CALIBRATION_END}. Before it is the data the tilt "
                                  f"parameters were calibrated on (in sample).",
                                  className="kpi-delta"), width="auto")),
        dcc.Loading(type="dot", children=[
            dbc.Row(dbc.Col(card("Growth of 1 (after trading costs)", graph("pb-growth", 380))), className="mb-4"),
            dbc.Row(dbc.Col(card("Performance", dash_table.DataTable(id="pb-stats", **TABLE_STYLE),
                                 note("Annualized from daily returns. Sharpe uses the 3-month T-bill; tracking error "
                                      "and info ratio are vs the benchmark. In sample: before "
                                      f"{CALIBRATION_END}; out of sample: from {CALIBRATION_END}."),
                                 extra=toggle("pb-period", {p: p for p in PERIODS}, "Out of sample"))),
                    className="mb-4"),
            dbc.Row([
                dbc.Col(card("Active return vs benchmark", graph("pb-active", 340)), lg=6),
                dbc.Col(card("Drawdown", graph("pb-drawdown", 340)), lg=6),
            ], className="g-4 mb-4"),
            dbc.Row([
                dbc.Col(card("Sleeve weights: Black-Litterman", graph("pb-sleeves-black_litterman", 340),
                             note("Dotted: baseline. Weights include leverage.")), lg=6),
                dbc.Col(card("Sleeve weights: TE budget", graph("pb-sleeves-te_budget", 340),
                             note("Dotted: baseline. Weights include leverage.")), lg=6),
            ], className="g-4"),
        ]),
    ]


def signals_body() -> list:
    return [
        controls(_start_picker("pb-attr-start", CALIBRATION_END),
                 dbc.Col(html.Div("Each signal: the portfolio rebuilt with only that signal on, minus the portfolio "
                                  "with every signal off. The default start is precomputed; a new start date "
                                  "takes ~2 minutes the first time.",
                                  className="kpi-delta"))),
        dcc.Loading(type="dot", children=[
            dbc.Row(dbc.Col(card("Contribution by component", graph("pb-attr-bars", 540),
                                 note("Cumulative over the window, net of trading cost, with managers. Carino-linked, "
                                      "so the components add up to the total active return."))), className="mb-4"),
            dbc.Row(dbc.Col(card("Cumulative contribution over time", graph("pb-attr-line", 380),
                                 extra=toggle("pb-attr-method", {m: LABELS[m] for m in METHODS}, "black_litterman"))),
                    className="mb-4"),
            dbc.Row(dbc.Col(card("Contribution and IC by component", dash_table.DataTable(id="pb-attr-table", **TABLE_STYLE),
                                 note("IC before = on the calibration data; IC in window = over this backtest.")))),
        ]),
    ]


@callback(Output("pb-content", "children"), Input("pb-tabs", "active_tab"))
def render_tab(tab):
    if tab == "brinson":
        return brinson.body()
    if tab == "signals":
        return signals_body()
    return performance_body()


def _lines(df: pd.DataFrame, keys: list[str], fmt: str) -> list[go.Scatter]:
    return [go.Scatter(x=df.index, y=df[k], name=LABELS[k], mode="lines",
                       line={"color": COLOR[k], "width": 2, "dash": "dot" if k == "benchmark" else "solid"},
                       hovertemplate=f"{LABELS[k]}: %{{y:{fmt}}}<extra></extra>") for k in keys]


@callback(
    Output("pb-growth", "figure"), Output("pb-stats", "data"), Output("pb-stats", "columns"),
    Output("pb-active", "figure"), Output("pb-drawdown", "figure"),
    Output("pb-sleeves-black_litterman", "figure"), Output("pb-sleeves-te_budget", "figure"),
    Input("pb-start", "date"), Input("pb-period", "value"),
)
def update_performance(start, period):
    res = performance(str(start)[:10])
    r = res["returns"]
    # Shade out of sample only when the window spans the split.
    split = pd.Timestamp(CALIBRATION_END)
    shade = (lambda fig: oos_shade(fig, CALIBRATION_END, r.index[-1])) if r.index[0] < split <= r.index[-1]         else (lambda fig: fig)
    growth = pd.concat([pd.DataFrame(1.0, index=[r.index[0] - pd.Timedelta(days=1)], columns=r.columns),
                        (1 + r).cumprod()])
    keys = METHODS + ["benchmark"]

    g = shade(base_layout(go.Figure(_lines(growth, keys, ".3f")), hovermode="x unified"))
    g.update_yaxes(tickformat=".2f")

    # Relative, not a difference of growth levels, which balloons over long windows.
    active = growth[METHODS].div(growth["benchmark"], axis=0) - 1
    a = shade(zero_line(base_layout(go.Figure(_lines(active, METHODS, "+.2%")), hovermode="x unified")))
    a.update_yaxes(tickformat="+.0%")

    dd = growth / growth.cummax() - 1
    d = shade(base_layout(go.Figure(_lines(dd, keys, ".1%")), hovermode="x unified"))
    d.update_yaxes(tickformat=".0%")

    stats = res["period_stats"].get(period, res["stats"]).reset_index(names="Portfolio")
    for key, label in LABELS.items():
        stats["Portfolio"] = stats["Portfolio"].str.replace(key, label)
    columns = [{"name": "Portfolio", "id": "Portfolio"}] + \
              [c for k, spec in STAT_FORMATS.items() for c in num_cols([k], spec)]

    ymax = max(res["sleeves"][m][list(SLEEVE_LABELS)].max().max() for m in METHODS) * 1.1
    sleeve_figs = []
    for m in METHODS:
        sl = res["sleeves"][m]
        fig = go.Figure([go.Scatter(x=sl.index, y=sl[s], name=label, mode="lines",
                                    line={"color": SLEEVE_COLOR[s], "width": 2, "shape": "hv"},
                                    hovertemplate=f"{label}: %{{y:.1%}}<extra></extra>")
                         for s, label in SLEEVE_LABELS.items()])
        for s in SLEEVE_LABELS:
            fig.add_hline(y=BASELINE_WEIGHTS[s], line={"color": MUTED, "width": 1, "dash": "dot"})
        shade(base_layout(fig, hovermode="x unified"))
        fig.update_yaxes(tickformat=".0%", range=[0, ymax])
        sleeve_figs.append(fig)

    return (g, stats.to_dict("records"), columns, a, d, *sleeve_figs)


@callback(
    Output("pb-attr-bars", "figure"), Output("pb-attr-line", "figure"),
    Output("pb-attr-table", "data"), Output("pb-attr-table", "columns"), Output("pb-attr-table", "style_data_conditional"),
    Input("pb-attr-start", "date"), Input("pb-attr-method", "value"),
)
def update_attribution(start, method):
    s = attribution(str(start)[:10])
    table = s["table"]
    components = [c for c in table.index if c != "Total active"]

    comps = components[::-1]  # first component on top
    bars = go.Figure([go.Bar(y=comps, x=table.loc[comps, m], name=LABELS[m], orientation="h", width=0.36,
                             marker={"color": COLOR[m], "line": {"width": 0}},
                             hovertemplate="%{y}<br>" + LABELS[m] + ": %{x:+.2%}<extra></extra>") for m in METHODS])
    base_layout(bars, barmode="group", bargap=0.3, margin={"t": 30, "l": 210, "r": 20, "b": 30})
    bars.update_xaxes(tickformat="+.0%", showgrid=True, gridcolor="rgba(255,255,255,0.06)",
                      zeroline=True, zerolinecolor="rgba(255,255,255,0.25)")

    grouped = s["results"][method]["daily"].T.groupby(component_group).sum().T[GROUPS].cumsum()
    line = go.Figure([go.Scatter(x=grouped.index, y=grouped[gname], name=gname, mode="lines",
                                 line={"color": GROUP_COLOR[gname], "width": 2,
                                       "dash": "dot" if gname == "Baseline vs benchmark" else "solid"},
                                 hovertemplate=f"{gname}: %{{y:+.2%}}<extra></extra>") for gname in GROUPS])
    zero_line(base_layout(line, hovermode="x unified"))
    line.update_yaxes(tickformat="+.0%")

    ic = s["ic"].reindex(table.index)
    rows = table.rename(columns=LABELS).assign(**{"IC before": ic["IC before"], "IC in window": ic["IC in window"]})
    rows = rows.reset_index(names="Component")
    cols = [{"name": "Component", "id": "Component"}] + num_cols([LABELS[m] for m in METHODS], "+.2%") + \
           num_cols(["IC before", "IC in window"], "+.3f")
    style = signed_style([LABELS[m] for m in METHODS]) + \
        [{"if": {"filter_query": '{Component} = "Total active"'}, "fontWeight": "700", "backgroundColor": "var(--card-bg-alt)"}]
    return bars, line, rows.to_dict("records"), cols, style
