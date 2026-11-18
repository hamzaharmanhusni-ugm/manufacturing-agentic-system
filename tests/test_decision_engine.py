import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared import decision_engine as de  # noqa: E402


def test_weights_sum_to_one():
    assert abs(sum(de.PLANT_WEIGHTS.values()) - 1) < 1e-9
    assert abs(sum(de.SHIP_WEIGHTS.values()) - 1) < 1e-9


def test_usable_stock_and_days_of_cover():
    silos = [{"level_pct": 0.5, "capacity_ton": 1000, "dead_stock_ton": 80}, {"level_pct": 0.05, "capacity_ton": 1000, "dead_stock_ton": 80}]
    assert de.usable_stock(silos) == 420  # second silo is below dead stock -> 0
    assert de.days_of_cover(420, [100, 110, 90]) == 4.2


def test_grade_direction():
    assert de.grade(1.0, [2, 4, 7, 10], True) == 5    # 1 day to stock-out: most urgent
    assert de.grade(12, [2, 4, 7, 10], True) == 1
    assert de.grade(900, [300, 450, 600, 800], False) == 5


def test_plant_priority_ranks_urgent_first():
    base = {"selling_price": 1_400_000, "forecast_demand": 500, "contribution_margin": 300_000}
    r = de.plant_priority([{"plant_id": "A", "stockout_days": 9, "endurance_days": 10, **base},
                           {"plant_id": "B", "stockout_days": 1.5, "endurance_days": 2, **base}])
    assert [x["plant_id"] for x in r] == ["B", "A"] and r[0]["rank"] == 1


def test_saw_cost_and_benefit():
    c = [{"vessel": "fast", "arrival_hours": 20, "capacity_ton": 5000, "proven_calls": 1, "evidence": 1, "wave_m": 1},
         {"vessel": "slow", "arrival_hours": 40, "capacity_ton": 5000, "proven_calls": 1, "evidence": 1, "wave_m": 1}]
    r = de.saw_rank(c)
    assert r[0]["vessel"] == "fast" and r[0]["saw_score"] == 1.0 and r[1]["normalized"]["arrival_hours"] == 0.5


def test_saw_missing_criterion_rescales_weights():
    c = [{"vessel": "a", "arrival_hours": 10, "capacity_ton": 1}, {"vessel": "b", "arrival_hours": 20, "capacity_ton": 1}]
    r = de.saw_rank(c)
    assert abs(sum(r[0]["weights_used"].values()) - 1) < 1e-3


def test_assignment_one_ship_per_plant_and_hard_filters():
    pri = de.plant_priority([
        {"plant_id": "A", "stockout_days": 1, "endurance_days": 1, "selling_price": 1, "forecast_demand": 1, "contribution_margin": 1},
        {"plant_id": "B", "stockout_days": 3, "endurance_days": 3, "selling_price": 1, "forecast_demand": 1, "contribution_margin": 1}])
    ship = lambda v, h, wave=1.0, types=("PCC",): {"vessel": v, "arrival_hours": h, "capacity_ton": 5000, "proven_calls": 1, "evidence": 1,
                                                   "wave_m": wave, "cement_types": list(types)}
    opts = {"A": [ship("S1", 10), ship("S2", 12), ship("S3", 5, wave=3.4)], "B": [ship("S1", 10), ship("S2", 12)]}
    needs = {"A": {"cement_type": "PCC", "space_ton": 4000, "needs_delivery": True}, "B": {"cement_type": "PCC", "space_ton": 9000, "needs_delivery": True}}
    plan, excluded = de.assign(pri, opts, needs)
    assert [(p["plant_id"], p["vessel"]) for p in plan] == [("A", "S1"), ("B", "S2")]
    assert plan[0]["quantity_ton"] == 4000
    assert any(e["vessel"] == "S3" and "sailing not advised" in e["reason"] for e in excluded)
