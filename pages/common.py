import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

# Shared building blocks for every page of the app: header with the page
# switcher, cards, KPI tiles, table style, chart theme and colors.

# Page switcher, in the order shown in every header.
PAGES = {
    "/": "ETF Constructor",
    "/signals": "Signal Backtest",
    "/snapshot": "Snapshot",
    "/backtest": "Portfolio Backtest",
}

# Categorical colors in fixed order (dataviz reference palette, dark steps).
SERIES = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
UP, DOWN, MUTED = "#34c778", "#ff5d72", "#8b96ac"
GRAPH_CONFIG = {"displayModeBar": False}


def page_header(title: str, subtitle, active: str, extra=None) -> html.Div:
    """Gradient header: title + subtitle on the left, page switcher (and `extra`) on the right."""
    nav = html.Div([dcc.Link(label, href=path, className="page-link" + (" active" if path == active else ""))
                    for path, label in PAGES.items()], className="page-nav")
    return html.Div(className="app-navbar", children=dbc.Row([
        dbc.Col([html.H2(title), html.Div(subtitle, className="app-subtitle")], width="auto"),
        dbc.Col([nav, extra] if extra is not None else nav, width="auto", align="center",
                className="ms-auto navbar-right"),
    ], justify="between", align="center"))


def controls(*cols) -> dbc.Row:
    """A card holding a row of controls (each argument is a dbc.Col)."""
    return dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(dbc.Row(list(cols), align="center", className="g-3")),
                                    className="section-card")))


def toggle(id_: str, options: dict, value) -> dbc.RadioItems:
    """Segmented button group; `options` maps value -> label."""
    return dbc.RadioItems(id=id_, options=[{"label": l, "value": v} for v, l in options.items()], value=value,
                          inline=True, className="btn-group period-btns", inputClassName="btn-check",
                          labelClassName="btn btn-outline-secondary btn-sm", labelCheckedClassName="active")


def card(title, *children, extra=None) -> dbc.Card:
    header = dbc.Row([dbc.Col(html.Div(title, className="section-title"), width="auto"),
                      dbc.Col(extra, width="auto") if extra is not None else None],
                     justify="between", align="center", className="mb-2")
    return dbc.Card(dbc.CardBody([header, *children]), className="section-card h-100")


def note(text: str) -> html.Div:
    return html.Div(text, className="kpi-delta mt-2", style={"textAlign": "left"})


def graph(id_: str, height: int | None = None) -> dcc.Graph:
    return dcc.Graph(figure=EMPTY_FIG, id=id_, config=GRAPH_CONFIG, style={"height": f"{height}px"} if height else None)


def pct(x: float, digits: int = 2) -> str:
    return "-" if pd.isna(x) else f"{round(x, digits + 2) + 0.0:+.{digits}%}"  # + 0.0 turns -0.0 into 0.0


def bps(x: float) -> str:
    return "-" if pd.isna(x) else f"{round(x * 1e4) + 0.0:+,.0f} bp"


def kpi(label: str, value_id: str, sub_id: str) -> dbc.Col:
    return dbc.Col(
        dbc.Card([html.Div(label, className="kpi-label"), html.Div(id=value_id), html.Div(id=sub_id, className="kpi-delta")],
                 className="kpi-card"),
        xs=6, md=3, xl=True,
    )


def kpi_value(x: float, neutral: bool = False, fmt=None) -> html.Span:
    """KPI number: green / red by sign unless `neutral`. `fmt` formats the number (default: signed %)."""
    x = round(x, 4) + 0.0 if not pd.isna(x) else x
    color = "var(--text-primary)" if neutral or pd.isna(x) else ("var(--up-green)" if x >= 0 else "var(--down-red)")
    text = "-" if pd.isna(x) else (fmt(x) if fmt else pct(x))
    return html.Span(text, className="kpi-value", style={"color": color})


def base_layout(fig: go.Figure, **kw) -> go.Figure:
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": "#e7ebf3"}, hoverlabel={"font": {"family": "Inter"}},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
        **{"margin": {"t": 30, "l": 50, "r": 20, "b": 30}, **kw},
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(255,255,255,0.15)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.25)")
    return fig


def zero_line(fig: go.Figure, y: float = 0) -> go.Figure:
    fig.add_hline(y=y, line={"color": "rgba(255,255,255,0.25)", "width": 1})
    return fig


def oos_shade(fig: go.Figure, split: str, end="2100-01-01") -> go.Figure:
    """Shade the out-of-sample period, from `split` to `end`."""
    fig.add_vrect(x0=split, x1=end, fillcolor="#8b96ac", opacity=0.10, line_width=0, layer="below")
    fig.add_vline(x=split, line={"color": "#8b96ac", "width": 1})
    fig.add_annotation(x=split, y=1, yref="paper", text="out of sample", showarrow=False,
                       xanchor="left", yanchor="top", xshift=4, font={"color": "#8b96ac", "size": 11})
    return fig


EMPTY_FIG = base_layout(go.Figure())
EMPTY_FIG.update_xaxes(visible=False)
EMPTY_FIG.update_yaxes(visible=False)

TEXT_COLUMNS = ["Segment", "Asset", "Signal", "Layer", "Side", "Inputs", "Sleeve", "Holding", "Portfolio", "Component",
                "ETF", "Tilt"]

TABLE_STYLE = {
    "style_as_list_view": True,
    "style_table": {"overflowX": "auto"},
    "style_cell": {"textAlign": "right", "padding": "9px 12px", "fontFamily": "Inter",
                   "backgroundColor": "var(--card-bg)", "color": "var(--text-primary)", "fontSize": "0.9rem"},
    "style_cell_conditional": [{"if": {"column_id": c}, "textAlign": "left", "fontWeight": "600"} for c in TEXT_COLUMNS],
    "style_header": {"fontWeight": "600", "backgroundColor": "var(--card-bg-alt)", "color": "var(--text-primary)",
                     "border": "none", "textAlign": "right"},
    "style_header_conditional": [{"if": {"column_id": c}, "textAlign": "left"} for c in TEXT_COLUMNS],
    "style_data": {"border": "none", "borderBottom": "1px solid var(--hairline)"},
}


def num_cols(cols: list[str], spec: str) -> list[dict]:
    """DataTable numeric columns with a d3 format `spec` (e.g. "+.2%")."""
    return [{"name": c, "id": c, "type": "numeric", "format": {"specifier": spec}} for c in cols]


def signed_style(cols: list[str]) -> list:
    out = []
    for c in cols:
        out += [{"if": {"filter_query": f"{{{c}}} > 0", "column_id": c}, "color": "var(--up-green)"},
                {"if": {"filter_query": f"{{{c}}} < 0", "column_id": c}, "color": "var(--down-red)"}]
    return out
