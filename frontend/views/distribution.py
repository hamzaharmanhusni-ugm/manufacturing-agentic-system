"""Enterprise 3: Distribution (PROTOTYPE EXTENSION, synthetic)."""
import pandas as pd
import plotly.express as px
import streamlit as st

import agents_panel
import ui
from client import get

ui.guard("distribution")
ui.header("Distribution", "Enterprise 3 · prototype extension (not in the original proposal) · SQLite · REST :8003 · unit: 50 kg bags")

regions = get("distribution", "/regions")
if not ui.check(regions):
    st.stop()
r = pd.DataFrame(regions)
orders = pd.DataFrame(get("distribution", "/orders") or [])
tabs = st.tabs(["Regional Inventory", "Distributor Orders", "Regional Demand", "Order Fulfillment", "Distribution Performance", "Stock Alerts", "Agents"])

with tabs[0]:
    ui.kpis([("Regions", len(r), "served by 9 plants"), ("Distributor stock", f"{r.stock_bags.sum():,} bags", f"{r.stock_bags.sum() / 20:,.0f} t"),
             ("Daily offtake", f"{r.daily_offtake_bags.sum():,} bags", f"{r.daily_offtake_bags.sum() / 20:,.0f} t/day"),
             ("Below safety stock", int(r.below_safety.sum()), "regions", "bad" if r.below_safety.any() else "good")])
    fig = px.bar(r, x="region_name", y=["stock_bags", "safety_stock_bags"], barmode="group", height=330, title="Distributor stock vs safety stock (bags)",
                 color_discrete_sequence=["#0891b2", "#cbd5e1"])
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), xaxis_title=None, legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(r, hide_index=True, use_container_width=True)

with tabs[1]:
    stt = st.multiselect("Status", sorted(orders.status.unique()), default=sorted(orders.status.unique()))
    st.dataframe(orders[orders.status.isin(stt)], hide_index=True, use_container_width=True)

with tabs[2]:
    d = pd.DataFrame(get("distribution", "/demand") or [])
    d = d.merge(r[["region_code", "region_name"]], on="region_code")
    fig = px.line(d, x="week", y="demand_bags", color="region_name", height=360, title="Regional weekly demand (bags)")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    fig = px.bar(r.sort_values("fill_rate"), x="fill_rate", y="region_name", orientation="h", height=340, title="Order fill rate by region",
                 color="fill_rate", color_continuous_scale=["#dc2626", "#d97706", "#16a34a"], range_color=[0, 1])
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), xaxis_tickformat=".0%", coloraxis_showscale=False, yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    ui.kpis([("Average fill rate", f"{r.fill_rate.mean():.0%}", "fulfilled / ordered"), ("Open order volume", f"{r.open_order_bags.sum() / 20:,.0f} t", "unfulfilled"),
             ("Median days of stock", f"{r.days_of_stock.median():.1f}", "at distributors")])
    fig = px.scatter(r, x="days_of_stock", y="fill_rate", size="open_order_bags", text="served_by_plant", height=330, title="Days of stock vs fill rate")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    risk = r[r.below_safety | (r.days_of_stock < 3)]
    if risk.empty:
        st.success("No regional stock alerts.")
    for x in risk.itertuples():
        st.warning(f"{x.region_name} (served by {x.served_by_plant}): {x.stock_bags:,} bags, {x.days_of_stock} days of stock, safety {x.safety_stock_bags:,} bags")

with tabs[6]:
    agents_panel.render("distribution", {"Distribution Agent": "/agents/distribution/run"})
