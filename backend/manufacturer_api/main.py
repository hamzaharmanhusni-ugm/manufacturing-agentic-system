"""Enterprise 1: Cement Manufacturing API (port 8001).
Store: PostgreSQL via SQLAlchemy (Docker), relational tables. Units: tons. snake_case.
Agents hosted here: Stock Monitoring, ML Forecasting, Demand & Priority (proposal agents)."""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd  # noqa: E402
from fastapi import Depends, FastAPI  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from sqlalchemy import inspect, text  # noqa: E402

from data.generate import generate_manufacturer  # noqa: E402
from shared import decision_engine as de  # noqa: E402
from shared.config import LOW_STOCK_PCT  # noqa: E402
from shared.stores import engine as get_engine  # noqa: E402
from shared.ml_models import DemandForecaster, arima_stockout_days  # noqa: E402
from shared.security import setup  # noqa: E402

engine = get_engine("manufacturer")  # PostgreSQL in Docker (SQLite when MAS_STORAGE=local)
if not inspect(engine).has_table("silos"):
    generate_manufacturer()

ALL = {"read:shared", "marketing", "finance", "operations", "agents", "simulate", "execute"}
POLICY = {  # G_1: data-sharing agreement of the manufacturer
    "global-orchestrator": {"read:shared", "agents", "simulate", "execute"},  # no raw price/margin
    "global-admin": ALL, "manufacturer-portal": ALL,
    "shipping-portal": {"read:shared"}, "distribution-portal": {"read:shared"},
}
app = FastAPI(title="Manufacturer API (Enterprise 1)", version="1.0",
              description="Cement manufacturer: Marketing + Operations. SYNTHETIC data.")
require = setup(app, "manufacturer", POLICY)

STATE = {"version": 0, "cache": None, "alerted": set(), "rates": None}


def q(sql, **kw):
    return pd.read_sql(text(sql), engine, params=kw)


def run(sql, **kw):
    with engine.begin() as c:
        c.execute(text(sql), kw)
    STATE["version"] += 1


def setting(key, default=1.0):
    r = q("SELECT value FROM settings WHERE key=:k", k=key)
    return float(r.value.iloc[0]) if len(r) else default


forecaster = DemandForecaster().fit(q("SELECT * FROM sales_history"))


def snapshot():
    """Everything the three agents compute, cached until data changes."""
    if STATE["cache"] and STATE["cache"][0] == STATE["version"]:
        return STATE["cache"][1]
    sales = q("SELECT * FROM sales_history")
    mult = setting("demand_multiplier_PP F")
    fc = pd.DataFrame(forecaster.forecast(sales, {"PP F": 1 + (mult - 1) / 2}))
    silos = q("SELECT * FROM silos")
    plants = q("SELECT * FROM packing_plants")
    incoming = q("SELECT * FROM incoming_deliveries")
    now = datetime.now()
    series, plant_rows, needs = [], [], {}
    for _, p in plants.iterrows():
        per_type = []
        for ctype, grp in silos[silos.plant_id == p.plant_id].groupby("cement_type"):
            usable = de.usable_stock(grp.to_dict("records"))
            stock = float((grp.level_pct * grp.capacity_ton).sum())
            cap = float(grp.capacity_ton.sum())
            p50 = fc[(fc.plant_id == p.plant_id) & (fc.cement_type == ctype)].p50.tolist()
            inc = incoming[(incoming.plant_id == p.plant_id) & (incoming.cement_type == ctype)]
            deliveries = [(max(0, (datetime.fromisoformat(r.eta) - now).total_seconds() / 86400), r.quantity_ton)
                          for r in inc.itertuples()]
            draw = sales[(sales.plant_id == p.plant_id) & (sales.cement_type == ctype)].sales_ton.tail(60).tolist()
            so_days, _ = arima_stockout_days(draw, usable, p50, deliveries)
            doc = de.days_of_cover(usable, p50)
            series.append({"plant_id": p.plant_id, "cement_type": ctype, "usable_ton": round(usable, 1),
                           "stock_ton": round(stock, 1), "capacity_ton": cap, "level_pct": round(stock / cap, 4),
                           "daily_demand_p50": round(sum(p50) / len(p50), 1), "days_of_cover": round(doc, 2),
                           "stockout_days": so_days, "incoming_ton": float(inc.quantity_ton.sum()),
                           "low_stock": bool((grp.level_pct < LOW_STOCK_PCT).any()), "silos": len(grp)})
            per_type.append(series[-1])
        crit = min(per_type, key=lambda r: r["stockout_days"])
        plant_rows.append({"plant_id": p.plant_id, "stockout_days": crit["stockout_days"],
                           "endurance_days": min(r["days_of_cover"] for r in per_type),
                           "selling_price": float(p.selling_price_idr_ton), "contribution_margin": float(p.contribution_margin_idr_ton),
                           "forecast_demand": round(sum(r["daily_demand_p50"] for r in per_type), 1)})
        needs[p.plant_id] = {"cement_type": crit["cement_type"],
                             "space_ton": round(crit["capacity_ton"] * 0.95 - crit["stock_ton"] - crit["incoming_ton"], 1),
                             "needs_delivery": crit["stockout_days"] < 12 and crit["capacity_ton"] * 0.95 - crit["stock_ton"] - crit["incoming_ton"] > 1000}
    ranking = de.plant_priority(plant_rows)
    snap = json.loads(json.dumps({"series": series, "ranking": ranking, "needs": needs, "forecast": fc.to_dict("records"),
                                  "computed_at": now.isoformat(timespec="seconds")}, default=lambda o: o.item()))
    STATE["cache"] = (STATE["version"], snap)
    return snap


