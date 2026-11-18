"""Synthetic dataset generator (SYNTHETIC DATA, seeded, reproducible).

Each enterprise gets its own store in its own technology and data shape:
  manufacturer -> SQLite through SQLAlchemy (snake_case tables, tons)
  shipping     -> JSON document store, Mongo-style collections (camelCase, nested)
  distribution -> raw sqlite3 (quantities in 50 kg bags)
  supplier     -> CSV flat files (ERP export style)
All four derive from one seeded "world" so cross-enterprise records stay consistent
(e.g. a laden vessel in the shipping store is an incoming delivery in the manufacturer store).
"""
import csv
import json
import math
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.config import (DEAD_STOCK_PCT, LOAD_PORT, OTHER_PORTS, PLANTS, SEED, STORES,  # noqa: E402
                           VESSEL_NAMES)
from shared.geo import interpolate, sea_distance_nm  # noqa: E402
from shared.stores import Collection, engine  # noqa: E402

HISTORY_DAYS = 400


def now_hour() -> datetime:
    return datetime.now().replace(minute=0, second=0, microsecond=0)


def _rng(offset=0):
    return np.random.default_rng(SEED + offset)


# ----------------------------------------------------------------- shared world
def world():
    """Deterministic fleet state shared by shipping (owner) and manufacturer (incoming deliveries)."""
    rng = _rng(1)
    plan = (["laden"] * 5 + ["ballast"] * 4 + ["loading"] * 3 + ["discharging"] * 2
            + ["anchored"] * 3 + ["maintenance"] * 2)
    laden_targets = ["PP A", "PP D", "PP E", "PP H", "PP B"]
    discharge_at = ["PP G", "PP I"]
    vessels = []
    for i, name in enumerate(VESSEL_NAMES):
        mode = plan[i]
        cap = int(rng.integers(30, 86) * 100)
        v = {"name": name, "capacity": cap, "mode": mode, "speed_kn": round(float(rng.uniform(9.5, 12.5)), 1),
             "types": ["PCC", "OPC"] if rng.random() < 0.7 else ["PCC"], "dest": None, "progress": None,
             "cargo": 0, "cargo_type": None}
        if mode == "laden":
            v["dest"] = laden_targets.pop(0)
            v["progress"] = float(rng.uniform(0.2, 0.8))
            v["cargo"] = int(cap * rng.uniform(0.9, 1.0))
            v["cargo_type"] = "PCC"
        elif mode == "ballast":
            v["origin"] = PLANTS[int(rng.integers(0, 9))]["id"]
            v["progress"] = float(rng.uniform(0.2, 0.9))
        elif mode == "discharging":
            v["dest"] = discharge_at.pop(0)
            v["cargo"] = int(cap * 0.5)
            v["cargo_type"] = "PCC"
        vessels.append(v)
    # The demo narrative needs these two named ships (proposal example: Ship N and Ship M).
    for v in vessels:
        if v["name"] == "Ship N":
            v.update(mode="loading", capacity=7500, types=["PCC", "OPC"], speed_kn=11.8)
        if v["name"] == "Ship M":
            v.update(mode="anchored", capacity=5200, types=["PCC", "OPC"], speed_kn=10.9)
    return vessels


def _position(v):
    lp = (LOAD_PORT["lat"], LOAD_PORT["lon"])
    pj = (OTHER_PORTS[0]["lat"], OTHER_PORTS[0]["lon"])
    pk = (OTHER_PORTS[1]["lat"], OTHER_PORTS[1]["lon"])
    plant = {p["id"]: (p["lat"], p["lon"]) for p in PLANTS}
    m = v["mode"]
    if m == "laden":
        return interpolate(lp, plant[v["dest"]], v["progress"])
    if m == "ballast":
        return interpolate(plant[v["origin"]], lp, v["progress"])
    if m == "loading":
        return lp
    if m == "discharging":
        return plant[v["dest"]]
    if m == "anchored":
        return pk
    return pj


