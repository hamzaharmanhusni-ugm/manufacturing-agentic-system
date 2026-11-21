"""Live Operations: the agents as robot colleagues (left) and the physical world they act on (right), on one simulated clock.
A teaching view of the real case: demand drains silos, a sensor wakes the agents, a person signs, a vessel sails, the silo refills."""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import ui
from client import role
from shared.config import url
from shared.rbac import can

ui.guard("global")
ui.header("Live Operations", "One simulated clock for the whole ecosystem: watch the agents think on the left and the real supply chain move on the right.")

st.markdown(
    '<div class="notice info"><span class="t">How to run the real case.</span> Press <b>Play</b>. Plants sell cement every simulated hour, '
    "so silos drain at each plant's own daily demand. When a silo falls below 25 %, the sensor wakes the agents by itself. "
    "The clock stops while they work and waits for your signature in Box 8. After you approve, the vessel loads, sails and unloads, "
    "and the silo refills on the map. A storm and a supplier problem arrive later in the story.</div>", unsafe_allow_html=True)

html = (Path(__file__).resolve().parent.parent / "office3d.html").read_text(encoding="utf-8")
html = (html.replace("__ORCH__", url("orchestrator").replace("127.0.0.1", "localhost"))
            .replace("__ROLE__", role())
            .replace("__CAN_APPROVE__", "true" if can(role(), "approve") else "false")
            .replace("__CAN_SIM__", "true" if can(role(), "simulate") else "false"))
components.html(html, height=900)

c1, c2 = st.columns(2)
c1.page_link("views/control_center.py", label="Open the full dispatch docket", icon=":material/assignment:")
c2.page_link("views/simulation.py", label="Analyse one scenario step by step", icon=":material/play_circle:")

ui.section("How to read this view", "concepts from the course, shown by the agents and the world")
st.markdown("""
<table class="rt">
<tr><th>What you see</th><th>What it means</th><th>Agentic concept</th></tr>
<tr><td>The clock runs and silo gauges on the map go down</td><td>Plants sell cement every hour at their own daily demand.</td><td>The environment an agent perceives</td></tr>
<tr><td>The orange beacon flashes, a log line says "IIoT silo sensor"</td><td>A rule fired (silo below 25 percent) and became an event.</td><td>Event-driven architecture, reactive trigger</td></tr>
<tr><td>The Orchestrator sends envelopes to four robots at once</td><td>Task plan and parallel dispatch; agents never call each other.</td><td>Orchestrator-worker, fan-out and fan-in</td></tr>
<tr><td>A robot walks with a cyan ring; its screen shows silo levels, a forecast or a ranking</td><td>The agent is working with its own tools inside its own enterprise API.</td><td>Perceive, reason, act; tool use</td></tr>
<tr><td>Envelopes cross between platforms</td><td>Real messages crossing company boundaries with an API key.</td><td>Agent-to-agent (A2A) communication, governance</td></tr>
<tr><td>The Dispatch Planner's screen shows "Ship N → PP C"</td><td>The plan comes from deterministic code (SAW, greedy assignment).</td><td>Code decides</td></tr>
<tr><td>The clock stops and Box 8 appears above the views</td><td>Nothing moves in the real world until a person signs.</td><td>Human in the loop: people act</td></tr>
<tr><td>After approval the vessel sails on the map and the silo refills</td><td>The decision changes the environment; the next sensor reading reflects it.</td><td>Closed loop: act, then perceive again</td></tr>
<tr><td>A storm turns a route red and slows a laden vessel; agents replan</td><td>New information arrives mid-plan and the ecosystem adapts.</td><td>Adaptive replanning</td></tr>
</table>
""", unsafe_allow_html=True)
st.caption("All plant, vessel and demand data is synthetic. Robot model: RobotExpressive by Tomás Laulhé (Quaternius), CC0 1.0. "
           "Rendering: three.js (MIT). Map: Leaflet (BSD 2-Clause), CARTO basemap with OpenStreetMap data.")
