"""Architecture: E_i = (U_i, M_i, D_i, A_i, P_i, G_i) for each enterprise, heterogeneity table, system diagram."""
import pandas as pd
import streamlit as st

import ui
from client import get

ui.header("Architecture", "Every enterprise is an independent environment E_i = (U_i, M_i, D_i, A_i, P_i, G_i)", synthetic=False)

arch = get("orchestrator", "/architecture")
if not ui.check(arch):
    st.stop()

st.graphviz_chart("""
digraph G { rankdir=TB; bgcolor="transparent"; compound=true; nodesep=0.35; ranksep=0.5;
  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, fillcolor="#ffffff", color="#94a3b8"];
  subgraph cluster_ui { label="People and channels"; style="rounded,dashed"; color="#94a3b8"; fontsize=10;
    ui [label="Streamlit dashboards :3000\\nGlobal Control Center, 4 enterprise views, RBAC", fillcolor="#e0f2fe"];
    push [label="Notifications (Telegram / WhatsApp simulated)", fillcolor="#e0f2fe"]; }
  subgraph cluster_g { label="Global Orchestrator :8000 (agentic core)"; style="rounded,filled"; fillcolor="#0b1b33"; fontcolor="white"; fontsize=10;
    orch [label="Orchestrator Agent\\nevent -> task plan -> parallel dispatch", fillcolor="#13284a", fontcolor="white"];
    dp [label="Dispatch Planner Agent\\nSAW + greedy assignment", fillcolor="#13284a", fontcolor="white"];
    nar [label="Narrator Agent\\nexplains verified numbers", fillcolor="#13284a", fontcolor="white"];
    appr [label="Human approval\\nDecision Center", fillcolor="#7c3aed", fontcolor="white"]; }
  subgraph cluster_m { label="E1 Manufacturer :8001 (PostgreSQL)"; style=rounded; color="#0891b2"; fontsize=10;
    sm [label="Stock Monitoring\\nARIMA"]; ml [label="ML Forecasting\\nLightGBM / TFT sim"]; dpa [label="Demand & Priority\\nEq. 14"]; }
  subgraph cluster_s { label="E2 Shipping :8002 (MongoDB)"; style=rounded; color="#0891b2"; fontsize=10;
    ft [label="Fleet Tracking\\nRF ETA, DBSCAN, Weibull"]; }
  subgraph cluster_d { label="E3 Distribution :8003 (SQLite) extension"; style="rounded,dashed"; color="#0891b2"; fontsize=10;
    da [label="Distribution Agent"]; }
  subgraph cluster_p { label="E4 Supplier :8004 (PostgreSQL) extension"; style="rounded,dashed"; color="#0891b2"; fontsize=10;
    pa [label="Procurement Agent"]; }
  ui -> orch [label="REST"]; orch -> sm; orch -> ml; orch -> dpa; orch -> ft; orch -> da; orch -> pa;
  sm -> dp [style=dashed]; ml -> dp [style=dashed]; dpa -> dp [style=dashed]; ft -> dp [style=dashed];
  dp -> nar -> appr; appr -> ui; nar -> push;
}""", use_container_width=True)
st.caption("Solid arrows: A2A task calls over HTTP (X-API-Key). Dashed arrows: results returned to the orchestrator and merged once by the Dispatch Planner.")

st.subheader("Enterprise environments E_i")
labels = {"U": "U · Users and roles", "M": "M · Application modules", "D": "D · Local datasets", "A": "A · AI agents", "P": "P · Protocols and APIs", "G": "G · Governance policy"}
cols = st.columns(4)
for c, (ent, e) in zip(cols, arch.items()):
    with c.container(border=True):
        st.markdown(f"**{ent.title()}** <span class='tag'>{e['origin']}</span>", unsafe_allow_html=True)
        for key in "UMDAP":
            st.markdown(f"<div class='subtle'><b>{labels[key]}</b></div>", unsafe_allow_html=True)
            st.markdown("\n".join(f"- {x}" for x in e[key]))
        st.markdown(f"<div class='subtle'><b>{labels['G']}</b></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{"principal": k, "scopes": ", ".join(v)} for k, v in (e["G"] or {}).items()]), hide_index=True, use_container_width=True)

st.subheader("Heterogeneous technology choices (prototype, not the organisations' real systems)")
st.dataframe(pd.DataFrame([
    {"Enterprise": "Cement Manufacturer", "Database": "PostgreSQL (Docker)", "Data shape": "relational, snake_case, tons", "API": "REST JSON :8001", "Origin": "proposal"},
    {"Enterprise": "Shipping & Logistics", "Database": "MongoDB (Docker)", "Data shape": "nested documents, camelCase", "API": "REST JSON :8002", "Origin": "proposal (subsidiary)"},
    {"Enterprise": "Distribution", "Database": "SQLite file", "Data shape": "raw SQL, 50 kg bags", "API": "REST JSON :8003", "Origin": "prototype extension"},
    {"Enterprise": "Supplier & Procurement", "Database": "PostgreSQL (Docker)", "Data shape": "ERP CSV export, UPPER_SNAKE", "API": "REST JSON :8004", "Origin": "prototype extension"},
]), hide_index=True, use_container_width=True)

st.subheader("What comes from the proposal and what was added")
st.dataframe(pd.DataFrame([
    {"Component": "7 agents (Orchestrator, ML Forecasting, Demand & Priority, Stock Monitoring, Fleet Tracking, Dispatch Planner, Narrator)", "Source": "proposal"},
    {"Component": "LightGBM champion, TFT challenger, RF ETA, ARIMA stock-out, Weibull maintenance, geofence status", "Source": "proposal (TFT in simulation mode)"},
    {"Component": "Eq. 14 priority grades, SAW ship ranking, greedy assignment, weights 0.35/0.20/0.20/0.15/0.10", "Source": "proposal"},
    {"Component": "Distribution and Supplier enterprises, Distribution Agent, Procurement Agent", "Source": "academic prototype extension"},
    {"Component": "DBSCAN vessel activity detection", "Source": "course requirement (added next to the proposal's geofence rule)"},
    {"Component": "All datasets (9 plants, 22 silos, 19 vessels, 282 voyages, sales, weather, distributors, suppliers)", "Source": "synthetic"},
]), hide_index=True, use_container_width=True)
st.markdown("API documentation (Swagger): [Orchestrator :8000](http://localhost:8000/docs) · [Manufacturer :8001](http://localhost:8001/docs) · "
            "[Shipping :8002](http://localhost:8002/docs) · [Distribution :8003](http://localhost:8003/docs) · [Supplier :8004](http://localhost:8004/docs)")
