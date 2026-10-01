import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

from pages import constructor, portfolio_backtest, signal_backtest, snapshot

# The web app: one page per module in pages/, switched by URL.
#   /           ETF Constructor     pages/constructor.py
#   /signals    Signal Backtest     pages/signal_backtest.py
#   /snapshot   Snapshot            pages/snapshot.py
#   /backtest   Portfolio Backtest  pages/portfolio_backtest.py (performance, Brinson and signal attribution)
# Run: python app.py, then open http://localhost:8050

PAGES = {
    "/": constructor.layout,
    "/signals": signal_backtest.layout,
    "/snapshot": snapshot.layout,
    "/backtest": portfolio_backtest.layout,
}
# Old links that moved.
REDIRECTS = {"/attribution": "/backtest"}

# suppress_callback_exceptions: each page's components only exist while that
# page is shown, so callbacks may reference ids missing from the current layout.
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], title="ETF Allocator",
                suppress_callback_exceptions=True)
server = app.server

app.layout = dbc.Container(fluid=True, className="pb-5", children=[
    dcc.Location(id="url"),
    # Spinner only while switching pages, not while a page's own charts update.
    dcc.Loading(html.Div(id="page-content"), type="dot", delay_show=300,
                target_components={"page-content": "children"}),
])


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname):
    if pathname in REDIRECTS:
        return dcc.Location(id="redirect", href=REDIRECTS[pathname])
    return PAGES.get(pathname, constructor.layout)()


if __name__ == "__main__":
    app.run(debug=True)
