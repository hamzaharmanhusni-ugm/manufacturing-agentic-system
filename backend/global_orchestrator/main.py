"""Global Agentic Control Center backend (port 8000).

Hosts the Orchestrator Agent, Dispatch Planner Agent (DSS engine) and Narrator Agent.
Worker agents live inside each enterprise API and are called over HTTP (A2A-style task calls):
  manufacturer: Stock Monitoring, ML Forecasting, Demand & Priority
  shipping:     Fleet Tracking
  distribution: Distribution Agent (extension), supplier: Procurement Agent (extension)
Principle: code decides (decision_engine), AI explains (Narrator), people act (approval)."""
import json
import os
import re
import sys
import threading
import time
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import httpx  # noqa: E402
from fastapi import FastAPI, Header, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from shared import decision_engine as de  # noqa: E402
from shared.config import ENTERPRISES, ORCH_KEY, SERVICES, STORES, url  # noqa: E402
from shared.rbac import ROLES, can  # noqa: E402

DEMO_DELAY = float(os.getenv("DEMO_DELAY", "0.6"))  # pacing so the UI can show progress
STATE_FILE = STORES / "orchestrator_state.json"

app = FastAPI(title="Global Orchestrator", version="1.0",
              description="Global Agentic Control Center: orchestration, dispatch planning, narration, approvals, KPIs.")
# The 3D Agent Office reads agent state from the browser; allow the local dashboard origin (read-only GETs).
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], allow_methods=["GET", "POST"], allow_headers=["*"])


def now():
    return datetime.now().isoformat(timespec="seconds")


# ------------------------------------------------------------------ state
AGENTS = {a["name"]: {**a, "status": "Idle", "last_run": None, "last_duration_ms": None, "runs": 0, "failures": 0} for a in [
    {"name": "Orchestrator Agent", "host": "orchestrator", "origin": "proposal", "role": "Receives events, plans tasks, dispatches in parallel, merges results"},
    {"name": "Stock Monitoring Agent", "host": "manufacturer", "origin": "proposal", "role": "Silo levels, usable stock, days of cover, ARIMA stock-out time", "path": "/agents/stock-monitoring/run"},
    {"name": "ML Forecasting Agent", "host": "manufacturer", "origin": "proposal", "role": "14-day P10/P50/P90 demand forecast (LightGBM champion, TFT challenger)", "path": "/agents/ml-forecasting/run"},
    {"name": "Demand & Priority Agent", "host": "manufacturer", "origin": "proposal", "role": "Plant priority score (Eq. 14) from sales, S&OP, forecast, price, margin", "path": "/agents/demand-priority/run"},
    {"name": "Fleet Tracking Agent", "host": "shipping", "origin": "proposal", "role": "GPS, vessel status, RF ETA, Weibull failure risk", "path": "/agents/fleet-tracking/run"},
    {"name": "Dispatch Planner Agent", "host": "orchestrator", "origin": "proposal", "role": "SAW ship ranking (Eq. 15-16) and greedy assignment (Eq. 17-18)"},
    {"name": "Narrator Agent", "host": "orchestrator", "origin": "proposal", "role": "Explains verified results (template, optional LLM); never creates numbers"},
    {"name": "Distribution Agent (extension)", "host": "distribution", "origin": "prototype extension", "role": "Regional stock, orders at risk", "path": "/agents/distribution/run"},
    {"name": "Procurement Agent (extension)", "host": "supplier", "origin": "prototype extension", "role": "Raw material supply risk, alternatives, production impact", "path": "/agents/procurement/run"},
]}
WORKERS = ["Stock Monitoring Agent", "ML Forecasting Agent", "Fleet Tracking Agent", "Demand & Priority Agent"]
EXT = {"distribution": "Distribution Agent (extension)", "supplier": "Procurement Agent (extension)"}

MESSAGES, OUTBOUND = deque(maxlen=400), deque(maxlen=500)
RUNS, DECISIONS = {}, {}
AUDIT, NOTIFICATIONS, KPI_HISTORY = [], deque(maxlen=200), []
SYNC = {e: {"last_ok": None, "last_error": None} for e in ENTERPRISES}
COUNTERS = {"replanning_events": 0, "agent_calls": 0, "agent_ok": 0}
LOCK = threading.Lock()


def save_state():
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"audit": AUDIT[-500:], "decisions": DECISIONS, "kpi_history": KPI_HISTORY[-100:],
                                          "counters": COUNTERS}, default=str), encoding="utf-8")
    except OSError:
        pass


if STATE_FILE.exists():
    try:
        _s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        AUDIT.extend(_s.get("audit", []))
        DECISIONS.update(_s.get("decisions", {}))
        KPI_HISTORY.extend(_s.get("kpi_history", []))
        COUNTERS.update(_s.get("counters", {}))
    except (OSError, ValueError):
        pass


def audit(actor, action, detail):
    AUDIT.append({"ts": now(), "actor": actor, "action": action, "detail": detail})
    save_state()


def message(frm, to, content, kind="request", frm_ent=None, to_ent=None, run_id=None):
    MESSAGES.append({"ts": now(), "from": frm, "from_enterprise": frm_ent or AGENTS.get(frm, {}).get("host", "global"),
                     "to": to, "to_enterprise": to_ent or AGENTS.get(to, {}).get("host", "global"),
                     "content": content, "type": kind, "run_id": run_id})


def notify(role, text, severity="info", channel="Telegram (simulated)"):
    NOTIFICATIONS.appendleft({"ts": now(), "role": role, "channel": channel, "severity": severity, "text": text})


# ------------------------------------------------------------------ cross-enterprise HTTP
def call(ent, method, path, body=None, timeout=60):
    """Every cross-enterprise request goes through here: auth header, retry once, logs, sync status."""
    last = None
    for attempt in range(2):
        t0 = time.perf_counter()
        try:
            r = httpx.request(method, url(ent) + path, json=body, timeout=timeout, headers={"X-API-Key": ORCH_KEY})
            ms = round((time.perf_counter() - t0) * 1000, 1)
            OUTBOUND.append({"ts": now(), "target": ent, "method": method, "path": path, "status": r.status_code, "ms": ms,
                             "ok": r.is_success, "attempt": attempt + 1})
            if r.is_success:
                SYNC[ent]["last_ok"] = now()
                return r.json()
            last = f"HTTP {r.status_code}: {r.text[:200]}"
            if r.status_code < 500:
                break
        except httpx.HTTPError as e:
            OUTBOUND.append({"ts": now(), "target": ent, "method": method, "path": path, "status": 0,
                             "ms": round((time.perf_counter() - t0) * 1000, 1), "ok": False, "attempt": attempt + 1})
            last = f"{type(e).__name__}: {e}"
    SYNC[ent]["last_error"] = {"ts": now(), "error": last}
    raise RuntimeError(f"{ent} {path} failed: {last}")


