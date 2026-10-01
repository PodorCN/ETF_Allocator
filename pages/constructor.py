from functools import cache

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, callback, ctx, dash_table, dcc, html, no_update

from config import BENCHMARK_TICKER, CORR_LOOKBACK_OPTIONS, DEFAULT_CORR_LOOKBACK, HOLDINGS, REFRESH_INTERVAL_MS
from data.results import cached
from data_utils import (
    compute_correlation,
    compute_portfolio_summary,
    compute_summary_returns,
    fetch_price_data,
    status as fetch_status,
)
from pages.common import page_header
from port_con.config import METHOD
from port_con.explain import snapshot
from port_con.portfolio import rebalance_dates

# ETF Constructor page (/): what-if weights on the ETFs we actually hold, with
# live returns from Yahoo Finance. Starts from the strategy's latest weights.

INSTRUMENTS = list(HOLDINGS)
STEP = 0.1


@cache
def strategy_weights() -> dict[str, float]:
    """Latest strategy weight per instrument, in % (managers under their own label). Saved by precompute.py."""
    def compute():
        w = snapshot(rebalance_dates()[-1], METHOD)["weights"]
        held = w["Holding"].str.split(".").str[0]
        out = w["Final"].fillna(0).groupby(held).sum() * 100
        return {t: round(float(out.get(t, 0.0)), 1) for t in INSTRUMENTS}
    return cached("constructor_weights", compute)


def ret_value(value) -> html.Span:
    if pd.isna(value):
        return html.Span("-", className="kpi-value")
    color = "var(--up-green)" if value >= 0 else "var(--down-red)"
    return html.Span(f"{value:+.2f}%", className="kpi-value", style={"color": color})


def ret_delta(value) -> html.Span:
    if pd.isna(value):
        return html.Span(f"vs {BENCHMARK_TICKER}: -", className="kpi-delta")
    color = "var(--up-green)" if value >= 0 else "var(--down-red)"
    return html.Span(f"vs {BENCHMARK_TICKER}: {value:+.2f}%", className="kpi-delta", style={"color": color})


def ret_card(label: str, value_id: str, delta_id: str) -> dbc.Col:
    return dbc.Col(dbc.Card([html.Div(label, className="kpi-label"), html.Div(id=value_id), html.Div(id=delta_id)],
                            className="kpi-card"), width=4)


def pct_style(col_id: str) -> list:
    return [
        {"if": {"filter_query": f"{{{col_id}}} >= 0", "column_id": col_id}, "color": "var(--up-green)", "fontWeight": "600"},
        {"if": {"filter_query": f"{{{col_id}}} < 0", "column_id": col_id}, "color": "var(--down-red)", "fontWeight": "600"},
    ]


def weight_row(ticker: str, value: float) -> html.Div:
    return html.Div([
        html.Div([
            dbc.Checklist(id=f"pin-{ticker}", options=[{"label": "\U0001f4cc", "value": "pin"}], value=[], inline=True,
                          className="pin-check", persistence=True, persistence_type="memory"),
            html.Span(ticker, className="weight-label"),
            dbc.InputGroup([
                dcc.Input(id=f"weight-{ticker}", type="number", min=0, max=100, step=STEP, value=value,
                          className="form-control", persistence=True, persistence_type="memory"),
                dbc.InputGroupText("%"),
            ], size="sm", className="weight-input-group"),
        ], className="weight-row-top"),
        dcc.Slider(id=f"weight-slider-{ticker}", min=0, max=100, step=STEP, value=value, persistence=True,
                   persistence_type="memory", marks=None, tooltip={"placement": "bottom", "always_visible": False},
                   className="weight-slider"),
    ], className="weight-row")


def returns_table() -> dash_table.DataTable:
    cols = [{"name": "ETF", "id": "ETF"}, {"name": "Last Close", "id": "Last Close", "type": "numeric",
                                            "format": {"specifier": ".2f"}}]
    cols += [{"name": c, "id": c, "type": "numeric", "format": {"specifier": "+.2f"}} for c in ["Daily %", "MTD %", "QTD %"]]
    return dash_table.DataTable(
        id="returns-table", columns=cols, style_as_list_view=True,
        style_table={"overflowX": "auto", "maxHeight": "420px", "overflowY": "auto"}, fixed_rows={"headers": True},
        style_cell={"textAlign": "center", "padding": "10px", "fontFamily": "Inter",
                    "backgroundColor": "var(--card-bg)", "color": "var(--text-primary)"},
        style_header={"fontWeight": "600", "backgroundColor": "var(--card-bg-alt)", "color": "var(--text-primary)",
                      "border": "none"},
        style_data={"border": "none", "borderBottom": "1px solid var(--hairline)"},
        style_data_conditional=pct_style("Daily %") + pct_style("MTD %") + pct_style("QTD %"),
    )


