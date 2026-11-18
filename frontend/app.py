"""Streamlit entry point: navigation, role sign-in simulation, notification tray."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT.parent)]

import streamlit as st  # noqa: E402

import charts  # noqa: E402
import ui  # noqa: E402
from client import get  # noqa: E402
from shared.rbac import ROLES  # noqa: E402

st.set_page_config(page_title="Cement Dispatch Control", page_icon=":material/local_shipping:", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)
charts.register()

with st.sidebar:
    st.markdown('<div class="brand"><div class="w">CEMENT DISPATCH CONTROL</div>'
                '<div class="d">Multi-enterprise agentic decision support</div></div>', unsafe_allow_html=True)

pages = {
    "Global": [st.Page("views/control_center.py", title="Control Center", icon=":material/assignment:", default=True),
               st.Page("views/simulation.py", title="Simulation Center", icon=":material/play_circle:"),
               st.Page("views/analytics.py", title="KPI & Analytics", icon=":material/monitoring:")],
    "Enterprises": [st.Page("views/manufacturer.py", title="Cement Manufacturing", icon=":material/factory:"),
                    st.Page("views/shipping.py", title="Shipping & Logistics", icon=":material/directions_boat:"),
                    st.Page("views/distribution.py", title="Distribution", icon=":material/local_shipping:"),
                    st.Page("views/supplier.py", title="Supplier & Procurement", icon=":material/inventory_2:")],
    "System": [st.Page("views/architecture.py", title="Architecture", icon=":material/account_tree:"),
               st.Page("views/governance.py", title="Governance & Security", icon=":material/shield:")],
}
nav = st.navigation(pages)

with st.sidebar:
    st.selectbox("Signed in as", list(ROLES), key="role", help="Role simulation: each role sees only what its enterprise policy shares")
    r = ROLES[st.session_state.role]
    st.caption(f"Can sign dispatches: {'yes' if r['approve'] else 'no'} · Can run scenarios: {'yes' if r['simulate'] else 'no'}")
    notes = get("orchestrator", "/notifications") or []
    mine = [n for n in notes if st.session_state.role == "Global Administrator" or n["role"] == st.session_state.role]
    with st.popover(f"Notifications ({len(mine)})", icon=":material/notifications:", use_container_width=True):
        if not mine:
            st.caption("No notifications for this role.")
        for n in mine[:15]:
            st.markdown(f'<div class="notice {"critical" if n["severity"] == "critical" else ("info" if n["severity"] == "info" else "")}">'
                        f'<span class="t">{ui.e(n["channel"])} to {ui.e(n["role"])}</span><br>{ui.e(n["text"])}'
                        f'<div class="subtle">{ui.hhmmss(n["ts"])}</div></div>', unsafe_allow_html=True)
    st.caption("Code decides · AI explains · People act")

nav.run()