def run_agent(name, run):
    a = AGENTS[name]
    step = {"agent": name, "enterprise": a["host"], "status": "Running", "started": now(), "t0": time.perf_counter()}
    run["steps"].append(step)
    a["status"] = "Running"
    message("Orchestrator Agent", name, f"Task: {a['role']}", "request", run_id=run["id"])
    COUNTERS["agent_calls"] += 1
    try:
        time.sleep(DEMO_DELAY)
        res = call(a["host"], "POST", a["path"])
        step.update(status="Completed", inputs=res["inputs"], outputs=res["outputs"], log=res["log"])
        a["status"] = "Completed"
        COUNTERS["agent_ok"] += 1
        message(name, "Orchestrator Agent", res["log"][-1], "response", run_id=run["id"])
        return res["outputs"]
    except Exception as e:  # noqa: BLE001
        step.update(status="Failed", log=[str(e)])
        a["status"] = "Failed"
        a["failures"] += 1
        message(name, "Orchestrator Agent", f"FAILED: {e}", "error", run_id=run["id"])
        return None
    finally:
        step["duration_ms"] = round((time.perf_counter() - step.pop("t0")) * 1000, 1)
        step["ended"] = now()
        a.update(last_run=now(), last_duration_ms=step["duration_ms"], runs=a["runs"] + 1, last_log=(step.get("log") or [""])[-1])


