"""KPI and performance evaluation."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import ui
from client import get

ui.guard("global")
ui.header("KPI & Analytics", "All values are computed live from the enterprise APIs on synthetic data; before-AI values are illustrative assumptions")

data = get("orchestrator", "/kpis")
if not ui.check(data):
    st.stop()
k, base, hist = data["current"], data["baseline_manual"], data["history"]


def pct(x):
    return f"{x:.0%}" if x is not None else "n/a"


ui.kpis([("Forecast WAPE", f"{k.get('wape', 0):.3f}", "LightGBM backtest"), ("ETA MAE", f"{k.get('eta_mae_hours')} h", "Random Forest"),
         ("Stock-out risk series", k.get("stockout_events"), "< 3 days", "bad" if k.get("stockout_events") else "good"),
         ("Avg days of cover", k.get("avg_days_of_cover"), "all series"), ("On-time delivery", pct(k.get("on_time_delivery")), "history x live delays"),
         ("Dispatch response", f"{k.get('dispatch_response_s')} s" if k.get("dispatch_response_s") else "n/a", "last run")])
st.write("")
ui.kpis([("Agent success", pct(k.get("agent_success_rate")), "worker calls"), ("API success", pct(k.get("api_success_rate")), "cross-enterprise"),
         ("Sync rate", pct(k.get("sync_rate")), "enterprises synced"), ("Replanning events", k.get("replanning_events"), "adaptive"),
         ("Human approval rate", pct(k.get("human_approval_rate")), "approved / decided"), ("Pending decisions", k.get("pending_decisions"), "awaiting approval", "warn")])

st.subheader("Before AI vs after AI")
st.caption(base["note"])
rows = [("Dispatch response (minutes)", base["dispatch_response_s"] / 60, (k.get("dispatch_response_s") or 0) / 60),
        ("Forecast WAPE (naive vs LightGBM)", k.get("wape_naive_baseline"), k.get("wape")),
        ("Stock-out risk series", base["stockout_events"], k.get("stockout_events")),
        ("Avg days of cover", base["avg_days_of_cover"], k.get("avg_days_of_cover")),
        ("On-time delivery", base["on_time_delivery"], k.get("on_time_delivery"))]
c = st.columns(len(rows))
for col, (name, b, a) in zip(c, rows):
    fig = go.Figure([go.Bar(x=["Before AI", "After AI"], y=[b, a], marker_color=["#cbd5e1", "#0891b2"], text=[f"{b:.3g}" if b is not None else "", f"{a:.3g}" if a is not None else ""],
                            textposition="outside")])
    fig.update_layout(title=dict(text=name, font=dict(size=12)), height=260, margin=dict(l=5, r=5, t=40, b=5), yaxis_visible=False)
    col.plotly_chart(fig, use_container_width=True)

st.subheader("Normal operation vs disruption")
if not hist:
    st.info("Run scenarios in the Simulation Center to fill this comparison.")
else:
    metrics = {"avg_days_of_cover": "Avg days of cover", "stockout_events": "Stock-out risk series", "on_time_delivery": "On-time delivery",
               "vessels_delayed": "Vessels delayed", "min_material_coverage": "Min material coverage"}
    h = pd.DataFrame([{"run": f"{i + 1}. {x['title']}", "metric": lbl, "value": x["after"].get(m)} for i, x in enumerate(hist) for m, lbl in metrics.items()])
    fig = px.bar(h, x="run", y="value", color="run", facet_col="metric", facet_col_wrap=5, height=360,
                 color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_yaxes(matches=None, showticklabels=True)
    fig.update_xaxes(showticklabels=False, title=None)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.1, title=None))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pd.DataFrame([{"run": x["title"], "ts": x["ts"], **{f"{lbl} (before)": x["before"].get(m) for m, lbl in metrics.items()},
                                **{f"{lbl} (after)": x["after"].get(m) for m, lbl in metrics.items()}} for x in hist]), hide_index=True, use_container_width=True)

st.subheader("Original dispatch plan vs adaptive dispatch plan")
runs = [r for r in (get("orchestrator", "/runs") or []) if r["scenario"] == "shipping_disruption"]
if not runs:
    st.info("Run scenario 4 (shipping disruption) to see the adaptive replanning comparison.")
else:
    run = get("orchestrator", f"/runs/{runs[0]['id']}")
    comp = pd.DataFrame(run.get("comparison") or [])
    if len(comp):
        fig = go.Figure([go.Bar(x=comp.plant_id, y=comp.original_arrival_h, name="Original plan arrival (h)", marker_color="#cbd5e1",
                                text=comp.original_vessel, textposition="inside"),
                         go.Bar(x=comp.plant_id, y=comp.adaptive_arrival_h, name="Adaptive plan arrival (h)", marker_color="#0891b2",
                                text=comp.adaptive_vessel, textposition="inside")])
        fig.add_scatter(x=comp.plant_id, y=comp.stockout_days * 24, mode="markers", name="Projected stock-out (h)", marker=dict(color="#dc2626", size=12, symbol="x"))
        fig.update_layout(barmode="group", height=360, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(comp, hide_index=True, use_container_width=True)
