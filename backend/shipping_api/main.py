"""Enterprise 2: Shipping & Logistics API (port 8002), a separate subsidiary.
Store: MongoDB (Docker) document collections, camelCase nested documents.
Agent hosted here: Fleet Tracking Agent (proposal agent)."""
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from fastapi import Depends, FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from data.generate import generate_shipping  # noqa: E402
from shared.config import FAILURE_RISK_WARN, LOAD_PORT, OTHER_PORTS, PLANTS, WAVE_LIMIT_M  # noqa: E402
from shared.stores import Collection  # noqa: E402
from shared.geo import haversine_nm, sea_distance_nm  # noqa: E402
from shared.ml_models import EtaModel, WeibullMaintenance, dbscan_status, geofence_status  # noqa: E402
from shared.security import setup  # noqa: E402

if Collection("vessels").count() == 0:
    generate_shipping()

vessels_c, voyages_c, weather_c, assign_c = (Collection(n) for n in ("vessels", "voyages", "weather", "assignments"))

ALL = {"read:shared", "read:internal", "agents", "simulate", "execute"}
POLICY = {  # G_2: shares only GPS position, vessel status, ETA and voyage history (proposal ch. 8)
    "global-orchestrator": {"read:shared", "agents", "simulate", "execute"},
    "global-admin": ALL, "shipping-portal": ALL,
    "manufacturer-portal": {"read:shared"},
}
app = FastAPI(title="Shipping API (Enterprise 2)", version="1.0",
              description="Shipment subsidiary: fleet, voyages, ETA. SYNTHETIC data.")
require = setup(app, "shipping", POLICY)

eta_model = EtaModel().fit(voyages_c.find())
weibull = WeibullMaintenance().fit()
PORTS = [LOAD_PORT, *OTHER_PORTS] + [{"id": p["id"], "lat": p["lat"], "lon": p["lon"]} for p in PLANTS]
LP = (LOAD_PORT["lat"], LOAD_PORT["lon"])
PLANT_XY = {p["id"]: (p["lat"], p["lon"]) for p in PLANTS}


def route_wave():
    out = {}
    for wp in weather_c.find():
        if wp["route"] in PLANT_XY:
            out[wp["route"]] = max(out.get(wp["route"], 0), max(f["waveHeightM"] for f in wp["forecast"]))
    return out


def ping_age_h(doc):
    return (datetime.now() - datetime.fromisoformat(doc["position"]["lastPingAt"])).total_seconds() / 3600


def availability_h(doc):
    """Hours until the vessel is loaded and ready at the load port (route rule, Eq. 8)."""
    op, spd = doc["operation"], doc["spec"]["serviceSpeedKn"]
    pos = (doc["position"]["lat"], doc["position"]["lon"])
    m = op["mode"]
    if m == "loading":
        h = 12
    elif m == "anchored":
        h = 18 + 24
    elif m == "ballast":
        h = sea_distance_nm(pos, LP) / spd + 24
    elif m == "discharging":
        h = 18 + sea_distance_nm(pos, LP) / spd + 24
    else:
        return None
    return h + op.get("delayHours", 0)


