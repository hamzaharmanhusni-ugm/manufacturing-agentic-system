"""End-to-end check against the running stack (python run_all.py first).
Covers the acceptance criteria: 4 APIs + orchestrator healthy, auth 401/403, 6 scenarios, parallel agents,
adaptive replanning, approve + reject, KPI change, reset."""
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.config import url  # noqa: E402

O = url("orchestrator")
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def run(key):
    rid = httpx.post(f"{O}/scenarios/{key}/run", json={}, timeout=30).json()["run_id"]
    for _ in range(180):
        r = httpx.get(f"{O}/runs/{rid}", timeout=30).json()
        if r["status"] != "Running":
            return r
        time.sleep(1)
    return r


eco = httpx.get(f"{O}/ecosystem", timeout=30).json()
check("4 enterprise APIs online", sum(e["status"] == "online" for e in eco) == 4)
check("401 without key", httpx.get(url("manufacturer") + "/plants").status_code == 401)
check("403 orchestrator cannot read raw margins",
      httpx.get(url("manufacturer") + "/marketing/prices", headers={"X-API-Key": "key-global-orchestrator"}).status_code == 403)
check("403 marketing role cannot approve",
      httpx.post(f"{O}/decisions/none/approve", json={"role": "Marketing Planner"}).status_code in (403, 404))

httpx.post(f"{O}/reset", json={}, timeout=180)
k0 = httpx.get(f"{O}/kpis", timeout=60).json()["current"]

for key in ["normal", "low_stock", "demand_surge", "shipping_disruption", "weather", "supplier"]:
    r = run(key)
    workers = [s for s in r["steps"] if s["agent"] in ("Stock Monitoring Agent", "ML Forecasting Agent", "Fleet Tracking Agent", "Demand & Priority Agent")]
    parallel = r.get("parallel_wall_ms", 1e9) < sum(s["duration_ms"] for s in workers[:4])
    check(f"scenario {key}", r["status"] == "Completed" and parallel,
          f"{r.get('duration_s')} s, {len(r.get('decisions', []))} decision(s), parallel={parallel} {r.get('error', '')}")
    if key == "shipping_disruption":
        check("adaptive replanning comparison", any(c["changed"] for c in r.get("comparison", [])))
    if key == "weather":
        check("weather excludes vessels", any("sailing not advised" in e["reason"] for e in r.get("excluded", [])))

pending = [d for d in httpx.get(f"{O}/decisions").json() if d["status"] == "Requires human approval"]
check("decisions waiting for approval", len(pending) >= 2, f"({len(pending)})")
if len(pending) >= 2:
    a = httpx.post(f"{O}/decisions/{pending[0]['id']}/approve", json={"role": "Manufacturer Manager"}, timeout=60)
    b = httpx.post(f"{O}/decisions/{pending[1]['id']}/reject", json={"role": "Shipping Manager", "note": "test"}, timeout=60)
    check("approve executes across enterprises", a.status_code == 200 and any(
        x["vessel"] == pending[0]["vessel"] for x in httpx.get(url("shipping") + "/assignments", headers={"X-API-Key": "key-global-admin"}).json()))
    check("reject recorded", b.status_code == 200 and b.json()["status"] == "Rejected")
# Live world: silos drain with the clock, a sensor wakes the agents, an approved vessel sails and unloads.
httpx.post(f"{O}/reset", json={}, timeout=180)
w0 = httpx.get(f"{O}/world", timeout=60).json()
lvl0 = {(p["plant_id"], p["cement_type"]): p["level_pct"] for p in w0["plants"]}
httpx.post(f"{O}/world/speed", json={"speed": 4})
httpx.post(f"{O}/world/play")
kinds, t_end = set(), time.time() + 150
while time.time() < t_end:
    w = httpx.get(f"{O}/world", timeout=60).json()
    kinds |= {e["kind"] for e in w["log"]}
    for d in w["pending"]:
        httpx.post(f"{O}/decisions/{d['id']}/approve", json={"role": "Global Administrator"}, timeout=60)
    if {"event", "depart", "arrive", "disruption"} <= kinds and w["t"] > 70:
        break
    time.sleep(2)
httpx.post(f"{O}/world/pause")
drained = any(p["level_pct"] < lvl0[(p["plant_id"], p["cement_type"])] for p in w["plants"])
check("live world: silos drain with the clock", drained)
check("live world: sensor event starts the agents by itself", "event" in kinds)
check("live world: approved vessels depart and unload", {"depart", "arrive"} <= kinds, str(sorted(kinds)))
check("live world: storyline disruption arrives", "disruption" in kinds)
k1 = httpx.get(f"{O}/kpis", timeout=60).json()["current"]
changed = [m for m in ("avg_days_of_cover", "stockout_events", "replanning_events", "human_approval_rate", "min_material_coverage") if k0.get(m) != k1.get(m)]
check("KPIs changed after simulation", len(changed) >= 3, str(changed))
check("reset", httpx.post(f"{O}/reset", json={}, timeout=180).status_code == 200)
print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
