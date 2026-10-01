import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, callback, dash_table, dcc, html

from pages.common import (
    DOWN, EMPTY_FIG, TABLE_STYLE, UP, base_layout, bps, card, kpi, kpi_value, note, num_cols, page_header,
    signed_style,
)
from port_con.config import L1_ON, L2_ON, METHOD
from port_con.explain import snapshot
from port_con.portfolio import METHODS, rebalance_dates

# Snapshot page (/snapshot).
# Display only: pick a date and a method, see everything that went into the
# portfolio on that rebalance date (port_con.explain.snapshot).

METHOD_LABELS = {"black_litterman": "Black-Litterman", "te_budget": "TE budget"}


def _table(id_: str) -> dash_table.DataTable:
    return dash_table.DataTable(id=id_, **TABLE_STYLE)


def layout() -> list:
    dates = rebalance_dates()
    return [
        page_header("Snapshot", "Everything that goes into the portfolio on one rebalance date", "/snapshot"),

        dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(dbc.Row([
            dbc.Col(dcc.DatePickerSingle(id="snap-date", date=dates[-1].date(), min_date_allowed=dates[0].date(),
                                         max_date_allowed=dates[-1].date(), display_format="YYYY-MM-DD"), width="auto"),
            dbc.Col(dbc.RadioItems(id="snap-method", options=[{"label": METHOD_LABELS[m], "value": m} for m in METHODS],
                                   value=METHOD, inline=True, className="btn-group period-btns",
                                   inputClassName="btn-check", labelClassName="btn btn-outline-secondary btn-sm",
                                   labelCheckedClassName="active"), width="auto"),
            dbc.Col(html.Div(id="snap-date-label", className="kpi-delta"), width="auto", className="ms-auto"),
        ], align="center", className="g-3")), className="section-card"))),

        dbc.Row([
            kpi("SAA value", "snap-k-saa", "snap-k-saa-sub"),
            kpi("TAA value", "snap-k-taa", "snap-k-taa-sub"),
            kpi("Avg L1 signal", "snap-k-avg", "snap-k-avg-sub"),
            kpi("Target vol", "snap-k-vol", "snap-k-vol-sub"),
            kpi("Leverage", "snap-k-lev", "snap-k-lev-sub"),
        ], className="g-3 mb-4"),

        dbc.Row(dbc.Col(card("L1 signals", _table("snap-l1"),
                             html.Div("Raw = the signal function's output; Z = after normalization. Contribution = "
                                      "Z x weight x side (+1 equity, -1 bond), summed into the SAA / TAA value."
                                      + ("" if L1_ON else " L1 is switched off (port_con/config.py): shown "
                                                          "for reference, contributions are 0."),
                                      className="kpi-delta mt-2", style={"textAlign": "left"}))), className="mb-4"),

        dbc.Row(dbc.Col(card("Sleeve weights, step by step", _table("snap-sleeves"),
                             html.Div(id="snap-sleeve-note", className="kpi-delta mt-2", style={"textAlign": "left"}))),
                className="mb-4"),

        dbc.Row(dbc.Col(card("L2: sector signals and weights inside equity", _table("snap-l2"),
                             html.Div("Raw = the signal function's output; z = after normalization (cross-sectional, "
                                      "or vs own history for value). L2 value = weighted average of the z's."
                                      + ("" if L2_ON else " L2 is switched off (port_con/config.py): shown "
                                                          "for reference, L2 value is 0."),
                                      className="kpi-delta mt-2", style={"textAlign": "left"}))), className="mb-4"),

        dbc.Row(dbc.Col(card("Tracking error: from signals to risk", _table("snap-te-layers"),
                             note("Tracking error (TE) = how much the portfolio's yearly return is expected to differ "
                                  "from the baseline. TE alone = the layer's TE on its own; Contribution = its share of "
                                  "the total (the two layers partly offset, so contributions add up to the total). "
                                  "TE budget method: Target = Budget x score / strength, the TE the layer aims for "
                                  "(strength is at most 1, so the full budget is used only when the signal is strong)."))),
                className="mb-4"),

        dbc.Row([
            dbc.Col(card("TE by signal", _table("snap-te-signals"), note(
                "Which signal drives how much TE. Tilt = the direction the signal pushes (L2: its biggest "
                "overweight / underweight). Negative = the signal pushes against the others and lowers TE. "
                "caps = what the sector cap and no-shorting rule changed. Shown for the TE budget method only.")),
                xl=7),
            dbc.Col(card("TE contribution by signal", dcc.Graph(figure=EMPTY_FIG, id="snap-te-signal-bar",
                                                   config={"displayModeBar": False})), xl=5),
        ], className="g-4 mb-4"),

        dbc.Row(dbc.Col(card("TE by asset", _table("snap-te-assets"), note(
            "L2 value = the sector's combined signal score. Active vol = how much the asset moves apart from the "
            "baseline portfolio each year. Active = weight vs baseline (L1 part + L2 part). Contribution = the asset's "
            "share of the total TE; together they add up to the total."))), className="mb-4"),

        dbc.Row([
            dbc.Col(card("Final weights", _table("snap-weights"),
                         html.Div("Holding = what is actually bought (manager where one replaces the slot). "
                                  "Last week / Change are vs the previous rebalance date.",
                                  className="kpi-delta mt-2", style={"textAlign": "left"})), xl=8),
            dbc.Col(card("Active weight vs baseline",
                         dcc.Graph(figure=EMPTY_FIG, id="snap-active", config={"displayModeBar": False})), xl=4),
        ], className="g-4"),
    ]