def shared_ranking(snap):
    """Price and margin are converted to grades before leaving the enterprise (data minimisation)."""
    return [{k: v for k, v in r.items() if k not in ("selling_price", "contribution_margin")} for r in snap["ranking"]]


# ------------------------------------------------------------------ read endpoints
@app.get("/plants", tags=["operations"])
def plants(_=Depends(require("read:shared"))):
    snap = snapshot()
    meta = q("SELECT plant_id, region, lat, lon, berth_draft_m FROM packing_plants").to_dict("records")
    rank = {r["plant_id"]: r for r in shared_ranking(snap)}
    return [{**m, "priority": rank[m["plant_id"]], "need": snap["needs"][m["plant_id"]],
             "series": [s for s in snap["series"] if s["plant_id"] == m["plant_id"]]} for m in meta]


@app.get("/silos", tags=["operations"])
def silos(_=Depends(require("read:shared"))):
    return q("SELECT * FROM silos").to_dict("records")


@app.get("/silos/history", tags=["operations"])
def silo_history(plant_id: str, _=Depends(require("operations"))):
    return q("SELECT h.* , s.cement_type FROM silo_level_history h JOIN silos s USING(silo_id) "
             "WHERE s.plant_id=:p ORDER BY date", p=plant_id).to_dict("records")


@app.get("/incoming", tags=["operations"])
def incoming(_=Depends(require("read:shared"))):
    return q("SELECT * FROM incoming_deliveries ORDER BY eta").to_dict("records")


@app.get("/load-port", tags=["operations"])
def load_port(_=Depends(require("read:shared"))):
    return {"stock": q("SELECT * FROM load_port_stock").to_dict("records"),
            "production_capacity_factor": setting("production_capacity_factor")}


@app.get("/alerts", tags=["operations"])
def alerts(_=Depends(require("read:shared"))):
    return [s for s in snapshot()["series"] if s["low_stock"] or s["stockout_days"] < 3]


@app.get("/forecast", tags=["marketing"])
def forecast(plant_id: str | None = None, _=Depends(require("read:shared"))):
    rows = snapshot()["forecast"]
    return [r for r in rows if not plant_id or r["plant_id"] == plant_id]


@app.get("/forecast/metrics", tags=["marketing"])
def forecast_metrics(_=Depends(require("read:shared"))):
    return forecaster.metrics


@app.get("/marketing/sales", tags=["marketing"])
def sales(plant_id: str | None = None, _=Depends(require("marketing"))):
    df = q("SELECT * FROM sales_history" + (" WHERE plant_id=:p" if plant_id else ""), p=plant_id)
    return df.to_dict("records")


@app.get("/marketing/sop", tags=["marketing"])
def sop(_=Depends(require("marketing"))):
    return q("SELECT * FROM sop_plan").to_dict("records")


@app.get("/marketing/prices", tags=["marketing"])
def prices(_=Depends(require("finance"))):
    return q("SELECT plant_id, selling_price_idr_ton, contribution_margin_idr_ton FROM packing_plants").to_dict("records")


@app.get("/marketing/priority-full", tags=["marketing"])
def priority_full(_=Depends(require("finance"))):
    return snapshot()["ranking"]


# ------------------------------------------------------------------ agents (A2A endpoints)
def agent_result(name, inputs, outputs, log, t0):
    return {"agent": name, "enterprise": "manufacturer", "status": "Completed", "inputs": inputs,
            "outputs": outputs, "log": log, "duration_ms": round((time.perf_counter() - t0) * 1000, 1)}