def local_step(run, name, fn):
    a = AGENTS[name]
    step = {"agent": name, "enterprise": "global", "status": "Running", "started": now()}
    run["steps"].append(step)
    a["status"] = "Running"
    t0 = time.perf_counter()
    time.sleep(DEMO_DELAY)
    try:
        inputs, outputs, log = fn()
        step.update(status="Completed", inputs=inputs, outputs=outputs, log=log)
        a["status"] = "Completed"
        return outputs
    except Exception as e:  # noqa: BLE001
        step.update(status="Failed", log=[f"{type(e).__name__}: {e}"])
        a["status"] = "Failed"
        a["failures"] += 1
        raise
    finally:
        step["duration_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        step["ended"] = now()
        a.update(last_run=now(), last_duration_ms=step["duration_ms"], runs=a["runs"] + 1, last_log=(step.get("log") or [""])[-1])


# ------------------------------------------------------------------ dispatch planner + narrator
def plan_dispatch(results, load_port):
    pri = results["Demand & Priority Agent"]
    fleet = results["Fleet Tracking Agent"]
    plan, excluded = de.assign(pri["ranking"], fleet["options"], pri["needs"])
    avail = {s["cement_type"]: s["available_ton"] for s in load_port["stock"]}
    for p in plan:  # load port stock caps the quantity (supplier disruption reduces it)
        if p.get("vessel"):
            q = min(p["quantity_ton"], max(0, avail.get(p["cement_type"], 0)))
            if q < p["quantity_ton"]:
                p["warnings"].append(f"quantity limited by load port stock ({int(q)} t available)")
            p["quantity_ton"] = int(q)
            avail[p["cement_type"]] = avail.get(p["cement_type"], 0) - q
    return plan, excluded


def fmt_h(h):
    return f"{h / 24:.1f} days" if h is not None else "n/a"


def narrate(plan, context):
    """Template narration from verified numbers. Optional LLM rewrite, rejected if it adds any number."""
    lines = []
    for p in plan:
        pr = p["priority"]
        if not p.get("vessel"):
            lines.append(f"{p['plant_id']} needs cement (stock-out in {pr['stockout_days']} days) but no eligible vessel is available; "
                         f"escalate to Shipment.")
            continue
        alt = ", ".join(p["alternatives"]) or "none"
        rng = f" (+/- {p['arrival_range_hours']} h)" if p.get("arrival_range_hours") is not None else ""
        late = p["arrival_hours"] / 24 > pr["stockout_days"]
        timing = (f"after the projected stock-out in {pr['stockout_days']} days, so a short supply gap remains; "
                  f"this is the fastest eligible vessel" if late else f"before the projected stock-out in {pr['stockout_days']} days")
        lines.append(f"Send {p['vessel']} to {p['plant_id']} with {p['quantity_ton']} t {p['cement_type']}: arrival in "
                     f"{fmt_h(p['arrival_hours'])}{rng}, {timing}. "
                     f"Priority score {pr['priority_score']} (rank {pr['rank']}), ship SAW score {p['saw_score']}. Alternatives: {alt}."
                     + (f" Warning: {'; '.join(p['warnings'])}." if p["warnings"] else ""))
    text = " ".join(lines) or "No plant needs a new dispatch within the planning window."
    if context:
        text = context + " " + text
    source = "template"
    key = os.getenv("ANTHROPIC_API_KEY")
    if key and plan:
        try:
            r = httpx.post("https://api.anthropic.com/v1/messages", timeout=20, headers={
                "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": os.getenv("NARRATOR_MODEL", "claude-haiku-5-5"), "max_tokens": 400,
                      "system": "You explain a cement dispatch plan to managers. Use ONLY the facts given. "
                                "Do not compute, round or invent any number. Max 120 words.",
                      "messages": [{"role": "user", "content": text}]})
            llm = r.json()["content"][0]["text"]
            facts = set(re.findall(r"\d+(?:\.\d+)?", text))
            if set(re.findall(r"\d+(?:\.\d+)?", llm)) <= facts:  # number guard
                text, source = llm, "LLM (number-guarded)"
            else:
                source = "template (LLM output rejected: introduced numbers)"
        except Exception:  # noqa: BLE001  fail-safe delivery: plan goes out without LLM
            source = "template (LLM unavailable)"
    return text, source


# ------------------------------------------------------------------ scenarios
SCENARIOS = {
    "normal": {"title": "1. Normal operation", "description": "Stable demand, sufficient silo stock, vessels operating normally.",
               "event": "Scheduled daily planning cycle", "inject": [], "ext": []},
    "low_stock": {"title": "2. Low stock at PP C", "description": "PP C PCC silo level drops below 25 %.",
                  "event": "IIoT silo sensor: PP C PCC level 20 % (rule: < 25 %)",
                  "inject": [("manufacturer", "/events/silo-drop", {"plant_id": "PP C", "cement_type": "PCC", "level_pct": 0.20})], "ext": []},
    "demand_surge": {"title": "3. Demand surge at PP F", "description": "Demand at PP F rises 80 %; forecast and ranking are recomputed.",
                     "event": "ERP sales + distributor orders: PP F demand +80 %",
                     "inject": [("manufacturer", "/events/demand-surge", {"plant_id": "PP F", "factor": 1.8}),
                                ("distribution", "/events/order-surge", {"plant_id": "PP F", "factor": 1.8})], "ext": ["distribution"]},
    "shipping_disruption": {"title": "4. Shipping disruption (adaptive replanning)", "description": "The recommended vessel is delayed 60 h; alternatives are evaluated.",
                            "event": "Shipment voyage log: recommended vessel delayed 60 h", "inject": [], "ext": [], "replan": True},
    "weather": {"title": "5. Weather disruption", "description": "Severe waves on the PP F route and rough sea toward PP C.",
                "event": "Marine weather API: wave 3.4 m on PP F route, 2.3 m on PP C route",
                "inject": [("shipping", "/events/weather", {"plants": ["PP F"], "wave_m": 3.4}),
                           ("shipping", "/events/weather", {"plants": ["PP C"], "wave_m": 2.3})], "ext": []},
    "supplier": {"title": "6. Supplier disruption", "description": "Main clinker supplier availability drops to 30 %.",
                 "event": "Supplier portal: Supplier Alpha (clinker) availability 30 %",
                 "inject": [("supplier", "/events/disruption", {"supplier_id": "SUP-01", "availability_pct": 30})], "ext": ["supplier"]},
}


def pipeline(run, event_text, context=""):
    """Event -> Orchestrator -> parallel workers -> Dispatch Planner -> Narrator -> Human approval."""
    rid = run["id"]
    run["steps"].append({"agent": "Event Detected", "enterprise": "global", "status": "Completed", "started": now(),
                         "ended": now(), "duration_ms": 0, "inputs": {}, "outputs": {"event": event_text}, "log": [event_text]})
    message("Event Bus", "Orchestrator Agent", event_text, "event", frm_ent="event-bus", run_id=rid)
    agents = WORKERS + [EXT[e] for e in run["ext"]]
    local_step(run, "Orchestrator Agent", lambda: (
        {"event": event_text}, {"task_plan": agents, "mode": "parallel fan-out / fan-in"},
        [f"Task plan: {len(agents)} agents in parallel", "Agents do not call each other; only the orchestrator sequences work"]))
    AGENTS["Orchestrator Agent"]["status"] = "Waiting for response"
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(agents)) as pool:
        results = dict(zip(agents, pool.map(lambda n: run_agent(n, run), agents)))
    run["parallel_wall_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    AGENTS["Orchestrator Agent"]["status"] = "Completed"
    if any(results[a] is None for a in WORKERS):
        raise RuntimeError("a required worker agent failed; plan not produced (fail-safe)")

    proc = results.get(EXT["supplier"])
    if proc and proc.get("production_impact"):
        imp = proc["production_impact"]
        call("manufacturer", "POST", "/events/production-cap", {"factor": imp["production_capacity_factor"]})
        message("Orchestrator Agent", "Manufacturer API", f"Ecosystem impact: {imp['material']} shortage limits production to "
                f"{int(imp['production_capacity_factor'] * 100)} % capacity; load port stock adjusted", "notification",
                to_ent="manufacturer", run_id=rid)
        notify("Manufacturer Manager", f"Supplier disruption: {imp['material']} coverage low, production capped at "
               f"{int(imp['production_capacity_factor'] * 100)} %", "warning")
    for e in results[WORKERS[0]]["low_stock_events"]:
        notify("Operations Planner", f"LOW STOCK {e['plant_id']} {e['cement_type']}: level {e['level_pct']:.0%}, "
               f"stock-out in {e['stockout_days']} days", "critical")
    for p in results["Fleet Tracking Agent"]["sailing_not_advised"]:
        notify("Shipping Manager", f"Sailing not advised on route to {p} (wave above {2.5} m)", "warning")
    dist = results.get(EXT["distribution"])
    if dist:
        for s in dist["regions_at_risk"]:
            if s["plant_id"] in ("PP F",):
                message("Distribution Agent (extension)", "Orchestrator Agent",
                        f"{s['region']} distributors: {s['open_order_ton']} t open orders, {s['days_of_stock']} days of stock", "response", run_id=rid)

    load_port = call("manufacturer", "GET", "/load-port")

    def planner():
        plan, excluded = plan_dispatch(results, load_port)
        return ({"plant_priority": "from Demand & Priority Agent", "ship_options": "from Fleet Tracking Agent", "load_port": load_port},
                {"plan": plan, "excluded": excluded[:40]},
                [f"Ranked candidates with SAW weights {list(de.SHIP_WEIGHTS.values())}",
                 f"Greedy assignment: {sum(1 for p in plan if p.get('vessel'))} dispatches, {len(excluded)} exclusions recorded"])
    out = local_step(run, "Dispatch Planner Agent", planner)
    run["plan"] = out["plan"]
    run["excluded"] = out["excluded"]
    for p in run["plan"][:3]:
        if p.get("vessel"):
            message("Dispatch Planner Agent", "Global Control Center",
                    f"Recommends {p['vessel']} for {p['plant_id']} ({p['quantity_ton']} t, arrival {fmt_h(p['arrival_hours'])})", "recommendation",
                    to_ent="global", run_id=rid)

    def narrator():
        text, source = narrate(run["plan"], context)
        return {"facts": "verified plan only"}, {"narrative": text, "source": source}, [f"Narration source: {source}"]
    nout = local_step(run, "Narrator Agent", narrator)
    run["narrative"] = nout["narrative"]
    message("Narrator Agent", "Management", nout["narrative"][:300], "notification", to_ent="management", run_id=rid)
    return results


def create_decisions(run):
    for old in DECISIONS.values():  # a newer plan replaces every pending recommendation
        if old["status"] == "Requires human approval":
            old.update(status="Superseded", decided_at=now(), note=f"replaced by newer plan {run['id']}")
    ids = []
    for p in run["plan"]:
        if not p.get("vessel"):
            continue
        pr = p["priority"]
        did = "D-" + uuid.uuid4().hex[:6].upper()
        DECISIONS[did] = {
            "id": did, "run_id": run["id"], "scenario": run["scenario"], "created": now(), "status": "Requires human approval",
            "action": f"Dispatch {p['vessel']} to {p['plant_id']} with {p['quantity_ton']} t {p['cement_type']}",
            "vessel": p["vessel"], "plant_id": p["plant_id"], "cement_type": p["cement_type"], "quantity_ton": p["quantity_ton"],
            "arrival_hours": p["arrival_hours"], "arrival_range_hours": p.get("arrival_range_hours"),
            "enterprises": ["manufacturer", "shipping"] + (["distribution"] if p["plant_id"] == "PP F" else []),
            "priority": "High" if pr["priority_score"] >= 3.5 else ("Medium" if pr["priority_score"] >= 2.5 else "Low"),
            "priority_score": pr["priority_score"], "stockout_days": pr["stockout_days"], "saw_score": p["saw_score"],
            "confidence": f"ETA +/- {p.get('arrival_range_hours')} h (RF tree spread); demand P10-P90 band from LightGBM",
            "reasoning": f"{p['plant_id']} rank {pr['rank']} (score {pr['priority_score']}), stock-out in {pr['stockout_days']} days; "
                         f"{p['vessel']} best SAW {p['saw_score']} among {len(p['ranking'])} eligible. Alternatives: {', '.join(p['alternatives']) or 'none'}.",
            "expected_impact": f"Arrives in {fmt_h(p['arrival_hours'])} vs stock-out in {pr['stockout_days']} days; adds {p['quantity_ton']} t "
                               f"(~{p['quantity_ton'] / max(pr['forecast_demand'], 1):.1f} days of demand)",
            "warnings": p["warnings"], "alternatives": p["alternatives"], "ranking": p["ranking"]}
        ids.append(did)
        if len(ids) == 3:
            break
    if ids:
        AGENTS["Dispatch Planner Agent"]["status"] = "Requires human approval"
        notify("Manufacturer Manager", f"{len(ids)} dispatch recommendation(s) await approval", "info")
    run["decisions"] = ids
    run["steps"].append({"agent": "Human Approval", "enterprise": "management", "status": "Requires human approval" if ids else "Completed",
                         "started": now(), "ended": now(), "duration_ms": 0, "inputs": {}, "outputs": {"decisions": ids},
                         "log": [f"{len(ids)} decision(s) waiting for an authorised role"]})
    save_state()
    return ids


def execute_scenario(run):
    sc = SCENARIOS.get(run["scenario"]) or run["live"]
    t0 = time.perf_counter()
    try:
        run["kpi_before"] = compute_kpis()
        run["dashboards_before"] = dashboards_probe()
        for ent, path, body in sc["inject"]:
            call(ent, "POST", path, body)
        if sc.get("replan"):
            pipeline(run, "Planning cycle before disruption")
            first = next((p for p in run["plan"] if p.get("vessel")), None)
            run["previous_plan"] = run["plan"]
            if first:
                delay = 60
                call("shipping", "POST", "/events/vessel-delay", {"vessel": first["vessel"], "hours": delay})
                COUNTERS["replanning_events"] += 1
                pr = first["priority"]
                negotiation = [
                    ("Stock Monitoring Agent", "manufacturer", f"{first['plant_id']} requires urgent replenishment within {pr['stockout_days']} days."),
                    ("Fleet Tracking Agent", "shipping", f"{first['vessel']} is delayed {delay} h (Shipment voyage log)."),
                ]
                for frm, ent, txt in negotiation:
                    message(frm, "Orchestrator Agent", txt, "negotiation", frm_ent=ent, run_id=run["id"])
                run["steps"].append({"agent": "Event Detected", "enterprise": "shipping", "status": "Completed", "started": now(), "ended": now(),
                                     "duration_ms": 0, "inputs": {}, "outputs": {"event": f"{first['vessel']} delayed {delay} h"},
                                     "log": ["Adaptive replanning triggered"]})
                pipeline(run, f"{first['vessel']} delayed {delay} h: replan", context=f"Replan after {first['vessel']} delay of {delay} h.")
                new = next((p for p in run["plan"] if p["plant_id"] == first["plant_id"]), None)
                run["negotiation"] = [{"ts": now(), "who": f"Manufacturer ({w})" if e == "manufacturer" else f"Shipping ({w})", "text": t}
                                      for w, e, t in negotiation]
                if new and new.get("vessel"):
                    alt = next((r for r in new["ranking"] if r["vessel"] == new["vessel"]), {})
                    run["negotiation"].append({"ts": now(), "who": "Shipping (Fleet Tracking Agent)",
                                               "text": f"{new['vessel']} is available: capacity {alt.get('capacity_ton')} t, arrival {fmt_h(new['arrival_hours'])}."})
                    run["negotiation"].append({"ts": now(), "who": "Dispatch Planner Agent",
                                               "text": f"{new['vessel']} is recommended as the alternative for {first['plant_id']} "
                                                       f"(was {first['vessel']}, now delayed)."})
                    message("Dispatch Planner Agent", "Global Control Center", f"Alternative: {new['vessel']} replaces {first['vessel']} for {first['plant_id']}",
                            "negotiation", to_ent="global", run_id=run["id"])
                run["negotiation"].append({"ts": now(), "who": "Management", "text": "Approve alternative dispatch? (Decision Center)"})
                run["comparison"] = compare(run["previous_plan"], run["plan"])
        else:
            pipeline(run, sc["event"])
        create_decisions(run)
        run["status"] = "Completed"
    except Exception as e:  # noqa: BLE001
        run["status"] = "Failed"
        run["error"] = str(e)
        AGENTS["Orchestrator Agent"]["status"] = "Failed"
    run["duration_s"] = round(time.perf_counter() - t0, 2)
    run["finished"] = now()
    run["kpi_after"] = compute_kpis(force=True)
    run["dashboards_after"] = dashboards_probe()
    KPI_HISTORY.append({"ts": now(), "scenario": run["scenario"], "title": run["title"],
                        "before": run["kpi_before"], "after": run["kpi_after"]})
    audit("system", "scenario run", f"{run['scenario']} -> {run['status']} in {run['duration_s']} s")


def compare(old, new):
    o = {p["plant_id"]: p for p in old if p.get("vessel")}
    n = {p["plant_id"]: p for p in new if p.get("vessel")}
    rows = []
    for pid in sorted(set(o) | set(n)):
        a, b = o.get(pid, {}), n.get(pid, {})
        rows.append({"plant_id": pid, "original_vessel": a.get("vessel"), "adaptive_vessel": b.get("vessel"),
                     "original_arrival_h": a.get("arrival_hours"), "adaptive_arrival_h": b.get("arrival_hours"),
                     "stockout_days": (b or a).get("priority", {}).get("stockout_days"), "changed": a.get("vessel") != b.get("vessel")})
    return rows


def dashboards_probe():
    """Small cross-enterprise snapshot used to show 'what changed in each dashboard'."""
    out = {}
    try:
        plants = call("manufacturer", "GET", "/plants")
        out["manufacturer"] = {p["plant_id"]: {"stockout_days": p["priority"]["stockout_days"], "score": p["priority"]["priority_score"],
                                               "rank": p["priority"]["rank"]} for p in plants}
        out["shipping"] = {v["vessel"]: {"delay_h": v["delay_hours"], "assigned": v["assigned_plant"]} for v in call("shipping", "GET", "/vessels")}
        out["load_port"] = call("manufacturer", "GET", "/load-port")
        out["supplier"] = {m["material"]: m["supply_coverage"] for m in call("supplier", "GET", "/materials")}
        out["distribution"] = {r["served_by_plant"]: r["days_of_stock"] for r in call("distribution", "GET", "/regions")}
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
    return out


# ------------------------------------------------------------------ KPIs
_kpi_cache = {"t": 0, "v": None}


def compute_kpis(force=False):
    if not force and _kpi_cache["v"] and time.time() - _kpi_cache["t"] < 3:
        return _kpi_cache["v"]
    k = {"data": "synthetic, computed live from enterprise APIs"}
    try:
        plants = call("manufacturer", "GET", "/plants")
        series = [s for p in plants for s in p["series"]]
        fm = call("manufacturer", "GET", "/forecast/metrics")
        vessels = call("shipping", "GET", "/vessels")
        models = call("shipping", "GET", "/models")
        voyages = call("shipping", "GET", "/voyages")
        regions = call("distribution", "GET", "/regions")
        mats = call("supplier", "GET", "/materials")
        active = [v for v in vessels if v["mode"] in ("laden",) or v["assigned_plant"]]
        hist = sum(v["onTime"] for v in voyages) / len(voyages)
        delayed = sum(1 for v in vessels if v["delay_hours"] > 0)
        k.update({
            "wape": fm["wape_champion"], "wape_naive_baseline": fm["wape_challenger"], "forecast_coverage": fm["coverage_p10_p90"],
            "eta_mae_hours": models["eta"]["mae_hours"],
            "stockout_events": sum(1 for s in series if s["stockout_days"] < 3),
            "avg_days_of_cover": round(sum(min(s["days_of_cover"], 30) for s in series) / len(series), 2),
            "on_time_delivery": round(hist * (1 - delayed / max(len(active), 1) * 0.5), 3),
            "vessels_operating": sum(1 for v in vessels if v["mode"] != "maintenance"),
            "vessels_delayed": delayed, "low_stock_series": sum(1 for s in series if s["low_stock"]),
            "distribution_fill_rate": round(sum(r["fill_rate"] or 0 for r in regions) / len(regions), 3),
            "regions_below_safety": sum(1 for r in regions if r["below_safety"]),
            "min_material_coverage": min(m["supply_coverage"] for m in mats),
            "sailing_not_advised": 0,
        })
    except Exception as e:  # noqa: BLE001
        k["error"] = str(e)
    done = [r for r in RUNS.values() if r.get("status") == "Completed"]
    decided = [d for d in DECISIONS.values() if d["status"] in ("Approved", "Rejected")]
    k.update({
        "dispatch_response_s": done[-1]["duration_s"] if done else None,
        "agent_success_rate": round(COUNTERS["agent_ok"] / COUNTERS["agent_calls"], 3) if COUNTERS["agent_calls"] else None,
        "api_success_rate": round(sum(o["ok"] for o in OUTBOUND) / len(OUTBOUND), 3) if OUTBOUND else None,
        "sync_rate": round(sum(1 for e in ENTERPRISES if SYNC[e]["last_ok"]) / 4, 2),
        "replanning_events": COUNTERS["replanning_events"],
        "human_approval_rate": round(sum(d["status"] == "Approved" for d in decided) / len(decided), 3) if decided else None,
        "pending_decisions": sum(1 for d in DECISIONS.values() if d["status"] == "Requires human approval"),
    })
    _kpi_cache.update(t=time.time(), v=k)
    return k


# Manual-process baseline for "Before AI vs After AI". ILLUSTRATIVE ASSUMPTIONS, not measured values.
BASELINE = {"dispatch_response_s": 4 * 3600, "on_time_delivery": 0.78, "stockout_events": 3, "avg_days_of_cover": 4.5,
            "note": "Before-AI values are illustrative assumptions of a manual spreadsheet process (synthetic)."}


# ------------------------------------------------------------------ API
@app.get("/health")
def health():
    return {"service": "global-orchestrator", "status": "ok", "ts": now()}


@app.get("/ecosystem")
def ecosystem():
    out = []
    for e in ENTERPRISES:
        t0 = time.perf_counter()
        try:
            r = httpx.get(url(e) + "/health", timeout=3)
            st, code = ("online" if r.is_success else "degraded"), r.status_code
        except httpx.HTTPError:
            st, code = "offline", 0
        last = SYNC[e]["last_ok"]
        age = (datetime.now() - datetime.fromisoformat(last)).total_seconds() if last else None
        out.append({"enterprise": e, "name": SERVICES[e]["name"], "port": SERVICES[e]["port"], "status": st, "api_status": code,
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                    "sync": "synced" if age is not None and age < 300 else ("stale" if last else "not synced"),
                    "last_communication": last, "last_error": SYNC[e]["last_error"],
                    "agents": [a["name"] for a in AGENTS.values() if a["host"] == e],
                    "active_agents": sum(1 for a in AGENTS.values() if a["host"] == e and a["status"] != "Idle")})
    return out


@app.get("/overview")
def overview():
    eco = ecosystem()
    k = compute_kpis()
    alerts = list(NOTIFICATIONS)[:50]
    try:
        orders = sum(1 for o in call("distribution", "GET", "/orders") if o["status"] != "fulfilled") + len(call("manufacturer", "GET", "/incoming"))
    except Exception:  # noqa: BLE001
        orders = None
    online = sum(e["status"] == "online" for e in eco)
    health = None
    if "avg_days_of_cover" in k:
        health = round(100 * (0.3 * online / 4 + 0.3 * min(k["avg_days_of_cover"] / 10, 1) + 0.2 * k["on_time_delivery"]
                              + 0.2 * (1 - min(k["stockout_events"] / 5, 1))), 1)
    return {"enterprises_connected": online, "enterprises_total": 4, "agents_total": len(AGENTS),
            "agents_active": sum(a["status"] not in ("Idle",) for a in AGENTS.values()),
            "pending_decisions": k["pending_decisions"], "supply_chain_orders": orders,
            "vessels_operating": k.get("vessels_operating"), "packing_plants": 9, "supply_chain_health": health,
            "active_alerts": sum(1 for a in alerts if a["severity"] in ("critical", "warning")),
            "system_status": "operational" if online == 4 else ("degraded" if online else "down"), "kpis": k}


@app.get("/agents")
def agents():
    return list(AGENTS.values())


@app.get("/messages")
def messages(limit: int = 100, run_id: str | None = None):
    rows = [m for m in MESSAGES if not run_id or m["run_id"] == run_id]
    return rows[-limit:][::-1]


@app.get("/scenarios")
def scenarios():
    return [{"key": k, **{x: v[x] for x in ("title", "description", "event")}, "extensions": v["ext"], "replan": v.get("replan", False)}
            for k, v in SCENARIOS.items()]


class Actor(BaseModel):
    role: str = "Global Administrator"
    user: str = "demo-user"
    note: str = ""


@app.post("/scenarios/{key}/run")
def run_scenario(key: str, actor: Actor = Actor()):
    if key not in SCENARIOS:
        raise HTTPException(404, "unknown scenario")
    if not can(actor.role, "simulate"):
        raise HTTPException(403, f"role '{actor.role}' cannot trigger simulations")
    if any(r["status"] == "Running" for r in RUNS.values()):
        raise HTTPException(409, "another run is in progress")
    for a in AGENTS.values():
        a["status"] = "Idle"
    rid = "R-" + uuid.uuid4().hex[:6].upper()
    RUNS[rid] = {"id": rid, "scenario": key, "title": SCENARIOS[key]["title"], "status": "Running", "started": now(),
                 "steps": [], "ext": SCENARIOS[key]["ext"], "plan": [], "by": actor.role}
    audit(actor.role, "trigger scenario", key)
    threading.Thread(target=execute_scenario, args=(RUNS[rid],), daemon=True).start()
    return {"run_id": rid}


@app.get("/runs")
def runs():
    return [{k: r.get(k) for k in ("id", "scenario", "title", "status", "started", "finished", "duration_s")} for r in RUNS.values()][::-1]


@app.get("/runs/{rid}")
def get_run(rid: str):
    if rid not in RUNS:
        raise HTTPException(404, "run not found")
    return RUNS[rid]


@app.get("/runs/latest/plan")
def latest_plan():
    done = [r for r in RUNS.values() if r.get("plan")]
    return done[-1] if done else {}


@app.get("/decisions")
def decisions():
    return sorted(DECISIONS.values(), key=lambda d: d["created"], reverse=True)


@app.post("/decisions/{did}/{verdict}")
def decide(did: str, verdict: str, actor: Actor, x_user_role: str = Header(default="")):
    d = DECISIONS.get(did)
    if not d:
        raise HTTPException(404, "decision not found")
    if verdict not in ("approve", "reject"):
        raise HTTPException(400, "verdict must be approve or reject")
    if not can(actor.role, "approve"):
        audit(actor.role, "approval denied", did)
        raise HTTPException(403, f"role '{actor.role}' is not authorised to approve dispatch decisions")
    if d["status"] != "Requires human approval":
        raise HTTPException(409, f"decision already {d['status']}")
    if verdict == "approve":
        call("shipping", "POST", "/assignments", {"vessel": d["vessel"], "plant_id": d["plant_id"], "cement_type": d["cement_type"],
                                                   "quantity_ton": d["quantity_ton"], "decision_id": did})
        call("manufacturer", "POST", "/incoming", {"plant_id": d["plant_id"], "cement_type": d["cement_type"], "vessel": d["vessel"],
                                                    "quantity_ton": d["quantity_ton"], "eta_hours": d["arrival_hours"]})
        message("Management", "Dispatch Planner Agent", f"Approved: {d['action']}", "decision", frm_ent="management")
        message("Orchestrator Agent", "Shipping API", f"Assignment {d['vessel']} -> {d['plant_id']} confirmed", "execution", to_ent="shipping")
        notify("Shipping Manager", f"Approved dispatch: {d['action']}", "info", "WhatsApp (simulated)")
    else:
        message("Management", "Dispatch Planner Agent", f"Rejected: {d['action']} {actor.note}", "decision", frm_ent="management")
    d.update(status="Approved" if verdict == "approve" else "Rejected", decided_by=actor.role, decided_at=now(), note=actor.note)
    for other in DECISIONS.values():  # same vessel cannot serve two plants
        if verdict == "approve" and other is not d and other["status"] == "Requires human approval" and other["vessel"] == d["vessel"]:
            other.update(status="Superseded", decided_at=now(), note=f"{d['vessel']} assigned by {did}")
    if not any(x["status"] == "Requires human approval" for x in DECISIONS.values()):
        AGENTS["Dispatch Planner Agent"]["status"] = "Completed"
    audit(actor.role, verdict, f"{did}: {d['action']}")
    _kpi_cache["v"] = None
    return d


@app.get("/kpis")
def kpis():
    return {"current": compute_kpis(), "baseline_manual": BASELINE, "history": KPI_HISTORY[-30:]}


@app.get("/audit")
def get_audit(limit: int = 200):
    return AUDIT[-limit:][::-1]


@app.get("/notifications")
def notifications():
    return list(NOTIFICATIONS)


@app.get("/api-logs")
def api_logs():
    inbound = []
    for e in ENTERPRISES:
        try:
            inbound += call(e, "GET", "/logs?limit=60")
        except Exception:  # noqa: BLE001
            pass
    return {"outbound": list(OUTBOUND)[-200:][::-1], "inbound": sorted(inbound, key=lambda r: r["ts"], reverse=True)[:200]}


@app.get("/governance")
def governance():
    out = {}
    for e in ENTERPRISES:
        try:
            out[e] = call(e, "GET", "/governance")["policy"]
        except Exception as ex:  # noqa: BLE001
            out[e] = {"error": str(ex)}
    return {"enterprise_policies": out, "roles": {k: {**v, "views": sorted(v["views"]), "tabs": v["tabs"] if v["tabs"] == "all" else sorted(v["tabs"])}
                                                  for k, v in ROLES.items()},
            "principle": "Code decides, AI explains, people act"}


@app.post("/reset")
def reset(actor: Actor = Actor()):
    if any(r["status"] == "Running" for r in RUNS.values()):
        raise HTTPException(409, "a run is in progress")
    for e in ENTERPRISES:
        call(e, "POST", "/reset", timeout=120)
    RUNS.clear()
    DECISIONS.clear()
    MESSAGES.clear()
    NOTIFICATIONS.clear()
    COUNTERS.update(replanning_events=0)
    for a in AGENTS.values():
        a["status"] = "Idle"
    _kpi_cache["v"] = None
    world_reset()
    audit(actor.role, "reset ecosystem", "all enterprise stores regenerated from seed")
    return {"ok": True}


class Question(BaseModel):
    question: str
    role: str = "Global Administrator"


@app.post("/ask")
def ask(q: Question):
    """Pull channel (proposal 7.3): answers only from the latest verified plan."""
    last = latest_plan()
    if not last:
        return {"answer": "No plan has been computed yet. Run a scenario in the Simulation Center first.", "source": "template"}
    plan = last["plan"]
    pid = re.search(r"pp\s*([a-i])\b", q.question.lower())
    if pid:
        target = f"PP {pid.group(1).upper()}"
        sel = [p for p in plan if p["plant_id"] == target]
        if not sel:
            rank = next((r for r in call("manufacturer", "GET", "/plants") if r["plant_id"] == target), None)
            pr = rank["priority"] if rank else {}
            return {"answer": f"{target} has no dispatch in the latest plan. Priority score {pr.get('priority_score')} (rank {pr.get('rank')}), "
                              f"stock-out in {pr.get('stockout_days')} days.", "source": "template", "run_id": last["id"]}
        text, src = narrate(sel, "")
        return {"answer": text, "source": src, "run_id": last["id"]}
    text, src = narrate(plan[:3], f"Latest plan from run {last['id']} ({last['title']}).")
    return {"answer": text, "source": src, "run_id": last["id"]}


ARCH = {
    "manufacturer": {"U": ["Manufacturer Manager", "Marketing Planner", "Operations Planner"],
                     "M": ["Marketing", "Operations", "Demand Forecasting", "Silo Monitoring", "Packing Plant Management"],
                     "D": ["PostgreSQL 'manufacturer': sales_history (400 d x 14 series), sop_plan, packing_plants (9), silos (22), silo_level_history, incoming_deliveries, load_port_stock"],
                     "A": ["Stock Monitoring Agent", "ML Forecasting Agent", "Demand & Priority Agent"],
                     "P": ["REST/JSON :8001", "A2A task endpoints /agents/*/run", "X-API-Key auth"], "origin": "proposal"},
    "shipping": {"U": ["Shipping Manager"], "M": ["Fleet Overview", "Live Tracking", "Voyage History", "ETA Prediction", "Ship Ranking", "Maintenance"],
                 "D": ["MongoDB 'shipping': vessels (19, nested GPS track/engine), voyages (282, 2,202 events), weather (91 route points), assignments"],
                 "A": ["Fleet Tracking Agent"], "P": ["REST/JSON :8002 (camelCase)", "A2A /agents/fleet-tracking/run", "X-API-Key auth"], "origin": "proposal (subsidiary)"},
    "distribution": {"U": ["Distributor Manager"], "M": ["Regional Inventory", "Distributor Orders", "Regional Demand", "Order Fulfillment"],
                     "D": ["SQLite: region (9), distributor (18), sales_order (72), regional_demand; unit = 50 kg bags"],
                     "A": ["Distribution Agent (extension)"], "P": ["REST/JSON :8003", "A2A /agents/distribution/run"], "origin": "prototype extension"},
    "supplier": {"U": ["Supplier Manager"], "M": ["Supplier Overview", "Raw Material Inventory", "Procurement Orders", "Procurement Risk"],
                 "D": ["PostgreSQL 'supplier' loaded from ERP CSV export: materials (6), suppliers (8), purchase_orders (40)"],
                 "A": ["Procurement Agent (extension)"], "P": ["REST/JSON :8004 (UPPER_SNAKE)", "A2A /agents/procurement/run"], "origin": "prototype extension"},
}


@app.get("/architecture")
def architecture():
    gov = governance()["enterprise_policies"]
    return {e: {**v, "G": gov.get(e)} for e, v in ARCH.items()}


# ------------------------------------------------------------------ live world: a simulated clock that drives the real case
# Each tick moves the physical world (silos drain, vessels sail, cargo is unloaded). When a sensor crosses a rule the
# orchestrator starts a pipeline by itself (event-driven). The clock stops while agents work and while a decision waits
# for a person, so the audience always sees that agents propose and people act. Storyline disruptions fire at fixed
# simulated hours. All values are synthetic.
STORY = [
    (30, "storm", "Marine weather service: storm on the PP F route, waves 3.4 m",
     [("shipping", "/events/weather", {"plants": ["PP F"], "wave_m": 3.4})], [], True),
    (54, "calm", "Marine weather service: the storm on the PP F route has passed",
     [("shipping", "/events/weather", {"plants": ["PP F"], "wave_m": 1.2})], [], False),
    (66, "supplier", "Supplier portal: main clinker supplier drops to 30 % availability",
     [("supplier", "/events/disruption", {"supplier_id": "SUP-01", "availability_pct": 30})], ["supplier"], True),
]
WORLD = {}


def world_reset():
    WORLD.update(running=False, speed=1.0, t=0.0, start=datetime.now().replace(minute=0, second=0, microsecond=0),
                 pause_reason="Press play to start the clock", log=deque(maxlen=80), last_trigger={}, story_done=set(),
                 plants=[], vessels=[], stockouts=set())
    try:
        WORLD["plants"] = call("manufacturer", "GET", "/world/state")
        WORLD["vessels"] = call("shipping", "GET", "/world/state")["vessels"]
    except Exception:  # noqa: BLE001  enterprise APIs may still be starting
        pass


def clock_label(t=None):
    t = WORLD.get("t", 0) if t is None else t
    ts = WORLD["start"] + timedelta(hours=t)
    return f"Day {(ts.date() - WORLD['start'].date()).days + 1} · {ts:%H:%M}"


def wlog(kind, text):
    WORLD["log"].appendleft({"clock": clock_label(), "t": round(WORLD["t"], 1), "kind": kind, "text": text})


def start_live_run(event, ext=(), title=None):
    for a in AGENTS.values():
        a["status"] = "Idle"
    rid = "R-" + uuid.uuid4().hex[:6].upper()
    RUNS[rid] = {"id": rid, "scenario": "live", "title": title or f"Live {clock_label()}: {event}", "status": "Running", "started": now(),
                 "steps": [], "ext": list(ext), "plan": [], "by": "event-driven (no human trigger)",
                 "live": {"event": f"{clock_label()} · {event}", "inject": [], "ext": list(ext)}}
    audit("orchestrator", "autonomous run", event)
    threading.Thread(target=execute_scenario, args=(RUNS[rid],), daemon=True).start()
    return rid


def world_step():
    if any(r["status"] == "Running" for r in RUNS.values()):
        WORLD["pause_reason"] = "Agents are working; the clock waits for their plan"
        return
    if any(d["status"] == "Requires human approval" for d in DECISIONS.values()):
        WORLD["pause_reason"] = "Waiting for a person to approve or reject the dispatch"
        return
    WORLD["pause_reason"] = None
    h = WORLD["speed"]
    ship = call("shipping", "POST", "/world/tick", {"hours": h})
    for dpt in ship["departures"]:
        wlog("depart", f"{dpt['vessel']} loaded {dpt['quantity_ton']:,.0f} t and sails for {dpt['plant_id']}")
    for arr in ship["arrivals"]:
        res = call("manufacturer", "POST", "/world/deliver", arr)
        wlog("arrive", f"{arr['vessel']} berthed at {arr['plant_id']} and unloaded {res['unloaded_ton']:,.0f} t {arr['cement_type']}")
    WORLD["plants"] = call("manufacturer", "POST", "/world/tick", {"hours": h})
    WORLD["vessels"] = ship["vessels"]
    WORLD["t"] += h
    for pl in WORLD["plants"]:
        key = f"{pl['plant_id']} {pl['cement_type']}"
        if pl["stocked_out"] and key not in WORLD["stockouts"]:
            WORLD["stockouts"].add(key)
            wlog("stockout", f"STOCK-OUT at {key}: the plant cannot sell this cement until a vessel arrives")
        elif not pl["stocked_out"]:
            WORLD["stockouts"].discard(key)
    for t_at, key, text, inject, ext, rerun in STORY:
        if WORLD["t"] >= t_at and key not in WORLD["story_done"]:
            WORLD["story_done"].add(key)
            wlog("disruption", text)
            for ent, path, body in inject:
                call(ent, "POST", path, body)
                if path == "/events/weather" and body["wave_m"] > 2.5:  # laden vessels already on that route slow down
                    for v in WORLD["vessels"]:
                        if v["mode"] == "laden" and v["destination"] in body["plants"]:
                            call("shipping", "POST", "/events/vessel-delay", {"vessel": v["vessel"], "hours": 14})
                            wlog("disruption", f"{v['vessel']} reduces speed in the storm on the way to {v['destination']}: about 14 h late")
            if rerun:
                start_live_run(text, ext=ext)
            return
    # Event detection: a silo crossing the 25 % rule wakes the agents (once per plant per 36 simulated hours).
    for pl in sorted(WORLD["plants"], key=lambda x: x["level_pct"]):
        key = f"{pl['plant_id']} {pl['cement_type']}"
        if pl["low"] and WORLD["t"] - WORLD["last_trigger"].get(key, -999) > 36:
            WORLD["last_trigger"][key] = WORLD["t"]
            text = f"IIoT silo sensor: {key} at {pl['level_pct']:.0%} (rule: below 25 %), {pl['days_left']} days of stock left"
            wlog("event", text)
            start_live_run(text, title=f"Live {clock_label()}: low stock at {key}")
            return


def world_loop():
    while True:
        time.sleep(1.0)
        if not WORLD or not WORLD.get("running"):
            continue
        try:
            world_step()
        except Exception as ex:  # noqa: BLE001
            WORLD["pause_reason"] = f"World tick failed: {ex}"


class Speed(BaseModel):
    speed: float = 1.0


@app.get("/world")
def world():
    if not WORLD.get("plants"):
        world_reset()
    pend = [{k: d[k] for k in ("id", "action", "priority", "expected_impact", "vessel", "plant_id")} for d in DECISIONS.values()
            if d["status"] == "Requires human approval"]
    return {"clock": clock_label(), "t": round(WORLD["t"], 2), "running": WORLD["running"], "speed": WORLD["speed"],
            "pause_reason": WORLD["pause_reason"], "plants": WORLD["plants"], "vessels": WORLD["vessels"],
            "log": list(WORLD["log"])[:30], "pending": pend, "story": [{"at": a, "text": t} for a, _, t, *_ in STORY],
            "storm_routes": ["PP F"] if "storm" in WORLD["story_done"] and "calm" not in WORLD["story_done"] else []}


@app.post("/world/play")
def world_play():
    if not WORLD.get("plants"):
        world_reset()
    WORLD["running"] = True
    if not WORLD["log"]:
        wlog("start", "Clock started. Plants sell cement every hour; silos drain at each plant's own daily demand.")
    return world()


@app.post("/world/pause")
def world_pause():
    WORLD["running"] = False
    WORLD["pause_reason"] = "Paused by the user"
    return world()


@app.post("/world/speed")
def world_speed(sp: Speed):
    WORLD["speed"] = max(0.25, min(sp.speed, 6.0))
    return world()


threading.Thread(target=world_loop, daemon=True).start()
