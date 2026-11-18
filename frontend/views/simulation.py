"""Event-driven Simulation Center: trigger scenarios, watch agents execute, see the 7-part result."""
import time

import pandas as pd
import plotly.express as px
import streamlit as st

import charts
import docket
import ui
from client import get, post, role
from shared.rbac import can

ui.guard("global")
ui.header("Simulation Center", "Trigger an event and watch the Orchestrator dispatch agents across enterprises")

scen = get("orchestrator", "/scenarios") or []
allowed = can(role(), "simulate")
SHORT = {"normal": "1 · Normal", "low_stock": "2 · Low stock PP C", "demand_surge": "3 · Demand surge PP F",
         "shipping_disruption": "4 · Vessel delay (replan)", "weather": "5 · Weather", "supplier": "6 · Supplier disruption"}
by_title = {SHORT.get(s["key"], s["title"]): s for s in scen}

# 1. Pick a scenario: compact selector instead of six large cards --------------------------
with st.container(border=True):
    c1, c2 = st.columns([3, 1.1])
    with c1:
        pick = st.pills("Scenario", list(by_title), default=list(by_title)[0], label_visibility="collapsed")
        sel = by_title.get(pick) or scen[0]
        tags = "".join(f"<span class='tag'>{t}</span>" for t in (["adaptive replanning"] if sel["replan"] else []) + [f"+ {e} agent" for e in sel["extensions"]])
        st.markdown(f"<div class='subtle'><b>Event:</b> {sel['event']}</div><div class='subtle'>{sel['description']} {tags}</div>",
                    unsafe_allow_html=True)
    with c2:
        if st.button(":material/play_arrow: Run scenario", type="primary", disabled=not allowed, use_container_width=True):
            try:
                st.session_state.run_id = post("orchestrator", f"/scenarios/{sel['key']}/run", {"role": role()})["run_id"]
            except RuntimeError as e:
                st.error(str(e))
        if st.button(":material/restart_alt: Reset ecosystem", disabled=not allowed, use_container_width=True,
                     help="Restore all four enterprises to the initial synthetic data"):
            with st.spinner("Regenerating every enterprise store from seed"):
                post("orchestrator", "/reset", {"role": role()})
            st.session_state.pop("run_id", None)
            st.toast("Ecosystem reset to the initial condition")
        if not allowed:
            st.caption("Your role cannot trigger simulations.")


def kpi_delta(before, after):
    keys = [("avg_days_of_cover", "Avg days of cover"), ("stockout_events", "Stock-out risk series"), ("on_time_delivery", "On-time delivery"),
            ("vessels_delayed", "Vessels delayed"), ("low_stock_series", "Low-stock series"), ("pending_decisions", "Pending decisions"),
            ("replanning_events", "Replanning events"), ("min_material_coverage", "Min material coverage"), ("regions_below_safety", "Regions below safety")]
    return pd.DataFrame([{"KPI": lbl, "Before": before.get(k), "After": after.get(k)} for k, lbl in keys])


rid = st.session_state.get("run_id") or ((get("orchestrator", "/runs") or [{}])[0].get("id"))
if not rid:
    st.info("Choose a scenario above and press Run scenario. The agent workflow, the recommendation and the KPI impact appear here.")
    st.stop()
run = get("orchestrator", f"/runs/{rid}")

# 2. The run as a dispatch docket ------------------------------------------------------------
segs = ui.segments(run["steps"])
if len(segs) > 1:
    with st.expander("Original planning cycle, before the disruption"):
        st.markdown(ui.pipeline(segs[0]), unsafe_allow_html=True)
        if run.get("previous_plan"):
            st.markdown(docket.plan_table(run["previous_plan"]), unsafe_allow_html=True)
docket.render(run, key="sim")

steps = [s for s in run["steps"] if s.get("started")]
if steps:
    with st.expander("Timeline: when each agent ran (parallel overlap)", expanded=run["status"] == "Running"):
        d = pd.DataFrame([{"Agent": s["agent"], "Start": pd.to_datetime(s["started"]), "End": pd.to_datetime(s.get("ended") or s["started"]) + pd.Timedelta(milliseconds=300),
                           "Status": s["status"]} for s in steps])
        fig = px.timeline(d, x_start="Start", x_end="End", y="Agent", color="Status", height=280,
                          color_discrete_map=charts.PALETTE)
        fig.update_yaxes(autorange="reversed", title=None)
        st.plotly_chart(charts.apply(fig, height=280), use_container_width=True)

if run["status"] == "Running":
    time.sleep(1.0)
    st.rerun()

if run["status"] == "Failed":
    st.error(run.get("error"))
tabs = st.tabs(["1 Initial condition", "2 Event", "3 Agents", "4 Reasoning", "5 Decision", "6 Dashboard changes", "7 KPI impact"])
with tabs[0]:
    b = run.get("kpi_before", {})
    ui.kpis([("Avg days of cover", ui.fmt(b.get("avg_days_of_cover"), 2)), ("Stock-out risk", b.get("stockout_events")),
             ("On-time", ui.fmt(b.get("on_time_delivery"), 1, True)), ("Vessels delayed", b.get("vessels_delayed"))])
    lp = (run.get("dashboards_before") or {}).get("load_port", {})
    stock = ", ".join(f"{x['cement_type']} {x['available_ton']:,.0f} t" for x in lp.get("stock", []))
    st.caption(f"Load port stock: {stock} · production capacity factor {lp.get('production_capacity_factor')}")
