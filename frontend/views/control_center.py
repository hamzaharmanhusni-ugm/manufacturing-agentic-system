"""A. Global Agentic Control Center: the live dispatch docket first, the ecosystem around it."""
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import docket
import ui
from client import get, post, role
from shared.config import LOAD_PORT, PLANTS
from shared.rbac import can

ui.guard("global")
ui.header("Global Agentic Control Center", "Four enterprises, nine agents, one dispatch docket. Code decides, AI explains, people act.")

ov = get("orchestrator", "/overview")
if not ui.check(ov):
    st.stop()
k = ov["kpis"]
health = ov["supply_chain_health"]
ui.kpis([
    ("Enterprises", f"{ov['enterprises_connected']}/{ov['enterprises_total']}", "independent APIs", "" if ov["enterprises_connected"] == 4 else "bad"),
    ("Agents", ov["agents_total"], f"{ov['agents_active']} active"),
    ("To sign", ov["pending_decisions"], "dispatch decisions", "appr" if ov["pending_decisions"] else ""),
    ("Orders", ui.fmt(ov["supply_chain_orders"]), "open + incoming"),
    ("Vessels", f"{ov['vessels_operating']}/19", f"{k.get('vessels_delayed', 0)} delayed", "warn" if k.get("vessels_delayed") else ""),
    ("Plants", ov["packing_plants"], f"{k.get('stockout_events', 0)} at stock-out risk", "bad" if k.get("stockout_events") else ""),
    ("Health", f"{health}" if health is not None else "n/a", "index of 100", "warn" if (health or 100) < 70 else ""),
    ("Alerts", ov["active_alerts"], f"system {ov['system_status']}", "bad" if ov["active_alerts"] else ""),
])

# Enterprise ledger ---------------------------------------------------------------------------
eco = get("orchestrator", "/ecosystem") or []
PAGES = {"manufacturer": "views/manufacturer.py", "shipping": "views/shipping.py", "distribution": "views/distribution.py", "supplier": "views/supplier.py"}
ui.section("Enterprise ledger", "each enterprise runs its own API, database, agents and data-sharing policy")
for col, en in zip(st.columns(4, gap="small"), eco):
    with col:
        st.markdown(f'<div class="ent"><div class="ln"><span>{ui.chip(en["enterprise"])}</span>{ui.badge(en["status"])}</div>'
                    f'<div class="nm">{ui.e(en["name"])}</div>'
                    f'<div class="ln"><span>:{en["port"]} &middot; {en["latency_ms"]:.0f} ms &middot; {en["active_agents"]}/{len(en["agents"])} agents</span>'
                    f'<span>{ui.badge(en["sync"])} {ui.hhmmss(en["last_communication"])}</span></div></div>',
                    unsafe_allow_html=True)
        st.page_link(PAGES[en["enterprise"]], label=f"Open {en['name']}", icon=":material/arrow_forward:")

# The live docket -----------------------------------------------------------------------------
scen = get("orchestrator", "/scenarios") or []
labels = {s["title"]: s["key"] for s in scen}
st.write("")
bar1, bar2, bar3 = st.columns([2.2, 1, 1], vertical_alignment="center")
pick = bar1.selectbox("Open a new docket from an event", list(labels), index=0, label_visibility="collapsed",
                      help="Open a new dispatch docket from this event")
if bar2.button(":material/play_arrow: Run", type="primary", use_container_width=True, disabled=not can(role(), "simulate")):
    try:
        post("orchestrator", f"/scenarios/{labels[pick]}/run", {"role": role()})
    except RuntimeError as ex:
        st.error(str(ex))
    time.sleep(0.4)
    st.rerun()
bar3.page_link("views/simulation.py", label="Full scenario analysis", icon=":material/analytics:")


@st.fragment(run_every=1.5)
def live_docket():
    runs = get("orchestrator", "/runs") or []
    if not runs:
        st.markdown('<div class="dk-head"><div><div class="lbl">Dispatch docket</div><div class="no">No docket open</div></div>'
                    '<div class="meta"><div><span class="lbl">Next step</span><b>Choose an event above and press Run</b></div></div></div>',
                    unsafe_allow_html=True)
        return
    run = get("orchestrator", f"/runs/{runs[0]['id']}")
    docket.render(run, key="cc")


live_docket()

