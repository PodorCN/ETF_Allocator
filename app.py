import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, ctx, dash_table, dcc, html, no_update

from config import (
    BENCHMARK_TICKER,
    COV_DEFAULT_HALFLIFE,
    COV_HALFLIFE_OPTIONS,
    CORR_LOOKBACK_OPTIONS,
    DEFAULT_CORR_LOOKBACK,
    OPT_COV_HALFLIFE,
    OPT_LOOKBACK,
    REFRESH_INTERVAL_MS,
    RISK_FREE_RATE,
    TARGET_EST_MONTHS,
    TARGET_HALFLIFE,
    TARGET_SKIP_MONTHS,
    TICKER_GROUPS,
    TICKER_NOTES,
    TICKERS,
)
from data_utils import (
    compute_correlation,
    compute_covariance,
    compute_portfolio_summary,
    compute_summary_returns,
    compute_target_portfolio,
    fetch_price_data,
    optimize_max_sharpe,
    status as fetch_status,
)

TICKER_LABELS = list(TICKERS.keys())
DEFAULT_WEIGHT = round(100 / len(TICKER_LABELS), 2)

GROUP_OF = {t: g for g, ts in TICKER_GROUPS for t in ts}

MARK_SPECS = [
    ("\u25c6", "#a78bfa"),  # Optimized (max Sharpe)
]