# ----------------------------------------------------------------- manufacturer
def _sales_history():
    rng = _rng(2)
    end = now_hour().date() - timedelta(days=1)
    dates = pd.date_range(end=end, periods=HISTORY_DAYS, freq="D")
    rows = []
    for p in PLANTS:
        for ctype in sorted(set(p["silos"])):
            base = rng.uniform(380, 820) if ctype == "PCC" else rng.uniform(90, 210)
            trend = rng.uniform(-0.0002, 0.0006)
            for i, d in enumerate(dates):
                dow = [1.05, 1.08, 1.06, 1.04, 1.02, 0.92, 0.55][d.dayofweek]
                season = 1 - 0.12 * math.cos(2 * math.pi * (d.dayofyear - 200) / 365)  # wet season dip
                y = base * dow * season * (1 + trend * i) * rng.normal(1, 0.08)
                rows.append({"date": d.date().isoformat(), "plant_id": p["id"], "cement_type": ctype,
                             "sales_ton": round(max(0.0, y), 1)})
    return pd.DataFrame(rows)


def generate_manufacturer():
    rng = _rng(3)
    eng = engine("manufacturer")
    sales = _sales_history()
    sales.to_sql("sales_history", eng, index=False, if_exists="replace")

    plants, silos, levels, sop = [], [], [], []
    today = now_hour().date()
    recent = sales[sales["date"] >= (today - timedelta(days=28)).isoformat()]
    mean_demand = recent.groupby(["plant_id", "cement_type"])["sales_ton"].mean().to_dict()
    target_pct = {"PP C": 0.33, "PP F": 0.52, "PP G": 0.40, "PP I": 0.45}
    for p in PLANTS:
        plants.append({"plant_id": p["id"], "region": p["region"], "lat": p["lat"], "lon": p["lon"],
                       "selling_price_idr_ton": int(rng.integers(115, 162) * 10000),
                       "contribution_margin_idr_ton": int(rng.integers(18, 42) * 10000),
                       "berth_draft_m": round(float(rng.uniform(6, 11)), 1)})
        type_count = {t: p["silos"].count(t) for t in set(p["silos"])}
        for j, ctype in enumerate(p["silos"]):
            cap = int(rng.integers(30, 61) * 100) if ctype == "PCC" else int(rng.integers(15, 26) * 100)
            level = target_pct.get(p["id"], 0.6) if ctype == "PCC" else float(rng.uniform(0.6, 0.8))
            level = level if p["id"] in target_pct or ctype == "OPC" else float(rng.uniform(0.38, 0.8))
            level = level + float(rng.uniform(-0.03, 0.03))
            sid = f"{p['id'].replace(' ', '')}-S{j + 1}"
            silos.append({"silo_id": sid, "plant_id": p["id"], "cement_type": ctype, "capacity_ton": cap,
                          "dead_stock_ton": round(cap * DEAD_STOCK_PCT, 1), "level_pct": round(level, 4),
                          "sensor": "IIoT level transmitter (simulated)",
                          "last_reading": now_hour().isoformat()})
            # Backward-reconstructed 60-day level history (sawtooth with deliveries).
            outflow = mean_demand[(p["id"], ctype)] / type_count[ctype]
            lvl = level * cap
            for d in range(60):
                day = today - timedelta(days=d)
                levels.append({"silo_id": sid, "date": day.isoformat(), "level_pct": round(lvl / cap, 4)})
                lvl += outflow * float(rng.normal(1, 0.1))
                if lvl > 0.92 * cap:
                    lvl -= 0.55 * cap
        for ctype in sorted(set(p["silos"])):
            for m in range(3):
                month = (pd.Timestamp(today).to_period("M") + m).strftime("%Y-%m")
                sop.append({"month": month, "plant_id": p["id"], "cement_type": ctype,
                            "planned_sales_ton": round(mean_demand[(p["id"], ctype)] * 30 * rng.uniform(1.0, 1.08))})
    pd.DataFrame(plants).to_sql("packing_plants", eng, index=False, if_exists="replace")
    pd.DataFrame(silos).to_sql("silos", eng, index=False, if_exists="replace")
    pd.DataFrame(levels).to_sql("silo_level_history", eng, index=False, if_exists="replace")
    pd.DataFrame(sop).to_sql("sop_plan", eng, index=False, if_exists="replace")

    incoming = []
    for v in world():
        if v["mode"] == "laden":
            dist = sea_distance_nm((LOAD_PORT["lat"], LOAD_PORT["lon"]),
                                   (next(p for p in PLANTS if p["id"] == v["dest"])["lat"],
                                    next(p for p in PLANTS if p["id"] == v["dest"])["lon"]))
            eta_h = dist * (1 - v["progress"]) / v["speed_kn"]
            incoming.append({"plant_id": v["dest"], "cement_type": v["cargo_type"], "vessel": v["name"],
                             "quantity_ton": v["cargo"], "eta": (now_hour() + timedelta(hours=eta_h)).isoformat(),
                             "status": "in transit", "source": "shipping voyage"})
    pd.DataFrame(incoming).to_sql("incoming_deliveries", eng, index=False, if_exists="replace")
    pd.DataFrame([{"cement_type": "PCC", "available_ton": 52000}, {"cement_type": "OPC", "available_ton": 14000}]
                 ).to_sql("load_port_stock", eng, index=False, if_exists="replace")
    pd.DataFrame([{"key": "production_capacity_factor", "value": 1.0},
                  {"key": "demand_multiplier_PP F", "value": 1.0}]).to_sql("settings", eng, index=False, if_exists="replace")


