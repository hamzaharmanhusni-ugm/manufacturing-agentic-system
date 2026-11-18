"""Enterprise 1: Cement Manufacturing dashboard (Marketing + Operations)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import agents_panel
import ui
from client import get

ui.guard("manufacturer")
ui.header("Cement Manufacturing", "Enterprise 1 · PostgreSQL · REST :8001 · Marketing and Operations departments (proposal scope)")

plants = get("manufacturer", "/plants")
if not ui.check(plants):
    st.stop()
series = pd.DataFrame([s for p in plants for s in p["series"]])
pri = pd.DataFrame([{**p["priority"], "region": p["region"], "need_type": p["need"]["cement_type"], "needs_delivery": p["need"]["needs_delivery"]} for p in plants])
incoming = pd.DataFrame(get("manufacturer", "/incoming") or [])
lp = get("manufacturer", "/load-port") or {}

names = ["Executive", "Marketing", "Operations", "Forecasting", "Silo Monitoring", "Packing Plants", "Stock-out", "Agents", "Decision History"]
shown = [n for n in names if ui.tab_allowed(n)]
tabs = dict(zip(shown, st.tabs(shown)))

if "Executive" in tabs:
    with tabs["Executive"]:
        ui.kpis([("Packing plants", 9, "PP A to PP I"), ("Silos monitored", int(series.silos.sum()), "IIoT level sensors"),
                 ("Usable stock", f"{series.usable_ton.sum():,.0f} t", "above dead stock"),
                 ("Daily demand P50", f"{series.daily_demand_p50.sum():,.0f} t", "14-day mean"),
                 ("Low-stock series", int(series.low_stock.sum()), "level < 25 %", "bad" if series.low_stock.any() else "good"),
                 ("Incoming", f"{incoming.quantity_ton.sum() if len(incoming) else 0:,.0f} t", f"{len(incoming)} deliveries"),
                 ("Load port stock", f"{sum(s['available_ton'] for s in lp.get('stock', [])):,.0f} t", f"production x{lp.get('production_capacity_factor')}")])
        c1, c2 = st.columns(2)
        fig = px.bar(pri.sort_values("priority_score"), x="priority_score", y="plant_id", orientation="h", color="priority_score",
                     color_continuous_scale=["#cbd5e1", "#0891b2", "#1e3a8a"], range_color=[1, 5], height=330, title="Plant priority score (Eq. 14, scale 1 to 5)")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), coloraxis_showscale=False, yaxis_title=None)
        c1.plotly_chart(fig, use_container_width=True)
        fig = px.scatter(series, x="days_of_cover", y="stockout_days", color="cement_type", text="plant_id", size="daily_demand_p50", height=330,
                         title="Days of cover vs ARIMA stock-out time", color_discrete_map={"PCC": "#0891b2", "OPC": "#1e3a8a"})
        fig.add_hrect(y0=0, y1=3, fillcolor="#fee2e2", opacity=0.5, line_width=0)
        fig.update_traces(textposition="top center")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        c2.plotly_chart(fig, use_container_width=True)

if "Marketing" in tabs:
    with tabs["Marketing"]:
        sales = get("manufacturer", "/marketing/sales")
        if ui.check(sales):
            s = pd.DataFrame(sales)
            s["date"] = pd.to_datetime(s["date"])
            pick = st.multiselect("Plants", sorted(s.plant_id.unique()), default=["PP C", "PP F"])
            w = s[s.plant_id.isin(pick)].groupby([pd.Grouper(key="date", freq="W"), "plant_id"]).sales_ton.sum().reset_index()
            fig = px.line(w, x="date", y="sales_ton", color="plant_id", height=300, title="Historical sales (weekly, tons)")
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            c1, c2 = st.columns(2)
            sop = get("manufacturer", "/marketing/sop")
            if ui.check(sop):
                sop = pd.DataFrame(sop)
                cur = sop[sop.month == sop.month.min()]
                last30 = s[s.date > s.date.max() - pd.Timedelta(days=30)].groupby(["plant_id", "cement_type"]).sales_ton.sum().reset_index()
                cmp_ = cur.merge(last30, on=["plant_id", "cement_type"])
                fig = go.Figure([go.Bar(x=cmp_.plant_id + " " + cmp_.cement_type, y=cmp_.planned_sales_ton, name="S&OP plan (month)", marker_color="#cbd5e1"),
                                 go.Bar(x=cmp_.plant_id + " " + cmp_.cement_type, y=cmp_.sales_ton, name="Actual last 30 days", marker_color="#0891b2")])
                fig.update_layout(barmode="group", height=320, title="Demand comparison: S&OP plan vs actual", margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h"))
                c1.plotly_chart(fig, use_container_width=True)
            prices = get("manufacturer", "/marketing/prices")
            if ui.check(prices):
                pr = pd.DataFrame(prices)
                fig = go.Figure([go.Bar(x=pr.plant_id, y=pr.selling_price_idr_ton, name="Selling price", marker_color="#1e3a8a"),
                                 go.Bar(x=pr.plant_id, y=pr.contribution_margin_idr_ton, name="Contribution margin", marker_color="#0891b2")])
                fig.update_layout(barmode="group", height=320, title="Selling price and contribution margin (IDR/t, restricted data)", margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h"))
                c2.plotly_chart(fig, use_container_width=True)
                st.caption("Price and margin never leave this enterprise as raw values: the orchestrator receives only Eq. 14 grades.")

if "Operations" in tabs:
    with tabs["Operations"]:
        low = series[(series.low_stock) | (series.stockout_days < 3)]
        if len(low):
            for r in low.itertuples():
                st.error(f"LOW STOCK · {r.plant_id} {r.cement_type}: level {r.level_pct:.0%}, usable {r.usable_ton:,.0f} t, stock-out in {r.stockout_days} days")
        else:
            st.success("No low-stock alerts.")
        c1, c2 = st.columns(2)
        fig = px.bar(series, x="plant_id", y="level_pct", color="cement_type", barmode="group", height=300, title="Live silo level by plant (%)",
                     color_discrete_map={"PCC": "#0891b2", "OPC": "#1e3a8a"})
        fig.add_hline(y=0.25, line_dash="dash", line_color="#dc2626", annotation_text="25 % low-stock rule")
        fig.update_layout(yaxis_tickformat=".0%", margin=dict(l=10, r=10, t=40, b=10))
        c1.plotly_chart(fig, use_container_width=True)
        fig = px.pie(series, names="plant_id", values="usable_ton", hole=0.55, height=300, title="Inventory distribution (usable tons)")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        c2.plotly_chart(fig, use_container_width=True)
        st.markdown("**Incoming shipments**")
        st.dataframe(incoming, hide_index=True, use_container_width=True)

if "Forecasting" in tabs:
    with tabs["Forecasting"]:
        m = get("manufacturer", "/forecast/metrics") or {}
        ui.kpis([("Champion", "LightGBM", "quantile, pinball loss"), ("WAPE champion", f"{m.get('wape_champion', 0):.3f}", "backtest, synthetic"),
                 ("WAPE challenger", f"{m.get('wape_challenger', 0):.3f}", "TFT simulation mode", "warn"), ("WAPE ensemble", f"{m.get('wape_ensemble', 0):.3f}",
                 "selected" if m.get("ensemble_selected") else "not selected"), ("P10-P90 coverage", f"{m.get('coverage_p10_p90', 0):.0%}", "target ~80 %")])
        st.caption(m.get("challenger", ""))
        fc = pd.DataFrame(get("manufacturer", "/forecast") or [])
        key = st.selectbox("Series", sorted((fc.plant_id + " " + fc.cement_type).unique()), index=4)
        p, t = key.rsplit(" ", 1)
        f = fc[(fc.plant_id == p) & (fc.cement_type == t)]
        fig = go.Figure([go.Scatter(x=f.date, y=f.p90, line=dict(width=0), showlegend=False),
                         go.Scatter(x=f.date, y=f.p10, fill="tonexty", fillcolor="rgba(8,145,178,0.15)", line=dict(width=0), name="P10-P90"),
                         go.Scatter(x=f.date, y=f.p50, line=dict(color="#0891b2", width=3), name="P50")])
        fig.update_layout(height=320, title=f"14-day daily demand forecast · {key} (tons/day)", margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

if "Silo Monitoring" in tabs:
    with tabs["Silo Monitoring"]:
        silos = pd.DataFrame(get("manufacturer", "/silos") or [])
        st.dataframe(silos[["silo_id", "plant_id", "cement_type", "capacity_ton", "dead_stock_ton", "level_pct", "last_reading", "sensor"]],
                     hide_index=True, use_container_width=True, column_config={"level_pct": st.column_config.ProgressColumn("Level", format="percent", min_value=0, max_value=1)})
        p = st.selectbox("Silo level history (60 days)", [x["plant_id"] for x in plants], index=2)
        hist = get("manufacturer", f"/silos/history?plant_id={p.replace(' ', '%20')}")
        if ui.check(hist):
            h = pd.DataFrame(hist)
            fig = px.line(h, x="date", y="level_pct", color="silo_id", height=300)
            fig.add_hline(y=0.25, line_dash="dash", line_color="#dc2626")
            fig.update_layout(yaxis_tickformat=".0%", margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

if "Packing Plants" in tabs:
    with tabs["Packing Plants"]:
        t = series.merge(pri[["plant_id", "priority_score", "rank", "region"]], on="plant_id")
        t["incoming"] = t.incoming_ton
        q = st.text_input("Search plant or region", "")
        if q:
            t = t[t.plant_id.str.contains(q, case=False) | t.region.str.contains(q, case=False)]
        st.dataframe(t[["plant_id", "region", "cement_type", "level_pct", "usable_ton", "daily_demand_p50", "days_of_cover", "stockout_days", "priority_score", "rank", "incoming"]]
                     .sort_values("rank"), hide_index=True, use_container_width=True,
                     column_config={"level_pct": st.column_config.ProgressColumn("Silo level", format="percent", min_value=0, max_value=1),
                                    "stockout_days": st.column_config.NumberColumn("Stock-out (d)", format="%.2f"),
                                    "priority_score": st.column_config.NumberColumn("Priority", format="%.2f")})

if "Stock-out" in tabs:
    with tabs["Stock-out"]:
        st.markdown("ARIMA(1,0,0) on daily silo drawdown, averaged with the P50 forecast, plus planned deliveries (proposal Eq. 9 to 10).")
        fig = px.bar(series.sort_values("stockout_days"), x="stockout_days", y=series.sort_values("stockout_days").plant_id + " " + series.sort_values("stockout_days").cement_type,
                     orientation="h", color="stockout_days", color_continuous_scale=["#dc2626", "#d97706", "#16a34a"], range_color=[0, 12], height=420)
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), yaxis_title=None, xaxis_title="days until usable stock reaches zero", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        g = pri[["plant_id", "priority_score", "stockout_days", "endurance_days", "forecast_demand"]].copy()
        grades = pd.DataFrame([p["grades"] for p in pri.to_dict("records")])
        st.markdown("**Eq. 14 grades (1 to 5) per criterion**")
        st.dataframe(pd.concat([g, grades.add_prefix("g_")], axis=1).sort_values("priority_score", ascending=False), hide_index=True, use_container_width=True)

if "Agents" in tabs:
    with tabs["Agents"]:
        agents_panel.render("manufacturer", {"Stock Monitoring": "/agents/stock-monitoring/run", "ML Forecasting": "/agents/ml-forecasting/run",
                                             "Demand & Priority": "/agents/demand-priority/run"})

if "Decision History" in tabs:
    with tabs["Decision History"]:
        d = pd.DataFrame(get("orchestrator", "/decisions") or [])
        if len(d):
            st.dataframe(d[["id", "created", "scenario", "action", "status", "priority", "decided_by", "decided_at"]] if "decided_by" in d else d[["id", "created", "scenario", "action", "status", "priority"]],
                         hide_index=True, use_container_width=True)
        else:
            st.info("No decisions yet.")
