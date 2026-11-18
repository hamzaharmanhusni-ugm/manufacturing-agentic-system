"""Security and governance: RBAC, data-sharing policies, audit trail, API access logs, auth demo."""
import httpx
import pandas as pd
import streamlit as st

import ui
from client import get
from shared.config import url

ui.guard("governance")
ui.header("Governance & Security", "Code decides, AI explains, people act", synthetic=False)

gov = get("orchestrator", "/governance")
if not ui.check(gov):
    st.stop()
tabs = st.tabs(["Roles (RBAC)", "Data-sharing policies", "Audit trail", "API access logs", "Authentication test", "Guardrails"])

with tabs[0]:
    rows = [{"Role": r, "Views": ", ".join(v["views"]), "Manufacturer tabs": v["tabs"] if v["tabs"] == "all" else ", ".join(v["tabs"]),
             "Approve dispatch": v["approve"], "Trigger simulation": v["simulate"], "API key used": v["key"]} for r, v in gov["roles"].items()]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

with tabs[1]:
    st.caption("Each enterprise API enforces its own policy G_i. Example: the orchestrator cannot read raw price/margin (manufacturer) or engine data (shipping).")
    cols = st.columns(4)
    for c, (ent, pol) in zip(cols, gov["enterprise_policies"].items()):
        c.markdown(f"**{ent.title()}**")
        c.dataframe(pd.DataFrame([{"principal": p, "scopes": ", ".join(s)} for p, s in pol.items()]), hide_index=True, use_container_width=True)

with tabs[2]:
    st.dataframe(pd.DataFrame(get("orchestrator", "/audit") or []), hide_index=True, use_container_width=True)
    st.markdown("**Agent activity history**")
    st.dataframe(pd.DataFrame(get("orchestrator", "/runs") or []), hide_index=True, use_container_width=True)

with tabs[3]:
    logs = get("orchestrator", "/api-logs") or {}
    c1, c2 = st.columns(2)
    c1.markdown("**Outbound (orchestrator to enterprises)**")
    c1.dataframe(pd.DataFrame(logs.get("outbound", [])), hide_index=True, use_container_width=True, height=420)
    c2.markdown("**Inbound (logged by each enterprise API)**")
    ib = pd.DataFrame(logs.get("inbound", []))
    if len(ib):
        f = c2.multiselect("Enterprise", sorted(ib.enterprise.unique()), default=sorted(ib.enterprise.unique()))
        c2.dataframe(ib[ib.enterprise.isin(f)], hide_index=True, use_container_width=True, height=380)

with tabs[4]:
    st.markdown("Send a live request to an enterprise API with a chosen key to see authentication (401) and policy (403) checks.")
    a, b, c = st.columns(3)
    ent = a.selectbox("Enterprise API", ["manufacturer", "shipping", "distribution", "supplier"])
    path = b.text_input("Path", {"manufacturer": "/marketing/prices", "shipping": "/vessels/internal", "distribution": "/distributors",
                                 "supplier": "/purchase-orders"}[ent])
    key = c.selectbox("X-API-Key", ["key-global-orchestrator", "key-global-admin", "key-manufacturer-portal", "key-shipping-portal",
                                    "key-distribution-portal", "key-supplier-portal", "invalid-key"])
    if st.button("Send request", type="primary"):
        r = httpx.get(url(ent) + path, headers={"X-API-Key": key}, timeout=30)
        (st.success if r.is_success else st.error)(f"HTTP {r.status_code}")
        st.code(r.text[:800])

with tabs[5]:
    st.dataframe(pd.DataFrame([
        {"Guardrail": "Deterministic numbers", "Implementation": "Scores, ETA, rankings come from shared/decision_engine.py and shared/ml_models.py"},
        {"Guardrail": "Bounded AI output", "Implementation": "Narrator uses a template; optional LLM output is rejected if it introduces any number not in the facts"},
        {"Guardrail": "Fail-safe delivery", "Implementation": "If the LLM fails, the computed plan is delivered without narration"},
        {"Guardrail": "Alert once", "Implementation": "Low-stock events fire once per series and re-arm after recovery"},
        {"Guardrail": "Cross-company data sharing", "Implementation": "Per-enterprise scopes (G_i); price/margin leave the manufacturer only as grades"},
        {"Guardrail": "Human in the loop", "Implementation": "Every dispatch is 'Requires human approval'; only authorised roles may approve"},
        {"Guardrail": "Audit trail", "Implementation": "Scenario runs, approvals, rejections, denied attempts and resets are logged"},
    ]), hide_index=True, use_container_width=True)
