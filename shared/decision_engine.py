"""Deterministic decision engine (proposal chapter 6). No LLM touches these numbers.

Eq. 1-2   usable stock, days of cover
Eq. 14    packing plant priority: grade 1-5 per criterion, weighted sum
Eq. 15-16 ship ranking: SAW normalisation (benefit x/max, cost min/x), weight re-scaling for missing data
Eq. 17-18 greedy assignment, one ship per plant, up to three alternatives
"""
from shared.config import FAILURE_RISK_WARN, WAVE_LIMIT_M

PLANT_WEIGHTS = {"stockout_days": 0.35, "endurance_days": 0.20, "selling_price": 0.20,
                 "forecast_demand": 0.15, "contribution_margin": 0.10}
SHIP_WEIGHTS = {"arrival_hours": 0.35, "capacity_ton": 0.20, "proven_calls": 0.20,
                "evidence": 0.15, "wave_m": 0.10}
SHIP_COST = {"arrival_hours", "wave_m"}

# Grade boundaries b(i,1..4). "smaller is more urgent" criteria get reversed grades.
PLANT_BOUNDS = {
    "stockout_days": ([2, 4, 7, 10], True),
    "endurance_days": ([3, 5, 8, 12], True),
    "selling_price": ([1_250_000, 1_350_000, 1_450_000, 1_550_000], False),
    "forecast_demand": ([300, 450, 600, 800], False),
    "contribution_margin": ([220_000, 270_000, 320_000, 370_000], False),
}


def usable_stock(silos):
    """Eq. 1: sum over silos of max(0, level x capacity - dead stock)."""
    return sum(max(0.0, s["level_pct"] * s["capacity_ton"] - s["dead_stock_ton"]) for s in silos)


def days_of_cover(usable, p50_daily):
    """Eq. 2: usable / mean P50 demand over the 14-day horizon."""
    mean = sum(p50_daily) / len(p50_daily) if p50_daily else 0
    return usable / mean if mean > 0 else float("inf")


def grade(value, bounds, smaller_is_urgent):
    g = 1 + sum(int(value >= b) for b in bounds)  # 1..5, larger value -> higher grade
    return 6 - g if smaller_is_urgent else g


def plant_priority(plants):
    """Eq. 14. plants: list of dicts with the five criteria. Returns sorted copies with grades and score."""
    out = []
    for p in plants:
        grades = {k: grade(p[k], *PLANT_BOUNDS[k]) for k in PLANT_WEIGHTS}
        score = sum(PLANT_WEIGHTS[k] * grades[k] for k in PLANT_WEIGHTS)
        out.append({**p, "grades": grades, "priority_score": round(score, 3)})
    out.sort(key=lambda r: (-r["priority_score"], r["stockout_days"]))
    for i, r in enumerate(out, 1):
        r["rank"] = i
    return out


def saw_rank(candidates, weights=SHIP_WEIGHTS, cost=SHIP_COST):
    """Eq. 15-16. Criteria missing for every candidate are dropped and weights re-scaled (w')."""
    if not candidates:
        return []
    active = {k: w for k, w in weights.items() if any(c.get(k) is not None for c in candidates)}
    total = sum(active.values())
    active = {k: w / total for k, w in active.items()}
    norm = {}
    for k in active:
        vals = [c[k] for c in candidates if c.get(k) is not None]
        hi, lo = max(vals), min(vals)
        norm[k] = (lo, hi)
    ranked = []
    for c in candidates:
        r = {}
        for k in active:
            x = c.get(k)
            lo, hi = norm[k]
            if x is None:
                r[k] = 0.0
            elif k in cost:
                r[k] = lo / x if x > 0 else 1.0
            else:
                r[k] = x / hi if hi > 0 else 0.0
        score = sum(active[k] * r[k] for k in active)
        ranked.append({**c, "normalized": {k: round(v, 3) for k, v in r.items()},
                       "weights_used": {k: round(v, 3) for k, v in active.items()}, "saw_score": round(score, 4)})
    ranked.sort(key=lambda c: -c["saw_score"])
    return ranked


def eligible(ship, cement_type):
    """Hard filters before ranking (proposal 6.8). Returns (ok, reason)."""
    if ship.get("in_maintenance"):
        return False, "in maintenance"
    if ship.get("committed"):
        return False, "committed to another voyage"
    if cement_type not in ship.get("cement_types", []):
        return False, f"cannot carry {cement_type}"
    if ship.get("wave_m") is not None and ship["wave_m"] > WAVE_LIMIT_M:
        return False, f"sailing not advised (wave {ship['wave_m']} m)"
    return True, ""


def assign(priorities, ship_options, needs, n_alternatives=3):
    """Eq. 17-18 greedy assignment.

    priorities: output of plant_priority (sorted).
    ship_options: {plant_id: [ship dicts with arrival_hours, capacity_ton, ...]}.
    needs: {plant_id: {"cement_type": .., "space_ton": .., "needs_delivery": bool}}.
    """
    free = {s["vessel"] for opts in ship_options.values() for s in opts}
    plan, excluded = [], []
    for p in priorities:
        pid = p["plant_id"]
        need = needs[pid]
        if not need["needs_delivery"]:
            continue
        cands, warnings = [], []
        for s in ship_options.get(pid, []):
            ok, why = eligible(s, need["cement_type"])
            if not ok:
                excluded.append({"plant_id": pid, "vessel": s["vessel"], "reason": why})
                continue
            if s["vessel"] in free:
                cands.append(s)
        ranked = saw_rank(cands)
        if not ranked:
            plan.append({"plant_id": pid, "vessel": None, "warning": "no eligible vessel", "priority": p})
            continue
        best = ranked[0]
        if best.get("failure_risk", 0) > FAILURE_RISK_WARN:
            warnings.append(f"{best['vessel']} failure risk {best['failure_risk']:.0%} in 14 days")
        free.discard(best["vessel"])
        qty = int(min(best["capacity_ton"], need["space_ton"]))
        plan.append({"plant_id": pid, "cement_type": need["cement_type"], "vessel": best["vessel"],
                     "quantity_ton": qty, "arrival_hours": best["arrival_hours"],
                     "arrival_range_hours": best.get("arrival_range_hours"), "saw_score": best["saw_score"],
                     "ranking": ranked[:n_alternatives + 1], "alternatives": [r["vessel"] for r in ranked[1:n_alternatives + 1]],
                     "warnings": warnings, "priority": p})
    return plan, excluded
