"""The dispatch docket: one orchestration run as a ruled form that agents fill and a person stamps.

Box 1 event · Boxes 2-5 (+extensions) parallel agents · Box 6 dispatch plan · Box 7 Narrator remarks · Box 8 authorisation."""
import streamlit as st

import ui
from client import get, post, role
from shared.rbac import can

WORKERS = ["Stock Monitoring Agent", "ML Forecasting Agent", "Fleet Tracking Agent", "Demand & Priority Agent",
           "Distribution Agent (extension)", "Procurement Agent (extension)"]
SHORT = {"Stock Monitoring Agent": "Stock Monitoring", "ML Forecasting Agent": "ML Forecasting", "Fleet Tracking Agent": "Fleet Tracking",
         "Demand & Priority Agent": "Demand & Priority", "Distribution Agent (extension)": "Distribution (ext.)",
         "Procurement Agent (extension)": "Procurement (ext.)"}
HOST = {"Stock Monitoring Agent": "manufacturer", "ML Forecasting Agent": "manufacturer", "Fleet Tracking Agent": "shipping",
        "Demand & Priority Agent": "manufacturer", "Distribution Agent (extension)": "distribution", "Procurement Agent (extension)": "supplier"}


def _summary(agent, s):
    """Two or three facts per box, read from the agent's own output (never invented)."""
    o = s.get("outputs") or {}
    try:
        if agent == "Stock Monitoring Agent":
            ser = sorted(o.get("series", []), key=lambda x: x["stockout_days"])[:2]
            out = [f"{x['plant_id']} {x['cement_type']}: stock-out in <b>{x['stockout_days']} d</b>, cover {x['days_of_cover']} d" for x in ser]
            ev = o.get("low_stock_events", [])
            return out + ([f"<b>{len(ev)}</b> new low-stock event(s)"] if ev else ["No new low-stock event"])
        if agent == "ML Forecasting Agent":
            m = o.get("metrics", {})
            top = sorted(o.get("summary_14d", []), key=lambda x: -x["p50"])[:1]
            return [f"14-day P50 for {len(o.get('summary_14d', []))} series"] + \
                   [f"Largest: {t['plant_id']} {t['cement_type']} <b>{t['p50']:,.0f} t</b> ({t['p10']:,.0f} to {t['p90']:,.0f})" for t in top] + \
                   [f"WAPE {m.get('wape_champion')} LightGBM vs {m.get('wape_challenger')} TFT sim"]
        if agent == "Fleet Tracking Agent":
            fl = o.get("fleet", [])
            avail = sum(1 for v in fl if v.get("available_in_h") is not None and not v.get("assigned_plant"))
            nsa = o.get("sailing_not_advised", [])
            return [f"<b>{avail}</b> of {len(fl)} vessels available", f"Sailing not advised: <b>{', '.join(nsa) or 'none'}</b>",
                    f"High failure risk: {', '.join(o.get('high_failure_risk', [])) or 'none'}"]
        if agent == "Demand & Priority Agent":
            r = o.get("ranking", [])[:3]
            return [f"#{x['rank']} {x['plant_id']} score <b>{x['priority_score']}</b>" for x in r]
        if agent.startswith("Distribution"):
            r = o.get("regions_at_risk", [])
            return [f"<b>{len(r)}</b> region(s) at risk"] + [f"{x['region']}: {x['open_order_ton']} t open" for x in r[:2]]
        if agent.startswith("Procurement"):
            imp = o.get("production_impact")
            return ([f"<b>{imp['material']}</b> short: production x{imp['production_capacity_factor']}"] if imp else ["No production impact"]) + \
                   [f"Alternative for {a['material']}: {', '.join(a['recommended_alternative']) or 'none'}" for a in o.get("alternatives", [])[:1]]
    except (KeyError, TypeError):
        pass
    return [ui.e(x) for x in (s.get("log") or [])[-2:]]


def html_text(fragment):
    """Plain text of a small HTML fragment, for hover titles."""
    import re
    return re.sub(r"<[^>]+>", "", str(fragment)).replace("&amp;", "&")


def _box(no, title, enterprise, status, body_lines, sig, live=False, empty=False, cls_extra=""):
    cls = "box" + (" live" if live else "") + (" empty" if empty else "") + (f" {cls_extra}" if cls_extra else "")
    body = "<ul>" + "".join(f'<li title="{ui.e(html_text(line))}">{line}</li>' for line in body_lines) + "</ul>" if body_lines else ""
    return (f'<div class="{cls}"><div class="bh"><div class="top"><span class="bt"><span class="bn">BOX {no}</span> {ui.e(title)}</span>'
            f'{ui.chip(enterprise)}</div><div>{ui.badge(status)}</div></div>'
            f'<div class="body">{body}</div><div class="sig">{sig}</div></div>')