# Supply chain -------------------------------------------------------------------------------
ui.section("Supply chain", "packing plant stock and the live fleet")
plants = get("manufacturer", "/plants")
vessels = get("shipping", "/vessels")
m1, m2 = st.columns([1, 1.25], gap="medium")
if ui.check(plants):
    with m1:
        d = pd.DataFrame([{"Plant": p["plant_id"], "Type": s["cement_type"], "Usable t": s["usable_ton"], "Stock-out d": s["stockout_days"],
                           "Cover d": s["days_of_cover"], "Incoming t": s["incoming_ton"]} for p in plants for s in p["series"]])
        fig = px.bar(d, x="Plant", y="Usable t", color="Type", barmode="group", hover_data=["Cover d", "Stock-out d"],
                     title="Usable stock by plant and cement type (t)", color_discrete_map={"PCC": "#0891b2", "OPC": "#0b1b33"})
        fig.update_layout(legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
        bott = d.sort_values("Stock-out d").head(4)
        st.markdown('<table class="rt"><tr><th>Earliest stock-out</th><th class="n">Days</th><th class="n">Cover d</th><th class="n">Incoming t</th></tr>'
                    + "".join(f'<tr><td><b>{r["Plant"]}</b> {r["Type"]}</td><td class="n {"late" if r["Stock-out d"] < 3 else ""}">{r["Stock-out d"]}</td>'
                              f'<td class="n">{r["Cover d"]}</td><td class="n">{r["Incoming t"]:,.0f}</td></tr>' for _, r in bott.iterrows())
                    + "</table>", unsafe_allow_html=True)
if ui.check(vessels):
    with m2:
        v = pd.DataFrame(vessels)
        fig = go.Figure()
        for p in PLANTS:
            fig.add_trace(go.Scattermap(lat=[LOAD_PORT["lat"], p["lat"]], lon=[LOAD_PORT["lon"], p["lon"]], mode="lines",
                                        line=dict(width=1, color="#9aa8bb"), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scattermap(lat=[p["lat"] for p in PLANTS], lon=[p["lon"] for p in PLANTS], mode="markers+text", text=[p["id"] for p in PLANTS],
                                    textposition="top right", textfont=dict(color="#0b1b33", size=12), marker=dict(size=10, color="#0b1b33"), name="Packing plant"))
        fig.add_trace(go.Scattermap(lat=[LOAD_PORT["lat"]], lon=[LOAD_PORT["lon"]], mode="markers+text", text=["Load port"], textposition="bottom right",
                                    marker=dict(size=13, color="#1d4ed8"), name="Load port"))
        colors = {"sailing": "#0891b2", "anchored": "#b45309", "berthed": "#0b1b33", "maintenance": "#9aa8bb"}
        for stt, grp in v.groupby("status"):
            fig.add_trace(go.Scattermap(lat=grp["lat"], lon=grp["lon"], mode="markers", name=f"Vessel {stt}", marker=dict(size=9, color=colors.get(stt)),
                                        text=grp["vessel"] + " · " + grp["mode"] + " · ETA " + grp["eta_hours"].astype(str) + " h", hoverinfo="text"))
        fig.update_layout(map=dict(style="carto-positron", center=dict(lat=-4.5, lon=117.5), zoom=3.4), height=440,
                          margin=dict(l=0, r=0, t=0, b=44), legend=dict(orientation="h", y=-0.02, yanchor="top", x=0, bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)
        moving = v[v.eta_hours.notna()].sort_values("eta_hours")
        st.markdown('<table class="rt"><tr><th>Vessel</th><th>Leg</th><th>Destination</th><th class="n">ETA h</th><th class="n">±</th><th class="n">Delay h</th></tr>'
                    + "".join(f'<tr><td><b>{r["vessel"]}</b></td><td>{r["mode"]}</td><td>{r["destination"]}</td><td class="n">{r["eta_hours"]}</td>'
                              f'<td class="n">{r["eta_range_hours"] if pd.notna(r["eta_range_hours"]) else "-"}</td>'
                              f'<td class="n {"late" if r["delay_hours"] else ""}">{r["delay_hours"]:.0f}</td></tr>' for _, r in moving.iterrows())
                    + "</table>", unsafe_allow_html=True)

# Agents and their messages -------------------------------------------------------------------
a1, a2 = st.columns([1.3, 1], gap="medium")
with a1:
    agents = get("orchestrator", "/agents") or []
    counts = {s: sum(a["status"] == s for a in agents) for s in ("Running", "Requires human approval", "Completed", "Failed", "Idle")}
    ui.section("Agent registry", " &nbsp; ".join(f"{ui.badge(s)} {n}" for s, n in counts.items() if n))
    st.markdown(ui.agent_grid(agents), unsafe_allow_html=True)
with a2:
    ui.section("Cross-enterprise message log", "agent to agent, newest first")
    msgs = get("orchestrator", "/messages?limit=40") or []
    with st.container(height=470, border=False):
        st.markdown(ui.message_log(msgs) if msgs else '<div class="subtle">No agent traffic yet.</div>', unsafe_allow_html=True)

# Decision history + pull channel ------------------------------------------------------------
decs = get("orchestrator", "/decisions") or []
hist = [d for d in decs if d["status"] != "Requires human approval"]
if hist:
    with st.expander(f"Decision history ({len(hist)} signed or superseded)"):
        st.markdown('<table class="rt"><tr><th>Decision</th><th>Run</th><th>Action</th><th>Status</th><th>By</th><th>At</th></tr>'
                    + "".join(f'<tr><td>{d["id"]}</td><td>{d["run_id"]}</td><td class="{"struck" if d["status"] == "Superseded" else ""}">{ui.e(d["action"])}</td>'
                              f'<td>{ui.badge(d["status"])}</td><td>{ui.e(d.get("decided_by", "-"))}</td><td>{ui.hhmmss(d.get("decided_at"))}</td></tr>' for d in hist[:30])
                    + "</table>", unsafe_allow_html=True)

ui.section("Ask the Narrator", "answers come only from the latest verified plan")
with st.form("ask", border=False):
    f1, f2 = st.columns([5, 1], vertical_alignment="bottom")
    q = f1.text_input("Question", placeholder="Which vessel goes to PP C, and why?", label_visibility="collapsed")
    asked = f2.form_submit_button("Ask", use_container_width=True)
if asked and q:
    ans = post("orchestrator", "/ask", {"question": q, "role": role()})
    st.markdown(f'<div class="notice info"><span class="t">Narrator</span> {ui.e(ans["answer"])}<div class="subtle">Source: {ui.e(ans["source"])}</div></div>',
                unsafe_allow_html=True)