def fleet_view(internal=False):
    waves = route_wave()
    docs = vessels_c.find()
    month = datetime.now().month
    voyages = voyages_c.find()
    out = []
    laden_rows = []
    for d in docs:
        op, pos = d["operation"], d["position"]
        geo = geofence_status(pos["lat"], pos["lon"], pos["speedKn"], PORTS)
        dbs, cluster = dbscan_status(d["gpsTrack"], PORTS)
        status = "maintenance" if op["mode"] == "maintenance" else geo
        risk = weibull.risk(d["engine"]["runningHoursSinceService"], d["engine"]["temperatureC"], d["engine"]["vibrationMmS"])
        nearest = min((wp for wp in weather_c.find()), key=lambda wp: haversine_nm((pos["lat"], pos["lon"]), (wp["lat"], wp["lon"])))
        v = {"vessel": d["vesselName"], "lat": pos["lat"], "lon": pos["lon"], "speed_kn": pos["speedKn"],
             "heading_deg": pos["headingDeg"], "capacity_ton": d["spec"]["capacityTon"], "cement_types": d["spec"]["cementTypes"],
             "cargo_ton": op["cargoTon"], "cargo_type": op["cargoType"], "destination": op["destination"],
             "mode": op["mode"], "status": status, "status_geofence": geo, "status_dbscan": dbs, "dbscan_cluster_size": cluster,
             "delay_hours": op.get("delayHours", 0), "assigned_plant": op.get("assignedPlant"),
             "wave_m_here": nearest["forecast"][0]["waveHeightM"], "wind_kn_here": nearest["forecast"][0]["windKn"],
             "ping_age_h": round(ping_age_h(d), 2), "evidence": round(max(0.05, 1 - ping_age_h(d) / 24), 3),
             "failure_risk_14d": round(risk, 3), "maintenance": d["maintenance"]["status"],
             "available_in_h": availability_h(d), "eta_hours": None, "eta_range_hours": None}
        if internal:
            v["commercial"] = d["commercial"]
            v["engine"] = d["engine"]
        if op["mode"] == "laden":
            rem = sea_distance_nm((pos["lat"], pos["lon"]), PLANT_XY[op["destination"]])
            laden_rows.append((v, (rem, pos["speedKn"], waves.get(op["destination"], 1), op["cargoTon"], op["destination"], month)))
        elif op["mode"] == "ballast":
            v["eta_hours"] = round(sea_distance_nm((pos["lat"], pos["lon"]), LP) / max(pos["speedKn"], 6) + op.get("delayHours", 0), 1)
        out.append(v)
    if laden_rows:
        # RF was trained on full legs; scale its prediction by the remaining share of the leg.
        preds = eta_model.predict([r for _, r in laden_rows])
        for (v, r), (mu, sd) in zip(laden_rows, preds):
            full = sea_distance_nm(LP, PLANT_XY[r[4]])
            share = r[0] / full
            v["eta_hours"] = round(mu * share + v["delay_hours"], 1)
            v["eta_range_hours"] = round(sd * share, 1)
    return out, voyages, waves


@app.get("/vessels", tags=["fleet"])
def vessels(_=Depends(require("read:shared"))):
    return fleet_view()[0]


@app.get("/vessels/internal", tags=["fleet"])
def vessels_internal(_=Depends(require("read:internal"))):
    return fleet_view(internal=True)[0]


@app.get("/vessels/{name}/track", tags=["fleet"])
def track(name: str, _=Depends(require("read:shared"))):
    for d in vessels_c.find():
        if d["vesselName"] == name:
            return d["gpsTrack"]
    raise HTTPException(404, "vessel not found")


@app.get("/voyages", tags=["voyages"])
def voyages(_=Depends(require("read:shared"))):
    return voyages_c.find()


@app.get("/weather", tags=["weather"])
def weather(_=Depends(require("read:shared"))):
    return weather_c.find()


@app.get("/models", tags=["models"])
def models(_=Depends(require("read:shared"))):
    return {"eta": eta_model.metrics, "maintenance": weibull.metrics,
            "activity": {"proposal": "geofence rule", "course_extension": "DBSCAN (eps 1 nm, min_samples 6)"}}


@app.get("/assignments", tags=["execution"])
def assignments(_=Depends(require("read:shared"))):
    return assign_c.find()


