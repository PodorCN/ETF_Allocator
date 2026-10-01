from functools import cache

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, callback, dash_table, dcc, html

from backtest.signal_tearsheet import build_data
from data.results import cached
from pages.common import SERIES, TABLE_STYLE, base_layout, card, graph, note, oos_shade, page_header, zero_line
from port_con.config import CALIBRATION_END, L1_SIGNALS, L2_SIGNALS

# Signal Backtest page (/signals): each signal's own backtest, in sample
# (before CALIBRATION_END, used to calibrate) vs out of sample. Calculation:
# backtest/signal_tearsheet.py.

IS_COLOR, OOS_COLOR = SERIES[0], SERIES[1]
SIGNALS = [(f"L1 {layer.upper()}", name) for layer, sigs in L1_SIGNALS.items() for name in sigs] + \
          [("L2", name) for name in L2_SIGNALS]
DIVERGING = [[0, "#e66767"], [0.5, "#383835"], [1, "#3987e5"]]


@cache
def data() -> dict:
    """Saved by precompute.py."""
    return cached("signal_backtest", build_data)


def _sheet(name: str) -> dict:
    return next(s for s in data()["sheets"] if s["name"] == name)


def layout() -> list:
    return [
        page_header("Signal Backtest",
                    f"Each signal on its own · in sample before {CALIBRATION_END} (used to calibrate), "
                    f"out of sample after", "/signals"),

        html.Div("Loads saved results from precompute.py (computes them, ~10 s, if missing).",
                 className="kpi-delta mb-2"),
        dcc.Loading(type="dot", children=[
        dbc.Row(dbc.Col(card("Summary: in sample vs out of sample", dash_table.DataTable(
            id="sig-summary", merge_duplicate_headers=True, **TABLE_STYLE),
            note("IC = rank correlation with the next 21 trading days' return (L1: equity minus bonds, signed so > 0 "
                 "means the signal helped; L2: across sectors). t-stats adjust for overlapping returns. IC IR = mean / "
                 "std of weekly IC (L2 only). Hit rate: L1 = signal and return had the same sign; L2 = weeks with "
                 "IC > 0. Curve = the signal's weekly strategy below, annualized. Autocorr = signal this week vs "
                 "last week (low = more turnover)."))), className="mb-4"),

        dbc.Row([
            dbc.Col(card("L1 signal correlation", graph("sig-corr-ts", 380),
                         note("Below the diagonal: in sample. Above: out of sample.")), lg=6),
            dbc.Col(card("L2 signal correlation", graph("sig-corr-cs", 380),
                         note("Below the diagonal: in sample. Above: out of sample. Pooled over sectors and weeks.")),
                    lg=6),
        ], className="g-4 mb-4"),

        dbc.Row(dbc.Col(dbc.Card(dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Div("Signal", className="section-title"), width="auto"),
                dbc.Col(dcc.Dropdown(id="sig-select", options=[{"label": f"{layer}: {n}", "value": n} for layer, n in SIGNALS],
                                     value=SIGNALS[0][1], clearable=False, persistence=True, persistence_type="memory"),
                        xs=12, md=4),
                dbc.Col(html.Div(id="sig-desc", className="kpi-delta"), className="ms-md-2"),
            ], align="center", className="g-2 mb-3"),
            dbc.Row([
                dbc.Col([html.Div(id="sig-ic-title", className="kpi-label mb-1"), graph("sig-ic", 300)], lg=6),
                dbc.Col([html.Div(id="sig-q-title", className="kpi-label mb-1"), graph("sig-q", 300)], lg=6),
                dbc.Col([html.Div(id="sig-curve-title", className="kpi-label mb-1 mt-3"), graph("sig-curve", 300)], lg=6),
                dbc.Col([html.Div("IC by year · blue in sample, orange out of sample", className="kpi-label mb-1 mt-3"),
                         graph("sig-year", 300)], lg=6),
            ], className="g-3"),
        ]), className="section-card"))),
        ]),
    ]


def _summary_table() -> tuple[list, list]:
    metrics = [("IC", "+.3f"), ("t", "+.2f"), ("IC IR", "+.2f"), ("Hit rate", ".0%"), ("Curve ann.", "+.1%")]
    columns = [{"name": ["", "Signal"], "id": "Signal"}]
    for m, spec in metrics:
        columns += [{"name": [m, p], "id": f"{m} {p}", "type": "numeric", "format": {"specifier": spec}}
                    for p in ["In", "Out"]]
    columns.append({"name": ["", "Autocorr"], "id": "Autocorr", "type": "numeric", "format": {"specifier": ".2f"}})
    rows = []
    for s in data()["sheets"]:
        row = {"Signal": f"{s['layer']}: {s['name']}", "Autocorr": s["summary"]["autocorr"]}
        for m, _ in metrics:
            row[f"{m} In"], row[f"{m} Out"] = s["summary"]["is"][m], s["summary"]["oos"][m]
        rows.append(row)
    return rows, columns