@app.post("/agents/stock-monitoring/run", tags=["agents"])
def stock_monitoring(_=Depends(require("agents"))):
    t0 = time.perf_counter()
    snap = snapshot()
    low = [s for s in snap["series"] if s["low_stock"]]
    new_events = []
    for s in low:  # alert once: re-arms after the level recovers
        key = f"{s['plant_id']}|{s['cement_type']}"
        if key not in STATE["alerted"]:
            STATE["alerted"].add(key)
            new_events.append({"event": "low_stock", **s})
    for key in list(STATE["alerted"]):
        if not any(f"{s['plant_id']}|{s['cement_type']}" == key for s in low):
            STATE["alerted"].discard(key)
    log = [f"Re-measured 22 silos at {snap['computed_at']}",
           f"ARIMA stock-out projection for {len(snap['series'])} plant/cement-type series",
           f"{len(low)} series below {int(LOW_STOCK_PCT * 100)} % level; {len(new_events)} new low-stock events"]
    return agent_result("Stock Monitoring Agent", {"silos": 22, "rule": "level < 25 %"},
                        {"series": snap["series"], "low_stock_events": new_events}, log, t0)


@app.post("/agents/ml-forecasting/run", tags=["agents"])
def ml_forecasting(_=Depends(require("agents"))):
    t0 = time.perf_counter()
    fc = pd.DataFrame(snapshot()["forecast"])
    summary = fc.groupby(["plant_id", "cement_type"])[["p10", "p50", "p90"]].sum().round(0).reset_index().to_dict("records")
    m = forecaster.metrics
    log = [f"LightGBM champion: 14-day P10/P50/P90 for {len(summary)} series",
           f"Backtest WAPE champion {m['wape_champion']:.3f} vs challenger {m['wape_challenger']:.3f} (synthetic data)",
           "Ensemble selected" if m["ensemble_selected"] else "Champion kept (ensemble not better)"]
    return agent_result("ML Forecasting Agent", {"history_days": 400, "horizon": 14},
                        {"summary_14d": summary, "metrics": m}, log, t0)


@app.post("/agents/demand-priority/run", tags=["agents"])
def demand_priority(_=Depends(require("agents"))):
    t0 = time.perf_counter()
    snap = snapshot()
    rank = shared_ranking(snap)
    log = ["Combined sales history, S&OP, forecast, price and margin (grades only leave the enterprise)",
           "Eq. 14 priority score with weights 0.35/0.20/0.20/0.15/0.10",
           f"Top plant: {rank[0]['plant_id']} score {rank[0]['priority_score']}"]
    return agent_result("Demand & Priority Agent", {"weights": de.PLANT_WEIGHTS},
                        {"ranking": rank, "needs": snap["needs"]}, log, t0)


# ------------------------------------------------------------------ execution + simulation events
class Delivery(BaseModel):
    plant_id: str
    cement_type: str
    vessel: str
    quantity_ton: float
    eta_hours: float


@app.post("/incoming", tags=["execution"])
def add_incoming(d: Delivery, _=Depends(require("execute"))):
    eta = (datetime.now() + pd.Timedelta(hours=d.eta_hours)).isoformat(timespec="seconds")
    run("INSERT INTO incoming_deliveries VALUES (:p,:c,:v,:q,:e,'scheduled','dispatch decision')",
        p=d.plant_id, c=d.cement_type, v=d.vessel, q=d.quantity_ton, e=eta)
    run("UPDATE load_port_stock SET available_ton = available_ton - :q WHERE cement_type=:c", q=d.quantity_ton, c=d.cement_type)
    return {"ok": True, "eta": eta}


class SiloDrop(BaseModel):
    plant_id: str = "PP C"
    cement_type: str = "PCC"
    level_pct: float = 0.20


@app.post("/events/silo-drop", tags=["simulation"])
def silo_drop(e: SiloDrop, _=Depends(require("simulate"))):
    run("UPDATE silos SET level_pct=:l, last_reading=:t WHERE plant_id=:p AND cement_type=:c",
        l=e.level_pct, t=datetime.now().isoformat(timespec="seconds"), p=e.plant_id, c=e.cement_type)
    return {"ok": True, "event": "silo level drop", **e.model_dump()}


class Surge(BaseModel):
    plant_id: str = "PP F"
    factor: float = 1.8


@app.post("/events/demand-surge", tags=["simulation"])
def demand_surge(e: Surge, _=Depends(require("simulate"))):
    last = q("SELECT MAX(date) d FROM sales_history").d.iloc[0]
    start = (pd.Timestamp(last) - pd.Timedelta(days=13)).date().isoformat()
    run("UPDATE sales_history SET sales_ton = sales_ton * :f WHERE plant_id=:p AND date >= :s", f=e.factor, p=e.plant_id, s=start)
    run("UPDATE settings SET value=:f WHERE key=:k", f=e.factor, k=f"demand_multiplier_{e.plant_id}")
    STATE["rates"] = None
    return {"ok": True, "event": "demand surge", **e.model_dump()}


class Capacity(BaseModel):
    factor: float = 0.6


