"""Enterprise 3: Distribution API (port 8003). PROTOTYPE EXTENSION, not part of the original proposal.
Store: raw sqlite3. Units: 50 kg bags (the orchestrator converts to tons: 20 bags = 1 ton).
Agent hosted here: Distribution Agent (extension)."""
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from fastapi import Depends, FastAPI  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from data.generate import generate_distribution  # noqa: E402
from shared.config import STORES  # noqa: E402
from shared.security import setup  # noqa: E402

DB = STORES / "distribution.db"
if not DB.exists():
    generate_distribution()

ALL = {"read:shared", "read:internal", "agents", "simulate"}
POLICY = {"global-orchestrator": {"read:shared", "agents", "simulate"}, "global-admin": ALL,
          "distribution-portal": ALL, "manufacturer-portal": {"read:shared"}}
app = FastAPI(title="Distribution API (Enterprise 3, prototype extension)", version="1.0",
              description="Regional distributors, orders, fulfillment. SYNTHETIC data, quantities in 50 kg bags.")
require = setup(app, "distribution", POLICY)


def rows(sql, *args):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, args)]
    finally:
        con.close()


def execute(sql, *args):
    con = sqlite3.connect(DB)
    try:
        con.execute(sql, args)
        con.commit()
    finally:
        con.close()


REGION_SQL = """
SELECT r.region_code, r.region_name, r.served_by_plant,
       SUM(d.stock_bags) stock_bags, SUM(d.safety_stock_bags) safety_stock_bags, SUM(d.daily_offtake_bags) daily_offtake_bags,
       (SELECT COALESCE(SUM(o.qty_bags - o.fulfilled_bags),0) FROM sales_order o JOIN distributor d2 USING(dist_code)
          WHERE d2.region_code = r.region_code AND o.status != 'fulfilled') open_order_bags,
       (SELECT ROUND(1.0*SUM(o.fulfilled_bags)/SUM(o.qty_bags),3) FROM sales_order o JOIN distributor d2 USING(dist_code)
          WHERE d2.region_code = r.region_code) fill_rate
FROM region r JOIN distributor d USING(region_code) GROUP BY r.region_code"""


@app.get("/regions", tags=["inventory"])
def regions(_=Depends(require("read:shared"))):
    out = rows(REGION_SQL)
    for r in out:
        r["days_of_stock"] = round(r["stock_bags"] / r["daily_offtake_bags"], 1)
        r["below_safety"] = r["stock_bags"] < r["safety_stock_bags"]
    return out


@app.get("/distributors", tags=["inventory"])
def distributors(_=Depends(require("read:internal"))):
    return rows("SELECT * FROM distributor")


@app.get("/orders", tags=["orders"])
def orders(_=Depends(require("read:shared"))):
    return rows("SELECT o.*, d.region_code FROM sales_order o JOIN distributor d USING(dist_code) ORDER BY order_date DESC")


@app.get("/demand", tags=["demand"])
def demand(_=Depends(require("read:shared"))):
    return rows("SELECT * FROM regional_demand ORDER BY week")


@app.post("/agents/distribution/run", tags=["agents"])
def distribution_agent(_=Depends(require("agents"))):
    t0 = time.perf_counter()
    reg = regions()
    at_risk = [r for r in reg if r["below_safety"] or r["days_of_stock"] < 3 or (r["fill_rate"] or 1) < 0.5]
    signals = [{"plant_id": r["served_by_plant"], "region": r["region_name"],
                "open_order_ton": round(r["open_order_bags"] / 20, 1), "days_of_stock": r["days_of_stock"]} for r in at_risk]
    return {"agent": "Distribution Agent (extension)", "enterprise": "distribution", "status": "Completed",
            "inputs": {"regions": len(reg), "unit": "bags (50 kg)"},
            "outputs": {"regions": reg, "regions_at_risk": signals},
            "log": [f"Checked {len(reg)} regions, 18 distributors", f"{len(at_risk)} regions below safety stock or low fill rate",
                    "Converted bags to tons for the orchestrator (20 bags = 1 t)"],
            "duration_ms": round((time.perf_counter() - t0) * 1000, 1)}


class OrderSurge(BaseModel):
    plant_id: str = "PP F"
    factor: float = 1.8


@app.post("/events/order-surge", tags=["simulation"])
def order_surge(e: OrderSurge, _=Depends(require("simulate"))):
    execute("UPDATE distributor SET daily_offtake_bags = CAST(daily_offtake_bags * ? AS INTEGER), stock_bags = CAST(stock_bags / ? AS INTEGER) "
            "WHERE region_code IN (SELECT region_code FROM region WHERE served_by_plant = ?)", e.factor, e.factor, e.plant_id)
    execute("UPDATE sales_order SET qty_bags = CAST(qty_bags * ? AS INTEGER), status = CASE status WHEN 'fulfilled' THEN 'partially fulfilled' ELSE status END "
            "WHERE dist_code IN (SELECT dist_code FROM distributor d JOIN region r USING(region_code) WHERE r.served_by_plant = ?)", e.factor, e.plant_id)
    return {"ok": True, "event": "regional order surge", **e.model_dump()}


@app.post("/reset", tags=["simulation"])
def reset(_=Depends(require("simulate"))):
    generate_distribution()
    return {"ok": True}