# ------------------------------------------------------------------ agent (A2A endpoint)
@app.post("/agents/fleet-tracking/run", tags=["agents"])
def fleet_tracking(_=Depends(require("agents"))):
    t0 = time.perf_counter()
    fleet, voyages_all, waves = fleet_view()
    month = datetime.now().month
    calls = {}
    for vy in voyages_all:
        calls[(vy["vesselName"], vy["toPlant"])] = calls.get((vy["vesselName"], vy["toPlant"]), 0) + 1
    free = [v for v in fleet if v["available_in_h"] is not None and not v["assigned_plant"]]
    rows = [(sea_distance_nm(LP, PLANT_XY[p["id"]]), v["speed_kn"] if v["speed_kn"] > 6 else 10.5,
             waves.get(p["id"], 1.0), v["capacity_ton"], p["id"], month) for v in free for p in PLANTS]
    preds = iter(eta_model.predict(rows)) if rows else iter([])
    options = {p["id"]: [] for p in PLANTS}
    for v in free:
        for p in PLANTS:
            mu, sd = next(preds)
            options[p["id"]].append({
                "vessel": v["vessel"], "arrival_hours": round(v["available_in_h"] + mu, 1), "arrival_range_hours": round(sd, 1),
                "capacity_ton": v["capacity_ton"], "proven_calls": calls.get((v["vessel"], p["id"]), 0),
                "evidence": v["evidence"], "wave_m": round(waves.get(p["id"], 1.0), 2), "failure_risk": v["failure_risk_14d"],
                "cement_types": v["cement_types"], "in_maintenance": False, "committed": False,
                "available_in_h": round(v["available_in_h"], 1), "delay_hours": v["delay_hours"]})
    for v in fleet:  # excluded vessels still reported so the planner can explain why
        if v not in free:
            for p in PLANTS:
                options[p["id"]].append({"vessel": v["vessel"], "arrival_hours": None, "capacity_ton": v["capacity_ton"],
                                         "proven_calls": 0, "evidence": v["evidence"], "wave_m": None,
                                         "failure_risk": v["failure_risk_14d"], "cement_types": v["cement_types"],
                                         "in_maintenance": v["mode"] == "maintenance", "committed": v["mode"] != "maintenance"})
    no_sail = [p for p, w in waves.items() if w > WAVE_LIMIT_M]
    risky = [v["vessel"] for v in fleet if v["failure_risk_14d"] > FAILURE_RISK_WARN]
    log = [f"Read IIoT GPS for {len(fleet)} vessels; geofence + DBSCAN activity detection",
           f"RF ETA for {len(free)} available vessels x {len(PLANTS)} plants (282-voyage model, MAE {eta_model.metrics['mae_hours']} h)",
           f"Weibull failure risk computed; above {int(FAILURE_RISK_WARN * 100)} %: {', '.join(risky) or 'none'}",
           f"Sailing not advised routes: {', '.join(no_sail) or 'none'}"]
    return {"agent": "Fleet Tracking Agent", "enterprise": "shipping", "status": "Completed",
            "inputs": {"vessels": len(fleet), "voyage_history": len(voyages_all), "weather_points": 91},
            "outputs": {"fleet": fleet, "options": options, "sailing_not_advised": no_sail, "high_failure_risk": risky,
                        "route_wave_m": waves},
            "log": log, "duration_ms": round((time.perf_counter() - t0) * 1000, 1)}


# ------------------------------------------------------------------ execution + simulation events
class Assignment(BaseModel):
    vessel: str
    plant_id: str
    cement_type: str
    quantity_ton: float
    decision_id: str = ""


@app.post("/assignments", tags=["execution"])
def assign(a: Assignment, _=Depends(require("execute"))):
    docs = vessels_c.find()
    for d in docs:
        if d["vesselName"] == a.vessel:
            d["operation"].update(assignedPlant=a.plant_id, destination=a.plant_id, cargoType=a.cement_type)
    vessels_c.save(docs)
    rows = assign_c.find()
    rows.append({**a.model_dump(), "assignedAt": datetime.now().isoformat(timespec="seconds"), "status": "confirmed by Shipment"})
    assign_c.save(rows)
    return {"ok": True}


class Delay(BaseModel):
    vessel: str = "Ship N"
    hours: float = 60


@app.post("/events/vessel-delay", tags=["simulation"])
def vessel_delay(e: Delay, _=Depends(require("simulate"))):
    docs = vessels_c.find()
    for d in docs:
        if d["vesselName"] == e.vessel:
            d["operation"]["delayHours"] = d["operation"].get("delayHours", 0) + e.hours
    vessels_c.save(docs)
    return {"ok": True, "event": "vessel delay", **e.model_dump()}


class Weather(BaseModel):
    plants: list[str] = ["PP G", "PP I"]
    wave_m: float = 3.4


@app.post("/events/weather", tags=["simulation"])
def weather_event(e: Weather, _=Depends(require("simulate"))):
    pts = weather_c.find()
    for wp in pts:
        if wp["route"] in e.plants:
            for f in wp["forecast"]:
                f["waveHeightM"] = round(e.wave_m + (f["waveHeightM"] - 1) * 0.1, 2)
                f["windKn"] = round(f["windKn"] + 18, 1)
    weather_c.save(pts)
    return {"ok": True, "event": "severe weather", **e.model_dump()}


@app.post("/reset", tags=["simulation"])
def reset(_=Depends(require("simulate"))):
    generate_shipping()
    return {"ok": True}