def build_slider_marks(*portfolios) -> dict:
    """Per-ticker dcc.Slider marks showing each portfolio's allocation.

    portfolios: aligned with MARK_SPECS - (weights Series | None) each.
    Returns {ticker: marks-dict}; weights are snapped to the slider's 5%
    step so the marker sits exactly on a stop.
    """
    out = {t: {} for t in TICKER_LABELS}
    for weights, (symbol, color) in zip(portfolios, MARK_SPECS):
        if weights is None:
            continue
        for t, w in weights.items():
            if t not in out:
                continue
            v = int(round(float(w) * 100 / 5.0) * 5)
            if v <= 0:
                continue
            entry = out[t].setdefault(v, {"label": "", "style": {}})
            entry["label"] += symbol
            entry["style"] = {
                "color": color,
                "fontSize": "10px",
                "fontWeight": "700",
                "lineHeight": "1",
            }
    return out

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
                    html.Span(ticker, id=f"lbl-{ticker}", className="weight-label"),
                    dbc.Tooltip(
                        TICKER_NOTES.get(ticker, ticker),
                        target=f"lbl-{ticker}",
                        placement="top",
                        className="etf-tip",
                    ),
                    dcc.Slider(
                        id=f"weight-slider-{ticker}",
                        min=0,
                        max=100,
                        step=5,
                        value=DEFAULT_WEIGHT,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": False},
                        className="weight-slider-inline",
                    ),
                    dbc.InputGroup(
                        [
                            dcc.Input(
                                id=f"weight-{ticker}",
                                type="number",
                                min=0,
                                max=100,
                                step=5,
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
        ],
        className="weight-row",
    )


def weights_panel() -> list:
    sections = []
    for group_name, tickers in TICKER_GROUPS:
        sections.append(
            html.Div(group_name.upper(), className="weights-group-header")
        )
        sections.extend(weight_row(t) for t in tickers)
    return sections


def brand_mark() -> html.Div:
    return html.Div("ET", className="brand-mark")


app.layout = dbc.Container(
    fluid=True,
    className="pb-5 app-shell",
    children=[
        html.Div(
            className="app-navbar",
            children=dbc.Container(
                fluid=True,
                children=dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [brand_mark(), html.H2("ETF Allocator")],
                                    className="brand-wrap",
                                ),
                                html.Div(
                                    "BMO SPDR US sector suite · global coverage · CAD total-return view",
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
                    className="g-3",
                ),
            ),
        ),
        dcc.Interval(id="interval-refresh", interval=REFRESH_INTERVAL_MS, n_intervals=0),
        dbc.Container(
            fluid=True,
            children=[
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("ETF / Index Total Returns", className="section-title"),
                                    dash_table.DataTable(
                                        id="returns-table",
                                        columns=[
                                            {"name": "", "id": "Group"},
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
                                            "padding": "9px 12px",
                                            "fontFamily": "Inter",
                                            "fontSize": "0.85rem",
                                            "backgroundColor": "transparent",
                                            "color": "var(--text-primary)",
                                            "border": "none",
                                        },
                                        style_cell_conditional=[
                                            {"if": {"column_id": "ETF"}, "textAlign": "left", "fontWeight": "600"},
                                            {"if": {"column_id": "Group"}, "width": "12%"},
                                        ],
                                        style_header={
                                            "fontWeight": "600",
                                            "fontSize": "0.72rem",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "0.06em",
                                            "backgroundColor": "transparent",
                                            "color": "var(--text-muted)",
                                            "border": "none",
                                            "borderBottom": "1px solid var(--hairline-strong)",
                                        },
                                        style_data={
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
                                            [
                                                html.Span("\u25c6 ", className="mark-opt"),
                                                html.Span("Optimized (max Sharpe) — hover a ticker for what it tracks"),
                                            ],
                                            className="marks-legend",
                                        ),
                                        html.Div(weights_panel(), className="weights-list"),
                                        html.Div(
                                            [
                                                html.Div(id="weight-total", className="weight-total-badge"),
                                                dbc.Button(
                                                    "Equal Weight (unpinned)",
                                                    id="btn-equal-weight",
                                                    size="sm",
                                                    className="btn-equal-weight",
                                                    color="secondary",
                                                    outline=True,
                                                ),
                                            ],
                                            className="weights-footer mt-2",
                                        ),
                                    ]
                                ),
                                className="section-card h-100 weights-card",
                            ),
                            width=12,
                            xl=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.Div("Portfolio Return", className="section-title"),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(
                                                        "Optimizers: max Sharpe on trailing 252d · Target on rolling 38M-2M window with exponential weights",
                                                        className="chart-caption no-margin",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown(
                                                        id="chart-window",
                                                        options=[
                                                            {"label": "Trailing 1Y", "value": 252},
                                                            {"label": "Trailing 2Y", "value": 504},
                                                            {"label": "Trailing 3Y", "value": 756},
                                                            {"label": "Full history", "value": "full"},
                                                        ],
                                                        value=252,
                                                        clearable=False,
                                                        className="matrix-dropdown chart-window-dd",
                                                    ),
                                                    width=6,
                                                    lg=2,
                                                ),
                                            ],
                                            justify="between",
                                            align="center",
                                            className="g-2",
                                        ),
                                        dbc.Row(
                                            [
                                                kpi_card("Daily", "port-daily", "port-daily-delta"),
                                                kpi_card("MTD", "port-mtd", "port-mtd-delta"),
                                                kpi_card("QTD", "port-qtd", "port-qtd-delta"),
                                            ],
                                            className="g-2",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dcc.Graph(id="portfolio-chart", className="mt-3 portfolio-chart"),
                                                    width=12,
                                                    xl=8,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.Div(
                                                            f"Optimized Allocation — max Sharpe, EWMA cov (hl {OPT_COV_HALFLIFE}d), rf {RISK_FREE_RATE:.0%}",
                                                            className="chart-caption",
                                                        ),
                                                        dcc.Graph(id="opt-alloc-chart", className="alloc-chart"),
                                                    ],
                                                    width=12,
                                                    xl=4,
                                                ),
                                            ],
                                        ),
                                    ]
                                ),
                                className="section-card h-100",
                            ),
                            width=12,
                            xl=8,
                        ),
                    ],
                    className="mt-4",
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                html.Div("Risk Matrix", className="section-title"),
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id="matrix-mode",
                                                    options=[
                                                        {
                                                            "label": "Correlation (equal-weighted)",
                                                            "value": "corr",
                                                        },
                                                        {
                                                            "label": "Covariance (exponential decay, annualized)",
                                                            "value": "cov",
                                                        },
                                                    ],
                                                    value="corr",
                                                    clearable=False,
                                                    className="matrix-dropdown",
                                                ),
                                                width=12,
                                                lg=4,
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
                                                    className="matrix-dropdown",
                                                ),
                                                width=6,
                                                lg=2,
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id="cov-halflife",
                                                    options=[
                                                        {"label": f"half-life {h}d", "value": h}
                                                        for h in COV_HALFLIFE_OPTIONS
                                                    ],
                                                    value=COV_DEFAULT_HALFLIFE,
                                                    clearable=False,
                                                    disabled=True,
                                                    className="matrix-dropdown",
                                                ),
                                                width=6,
                                                lg=2,
                                            ),
                                        ],
                                        justify="end",
                                        align="center",
                                        className="g-2 mb-2 matrix-controls",
                                    ),
                                    dcc.Graph(id="corr-heatmap"),
                                ]
                            ),
                            className="section-card",
                        ),
                        width=12,
                    ),
                    className="mt-4",
                ),
            ],
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
    Output("opt-alloc-chart", "figure"),
    *[Output(f"weight-slider-{t}", "marks") for t in TICKER_LABELS],
    Output("corr-heatmap", "figure"),
    Output("cov-halflife", "disabled"),
    Input("interval-refresh", "n_intervals"),
    Input("corr-lookback", "value"),
    Input("cov-halflife", "value"),
    Input("matrix-mode", "value"),
    Input("chart-window", "value"),
    [Input(f"weight-{t}", "value") for t in TICKER_LABELS],
)
def update_dashboard(_n, lookback, halflife, mode, chart_window, *weight_values):
    weights_pct = {t: (v or 0) for t, v in zip(TICKER_LABELS, weight_values)}
    total = sum(weights_pct.values())
    balanced = abs(total - 100) < 0.01
    weight_total_children = f"Total: {total:.1f}%" + ("" if balanced else " — should sum to 100%")
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
            *([{}] * len(TICKER_LABELS)),
            empty_fig,
            True,
        )

    as_of = fetch_status["as_of"]
    as_of_str = as_of.strftime("%Y-%m-%d") if as_of is not None else "-"
    if fetch_status["stale"]:
        status_children = f"Showing cached data as of {as_of_str} (refresh failed)"
        status_class = "status-pill stale"
    else:
        status_children = f"Data as of {as_of_str}"
        status_class = "status-pill"

    summary_rows = compute_summary_returns(df)
    if "Group" not in summary_rows.columns and not summary_rows.empty:
        summary_rows.insert(0, "Group", [GROUP_OF[t].split(" ")[0] for t in summary_rows["ETF"]])

    weights_frac = {t: w / 100.0 for t, w in weights_pct.items()}
    summary, port_index = compute_portfolio_summary(df, weights_frac)
    bench_summary, bench_index = compute_portfolio_summary(df, {BENCHMARK_TICKER: 1.0})

    def cut(idx: pd.Series) -> pd.Series:
        """Trim to the selected window and rebase so the window starts at 0%."""
        if isinstance(chart_window, int):
            idx = idx.iloc[-chart_window:]
        return idx / idx.iloc[0] if len(idx) else idx

    port_index, bench_index = cut(port_index), cut(bench_index)

    def delta(key: str) -> float:
        a, b = summary[key], bench_summary[key]
        return float("nan") if pd.isna(a) or pd.isna(b) else a - b

    port_fig = go.Figure()
    port_fig.add_trace(
        go.Scatter(
            x=port_index.index,
            y=(port_index - 1) * 100,
            mode="lines",
            line={"color": "#38bdf8", "width": 2.5},
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.12)",
            name="Portfolio",
        )
    )

    opt_weights = optimize_max_sharpe(
        df, risk_free=RISK_FREE_RATE, lookback=OPT_LOOKBACK, halflife=OPT_COV_HALFLIFE
    )
    if opt_weights is not None and opt_weights.sum() > 0:
        _, opt_index_full = compute_portfolio_summary(df, opt_weights.to_dict())
        opt_index = cut(opt_index_full)
        port_fig.add_trace(
            go.Scatter(
                x=opt_index.index,
                y=(opt_index - 1) * 100,
                mode="lines",
                line={"color": "#a78bfa", "width": 2.0},
                name="Optimized (max Sharpe)",
            )
        )
    else:
        opt_weights = None

    tgt_weights = compute_target_portfolio(
        df,
        risk_free=RISK_FREE_RATE,
        est_months=TARGET_EST_MONTHS,
        skip_months=TARGET_SKIP_MONTHS,
        halflife=TARGET_HALFLIFE,
    )
    if tgt_weights is not None and tgt_weights.sum() > 0:
        _, tgt_index_full = compute_portfolio_summary(df, tgt_weights.to_dict())
        tgt_index = cut(tgt_index_full)
        port_fig.add_trace(
            go.Scatter(
                x=tgt_index.index,
                y=(tgt_index - 1) * 100,
                mode="lines",
                line={"color": "#34d399", "width": 2.0, "dash": "dash"},
                name=f"Target ({TARGET_EST_MONTHS}M-{TARGET_SKIP_MONTHS}M EW, hl {TARGET_HALFLIFE}d)",
            )
        )

    port_fig.add_trace(
        go.Scatter(
            x=bench_index.index,
            y=(bench_index - 1) * 100,
            mode="lines",
            line={"color": "#64748b", "width": 1.75, "dash": "dot"},
            name=f"Benchmark ({BENCHMARK_TICKER})",
        )
    )
    port_fig.update_layout(
        title=None,
        yaxis_title="% Return",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "size": 12, "color": "#94a3b8"},
        hovermode="x unified",
        hoverlabel={"bgcolor": "#1e293b", "font_size": 12},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        margin={"t": 30, "l": 40, "r": 20, "b": 30},
        xaxis={"gridcolor": "rgba(148, 163, 184, 0.08)"},
        yaxis_gridcolor="rgba(148, 163, 184, 0.08)",
    )

    alloc_series = [
        ("Optimized", opt_weights, "#a78bfa"),
    ]
    if any(w is not None for _, w, _ in alloc_series):
        rows = {}
        for name, w, _ in alloc_series:
            if w is None:
                continue
            for t, v in w.items():
                if v > 0.0005:
                    rows.setdefault(t, {})[name] = v * 100
        alloc_df = pd.DataFrame.from_dict(rows, orient="index").fillna(0.0)
        alloc_df["total"] = alloc_df.max(axis=1)
        alloc_df = alloc_df.sort_values("total").drop(columns="total")
        fig = go.Figure()
        for name, w, color in alloc_series:
            if name not in alloc_df.columns:
                continue
            fig.add_trace(
                go.Bar(
                    x=alloc_df[name],
                    y=alloc_df.index,
                    orientation="h",
                    name=name,
                    marker={"color": color},
                    text=[f"{v:.1f}%" if v > 0 else "" for v in alloc_df[name]],
                    textposition="outside",
                    textfont={"size": 10, "color": "#94a3b8"},
                    cliponaxis=False,
                    hovertemplate="%{y}: %{x:.2f}%<extra>" + name + "</extra>",
                )
            )
        alloc_fig = fig
        max_x = float(alloc_df.to_numpy().max())
        alloc_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"family": "Inter", "size": 11, "color": "#94a3b8"},
            showlegend=True,
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.01,
                "xanchor": "left",
                "x": 0,
                "font": {"size": 10},
            },
            barmode="group",
            bargap=0.35,
            margin={"t": 26, "l": 52, "r": 48, "b": 24},
            xaxis={
                "gridcolor": "rgba(148, 163, 184, 0.08)",
                "range": [0, max_x * 1.2],
            },
            yaxis={"tickfont": {"size": 10}},
        )
    else:
        alloc_fig = go.Figure()

    slider_marks = build_slider_marks(opt_weights)

    is_cov = mode == "cov"
    if is_cov:
        matrix = compute_covariance(df, lookback=lookback, halflife=halflife)
        corr_fig = px.imshow(
            matrix,
            text_auto=".3f",
            color_continuous_scale="Sunsetdark",
            aspect="auto",
        )
        corr_fig.update_layout(coloraxis_colorbar={"title": "Cov"})
    else:
        matrix = compute_correlation(df, lookback=lookback)
        corr_fig = px.imshow(
            matrix,
            text_auto=".2f",
            color_continuous_scale="Tealrose",
            zmin=-1,
            zmax=1,
            aspect="auto",
        )
        corr_fig.update_layout(coloraxis_colorbar={"title": "ρ"})
    corr_fig.update_traces(xgap=2, ygap=2)
    corr_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "size": 11, "color": "#94a3b8"},
        margin={"t": 20, "l": 20, "r": 20, "b": 20},
    )

    return (
        status_children,
        status_class,
        weight_total_children,
        weight_total_class,
        summary_rows.to_dict("records"),
        kpi_value(summary["Daily %"]),
        kpi_value(summary["MTD %"]),
        kpi_value(summary["QTD %"]),
        kpi_delta(delta("Daily %")),
        kpi_delta(delta("MTD %")),
        kpi_delta(delta("QTD %")),
        port_fig,
        alloc_fig,
        *[slider_marks[t] for t in TICKER_LABELS],
        corr_fig,
        not is_cov,
    )


@app.callback(
    Output("cov-halflife", "disabled", allow_duplicate=True),
    Output("cov-halflife", "className"),
    Input("matrix-mode", "value"),
    prevent_initial_call=True,
)
def sync_halflife_visibility(mode):
    """Grey out (and disable) the half-life selector unless covariance is shown."""
    return mode != "cov", "" if mode == "cov" else "control-disabled"


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
