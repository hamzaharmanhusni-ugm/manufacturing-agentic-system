"""Enterprise 4: Supplier & Procurement (PROTOTYPE EXTENSION, synthetic)."""
import pandas as pd
import plotly.express as px
import streamlit as st

import agents_panel
import ui
from client import get

ui.guard("supplier")
ui.header("Supplier & Procurement", "Enterprise 4 · prototype extension (not in the original proposal) · PostgreSQL from ERP CSV export · REST :8004")

mats = get("supplier", "/materials")
if not ui.check(mats):
    st.stop()
m = pd.DataFrame(mats)
s = pd.DataFrame(get("supplier", "/suppliers") or [])
tabs = st.tabs(["Supplier Overview", "Raw Material Inventory", "Procurement Orders", "Supplier Performance", "Supply Availability", "Procurement Risk", "Agents"])

with tabs[0]:
    ui.kpis([("Suppliers", len(s), "8 active"), ("Materials", len(m), "clinker, gypsum, ..."), ("Disrupted", int((s.RISK_FLAG == "disrupted").sum()), "suppliers",
              "bad" if (s.RISK_FLAG == "disrupted").any() else "good"), ("Lowest coverage", f"{m.supply_coverage.min():.0%}", "supply vs daily use",
              "bad" if m.supply_coverage.min() < 0.9 else "good")])
    st.dataframe(s, hide_index=True, use_container_width=True,
                 column_config={"AVAILABILITY_PCT": st.column_config.ProgressColumn("Availability", format="%d%%", min_value=0, max_value=100)})

with tabs[1]:
    fig = px.bar(m, x="material", y=["on_hand", "daily_use"], barmode="group", height=330, title="On-hand vs daily use", color_discrete_sequence=["#0891b2", "#1e3a8a"])
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h"), xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(m, hide_index=True, use_container_width=True)

with tabs[2]:
    po = get("supplier", "/purchase-orders")
    if ui.check(po):
        po = pd.DataFrame(po)
        stt = st.multiselect("Status", sorted(po.STATUS.unique()), default=sorted(po.STATUS.unique()))
        st.dataframe(po[po.STATUS.isin(stt)], hide_index=True, use_container_width=True)

with tabs[3]:
    fig = px.scatter(s, x="LEAD_TIME_DAYS", y="OTIF_PCT", text="SUPPLIER_NAME", color="MATERIAL_CODE", size="CAPACITY_PER_DAY", height=360,
                     title="Supplier performance: OTIF vs lead time")
    fig.update_traces(textposition="top center")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    fig = px.bar(m, x="material", y="supply_coverage", height=320, title="Supply coverage (available supplier capacity / daily use)",
                 color="supply_coverage", color_continuous_scale=["#dc2626", "#d97706", "#16a34a"], range_color=[0, 1.2])
    fig.add_hline(y=0.9, line_dash="dash", line_color="#dc2626", annotation_text="0.9 alert")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), coloraxis_showscale=False, yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    for x in m.itertuples():
        fn = {"high": st.error, "medium": st.warning}.get(x.risk, st.success)
        fn(f"{x.material}: risk {x.risk} · coverage {x.supply_coverage:.0%} · {x.days_of_supply} days of supply" + (" · critical for production" if x.critical else ""))

with tabs[6]:
    agents_panel.render("supplier", {"Procurement Agent": "/agents/procurement/run"})
