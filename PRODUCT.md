# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Two audiences in equal measure (confirmed by the owner):
- **Lecturers and examiners** of the master's course "AI Agentic Technology Systems for Digital Enterprise Ecosystem", watching a live demo on a projector or shared screen. They must grasp within seconds how agents from different enterprises collaborate.
- **Supply chain planners and managers** (manufacturer, shipping subsidiary, distribution, supplier) using it as working software: reading stock, fleet and forecast data, and approving or rejecting dispatch recommendations.

## Product Purpose

An academic prototype of a multi-enterprise Agentic AI Decision Support System for bulk cement distribution: one load port, nine packing plants (PP A to PP I), 19 vessels. Independent enterprise APIs host their own agents; a Global Orchestrator dispatches them in parallel, a Dispatch Planner ranks plants and ships, a Narrator explains, and a human approves. Success for the demo: the audience sees an event trigger agents across enterprises, understands the recommendation and why, and sees KPIs change after approval.

## Positioning

"Code decides, AI explains, people act." Every number comes from deterministic code or validated models; the LLM only narrates verified facts; a person keeps final authority. Collaboration crosses enterprise boundaries (separate APIs, databases, governance policies), not departments inside one app.

## Operating Context

- Runs locally: Streamlit UI on :3000, Global Orchestrator :8000, four enterprise FastAPI services :8001 to :8004, PostgreSQL and MongoDB in Docker (local SQLite/JSON fallback).
- Used in a class presentation following docs/demo-script.md, and by planners switching roles (RBAC simulation) to see only authorised data.
- Six scenarios: normal, low stock PP C, demand surge PP F, vessel delay with adaptive replanning, weather disruption, supplier disruption.

## Capabilities and Constraints

- Seven proposal agents (Orchestrator, ML Forecasting, Demand & Priority, Stock Monitoring, Fleet Tracking, Dispatch Planner, Narrator) plus two extension agents (Distribution, Procurement).
- Models: LightGBM quantile forecast (TFT challenger in simulation mode), Random Forest ETA, ARIMA stock-out, Weibull failure risk, geofence + DBSCAN vessel status. SAW and Eq. 14 priority grades.
- Distribution and Supplier enterprises are prototype extensions, not facts from the proposal, and must stay labelled as such.
- Interface language: English (confirmed). Technical terms stay as-is.
- Brief constraints carried from the course assignment: enterprise SaaS feel, dark navy sidebar, light analytics background, blue and cyan accents, compact data cards, professional charts, status indicators; no excessive gradients or decorative animation; no generic landing page; no buttons without function.

## Evidence on Hand

- Proposal documents: ../Agentic-AI-Cement-Supply-Chain-Management-ID.docx and ../Agentic-AI-Cement-Distribution.pptx.
- All operational data is synthetic and must be labelled synthetic. No real customer, plant, vessel or performance claims may be invented; names stay masked (PP A to I, Port J and K, Ship letters).
- Design references (internal only): docs/design-references/.

## Product Principles

1. Show the collaboration first: what each agent did, for which enterprise, and in what order.
2. Every recommendation travels with its reason, its numbers and its uncertainty.
3. Human authority is visible: pending decisions are never hidden behind tabs.
4. Honest data: synthetic, simulated and model-predicted values are labelled where they appear.
5. Each role sees only what its enterprise policy shares.