# ----------------------------------------------------------------- shipping
def generate_shipping():
    rng = _rng(4)
    store = STORES / "shipping"
    store.mkdir(parents=True, exist_ok=True)
    now = now_hour()
    fleet = world()
    plant_xy = {p["id"]: (p["lat"], p["lon"]) for p in PLANTS}
    lp = (LOAD_PORT["lat"], LOAD_PORT["lon"])

    vessels = []
    for v in fleet:
        lat, lon = _position(v)
        age_h = float(rng.uniform(0.1, 3.0)) if rng.random() > 0.15 else float(rng.uniform(7, 14))
        sailing = v["mode"] in ("laden", "ballast")
        if sailing:
            a, b = (lp, plant_xy[v["dest"]]) if v["mode"] == "laden" else (plant_xy[v["origin"]], lp)
            leg = sea_distance_nm(a, b)
        heading = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360 if sailing else 0
        track = []
        for h in range(23, -1, -1):  # hourly GPS pings for the last 24 h (IIoT gateway, simulated)
            if sailing:
                plat, plon = interpolate(a, b, max(0.0, v["progress"] - v["speed_kn"] * h / leg))
                spd = v["speed_kn"] * float(rng.normal(1, 0.06))
            else:
                plat, plon = lat + float(rng.normal(0, 0.002)), lon + float(rng.normal(0, 0.002))
                spd = abs(float(rng.normal(0.3, 0.2)))
            track.append({"ts": (now - timedelta(hours=h + age_h)).isoformat(), "lat": round(plat, 5),
                          "lon": round(plon, 5), "speedKn": round(spd, 2)})
        doc = {
            "_id": v["name"].replace(" ", "").lower(), "vesselName": v["name"],
            "spec": {"capacityTon": v["capacity"], "serviceSpeedKn": v["speed_kn"], "cementTypes": v["types"],
                     "builtYear": int(rng.integers(2004, 2021))},
            "position": {"lat": round(lat, 5), "lon": round(lon, 5), "speedKn": track[-1]["speedKn"],
                         "headingDeg": round(heading), "lastPingAt": (now - timedelta(hours=age_h)).isoformat()},
            "gpsTrack": track,
            "operation": {"mode": v["mode"], "destination": v.get("dest") or ("Load Port" if v["mode"] == "ballast" else None),
                          "progress": v["progress"], "cargoTon": v["cargo"], "cargoType": v["cargo_type"],
                          "delayHours": 0, "assignedPlant": None},
            "engine": {"temperatureC": round(float(rng.normal(82, 5)), 1), "vibrationMmS": round(float(rng.gamma(4, 0.8)), 2),
                       "runningHoursSinceService": int(rng.integers(300, 5200))},
            "maintenance": {"status": "in maintenance" if v["mode"] == "maintenance" else "operational",
                            "nextServiceDue": (now + timedelta(days=int(rng.integers(5, 120)))).date().isoformat()},
            "commercial": {"charterRateUsdDay": int(rng.integers(45, 95)) * 100, "crew": int(rng.integers(14, 22))},
        }
        vessels.append(doc)
    for d in vessels:  # Ship N carries the most proven calls to PP C in history (demo narrative)
        if d["vesselName"] == "Ship M":
            d["engine"].update(temperatureC=81.0, vibrationMmS=2.4, runningHoursSinceService=900)

    # 282 historical voyages with 2,202 voyage events, 199 of them equipment delays.
    voyages = []
    names = [v["name"] for v in fleet]
    eq_set = set(int(x) for x in rng.choice(282, 199, replace=False))
    base_events = ["loading", "departure", "arrival", "berthing", "discharge", "departure-plant",
                   "weather delay", "port congestion"]
    for i in range(282):
        name = names[int(rng.integers(0, 19))] if i % 7 else "Ship N"
        plant = PLANTS[int(rng.integers(0, 9))]["id"] if i % 5 else "PP C"
        dist = sea_distance_nm(lp, plant_xy[plant])
        spd = float(rng.uniform(8.8, 12.4))
        wave = float(rng.gamma(2.2, 0.55))
        cargo = int(rng.integers(30, 86) * 100)
        wait = float(rng.gamma(2, 3))
        dur = dist / spd * (1 + 0.06 * max(0, wave - 1.0)) + wait * 0.4 + cargo / 4000 + float(rng.normal(0, 2.5))
        dep = now - timedelta(days=540) + timedelta(days=i * 1.9 + float(rng.uniform(0, 1)))
        types = base_events[:8 if i < 228 else 7]  # 228*8 + 54*7 = 2,202 events
        if i in eq_set:  # 199 equipment delays
            types = types[:-1] + ["equipment delay"]
        events = [{"type": t, "hours": round(float(rng.uniform(1, 8)), 1)} for t in types]
        planned = dist / 11.0 + 6
        voyages.append({"_id": f"V{i + 1:04d}", "vesselName": name, "fromPort": "Load Port", "toPlant": plant,
                        "departedAt": dep.isoformat(), "arrivedAt": (dep + timedelta(hours=dur)).isoformat(),
                        "distanceNm": round(dist, 1), "avgSpeedKn": round(spd, 2), "avgWaveM": round(wave, 2),
                        "cargoTon": cargo, "durationHours": round(dur, 2), "plannedHours": round(planned, 2),
                        "onTime": dur <= planned * 1.1, "events": events})

    # Marine weather: 91 route points (10 per plant route + load port), 6-hourly for 72 h.
    weather_points = [{"pointId": "WP-LP", "route": "Load Port", "lat": lp[0], "lon": lp[1]}]
    for p in PLANTS:
        for k in range(1, 11):
            la, lo = interpolate(lp, plant_xy[p["id"]], k / 10)
            weather_points.append({"pointId": f"WP-{p['id'][-1]}{k:02d}", "route": p["id"], "lat": round(la, 3), "lon": round(lo, 3)})
    for wp in weather_points:
        base = min(1.7, float(rng.gamma(2.0, 0.4)) + (0.2 if wp["lon"] > 122 else 0))
        wp["forecast"] = [{"ts": (now + timedelta(hours=6 * s)).isoformat(),
                           "waveHeightM": round(max(0.2, base + float(rng.normal(0, 0.15))), 2),
                           "windKn": round(max(2.0, 8 + base * 6 + float(rng.normal(0, 2))), 1)} for s in range(13)]
        wp["source"] = "synthetic (Open-Meteo Marine API ready)"
    for name, data in {"vessels": vessels, "voyages": voyages, "weather": weather_points,
                       "assignments": []}.items():
        Collection(name).save(data)


