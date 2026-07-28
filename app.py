import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, ctx, dash_table, dcc, html, no_update

from config import (
    BENCHMARK_TICKER,
    CORR_LOOKBACK_OPTIONS,
    DEFAULT_CORR_LOOKBACK,
    REFRESH_INTERVAL_MS,
    TICKERS,
)
from data_utils import (
    compute_correlation,
    compute_portfolio_summary,
    compute_summary_returns,
    fetch_price_data,
    status as fetch_status,
)

TICKER_LABELS = list(TICKERS.keys())
DEFAULT_WEIGHT = round(100 / len(TICKER_LABELS), 2)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], title="ETF Allocator")
server = app.server


def kpi_value(value) -> html.Span:
    if pd.isna(value):
        return html.Span("-", className="kpi-value")
    color = "var(--up-green)" if value >= 0 else "var(--down-red)"
    return html.Span(f"{value:+.2f}%", className="kpi-value", style={"color": color})


def kpi_delta(value) -> html.Span:
    if pd.isna(value):
        return html.Span(f"vs {BENCHMARK_TICKER}: -", className="kpi-delta")
    color = "var(--up-green)" if value >= 0 else "var(--down-red)"
    return html.Span(
        f"vs {BENCHMARK_TICKER}: {value:+.2f}%", className="kpi-delta", style={"color": color}
    )


def kpi_card(label: str, value_id: str, delta_id: str) -> dbc.Col:
    return dbc.Col(
        dbc.Card(
            [
                html.Div(label, className="kpi-label"),
                html.Div(id=value_id),
                html.Div(id=delta_id),
            ],
            className="kpi-card",
        ),
        width=4,
    )


def pct_style(col_id: str) -> list:
    return [
        {
            "if": {"filter_query": f"{{{col_id}}} >= 0", "column_id": col_id},
            "color": "var(--up-green)",
            "fontWeight": "600",
        },
        {
            "if": {"filter_query": f"{{{col_id}}} < 0", "column_id": col_id},
            "color": "var(--down-red)",
            "fontWeight": "600",
        },
    ]


def weight_row(ticker: str) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    dbc.Checklist(
                        id=f"pin-{ticker}",
                        options=[{"label": "\U0001f4cc", "value": "pin"}],
                        value=[],
                        inline=True,
                        className="pin-check",
                    ),
                    html.Span(ticker, className="weight-label"),
                    dbc.InputGroup(
                        [
                            dcc.Input(
                                id=f"weight-{ticker}",
                                type="number",
                                min=0,
                                max=100,
                                step=0.5,
                                value=DEFAULT_WEIGHT,
                                className="form-control",
                            ),
                            dbc.InputGroupText("%"),
                        ],
                        size="sm",
                        className="weight-input-group",
                    ),
                ],
                className="weight-row-top",
            ),
            dcc.Slider(
                id=f"weight-slider-{ticker}",
                min=0,
                max=100,
                step=0.5,
                value=DEFAULT_WEIGHT,
                marks=None,
                tooltip={"placement": "bottom", "always_visible": False},
                className="weight-slider",
            ),
        ],
        className="weight-row",
    )