def _corr_fig(C: dict) -> go.Figure:
    n = len(C["names"])
    z = [[None if r == c else (C["is"][r][c] if r > c else C["oos"][r][c]) for c in range(n)] for r in range(n)]
    fig = go.Figure(go.Heatmap(
        x=C["names"], y=C["names"], z=z, text=[["" if v is None else f"{v:.2f}" for v in row] for row in z],
        texttemplate="%{text}", zmin=-1, zmax=1, xgap=2, ygap=2, colorscale=DIVERGING,
        colorbar={"thickness": 10}, hovertemplate="%{y} vs %{x}: %{z:.2f}<extra></extra>"))
    base_layout(fig, margin={"t": 10, "l": 150, "r": 10, "b": 110})
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(tickangle=-30)
    return fig


def _oos(fig: go.Figure) -> go.Figure:
    return oos_shade(fig, CALIBRATION_END)


@callback(
    Output("sig-summary", "data"), Output("sig-summary", "columns"),
    Output("sig-corr-ts", "figure"), Output("sig-corr-cs", "figure"),
    Output("sig-desc", "children"),
    Output("sig-ic-title", "children"), Output("sig-q-title", "children"), Output("sig-curve-title", "children"),
    Output("sig-ic", "figure"), Output("sig-q", "figure"), Output("sig-curve", "figure"), Output("sig-year", "figure"),
    Input("sig-select", "value"),
)
def update(name):
    s = _sheet(name)
    x_range = [s["ic_line"]["dates"][0], s["curve"]["dates"][-1]]

    ic = go.Figure(go.Scatter(x=s["ic_line"]["dates"], y=s["ic_line"]["values"], mode="lines",
                              line={"color": IS_COLOR, "width": 2}, hovertemplate="%{x}: %{y:.3f}<extra></extra>"))
    base_layout(ic, showlegend=False, hovermode="x unified", margin={"t": 10, "l": 50, "r": 10, "b": 30})
    ic.update_xaxes(range=x_range)
    _oos(zero_line(ic))

    q = go.Figure([go.Bar(x=s["quantiles"]["labels"], y=s["quantiles"][p], name=label, width=0.3,
                          marker={"color": color, "line": {"width": 0}},
                          hovertemplate=label + " · %{x}: %{y:.2%}<extra></extra>")
                   for p, label, color in [("is", "In sample", IS_COLOR), ("oos", "Out of sample", OOS_COLOR)]])
    base_layout(q, barmode="group", bargap=0.35, margin={"t": 30, "l": 55, "r": 10, "b": 30})
    q.update_yaxes(tickformat=".1%")
    zero_line(q)

    curve = go.Figure(go.Scatter(x=s["curve"]["dates"], y=s["curve"]["values"], mode="lines",
                                 line={"color": IS_COLOR, "width": 2}, hovertemplate="%{x}: %{y:.3f}<extra></extra>"))
    base_layout(curve, showlegend=False, hovermode="x unified", margin={"t": 10, "l": 50, "r": 10, "b": 30})
    curve.update_xaxes(range=x_range)
    curve.update_yaxes(tickformat=".2f")
    _oos(zero_line(curve, 1))

    split_year = int(CALIBRATION_END[:4])
    year = go.Figure(go.Bar(x=s["yearly"]["years"], y=s["yearly"]["values"], width=0.6,
                            marker={"color": [IS_COLOR if y < split_year else OOS_COLOR for y in s["yearly"]["years"]],
                                    "line": {"width": 0}},
                            hovertemplate="%{x}: IC %{y:.3f}<extra></extra>"))
    base_layout(year, showlegend=False, margin={"t": 10, "l": 50, "r": 10, "b": 30})
    year.update_xaxes(dtick=2, tickformat="d")
    year.update_yaxes(tickformat=".2f")
    zero_line(year)

    bucket = "vs sector average" if s["kind"] == "cs" else "equity minus bonds"
    rows, columns = _summary_table()
    return (rows, columns, _corr_fig(data()["corr"]["ts"]), _corr_fig(data()["corr"]["cs"]), s["desc"],
            s["ic_line"]["label"], f"Average next-21-day return by signal bucket · {bucket}",
            f"{s['curve']['label']} · weekly, growth of 1", ic, q, curve, year)