def _sig(s):
    if not s or s.get("status") in (None, "Running"):
        return "<span>Awaiting signature</span>"
    return (f'<span title="Signed by {ui.e(s["agent"])}"><i>Signed</i> {ui.hhmmss(s.get("ended"))} &middot; {s.get("duration_ms", 0):,.0f} ms</span>')


def plan_table(plan, comparison=None, acknowledged=False):
    changed = {c["plant_id"] for c in (comparison or []) if c.get("changed")} if not acknowledged else set()
    was = {c["plant_id"]: c.get("original_vessel") for c in (comparison or [])}
    rows = []
    for p in plan:
        pr = p["priority"]
        v = p.get("vessel")
        arr = p.get("arrival_hours")
        late = v and arr and arr / 24 > pr["stockout_days"]
        prev = f' <span class="struck">{ui.e(was[p["plant_id"]])}</span>' if p["plant_id"] in changed and was.get(p["plant_id"]) else ""
        rng = p.get("arrival_range_hours")
        arr_txt = (f"{arr / 24:.1f} d" if arr else "-") + (f" ±{rng}h" if rng is not None else "")
        warn = "; ".join(p.get("warnings") or ([p["warning"]] if p.get("warning") else []))
        rows.append(f'<tr class="{"chg" if p["plant_id"] in changed else ""}"><td><b>{p["plant_id"]}</b></td><td class="n">{pr["rank"]}</td>'
                    f'<td class="n">{pr["priority_score"]}</td><td class="n">{pr["stockout_days"]}</td>'
                    f'<td>{prev} <b>{ui.e(v or "none eligible")}</b></td><td class="n">{p.get("quantity_ton") or "-"}</td>'
                    f'<td class="n {"late" if late else ""}">{arr_txt}</td>'
                    f'<td class="n">{p.get("saw_score", "-")}</td><td>{ui.e(", ".join(p.get("alternatives", [])))}</td>'
                    f'<td class="subtle">{ui.e(warn)}</td></tr>')
    return ('<div style="overflow-x:auto"><table class="rt"><tr><th>Plant</th><th class="n">Rank</th><th class="n">Score</th><th class="n">Stock-out</th><th>Vessel</th>'
            '<th class="n">Qty t</th><th class="n">Arrives</th><th class="n">SAW</th><th>Alternatives</th><th>Notes</th></tr>'
            + "".join(rows) + "</table></div>")


