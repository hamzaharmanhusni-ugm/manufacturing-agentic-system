"""Enterprise 2: Shipping & Logistics dashboard (Shipment subsidiary)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import agents_panel
import ui
from client import get, role
from shared.config import LOAD_PORT, PLANTS

ui.guard("shipping")
ui.header("Shipping & Logistics", "Enterprise 2 · separate subsidiary · MongoDB · REST :8002 · shares only GPS, status, ETA and voyage history")

internal = role() in ("Shipping Manager", "Global Administrator")
vessels = get("shipping", "/vessels/internal" if internal else "/vessels")
if not ui.check(vessels):
    st.stop()
v = pd.DataFrame(vessels)
tabs = st.tabs(["Fleet Overview", "Live Vessel Tracking", "Vessel Availability", "Voyage History", "ETA Prediction", "Ship Ranking",
                "Shipping Assignment", "Maintenance Status", "Agents"])

with tabs[0]:
    cnt = v.status.value_counts()
    ui.kpis([("Vessels", len(v), "fleet size"), ("Sailing", int(cnt.get("sailing", 0)), "GPS speed > 1.5 kn"),
             ("Berthed", int(cnt.get("berthed", 0)), "inside port geofence"), ("Anchored", int(cnt.get("anchored", 0)), "anchorage"),
             ("Maintenance", int(cnt.get("maintenance", 0)), "Port J yard", "warn"), ("Delayed", int((v.delay_hours > 0).sum()), "voyage log", "bad" if (v.delay_hours > 0).any() else "good"),
             ("Fleet capacity", f"{v.capacity_ton.sum():,} t", "19 vessels")])
    st.dataframe(v[["vessel", "status", "mode", "speed_kn", "heading_deg", "capacity_ton", "cargo_ton", "cargo_type", "destination", "eta_hours",
                    "eta_range_hours", "wave_m_here", "wind_kn_here", "ping_age_h"]], hide_index=True, use_container_width=True,
                 column_config={"eta_hours": "ETA (h)", "eta_range_hours": "± (h)", "wave_m_here": "Wave (m)", "wind_kn_here": "Wind (kn)", "ping_age_h": "GPS age (h)"})

with tabs[1]:
    sel = st.selectbox("Highlight vessel GPS track (last 24 h)", ["none"] + list(v.vessel))
    fig = go.Figure()
    for p in PLANTS:
        fig.add_trace(go.Scattermap(lat=[LOAD_PORT["lat"], p["lat"]], lon=[LOAD_PORT["lon"], p["lon"]], mode="lines", line=dict(width=1, color="#94a3b8"),
                                    hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scattermap(lat=[p["lat"] for p in PLANTS], lon=[p["lon"] for p in PLANTS], mode="markers+text", text=[p["id"] for p in PLANTS],
                                textposition="top right", marker=dict(size=10, color="#1e3a8a"), name="Packing plant"))
    fig.add_trace(go.Scattermap(lat=[LOAD_PORT["lat"]], lon=[LOAD_PORT["lon"]], mode="markers+text", text=["Load Port"], marker=dict(size=13, color="#dc2626"), name="Load port"))
    colors = {"sailing": "#0891b2", "anchored": "#d97706", "berthed": "#16a34a", "maintenance": "#64748b"}
    for stt, grp in v.groupby("status"):
        fig.add_trace(go.Scattermap(lat=grp["lat"], lon=grp["lon"], mode="markers+text", text=grp["vessel"].str.replace("Ship ", ""), textposition="bottom center",
                                    marker=dict(size=11, color=colors.get(stt)), name=stt,
                                    hovertext=grp["vessel"] + " · " + grp["mode"] + " · " + grp["speed_kn"].astype(str) + " kn · dest " + grp["destination"].astype(str),
                                    hoverinfo="text"))
    if sel != "none":
        tr = pd.DataFrame(get("shipping", f"/vessels/{sel.replace(' ', '%20')}/track") or [])
        fig.add_trace(go.Scattermap(lat=tr.lat, lon=tr.lon, mode="lines+markers", line=dict(color="#7c3aed", width=3), marker=dict(size=4), name=f"{sel} track"))
    fig.update_layout(map=dict(style="carto-positron", center=dict(lat=-4.5, lon=117.5), zoom=3.6), height=560, margin=dict(l=0, r=0, t=0, b=0),
                      legend=dict(orientation="h", y=0, bgcolor="rgba(255,255,255,0.8)"))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Status: geofence rule (proposal) and DBSCAN on GPS pings (course requirement). Positions are simulated IIoT data.")
    st.dataframe(v[["vessel", "status_geofence", "status_dbscan", "dbscan_cluster_size", "speed_kn", "ping_age_h"]], hide_index=True, use_container_width=True)

with tabs[2]:
    av = v[v.available_in_h.notna()].sort_values("available_in_h")
    fig = px.bar(av, x="available_in_h", y="vessel", orientation="h", color="mode", height=380, title="Hours until loaded and ready at load port (route rule Eq. 8)")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), yaxis={"categoryorder": "total descending"})
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Laden vessels and maintenance vessels are not available for a new dispatch.")

with tabs[3]:
    voy = pd.DataFrame(get("shipping", "/voyages") or [])
    ui.kpis([("Voyages", len(voy), "historical"), ("Voyage events", int(voy.events.apply(len).sum()), "loading, berthing, delays"),
             ("Equipment delays", int(voy.events.apply(lambda e: sum(x["type"] == "equipment delay" for x in e)).sum()), "Weibull failure history"),
             ("On-time share", f"{voy.onTime.mean():.0%}", "<= 110 % of plan")])
    c1, c2 = st.columns(2)
    fig = px.box(voy, x="toPlant", y="durationHours", height=320, title="Sailing time by destination (hours)")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    c1.plotly_chart(fig, use_container_width=True)
    fig = px.scatter(voy, x="avgWaveM", y="durationHours", color="toPlant", height=320, title="Wave height vs duration")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    c2.plotly_chart(fig, use_container_width=True)
    q = st.text_input("Filter voyages (vessel or plant)")
    show = voy[voy.vesselName.str.contains(q, case=False) | voy.toPlant.str.contains(q, case=False)] if q else voy
    st.dataframe(show.drop(columns=["events"]).sort_values("departedAt", ascending=False), hide_index=True, use_container_width=True, height=300)

with tabs[4]:
    m = get("shipping", "/models") or {}
    eta = m.get("eta", {})
    ui.kpis([("Model", "Random Forest", f"{eta.get('trees')} trees"), ("ETA MAE", f"{eta.get('mae_hours')} h", "hold-out 20 %, synthetic"),
             ("Train voyages", eta.get("train_voyages"), "of 282"), ("Weibull shape κ", m.get("maintenance", {}).get("kappa"), "κ > 1 = wear-out")])
    fi = pd.DataFrame(eta.get("feature_importance", {}).items(), columns=["feature", "importance"]).sort_values("importance")
    c1, c2 = st.columns(2)
    fig = px.bar(fi, x="importance", y="feature", orientation="h", height=300, title="RF feature importance")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    c1.plotly_chart(fig, use_container_width=True)
    moving = v[v.eta_hours.notna()]
    fig = go.Figure(go.Bar(x=moving.eta_hours, y=moving.vessel, orientation="h", error_x=dict(type="data", array=moving.eta_range_hours.fillna(0)),
                           marker_color="#0891b2"))
    fig.update_layout(height=300, title="Predicted ETA with range (sailing vessels)", margin=dict(l=10, r=10, t=40, b=10))
    c2.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    plan = (get("orchestrator", "/runs/latest/plan") or {}).get("plan", [])
    if not plan:
        st.info("Ship ranking is produced by the Dispatch Planner during a scenario run. Trigger one in the Simulation Center.")
    for p in plan:
        if p.get("ranking"):
            st.markdown(f"**{p['plant_id']}** needs {p['cement_type']} · recommended **{p['vessel']}** (SAW {p['saw_score']})")
            st.dataframe(pd.DataFrame([{"Vessel": r["vessel"], "SAW": r["saw_score"], "Arrival (h)": r["arrival_hours"], "Capacity (t)": r["capacity_ton"],
                                        "Proven calls": r["proven_calls"], "Evidence": r["evidence"], "Wave (m)": r["wave_m"],
                                        "Failure risk 14d": r["failure_risk"]} for r in p["ranking"]]), hide_index=True, use_container_width=True)

with tabs[6]:
    asg = get("shipping", "/assignments") or []
    st.dataframe(pd.DataFrame(asg), hide_index=True, use_container_width=True) if asg else st.info("No confirmed assignments. Approve a decision in the Global Control Center.")

with tabs[7]:
    cols = ["vessel", "maintenance", "failure_risk_14d"] + (["engine"] if internal else [])
    mt = v[cols].copy()
    if internal:
        mt = pd.concat([mt.drop(columns=["engine"]), pd.json_normalize(v.engine)], axis=1)
    st.dataframe(mt.sort_values("failure_risk_14d", ascending=False), hide_index=True, use_container_width=True,
                 column_config={"failure_risk_14d": st.column_config.ProgressColumn("Failure risk 14 d (Weibull)", format="percent", min_value=0, max_value=1)})
    if not internal:
        st.caption("Engine sensor details are internal to Shipment and not shared with your role.")

with tabs[8]:
    agents_panel.render("shipping", {"Fleet Tracking": "/agents/fleet-tracking/run"})