app.layout = dbc.Container(
    fluid=True,
    className="pb-5",
    children=[
        html.Div(
            className="app-navbar",
            children=dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("ETF Allocator"),
                            html.Div(
                                "ZSP · XIU · ZEB · HFIN · BANK · XEC · XCS  (CAD)",
                                className="app-subtitle",
                            ),
                        ],
                        width="auto",
                    ),
                    dbc.Col(
                        html.Span(id="status-pill", className="status-pill"),
                        width="auto",
                        align="center",
                        className="ms-auto",
                    ),
                ],
                justify="between",
                align="center",
            ),
        ),
        dcc.Interval(id="interval-refresh", interval=REFRESH_INTERVAL_MS, n_intervals=0),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div("ETF / Index Returns", className="section-title"),
                            dash_table.DataTable(
                                id="returns-table",
                                columns=[
                                    {"name": "ETF", "id": "ETF"},
                                    {
                                        "name": "Last Close",
                                        "id": "Last Close",
                                        "type": "numeric",
                                        "format": {"specifier": ".2f"},
                                    },
                                    {
                                        "name": "Daily %",
                                        "id": "Daily %",
                                        "type": "numeric",
                                        "format": {"specifier": "+.2f"},
                                    },
                                    {
                                        "name": "MTD %",
                                        "id": "MTD %",
                                        "type": "numeric",
                                        "format": {"specifier": "+.2f"},
                                    },
                                    {
                                        "name": "QTD %",
                                        "id": "QTD %",
                                        "type": "numeric",
                                        "format": {"specifier": "+.2f"},
                                    },
                                ],
                                style_as_list_view=True,
                                style_cell={
                                    "textAlign": "center",
                                    "padding": "10px",
                                    "fontFamily": "Inter",
                                    "backgroundColor": "var(--card-bg)",
                                    "color": "var(--text-primary)",
                                },
                                style_header={
                                    "fontWeight": "600",
                                    "backgroundColor": "var(--card-bg-alt)",
                                    "color": "var(--text-primary)",
                                    "border": "none",
                                },
                                style_data={
                                    "border": "none",
                                    "borderBottom": "1px solid var(--hairline)",
                                },
                                style_data_conditional=(
                                    pct_style("Daily %") + pct_style("MTD %") + pct_style("QTD %")
                                ),
                            ),
                        ]
                    ),
                    className="section-card",
                ),
                width=12,
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div("Portfolio Weights", className="section-title"),
                                html.Div(
                                    [weight_row(t) for t in TICKER_LABELS],
                                    className="weights-list",
                                ),
                                html.Div(id="weight-total", className="mt-2"),
                                dbc.Button(
                                    "Equal Weight (unpinned)",
                                    id="btn-equal-weight",
                                    size="sm",
                                    className="btn-equal-weight mt-2",
                                    color="secondary",
                                    outline=True,
                                ),
                            ]
                        ),
                        className="section-card h-100 weights-card",
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div("Portfolio Return", className="section-title"),
                                dbc.Row(
                                    [
                                        kpi_card("Daily", "port-daily", "port-daily-delta"),
                                        kpi_card("MTD", "port-mtd", "port-mtd-delta"),
                                        kpi_card("QTD", "port-qtd", "port-qtd-delta"),
                                    ],
                                    className="g-2",
                                ),
                                dcc.Graph(id="portfolio-chart", className="mt-3"),
                            ]
                        ),
                        className="section-card h-100",
                    ),
                    width=9,
                ),
            ]
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div("Correlation Matrix", className="section-title"),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="corr-lookback",
                                            options=[
                                                {"label": f"{d} trading days", "value": d}
                                                for d in CORR_LOOKBACK_OPTIONS
                                            ],
                                            value=DEFAULT_CORR_LOOKBACK,
                                            clearable=False,
                                        ),
                                        width=3,
                                    ),
                                ],
                                justify="between",
                                align="center",
                                className="mb-2",
                            ),
                            dcc.Graph(id="corr-heatmap"),
                        ]
                    ),
                    className="section-card",
                ),
                width=12,
            )
        ),
    ],
)