def render(run, key="dk"):
    """Draw one run as a docket. Returns nothing; approval buttons act through the orchestrator."""
    seg = (ui.segments(run["steps"]) or [[]])[-1]
    by = {}
    for s in seg:
        by[s["agent"]] = s
    event = next((s for s in seg if s["agent"] == "Event Detected"), None)
    workers = [w for w in WORKERS if w in by or (not w.endswith("(extension)"))]
    running = run["status"] == "Running"
    started, dur = ui.hhmmss(run.get("started")), run.get("duration_s")
    replan = len(ui.segments(run["steps"])) > 1
    par = f"{run['parallel_wall_ms'] / 1000:.1f} s" if run.get("parallel_wall_ms") else "-"
    elapsed = f"{dur} s" if dur else "running"
    st.markdown(f'<div class="dk-head"><div class="no">{ui.e(run["id"])} &middot; {ui.e(run["title"])}</div>'
                f'<div class="meta"><div><span class="lbl">Status</span><b>{ui.badge(run["status"])}</b></div>'
                f'<div><span class="lbl">Opened</span><b>{started}</b></div><div><span class="lbl">Elapsed</span><b>{elapsed}</b></div>'
                f'<div><span class="lbl">Parallel agents</span><b>{par}</b></div>'
                f'<div><span class="lbl">Cycle</span><b>{"replanned" if replan else "single"}</b></div></div></div>', unsafe_allow_html=True)

    # Row 1: event and parallel agents as one ruled row with hairline seams and equal heights.
    live_any = running and any(by.get(w, {}).get("status") == "Running" for w in workers)
    ev_lines = [ui.e(event["outputs"].get("event"))] if event else []
    if replan:
        ev_lines.append("Replanning: the first plan was superseded after the disruption")
    cells = [_box(1, "Event", "global" if not event else event["enterprise"], "Completed" if event else "Idle", ev_lines,
                  f'<span>Received {ui.hhmmss(event["started"]) if event else "-"}</span><span>{len(workers)} agents tasked</span>', empty=not event)]
    for i, w in enumerate(workers):
        s = by.get(w)
        status = s["status"] if s else ("Waiting for response" if running else "Idle")
        cells.append(_box(i + 2, SHORT[w], HOST[w], status,
                          _summary(w, s) if s and s.get("outputs") else ([] if not s else [ui.e(x) for x in s.get("log", [])]),
                          _sig(s), live=bool(s and s["status"] == "Running"), empty=not s))
    st.markdown(f'<div class="dk-row{" dim" if live_any else ""}" style="grid-template-columns:1.05fr repeat({len(workers)}, 1fr)">'
                + "".join(cells) + "</div>"
                + f'<div class="dk-note">Boxes 2 to {len(workers) + 1} are filled at the same time, each by an agent inside its own enterprise API.</div>',
                unsafe_allow_html=True)

    # Row 2: plan on the left; remarks and the signature box on the right, inside the first viewport.
    c6, c7 = st.columns([2.05, 1], gap="small")
    planner, narr = by.get("Dispatch Planner Agent"), by.get("Narrator Agent")
    with c6:
        ack_key = f"ack-{run['id']}"
        body = plan_table(run["plan"], run.get("comparison"), st.session_state.get(ack_key)) if run.get("plan") else ""
        st.markdown(f'<div class="box{" live" if planner and planner["status"] == "Running" else ""}{" empty" if not run.get("plan") else ""}">'
                    f'<div class="bh"><div class="top"><span class="bt"><span class="bn">BOX {len(workers) + 2}</span> Dispatch plan</span>{ui.chip("global")}</div>'
                    f'<div>{ui.badge(planner["status"] if planner else "Idle")}</div></div>'
                    f'<div class="body">{body or "The Dispatch Planner writes here once all agents have signed."}</div>'
                    f'<div class="sig">{_sig(planner)}<span>SAW weights 0.35 / 0.20 / 0.20 / 0.15 / 0.10 &middot; greedy, one vessel per plant</span></div></div>',
                    unsafe_allow_html=True)
        if run.get("comparison") and any(c["changed"] for c in run["comparison"]) and not st.session_state.get(ack_key):
            if st.button("Acknowledge plan changes", key=f"{key}-ack-{run['id']}", help="Highlighted rows changed after the disruption"):
                st.session_state[ack_key] = True
                st.rerun()
    with c7:
        text = run.get("narrative") or ""
        # One short line per dispatch; the Narrator's full text stays in the message log and the hover title.
        parts = [f"{p['vessel']} to {p['plant_id']}: {p['quantity_ton']:,} t, arrives {p['arrival_hours'] / 24:.1f} d"
                 + (f" (±{p['arrival_range_hours']} h)" if p.get("arrival_range_hours") is not None else "")
                 + (", after stock-out" if p["arrival_hours"] / 24 > p["priority"]["stockout_days"] else "")
                 for p in run.get("plan", []) if p.get("vessel")] if narr and narr.get("status") == "Completed" else []
        src = (narr or {}).get("outputs", {}).get("source", "template")
        st.markdown(_box(len(workers) + 3, "Narrator remarks", "global", narr["status"] if narr else "Idle",
                         [ui.e(p) for p in parts[:4]], f'<span title="{ui.e(text)}">Full narration in the message log &middot; source: {ui.e(src)}</span>' + _sig(narr),
                         live=bool(narr and narr["status"] == "Running"), empty=not parts, cls_extra="short"), unsafe_allow_html=True)
        authorisation(run, len(workers) + 4, key)


def authorisation(run, box_no, key):
    decs = [d for d in (get("orchestrator", "/decisions") or []) if d["run_id"] == run["id"]]
    allowed = can(role(), "approve")
    with st.container(key=f"auth-{key}-{run['id']}"):
        st.markdown(f'<div class="auth-h"><span class="bt"><span class="bn">BOX {box_no}</span> Authorisation</span>'
                    f'<span class="subtle">{ui.e(role())}{"" if allowed else ", cannot sign"}</span></div>', unsafe_allow_html=True)
        if run["status"] == "Running":
            st.markdown('<div class="subtle">Waiting for the agents to finish.</div>', unsafe_allow_html=True)
            return
        if not decs:
            st.markdown('<div class="subtle">No dispatch needs a signature for this run.</div>', unsafe_allow_html=True)
            return
        for d in decs:
            arr = f"arrives {d['arrival_hours'] / 24:.1f} d, stock-out {d['stockout_days']} d" if d.get("arrival_hours") else ""
            st.markdown(f'<div class="auth-row"><b>{ui.e(d["action"])}</b><div class="subtle">{ui.e(d["priority"])} priority &middot; {ui.e(arr)}</div></div>',
                        unsafe_allow_html=True)
            b, gap, c = st.columns([1, 0.35, 1], vertical_alignment="center")
            if d["status"] == "Requires human approval":
                if b.button("Approve", key=f"{key}-a-{d['id']}", type="primary", disabled=not allowed, use_container_width=True):
                    post("orchestrator", f"/decisions/{d['id']}/approve", {"role": role()})
                    st.rerun()
                if c.button("Reject", key=f"{key}-r-{d['id']}", disabled=not allowed, use_container_width=True):
                    post("orchestrator", f"/decisions/{d['id']}/reject", {"role": role()})
                    st.rerun()
            else:
                b.markdown(ui.stamp(d["status"]), unsafe_allow_html=True)
                c.markdown(f'<div class="subtle">{ui.e(d.get("decided_by", ""))}, {ui.hhmmss(d.get("decided_at"))}</div>', unsafe_allow_html=True)
