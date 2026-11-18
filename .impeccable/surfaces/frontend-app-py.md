---
version: 1
slug: "frontend-app-py"
primary_target: "frontend/app.py"
related_targets: ["frontend/ui.py","frontend/views/control_center.py","frontend/views/simulation.py"]
---

# Surface: Streamlit app (Global Agentic Control Center and all pages)

Mode: Operate. Audience: lecturers watching a projector demo and planners approving dispatches (equal weight). Language: English.

## Direction contract

THESIS: Every orchestration run is a dispatch docket. Each agent fills and signs its own numbered box, the Dispatch Planner writes the plan, the Narrator adds remarks, and a person stamps it. Refuses the KPI-card grid with charts and a status table.

OWN-WORLD: White ruled form stock on a cool #f3f5f8 ground, navy #0b1b33 ink and sidebar, 1px #c9d2de rules, zero radius on forms, field labels in 11px small caps above values in tabular figures. Blue #1d4ed8 for actions, cyan #0891b2 for live/running, red #b91c1c only for rejection, stock-out and failure. Approval is a ruled stamp. Enterprise identity by a 1px-ruled code chip (MFG, SHP, DST, SUP, GLB).

STORY: The viewer sees an event arrive, watches four agents from two enterprises fill their boxes at the same time, reads the plan and the plain remark, then sees who must sign. Planners act from the same docket.

FIRST VIEWPORT: Control Center = the live docket at full width: header strip (run id, scenario, status, elapsed), Box 1 Event, Boxes 2 to 5 parallel agents in one ruled row, Box 6 dispatch plan table, Box 7 Narrator remarks, Box 8 Authorisation with Approve, isolated Reject. Enterprise ledger strip above the docket. Map, stock and messages follow below.

FORM: Dispatch Manifest (bills of lading, cargo manifests, dispatch dockets), position 4 on the ordered list, seed key 18fc309b. Raises: changed rows stay lit until acknowledged (gate board); hairline seams and isolated Reject (dev console); states as printed marks, no radius (centre rail); hierarchy by scale contrast (type specimen); the filling box lifts, others dim (streaming wall).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