@app.post("/events/production-cap", tags=["simulation"])
def production_cap(e: Capacity, _=Depends(require("simulate"))):
    old = setting("production_capacity_factor")
    run("UPDATE settings SET value=:f WHERE key='production_capacity_factor'", f=e.factor)
    run("UPDATE load_port_stock SET available_ton = ROUND(available_ton * :r)", r=e.factor / old)
    return {"ok": True, "event": "production capacity limited", **e.model_dump()}


@app.post("/reset", tags=["simulation"])
def reset(_=Depends(require("simulate"))):
    generate_manufacturer()
    STATE.update(version=STATE["version"] + 1, cache=None, alerted=set(), rates=None)
    return {"ok": True}


# ------------------------------------------------------------------ live world (simulated clock)
def daily_rates():
    """Physical drawdown per plant and cement type (t/day): mean of the last 7 days of sales x demand multiplier."""
    if STATE.get("rates") is None:
        s = q("SELECT * FROM sales_history")
        last = sorted(s.date.unique())[-7:]
        r = s[s.date.isin(last)].groupby(["plant_id", "cement_type"]).sales_ton.mean().to_dict()
        mult = setting("demand_multiplier_PP F")
        STATE["rates"] = {k: v * (mult if k[0] == "PP F" else 1.0) for k, v in r.items()}
    return STATE["rates"]


def world_state():
    silos = q("SELECT plant_id, cement_type, capacity_ton, dead_stock_ton, level_pct FROM silos")
    meta = q("SELECT plant_id, lat, lon FROM packing_plants").set_index("plant_id")
    rates = daily_rates()
    out = []
    for (pid, ctype), g in silos.groupby(["plant_id", "cement_type"]):
        cap = float(g.capacity_ton.sum())
        stock = float((g.level_pct * g.capacity_ton).sum())
        usable = de.usable_stock(g.to_dict("records"))
        rate = rates.get((pid, ctype), 0)
        out.append({"plant_id": pid, "cement_type": ctype, "lat": float(meta.loc[pid, "lat"]), "lon": float(meta.loc[pid, "lon"]),
                    "level_pct": round(stock / cap, 4), "usable_ton": round(usable, 1), "capacity_ton": cap,
                    "daily_use_ton": round(rate, 1), "days_left": round(usable / rate, 2) if rate else None,
                    "low": stock / cap < LOW_STOCK_PCT, "stocked_out": usable <= 0})
    return out


class Tick(BaseModel):
    hours: float = 1.0


@app.post("/world/tick", tags=["live world"])
def world_tick(t: Tick, _=Depends(require("simulate"))):
    """Advance the plant world by t.hours: every silo drains at its plant's daily demand."""
    rates = daily_rates()
    silos = q("SELECT plant_id, cement_type, capacity_ton, level_pct FROM silos")
    with engine.begin() as c:
        for (pid, ctype), g in silos.groupby(["plant_id", "cement_type"]):
            stock = float((g.level_pct * g.capacity_ton).sum())
            if stock <= 0:
                continue
            factor = max(0.0, stock - rates.get((pid, ctype), 0) * t.hours / 24) / stock
            c.execute(text("UPDATE silos SET level_pct = level_pct * :f WHERE plant_id=:p AND cement_type=:c"), {"f": factor, "p": pid, "c": ctype})
    STATE["version"] += 1
    return world_state()


@app.get("/world/state", tags=["live world"])
def world_get(_=Depends(require("read:shared"))):
    return world_state()


class Unload(BaseModel):
    vessel: str
    plant_id: str
    cement_type: str
    quantity_ton: float


@app.post("/world/deliver", tags=["live world"])
def world_deliver(u: Unload, _=Depends(require("execute"))):
    """A vessel discharges: cement fills the plant's silos of that type in proportion to free space."""
    silos = q("SELECT silo_id, capacity_ton, level_pct FROM silos WHERE plant_id=:p AND cement_type=:c", p=u.plant_id, c=u.cement_type)
    free = (1 - silos.level_pct) * silos.capacity_ton
    total_free = float(free.sum())
    put = min(u.quantity_ton, total_free)
    with engine.begin() as c:
        for r, f in zip(silos.itertuples(), free):
            add = put * float(f) / total_free if total_free else 0
            c.execute(text("UPDATE silos SET level_pct = :l, last_reading=:t WHERE silo_id=:s"),
                      {"l": min(1.0, r.level_pct + add / r.capacity_ton), "s": r.silo_id, "t": datetime.now().isoformat(timespec="seconds")})
        c.execute(text("DELETE FROM incoming_deliveries WHERE vessel=:v AND plant_id=:p"), {"v": u.vessel, "p": u.plant_id})
    STATE["version"] += 1
    return {"unloaded_ton": round(put, 1), "spilled_back_ton": round(u.quantity_ton - put, 1), "state": world_state()}