@callback(
    Output("snap-date-label", "children"),
    Output("snap-k-saa", "children"), Output("snap-k-taa", "children"), Output("snap-k-avg", "children"),
    Output("snap-k-vol", "children"), Output("snap-k-lev", "children"),
    Output("snap-k-saa-sub", "children"), Output("snap-k-taa-sub", "children"), Output("snap-k-avg-sub", "children"),
    Output("snap-k-vol-sub", "children"), Output("snap-k-lev-sub", "children"),
    Output("snap-l1", "data"), Output("snap-l1", "columns"),
    Output("snap-sleeves", "data"), Output("snap-sleeves", "columns"), Output("snap-sleeve-note", "children"),
    Output("snap-l2", "data"), Output("snap-l2", "columns"),
    Output("snap-weights", "data"), Output("snap-weights", "columns"),
    Output("snap-active", "figure"),
    Output("snap-te-layers", "data"), Output("snap-te-layers", "columns"),
    Output("snap-te-signals", "data"), Output("snap-te-signals", "columns"), Output("snap-te-signals", "style_data_conditional"),
    Output("snap-te-signal-bar", "figure"),
    Output("snap-te-assets", "data"), Output("snap-te-assets", "columns"), Output("snap-te-assets", "style_data_conditional"),
    Input("snap-date", "date"), Input("snap-method", "value"),
)
def update(date, method):
    s = snapshot(date, method)
    v, vol = s["l1_values"], s["vol"]
    prev = f" · previous {s['prev_date']:%Y-%m-%d}" if s["prev_date"] is not None else ""
    label = f"Rebalance date used: {s['date']:%Y-%m-%d}{prev}"

    def num(x):
        return html.Span(f"{x:+.2f}", className="kpi-value")

    kpis = [num(v["saa"]), num(v["taa"]), num(v["avg_signal"]),
            kpi_value(vol["target_vol"], neutral=True), html.Span(f"{vol['leverage']:.2f}x", className="kpi-value")]
    subs = [">0 = tilt to equity", ">0 = tilt to equity", "sizes the target vol",
            f"baseline {vol['baseline_vol']:.1%}", f"uncapped {vol['raw_leverage']:.2f}x"]

    l1 = s["l1_signals"]
    l1_cols = ([{"name": c, "id": c} for c in ["Layer", "Signal", "Side", "Inputs"]]
               + num_cols(["Raw", "Z", "Contribution"], "+.3f") + num_cols(["Weight"], ".2f"))

    sl = s["sleeves"].reset_index(names="Sleeve")
    sl_cols = [{"name": "Sleeve", "id": "Sleeve"}] + num_cols(["Baseline", "Tilted", "Sized", "Final"], ".1%")
    sl_note = (f"Tilted = after {METHOD_LABELS[method]} (sums to 100%). Sized = x leverage {vol['leverage']:.2f} "
               f"(target vol {vol['target_vol']:.1%} / tilted vol {vol['tilted_vol']:.1%}). "
               f"Final = capped to baseline +/- max deviation.")

    l2 = s["l2"].reset_index(names="Asset")
    raw_cols = [c for c in l2.columns if c.endswith(" raw")]
    z_cols = [c for c in l2.columns if c.endswith(" z")]
    l2_cols = ([{"name": "Asset", "id": "Asset"}] + num_cols(raw_cols, "+.3f") + num_cols(z_cols + ["L2 value"], "+.2f")
               + num_cols(["Baseline in equity", "Tilted in equity"], ".1%"))

    w = s["weights"].reset_index(names="Asset")
    w_cols = ([{"name": c, "id": c} for c in ["Asset", "Sleeve", "Holding"]]
              + num_cols(["Baseline", "Final", "Last week"], ".1%") + num_cols(["Active", "Change"], "+.1%"))
    total = {"Asset": "Total", "Sleeve": "", "Holding": "", **{c: w[c].sum() for c in
             ["Baseline", "Final", "Last week", "Active", "Change"]}}

    a = s["weights"]["Active"].dropna().iloc[::-1]
    fig = go.Figure(go.Bar(
        x=a.values, y=a.index, orientation="h", marker={"color": [UP if x >= 0 else DOWN for x in a.values]},
        text=[bps(x) for x in a.values], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:+.2%}<extra></extra>",
    ))
    base_layout(fig, showlegend=False, height=560, margin={"t": 10, "l": 60, "r": 70, "b": 30})
    lo, hi = min(a.min(), 0), max(a.max(), 0)
    pad = max(hi - lo, 0.01) * 0.3
    # Room on both sides for the outside labels, so they never run into the asset names.
    fig.update_xaxes(tickformat=".1%", showgrid=True, gridcolor="rgba(255,255,255,0.06)",
                     range=[lo - pad - (hi - lo) * 0.15, hi + pad])
    fig.update_yaxes(ticklabelstandoff=8)

    te = s["te"]
    lay = te["layers"].reset_index(names="Layer")
    lay_cols = ([{"name": "Layer", "id": "Layer"}] + num_cols(["Score / strength"], "+.2f")
                + num_cols(["Budget", "Target", "TE alone", "Contribution"], ".2%"))

    sig = te["signals"]
    sig_cols = ([{"name": c, "id": c} for c in ["Layer", "Signal", "Tilt"]]
                + num_cols(["Contribution"], "+.2%") + num_cols(["Share of TE"], "+.0%"))
    bar = sig.iloc[::-1]
    sig_fig = go.Figure(go.Bar(
        x=bar["Contribution"], y=bar["Layer"] + " " + bar["Signal"], orientation="h",
        marker={"color": [UP if x >= 0 else DOWN for x in bar["Contribution"]]},
        text=[bps(x) for x in bar["Contribution"]], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:+.2%} TE<extra></extra>",
    ))
    base_layout(sig_fig, showlegend=False, height=max(260, 28 * len(bar) + 60), margin={"t": 10, "l": 10, "r": 70, "b": 30})
    lo, hi = (min(bar["Contribution"].min(), 0), max(bar["Contribution"].max(), 0)) if not bar.empty else (0, 0)
    pad = max(hi - lo, 1e-4) * 0.3
    sig_fig.update_xaxes(tickformat=".2%", showgrid=True, gridcolor="rgba(255,255,255,0.06)",
                         range=[lo - pad - (hi - lo) * 0.15 if lo < 0 else 0, hi + pad])
    sig_fig.update_yaxes(automargin=True, ticklabelstandoff=8)
    if sig.empty:
        sig_fig = EMPTY_FIG

    ta = te["assets"].reset_index(names="Asset")
    ta_cols = ([{"name": "Asset", "id": "Asset"}] + num_cols(["L2 value"], "+.2f") + num_cols(["Active vol"], ".1%")
               + num_cols(["L1 active", "L2 active", "Active", "Contribution"], "+.2%") + num_cols(["Share of TE"], "+.0%"))
    ta_total = {"Asset": "Total", **{c: ta[c].sum() for c in ["L1 active", "L2 active", "Active", "Contribution", "Share of TE"]}}

    return (label, *kpis, *subs,
            l1.to_dict("records"), l1_cols,
            sl.to_dict("records"), sl_cols, sl_note,
            l2.to_dict("records"), l2_cols,
            w.to_dict("records") + [total], w_cols,
            fig,
            lay.to_dict("records"), lay_cols,
            sig.to_dict("records"), sig_cols, signed_style(["Contribution", "Share of TE"]),
            sig_fig,
            ta.to_dict("records") + [ta_total], ta_cols, signed_style(["L2 value", "L1 active", "L2 active", "Active", "Contribution"]))
