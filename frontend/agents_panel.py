"""Per-enterprise 'AI Agent Monitoring' tab: agent registry status + run an agent directly on its own enterprise API."""
import streamlit as st

import ui
from client import get, post


def render(enterprise, endpoints):
    """endpoints: {agent name: path on this enterprise API}."""
    agents = [a for a in (get("orchestrator", "/agents") or []) if a["host"] == enterprise]
    st.markdown('<div class="agrid">' + "".join(ui.agent_card(a) for a in agents) + "</div>", unsafe_allow_html=True)
    st.caption("Agents run inside this enterprise's own API. The Global Orchestrator calls them over HTTP; you can also run one locally here.")
    cols = st.columns(len(endpoints))
    for c, (name, path) in zip(cols, endpoints.items()):
        if c.button(f"Run {name}", key=f"run-{path}", use_container_width=True):
            try:
                st.session_state[f"out-{enterprise}"] = post(enterprise, path)
            except RuntimeError as e:
                st.error(str(e))
    out = st.session_state.get(f"out-{enterprise}")
    if out:
        with st.container(border=True):
            st.markdown(f"**{out['agent']}** {ui.badge(out['status'])} · {out['duration_ms']} ms", unsafe_allow_html=True)
            for line in out["log"]:
                st.write("• " + line)
            with st.expander("Inputs and outputs (JSON)"):
                st.json({"inputs": out["inputs"], "outputs": out["outputs"]}, expanded=False)
    msgs = [m for m in (get("orchestrator", "/messages?limit=200") or []) if enterprise in (m["from_enterprise"], m["to_enterprise"])]
    if msgs:
        ui.section("Agent execution log", "A2A messages involving this enterprise")
        with st.container(height=380, border=False):
            st.markdown("".join(ui.message_bubble(m) for m in msgs[:40]), unsafe_allow_html=True)
