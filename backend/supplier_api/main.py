"""Enterprise 4: Supplier & Procurement API (port 8004). PROTOTYPE EXTENSION, not part of the original proposal.
Store: PostgreSQL (Docker) loaded from ERP-export CSV files, UPPER_SNAKE columns.
Agent hosted here: Procurement Agent (extension)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd  # noqa: E402
from fastapi import Depends, FastAPI  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from data.generate import generate_supplier  # noqa: E402
from shared.stores import engine as get_engine  # noqa: E402
from sqlalchemy import inspect  # noqa: E402
from shared.security import setup  # noqa: E402

engine = get_engine("supplier")  # separate PostgreSQL database in Docker
if not inspect(engine).has_table("suppliers"):
    generate_supplier()

ALL = {"read:shared", "read:internal", "agents", "simulate"}
POLICY = {"global-orchestrator": {"read:shared", "agents", "simulate"}, "global-admin": ALL,
          "supplier-portal": ALL, "manufacturer-portal": {"read:shared"}}
app = FastAPI(title="Supplier API (Enterprise 4, prototype extension)", version="1.0",
              description="Raw materials, suppliers, purchase orders. SYNTHETIC data, CSV store.")
require = setup(app, "supplier", POLICY)
CRITICAL = {"RM-CLK", "RM-GYP"}  # without clinker or gypsum the mill cannot produce cement


def csv(name):
    return pd.read_sql_table(name, engine)


def supply_view():
    mats, sups = csv("materials"), csv("suppliers")
    out = []
    for m in mats.itertuples():
        s = sups[sups.MATERIAL_CODE == m.MATERIAL_CODE]
        avail = float((s.CAPACITY_PER_DAY * s.AVAILABILITY_PCT / 100).sum())
        inflow_ratio = min(1.0, avail / m.DAILY_USE_QTY) if m.DAILY_USE_QTY else 1.0
        net_burn = m.DAILY_USE_QTY * (1 - inflow_ratio) or 1e-9
        dos = m.ON_HAND_QTY / net_burn if inflow_ratio < 1 else 999
        out.append({"material_code": m.MATERIAL_CODE, "material": m.MATERIAL_DESC, "on_hand": int(m.ON_HAND_QTY),
                    "daily_use": int(m.DAILY_USE_QTY), "supply_coverage": round(inflow_ratio, 3),
                    "days_of_supply": round(min(dos, 999), 1), "critical": m.MATERIAL_CODE in CRITICAL,
                    "risk": "high" if dos < m.SAFETY_DAYS else ("medium" if dos < 3 * m.SAFETY_DAYS else "low")})
    return out


@app.get("/materials", tags=["inventory"])
def materials(_=Depends(require("read:shared"))):
    return supply_view()


@app.get("/suppliers", tags=["suppliers"])
def suppliers(_=Depends(require("read:shared"))):
    return csv("suppliers").to_dict("records")


@app.get("/purchase-orders", tags=["procurement"])
def purchase_orders(_=Depends(require("read:internal"))):
    return csv("purchase_orders").to_dict("records")


@app.post("/agents/procurement/run", tags=["agents"])
def procurement_agent(_=Depends(require("agents"))):
    t0 = time.perf_counter()
    view, sups = supply_view(), csv("suppliers")
    alternatives, impact = [], None
    for m in view:
        if m["risk"] == "high" or m["supply_coverage"] < 0.9:
            s = sups[sups.MATERIAL_CODE == m["material_code"]].sort_values(["AVAILABILITY_PCT", "OTIF_PCT"], ascending=False)
            alternatives.append({"material": m["material"], "disrupted": s[s.RISK_FLAG == "disrupted"].SUPPLIER_NAME.tolist(),
                                 "recommended_alternative": s[s.RISK_FLAG != "disrupted"].SUPPLIER_NAME.head(1).tolist(),
                                 "days_of_supply": m["days_of_supply"]})
    crit = [m for m in view if m["critical"]]
    worst = min(crit, key=lambda m: m["supply_coverage"])
    if worst["supply_coverage"] < 0.9:
        # Production can run only as fast as the scarcest critical material allows (after stock buffer).
        impact = {"material": worst["material"], "production_capacity_factor": round(max(0.4, worst["supply_coverage"] + 0.15), 2),
                  "days_of_supply": worst["days_of_supply"]}
    log = [f"Evaluated {len(view)} materials and {len(sups)} suppliers",
           f"{len(alternatives)} materials need alternative sourcing",
           f"Ecosystem impact: production capacity factor {impact['production_capacity_factor']}" if impact else "No production impact"]
    return {"agent": "Procurement Agent (extension)", "enterprise": "supplier", "status": "Completed",
            "inputs": {"materials": len(view), "suppliers": len(sups)},
            "outputs": {"materials": view, "alternatives": alternatives, "production_impact": impact},
            "log": log, "duration_ms": round((time.perf_counter() - t0) * 1000, 1)}


class Disruption(BaseModel):
    supplier_id: str = "SUP-01"
    availability_pct: float = 30


@app.post("/events/disruption", tags=["simulation"])
def disruption(e: Disruption, _=Depends(require("simulate"))):
    s = csv("suppliers")
    s.loc[s.SUPPLIER_ID == e.supplier_id, ["AVAILABILITY_PCT", "RISK_FLAG"]] = [e.availability_pct, "disrupted"]
    s.to_sql("suppliers", engine, index=False, if_exists="replace")
    return {"ok": True, "event": "supplier disruption", **e.model_dump()}


@app.post("/reset", tags=["simulation"])
def reset(_=Depends(require("simulate"))):
    generate_supplier()
    return {"ok": True}