with tabs[1]:
    for s in run["steps"]:
        if s["agent"] == "Event Detected":
            st.markdown(f"**{s['started'][11:]}** · {s['outputs'].get('event')}")
with tabs[2]:
    for s in run["steps"]:
        with st.expander(f"{s['agent']} · {s['enterprise']} · {s['status']} · {s.get('duration_ms', 0)} ms"):
            for line in s.get("log", []):
                st.write("• " + line)
            if s.get("inputs"):
                st.caption("Inputs")
                st.json(s["inputs"], expanded=False)
            if s.get("outputs"):
                st.caption("Outputs")
                st.json(s["outputs"], expanded=False)
with tabs[3]:
    if run.get("narrative"):
        st.markdown("**Narrator Agent** (explains computed facts only)")
        st.info(run["narrative"])
    if run.get("negotiation"):
        st.markdown("**Negotiation timeline between enterprises**")
        for n in run["negotiation"]:
            ent = "management" if n["who"] == "Management" else ("shipping" if n["who"].startswith("Shipping") else ("global" if "Planner" in n["who"] else "manufacturer"))
            st.markdown(ui.message_bubble({"ts": n["ts"], "from": n["who"], "to": "Negotiation", "from_enterprise": ent, "to_enterprise": "global",
                                           "type": "negotiation", "content": n["text"]}), unsafe_allow_html=True)
    if run.get("excluded"):
        with st.expander("Vessels excluded by hard rules"):
            st.dataframe(pd.DataFrame(run["excluded"]).drop_duplicates(["vessel", "reason"]), hide_index=True, use_container_width=True)
with tabs[4]:
    plan = run.get("plan", [])
    if plan:
        st.dataframe(pd.DataFrame([{"Plant": p["plant_id"], "Rank": p["priority"]["rank"], "Priority score": p["priority"]["priority_score"],
                                    "Stock-out (d)": p["priority"]["stockout_days"], "Vessel": p.get("vessel") or "none eligible",
                                    "Qty (t)": p.get("quantity_ton"), "Arrival (h)": p.get("arrival_hours"), "± (h)": p.get("arrival_range_hours"),
                                    "SAW": p.get("saw_score"), "Alternatives": ", ".join(p.get("alternatives", [])),
                                    "Warnings": "; ".join(p.get("warnings", []) or ([p["warning"]] if p.get("warning") else []))} for p in plan]),
                     hide_index=True, use_container_width=True)
        first = next((p for p in plan if p.get("ranking")), None)
        if first:
            st.markdown(f"**SAW ship ranking for {first['plant_id']}** (normalised criteria x weights)")
            st.dataframe(pd.DataFrame([{"Vessel": r["vessel"], "SAW": r["saw_score"], "Arrival (h)": r["arrival_hours"], "Capacity (t)": r["capacity_ton"],
                                        "Proven calls": r["proven_calls"], "Evidence": r["evidence"], "Wave (m)": r["wave_m"], **{f"r_{k}": v for k, v in r["normalized"].items()}}
                                       for r in first["ranking"]]), hide_index=True, use_container_width=True)
    if run.get("comparison"):
        st.markdown("**Original vs adaptive plan**")
        st.dataframe(pd.DataFrame(run["comparison"]), hide_index=True, use_container_width=True)
    st.markdown(f"Decisions created: {', '.join(run.get('decisions', [])) or 'none'} · approve them in the Global Control Center.")
    if st.button("Go to Decision Center"):
        st.switch_page("views/control_center.py")
with tabs[5]:
    b, a = run.get("dashboards_before") or {}, run.get("dashboards_after") or {}
    rows = []
    for pid, v in (a.get("manufacturer") or {}).items():
        o = (b.get("manufacturer") or {}).get(pid, {})
        if o != v:
            rows.append({"Dashboard": "Manufacturer", "Item": pid, "Before": f"rank {o.get('rank')}, stock-out {o.get('stockout_days')} d",
                         "After": f"rank {v['rank']}, stock-out {v['stockout_days']} d"})
    for vs, v in (a.get("shipping") or {}).items():
        o = (b.get("shipping") or {}).get(vs, {})
        if o != v:
            rows.append({"Dashboard": "Shipping", "Item": vs, "Before": str(o), "After": str(v)})
    for k2 in ("supplier", "distribution"):
        for item, v in (a.get(k2) or {}).items():
            o = (b.get(k2) or {}).get(item)
            if o != v:
                rows.append({"Dashboard": k2.title(), "Item": item, "Before": str(o), "After": str(v)})
    if a.get("load_port") != b.get("load_port"):
        rows.append({"Dashboard": "Manufacturer", "Item": "Load port", "Before": str(b.get("load_port")), "After": str(a.get("load_port"))})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True) if rows else st.caption("No dashboard values changed.")
with tabs[6]:
    if run.get("kpi_after"):
        d = kpi_delta(run.get("kpi_before", {}), run["kpi_after"])
        st.dataframe(d, hide_index=True, use_container_width=True)
        st.caption("Approving decisions in the Decision Center changes KPIs further (incoming deliveries extend days of cover).")