@app.callback(
    Output("status-pill", "children"),
    Output("status-pill", "className"),
    Output("weight-total", "children"),
    Output("weight-total", "className"),
    Output("returns-table", "data"),
    Output("port-daily", "children"),
    Output("port-mtd", "children"),
    Output("port-qtd", "children"),
    Output("port-daily-delta", "children"),
    Output("port-mtd-delta", "children"),
    Output("port-qtd-delta", "children"),
    Output("portfolio-chart", "figure"),
    Output("corr-heatmap", "figure"),
    Input("interval-refresh", "n_intervals"),
    Input("corr-lookback", "value"),
    [Input(f"weight-{t}", "value") for t in TICKER_LABELS],
)
def update_dashboard(_n, lookback, *weight_values):
    weights_pct = {t: (v or 0) for t, v in zip(TICKER_LABELS, weight_values)}
    total = sum(weights_pct.values())
    balanced = abs(total - 100) < 0.01
    weight_total_children = f"Total: {total:.1f}%" + ("" if balanced else " (should sum to 100%)")
    weight_total_class = "weight-total-badge " + ("balanced" if balanced else "unbalanced")

    try:
        df = fetch_price_data()
    except Exception as e:
        status_children = f"Data unavailable: {e}"
        empty_fig = go.Figure()
        return (
            status_children,
            "status-pill stale",
            weight_total_children,
            weight_total_class,
            [],
            kpi_value(float("nan")),
            kpi_value(float("nan")),
            kpi_value(float("nan")),
            kpi_delta(float("nan")),
            kpi_delta(float("nan")),
            kpi_delta(float("nan")),
            empty_fig,
            empty_fig,
        )

    as_of = fetch_status["as_of"]
    as_of_str = as_of.strftime("%Y-%m-%d") if as_of is not None else "-"
    if fetch_status["stale"]:
        status_children = f"Showing cached data as of {as_of_str} (refresh failed)"
        status_class = "status-pill stale"
    else:
        status_children = f"Data as of {as_of_str}"
        status_class = "status-pill"

    summary_table = compute_summary_returns(df)

    weights_frac = {t: w / 100.0 for t, w in weights_pct.items()}
    summary, port_index = compute_portfolio_summary(df, weights_frac)
    bench_summary, bench_index = compute_portfolio_summary(df, {BENCHMARK_TICKER: 1.0})

    def delta(key: str) -> float:
        a, b = summary[key], bench_summary[key]
        return float("nan") if pd.isna(a) or pd.isna(b) else a - b

    port_fig = go.Figure()
    port_fig.add_trace(
        go.Scatter(
            x=port_index.index,
            y=(port_index - 1) * 100,
            mode="lines",
            line={"color": "#4f8fdb", "width": 2.5},
            fill="tozeroy",
            fillcolor="rgba(79, 143, 219, 0.15)",
            name="Portfolio",
        )
    )
    port_fig.add_trace(
        go.Scatter(
            x=bench_index.index,
            y=(bench_index - 1) * 100,
            mode="lines",
            line={"color": "#8b96ac", "width": 1.75, "dash": "dot"},
            name=f"Benchmark ({BENCHMARK_TICKER})",
        )
    )
    port_fig.update_layout(
        title="Cumulative Return",
        yaxis_title="% Return",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        margin={"t": 60, "l": 40, "r": 20, "b": 30},
    )

    corr = compute_correlation(df, lookback=lookback)
    corr_fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu",
        zmin=-1,
        zmax=1,
    )
    corr_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"t": 20, "l": 20, "r": 20, "b": 20},
    )

    return (
        status_children,
        status_class,
        weight_total_children,
        weight_total_class,
        summary_table.to_dict("records"),
        kpi_value(summary["Daily %"]),
        kpi_value(summary["MTD %"]),
        kpi_value(summary["QTD %"]),
        kpi_delta(delta("Daily %")),
        kpi_delta(delta("MTD %")),
        kpi_delta(delta("QTD %")),
        port_fig,
        corr_fig,
    )


@app.callback(
    [Output(f"weight-{t}", "value") for t in TICKER_LABELS]
    + [Output(f"weight-slider-{t}", "value") for t in TICKER_LABELS],
    [Input(f"weight-{t}", "value") for t in TICKER_LABELS]
    + [Input(f"weight-slider-{t}", "value") for t in TICKER_LABELS],
    prevent_initial_call=True,
)
def sync_weight_controls(*_values):
    """Keep each ticker's number input and slider mirrored.

    A single callback that owns both directions - Dash's documented pattern
    for linking two controls to the same value without a circular-callback
    error. Uses ctx.triggered (not triggered_id) because "Equal Weight" can
    change several number inputs at once, and every one of those needs its
    slider synced, not just the first.
    """
    n = len(TICKER_LABELS)
    num_out = [no_update] * n
    slider_out = [no_update] * n

    for trig in ctx.triggered:
        comp_id = trig["prop_id"].split(".")[0]
        if comp_id.startswith("weight-slider-"):
            t = comp_id[len("weight-slider-") :]
            idx = TICKER_LABELS.index(t)
            num_out[idx] = trig["value"]
        elif comp_id.startswith("weight-"):
            t = comp_id[len("weight-") :]
            idx = TICKER_LABELS.index(t)
            slider_out[idx] = trig["value"]

    return num_out + slider_out


@app.callback(
    [Output(f"weight-{t}", "value", allow_duplicate=True) for t in TICKER_LABELS],
    Input("btn-equal-weight", "n_clicks"),
    [State(f"pin-{t}", "value") for t in TICKER_LABELS],
    [State(f"weight-{t}", "value") for t in TICKER_LABELS],
    prevent_initial_call=True,
)
def reset_weights(_n_clicks, *args):
    """Equal-weight all unpinned tickers; pinned tickers keep their value.

    The unpinned share of the pie is (100 - sum of pinned weights), split
    evenly across however many tickers are unpinned.
    """
    n = len(TICKER_LABELS)
    pins = args[:n]
    current = args[n:]

    pinned_idx = [i for i in range(n) if "pin" in (pins[i] or [])]
    unpinned_idx = [i for i in range(n) if i not in pinned_idx]

    if not unpinned_idx:
        return [no_update] * n

    pinned_total = sum((current[i] or 0) for i in pinned_idx)
    remaining = max(100 - pinned_total, 0)
    equal_share = round(remaining / len(unpinned_idx), 2)

    return [no_update if i in pinned_idx else equal_share for i in range(n)]


if __name__ == "__main__":
    app.run(debug=True)
