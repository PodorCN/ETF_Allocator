# Shared pieces of the standalone HTML reports (backtest/report.py,
# backtest/signal_tearsheet.py): page styles and the chart theme helpers.
# Colors: the dataviz reference palette (categorical slots in fixed order,
# light and dark steps), chart chrome and ink tokens.

PLOTLY = '<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"></script>'

CSS = """:root {
  color-scheme: light;
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --ring: rgba(11,11,11,0.10); --up: #006300; --down: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --ring: rgba(255,255,255,0.10); --up: #0ca30c; --down: #e66767;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --ring: rgba(255,255,255,0.10); --up: #0ca30c; --down: #e66767;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
       font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1120px; margin: 0 auto; padding: 32px 16px 48px; }
h1 { font-size: 1.5rem; margin: 0 0 4px; }
.sub { color: var(--ink-2); margin: 0 0 24px; font-size: 0.95rem; line-height: 1.5; }
.card { background: var(--surface); border: 1px solid var(--ring); border-radius: 12px;
        padding: 16px 16px 8px; margin-bottom: 16px; }
.card h2 { font-size: 1rem; margin: 0 0 2px; }
.card p { color: var(--ink-2); font-size: 0.85rem; margin: 0 0 8px; }
.chart { width: 100%; height: 340px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 760px) { .grid2 { grid-template-columns: 1fr; } .chart { height: 280px; } }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 0.88rem; font-variant-numeric: tabular-nums; }
th, td { padding: 8px 10px; text-align: right; border-bottom: 1px solid var(--grid); white-space: nowrap; }
th:first-child, td:first-child { text-align: left; }
th { color: var(--ink-2); font-weight: 600; }
.key { display: inline-block; width: 14px; height: 2px; vertical-align: middle; margin-right: 8px; border-radius: 1px; }
.toggle button { font: inherit; font-size: 0.85rem; padding: 4px 12px; margin-right: 6px; border-radius: 6px;
  border: 1px solid var(--axis); background: transparent; color: var(--ink-2); cursor: pointer; }
.toggle button[aria-pressed="true"] { background: var(--grid); color: var(--ink); font-weight: 600; }
.notes { color: var(--ink-2); font-size: 0.82rem; line-height: 1.6; margin: 8px 0 0; padding-left: 18px; }
"""

# THEMES, mode(), pct(), layout(), line(), CONFIG. Re-render on theme change with
# watchTheme(render).
JS = """const THEMES = {
  light: { surface: "#fcfcfb", ink: "#0b0b0b", ink2: "#52514e", muted: "#898781", grid: "#e1e0d9", axis: "#c3c2b7",
           series: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"], groupExtra: ["#008300", "#4a3aa7", "#e34948"], bench: "#898781" },
  dark:  { surface: "#1a1a19", ink: "#ffffff", ink2: "#c3c2b7", muted: "#898781", grid: "#2c2c2a", axis: "#383835",
           series: ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"], groupExtra: ["#008300", "#9085e9", "#e66767"], bench: "#898781" },
};

function mode() {
  const t = document.documentElement.getAttribute("data-theme");
  if (t === "light" || t === "dark") return t;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

const pct = (v, d = 1) => v == null ? "–" : (v >= 0 ? "+" : "") + (v * 100).toFixed(d) + "%";

// Default x range for layout(): set X_RANGE = [first, last] in the page script.
var X_RANGE;

function layout(th, extra = {}) {
  return Object.assign({
    paper_bgcolor: th.surface, plot_bgcolor: th.surface,
    font: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', color: th.ink2, size: 12 },
    margin: { t: 56, r: 16, b: 32, l: 52 },
    hovermode: "x unified",
    hoverlabel: { bgcolor: th.surface, bordercolor: th.axis, font: { color: th.ink } },
    legend: { orientation: "h", x: 0, y: 1.02, yanchor: "bottom", font: { color: th.ink2 } },
    xaxis: { range: X_RANGE, showgrid: false, linecolor: th.axis, tickcolor: th.axis, showspikes: true, spikemode: "across",
             spikethickness: 1, spikecolor: th.muted, spikedash: "solid" },
    yaxis: { gridcolor: th.grid, gridwidth: 1, zeroline: false, linecolor: th.axis },
  }, extra);
}

function line(x, y, name, color, extra = {}) {
  return Object.assign({ x, y, name, type: "scatter", mode: "lines",
                         line: { color, width: 2, shape: "linear" } }, extra);
}

const CONFIG = { displayModeBar: false, responsive: true };

function watchTheme(render) {
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", render);
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
}
"""


def page(title: str, body: str, script: str, data_json: str) -> str:
    """A full HTML page: shared head and styles, `body`, then DATA + shared JS + `script`."""
    return "\n".join([
        "<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{title}</title>", PLOTLY, "<style>", CSS, "</style>", "</head>", "<body>", body,
        "<script>", f"const DATA = {data_json};", JS, script, "</script>", "</body>", "</html>", "",
    ])
