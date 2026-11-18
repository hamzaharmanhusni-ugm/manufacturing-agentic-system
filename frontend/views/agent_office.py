"""Agent Office 3D: the agents as robot colleagues in a shared office, driven live by the orchestrator. A teaching view."""
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import ui
from client import get, post, role
from shared.config import url
from shared.rbac import can

ui.guard("global")
ui.header("Agent Office 3D", "The nine agents as robot colleagues. Each zone is an enterprise; envelopes are real agent-to-agent messages.")

scen = get("orchestrator", "/scenarios") or []
labels = {s["title"]: s["key"] for s in scen}
c1, c2, c3 = st.columns([2.2, 1, 1], vertical_alignment="center")
pick = c1.selectbox("Event", list(labels), label_visibility="collapsed")
if c2.button(":material/play_arrow: Run and watch", type="primary", use_container_width=True, disabled=not can(role(), "simulate")):
    try:
        post("orchestrator", f"/scenarios/{labels[pick]}/run", {"role": role()})
    except RuntimeError as ex:
        st.error(str(ex))
    time.sleep(0.3)
c3.page_link("views/control_center.py", label="Sign the docket", icon=":material/assignment:")

# The browser polls the orchestrator directly (CORS allows the dashboard origin), so the 3D scene never reloads.
html = (Path(__file__).resolve().parent.parent / "office3d.html").read_text(encoding="utf-8").replace("__ORCH__", url("orchestrator").replace("127.0.0.1", "localhost"))
components.html(html, height=700)

ui.section("How to read the office", "concepts from the course, shown by the agents")
st.markdown("""
<table class="rt">
<tr><th>What you see</th><th>What it means</th><th>Agentic concept</th></tr>
<tr><td>Five platforms in different colours</td><td>Four independent enterprises and the global hub. Each runs its own API, database and policy.</td><td>Multi-enterprise ecosystem, E<sub>i</sub> = (U, M, D, A, P, G)</td></tr>
<tr><td>The orange beacon flashes</td><td>An event arrives: a silo sensor, a sales change, a vessel delay, a weather alert.</td><td>Event-driven architecture</td></tr>
<tr><td>The navy Orchestrator sends envelopes to several robots at once</td><td>Task plan and parallel dispatch; agents never call each other.</td><td>Orchestrator-worker, fan-out and fan-in</td></tr>
<tr><td>A robot walks with a pulsing cyan ring</td><td>The agent is working inside its own enterprise API.</td><td>Perceive, reason, act; tool use</td></tr>
<tr><td>Envelopes travel between zones</td><td>Real messages from the orchestrator log, crossing company boundaries with an API key.</td><td>Agent-to-agent (A2A) communication</td></tr>
<tr><td>The Dispatch Planner gives a thumbs up</td><td>The plan is computed by deterministic code (SAW and greedy assignment).</td><td>Code decides</td></tr>
<tr><td>The Narrator gives a thumbs up</td><td>The plan is explained in words; numbers are guarded.</td><td>AI explains, with guardrails</td></tr>
<tr><td>Robots wave, the person stamps</td><td>Decisions wait for an authorised person to approve or reject.</td><td>Human in the loop: people act</td></tr>
</table>
""", unsafe_allow_html=True)
st.caption("Robot model: RobotExpressive by Tomás Laulhé (Quaternius), CC0 1.0. Rendering: three.js (MIT). Both served locally from frontend/static.")