def layout() -> list:
    defaults = strategy_weights()
    return [
        page_header("ETF Constructor",
                    f"The {len(INSTRUMENTS)} ETFs we hold (CAD) · starts from the latest strategy weights",
                    "/", extra=html.Span(id="status-pill", className="status-pill")),
        dcc.Interval(id="interval-refresh", interval=REFRESH_INTERVAL_MS, n_intervals=0),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div("Portfolio Weights", className="section-title"),
                html.Div([weight_row(t, defaults[t]) for t in INSTRUMENTS], className="weights-list"),
                html.Div(id="weight-total", className="mt-2"),
                html.Div([
                    dbc.Button("Strategy weights", id="btn-strategy-weight", size="sm", color="secondary",
                               outline=True, className="btn-equal-weight me-2"),
                    dbc.Button("Equal weight (unpinned)", id="btn-equal-weight", size="sm", color="secondary",
                               outline=True, className="btn-equal-weight"),
                ], className="mt-2"),
            ]), className="section-card h-100 weights-card"), lg=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div("Portfolio Return", className="section-title"),
                dbc.Row([ret_card("Daily", "port-daily", "port-daily-delta"),
                         ret_card("MTD", "port-mtd", "port-mtd-delta"),
                         ret_card("QTD", "port-qtd", "port-qtd-delta")], className="g-2"),
                dcc.Graph(id="portfolio-chart", className="mt-3"),
            ]), className="section-card h-100"), lg=9),
        ]),

        dbc.Row(dbc.Col(dbc.Card(dbc.CardBody([
            html.Div("ETF Returns", className="section-title"),
            returns_table(),
        ]), className="section-card"))),

        dbc.Row(dbc.Col(dbc.Card(dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Div("Correlation Matrix", className="section-title"), width="auto"),
                dbc.Col(dcc.Dropdown(id="corr-lookback",
                                     options=[{"label": f"{d} trading days", "value": d} for d in CORR_LOOKBACK_OPTIONS],
                                     value=DEFAULT_CORR_LOOKBACK, clearable=False, persistence=True,
                                     persistence_type="memory"), width=3),
            ], justify="between", align="center", className="mb-2"),
            dcc.Graph(id="corr-heatmap", style={"height": "640px"}),
        ]), className="section-card"))),
    ]


@callback(
    Output("status-pill", "children"), Output("status-pill", "className"),
    Output("weight-total", "children"), Output("weight-total", "className"),
    Output("returns-table", "data"),
    Output("port-daily", "children"), Output("port-mtd", "children"), Output("port-qtd", "children"),
    Output("port-daily-delta", "children"), Output("port-mtd-delta", "children"), Output("port-qtd-delta", "children"),
    Output("portfolio-chart", "figure"), Output("corr-heatmap", "figure"),
    Input("interval-refresh", "n_intervals"), Input("corr-lookback", "value"),
    [Input(f"weight-{t}", "value") for t in INSTRUMENTS],
)
def update_dashboard(_n, lookback, *weight_values):
    weights_pct = {t: (v or 0) for t, v in zip(INSTRUMENTS, weight_values)}
    total = sum(weights_pct.values())
    if abs(total - 100) < 0.05:
        total_text, total_class = f"Total: {total:.1f}%", "balanced"
    elif total > 100:
        total_text, total_class = f"Total: {total:.1f}% ({total - 100:.1f}% leverage)", "balanced"
    else:
        total_text, total_class = f"Total: {total:.1f}% ({100 - total:.1f}% cash)", "unbalanced"

    try:
        df = fetch_price_data()
    except Exception as e:
        empty = go.Figure()
        return (f"Data unavailable: {e}", "status-pill stale", total_text, "weight-total-badge " + total_class, [],
                *[ret_value(float("nan"))] * 3, *[ret_delta(float("nan"))] * 3, empty, empty)

    as_of = fetch_status["as_of"]
    as_of_str = as_of.strftime("%Y-%m-%d") if as_of is not None else "-"
    if fetch_status["stale"]:
        status_children, status_class = f"Showing cached data as of {as_of_str} (refresh failed)", "status-pill stale"
    else:
        status_children, status_class = f"Data as of {as_of_str}", "status-pill"

    summary, port_index = compute_portfolio_summary(df, {t: w / 100.0 for t, w in weights_pct.items()})
    bench_summary, bench_index = compute_portfolio_summary(df, {BENCHMARK_TICKER: 1.0})

    def delta(key: str) -> float:
        a, b = summary[key], bench_summary[key]
        return float("nan") if pd.isna(a) or pd.isna(b) else a - b

    port_fig = go.Figure()
    port_fig.add_trace(go.Scatter(x=port_index.index, y=(port_index - 1) * 100, mode="lines", name="Portfolio",
                                  line={"color": "#4f8fdb", "width": 2.5}, fill="tozeroy",
                                  fillcolor="rgba(79, 143, 219, 0.15)"))
    port_fig.add_trace(go.Scatter(x=bench_index.index, y=(bench_index - 1) * 100, mode="lines",
                                  name=f"Benchmark ({BENCHMARK_TICKER})",
                                  line={"color": "#8b96ac", "width": 1.75, "dash": "dot"}))
    port_fig.update_layout(title="Cumulative Return", yaxis_title="% Return", template="plotly_dark",
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
                           margin={"t": 60, "l": 40, "r": 20, "b": 30})

    corr = compute_correlation(df, lookback=lookback)
    corr_fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu", zmin=-1, zmax=1)
    corr_fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           margin={"t": 20, "l": 20, "r": 20, "b": 20})

    return (status_children, status_class, total_text, "weight-total-badge " + total_class,
            compute_summary_returns(df).to_dict("records"),
            ret_value(summary["Daily %"]), ret_value(summary["MTD %"]), ret_value(summary["QTD %"]),
            ret_delta(delta("Daily %")), ret_delta(delta("MTD %")), ret_delta(delta("QTD %")),
            port_fig, corr_fig)