# ----------------------------------------------------------------- distribution
def generate_distribution():
    rng = _rng(5)
    STORES.mkdir(parents=True, exist_ok=True)
    db = STORES / "distribution.db"
    db.unlink(missing_ok=True)
    con = sqlite3.connect(db)
    con.executescript("""
      CREATE TABLE region (region_code TEXT PRIMARY KEY, region_name TEXT, served_by_plant TEXT);
      CREATE TABLE distributor (dist_code TEXT PRIMARY KEY, dist_name TEXT, region_code TEXT,
                                stock_bags INTEGER, safety_stock_bags INTEGER, daily_offtake_bags INTEGER);
      CREATE TABLE sales_order (order_no TEXT PRIMARY KEY, dist_code TEXT, qty_bags INTEGER,
                                order_date TEXT, due_date TEXT, status TEXT, fulfilled_bags INTEGER);
      CREATE TABLE regional_demand (region_code TEXT, week TEXT, demand_bags INTEGER);
    """)
    today = now_hour().date()
    for i, p in enumerate(PLANTS):
        rc = f"R{i + 1:02d}"
        con.execute("INSERT INTO region VALUES (?,?,?)", (rc, p["region"], p["id"]))
        for w in range(12):
            con.execute("INSERT INTO regional_demand VALUES (?,?,?)",
                        (rc, (today - timedelta(weeks=11 - w)).isoformat(), int(rng.integers(60, 140) * 1000)))
        for j in range(2):
            dc = f"D{i + 1:02d}{j + 1}"
            offt = int(rng.integers(8, 22) * 100)
            con.execute("INSERT INTO distributor VALUES (?,?,?,?,?,?)",
                        (dc, f"Distributor {p['region']} {j + 1}", rc, int(offt * rng.uniform(2, 9)), offt * 3, offt))
            for k in range(4):
                od = today - timedelta(days=int(rng.integers(0, 10)))
                status = ["open", "open", "partially fulfilled", "fulfilled"][int(rng.integers(0, 4))]
                qty = int(rng.integers(20, 90) * 100)
                ful = qty if status == "fulfilled" else (qty // 2 if status.startswith("partial") else 0)
                con.execute("INSERT INTO sales_order VALUES (?,?,?,?,?,?,?)",
                            (f"SO-{dc}-{k + 1}", dc, qty, od.isoformat(), (od + timedelta(days=5)).isoformat(), status, ful))
    con.commit()
    con.close()


# ----------------------------------------------------------------- supplier
def generate_supplier():
    rng = _rng(6)
    store = STORES / "supplier"
    store.mkdir(parents=True, exist_ok=True)
    materials = [("RM-CLK", "Clinker", 4200), ("RM-GYP", "Gypsum", 210), ("RM-LMS", "Limestone", 5200),
                 ("RM-FLY", "Fly ash", 650), ("RM-COL", "Coal", 900), ("PK-BAG", "Kraft paper bag (k pcs)", 160)]
    suppliers = [("SUP-01", "Supplier Alpha", "RM-CLK"), ("SUP-02", "Supplier Beta", "RM-CLK"),
                 ("SUP-03", "Supplier Gamma", "RM-GYP"), ("SUP-04", "Supplier Delta", "RM-GYP"),
                 ("SUP-05", "Supplier Epsilon", "RM-FLY"), ("SUP-06", "Supplier Zeta", "RM-COL"),
                 ("SUP-07", "Supplier Eta", "PK-BAG"), ("SUP-08", "Supplier Theta", "RM-LMS")]
    with open(store / "materials.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["MATERIAL_CODE", "MATERIAL_DESC", "DAILY_USE_QTY", "ON_HAND_QTY", "SAFETY_DAYS"])
        for code, desc, use in materials:
            w.writerow([code, desc, use, int(use * rng.uniform(12, 30)), 7])
    with open(store / "suppliers.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["SUPPLIER_ID", "SUPPLIER_NAME", "MATERIAL_CODE", "CAPACITY_PER_DAY", "AVAILABILITY_PCT",
                    "OTIF_PCT", "LEAD_TIME_DAYS", "RISK_FLAG"])
        for sid, name, mat in suppliers:
            use = next(m[2] for m in materials if m[0] == mat)
            share = 0.35 if sid == "SUP-02" else float(rng.uniform(1.0, 1.3))  # SUP-02 = small backup clinker source
            w.writerow([sid, name, mat, int(use * share), 100, round(float(rng.uniform(82, 98)), 1),
                        int(rng.integers(2, 9)), "normal"])
    with open(store / "purchase_orders.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["PO_NO", "SUPPLIER_ID", "MATERIAL_CODE", "QTY", "PO_DATE", "DUE_DATE", "STATUS"])
        today = now_hour().date()
        for i in range(40):
            sid, _, mat = suppliers[int(rng.integers(0, len(suppliers)))]
            od = today - timedelta(days=int(rng.integers(0, 30)))
            w.writerow([f"PO-{i + 1:04d}", sid, mat, int(rng.integers(5, 40) * 100), od.isoformat(),
                        (od + timedelta(days=int(rng.integers(3, 14)))).isoformat(),
                        ["open", "in transit", "received", "received", "late"][int(rng.integers(0, 5))]])
    # The CSV files are the ERP export; the supplier API serves them from its own PostgreSQL database.
    for name in ("materials", "suppliers", "purchase_orders"):
        pd.read_csv(store / f"{name}.csv").to_sql(name, engine("supplier"), index=False, if_exists="replace")


GENERATORS = {"manufacturer": generate_manufacturer, "shipping": generate_shipping,
              "distribution": generate_distribution, "supplier": generate_supplier}

if __name__ == "__main__":
    for name, fn in GENERATORS.items():
        fn()
        print("generated", name)