@callback(
    [Output(f"weight-{t}", "value") for t in INSTRUMENTS] + [Output(f"weight-slider-{t}", "value") for t in INSTRUMENTS],
    [Input(f"weight-{t}", "value") for t in INSTRUMENTS] + [Input(f"weight-slider-{t}", "value") for t in INSTRUMENTS],
    prevent_initial_call=True,
)
def sync_weight_controls(*_values):
    """Keep each ticker's number input and slider mirrored.

    A single callback that owns both directions - Dash's documented pattern
    for linking two controls to the same value without a circular-callback
    error. Uses ctx.triggered (not triggered_id) because the buttons can
    change several number inputs at once, and every one of those needs its
    slider synced, not just the first.
    """
    n = len(INSTRUMENTS)
    num_out, slider_out = [no_update] * n, [no_update] * n
    for trig in ctx.triggered:
        comp_id = trig["prop_id"].split(".")[0]
        if comp_id.startswith("weight-slider-"):
            num_out[INSTRUMENTS.index(comp_id[len("weight-slider-"):])] = trig["value"]
        elif comp_id.startswith("weight-"):
            slider_out[INSTRUMENTS.index(comp_id[len("weight-"):])] = trig["value"]
    return num_out + slider_out


@callback(
    [Output(f"weight-{t}", "value", allow_duplicate=True) for t in INSTRUMENTS],
    Input("btn-equal-weight", "n_clicks"),
    [State(f"pin-{t}", "value") for t in INSTRUMENTS],
    [State(f"weight-{t}", "value") for t in INSTRUMENTS],
    prevent_initial_call=True,
)
def reset_weights(_n_clicks, *args):
    """Equal-weight all unpinned tickers; pinned tickers keep their value.

    The unpinned share of the pie is (100 - sum of pinned weights), split
    evenly across however many tickers are unpinned.
    """
    n = len(INSTRUMENTS)
    pins, current = args[:n], args[n:]
    pinned_idx = [i for i in range(n) if "pin" in (pins[i] or [])]
    unpinned_idx = [i for i in range(n) if i not in pinned_idx]
    if not unpinned_idx:
        return [no_update] * n
    remaining = max(100 - sum((current[i] or 0) for i in pinned_idx), 0)
    equal_share = round(remaining / len(unpinned_idx), 2)
    return [no_update if i in pinned_idx else equal_share for i in range(n)]


@callback(
    [Output(f"weight-{t}", "value", allow_duplicate=True) for t in INSTRUMENTS],
    Input("btn-strategy-weight", "n_clicks"),
    [State(f"pin-{t}", "value") for t in INSTRUMENTS],
    prevent_initial_call=True,
)
def strategy_reset(_n_clicks, *pins):
    """Set every unpinned ticker back to its latest strategy weight."""
    w = strategy_weights()
    return [no_update if "pin" in (p or []) else w[t] for t, p in zip(INSTRUMENTS, pins)]
