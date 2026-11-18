"""Shared reference data and service registry.

Reference data here (plant codes, coordinates, ports) is what every enterprise
agrees on, like a master-data contract. Operational data lives only inside each
enterprise's own store under data/stores/.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORES = ROOT / "data" / "stores"
SEED = 42

SERVICES = {
    "orchestrator": {"name": "Global Orchestrator", "port": 8000},
    "manufacturer": {"name": "Cement Manufacturing", "port": 8001},
    "shipping": {"name": "Shipping & Logistics", "port": 8002},
    "distribution": {"name": "Distribution", "port": 8003},
    "supplier": {"name": "Supplier & Procurement", "port": 8004},
}
ENTERPRISES = ["manufacturer", "shipping", "distribution", "supplier"]


def url(service: str) -> str:
    env = os.getenv(f"{service.upper()}_URL")
    return env or f"http://127.0.0.1:{SERVICES[service]['port']}"


# Simulated API keys (authentication simulation, not real secrets).
API_KEYS = {
    "key-global-orchestrator": "global-orchestrator",
    "key-global-admin": "global-admin",
    "key-manufacturer-portal": "manufacturer-portal",
    "key-shipping-portal": "shipping-portal",
    "key-distribution-portal": "distribution-portal",
    "key-supplier-portal": "supplier-portal",
}
ORCH_KEY = "key-global-orchestrator"

# Masked names as in the proposal: PP A-I, Port J-K, Ship letters.
LOAD_PORT = {"id": "LP", "name": "Load Port", "lat": -6.90, "lon": 112.05}
OTHER_PORTS = [
    {"id": "PJ", "name": "Port J (repair yard)", "lat": -7.20, "lon": 112.73},
    {"id": "PK", "name": "Port K (anchorage)", "lat": -6.75, "lon": 111.80},
]
# Synthetic locations of the nine packing plants (masked, illustrative coordinates).
PLANTS = [
    {"id": "PP A", "region": "Banten", "lat": -6.02, "lon": 105.95, "silos": ["PCC", "PCC", "OPC"]},
    {"id": "PP B", "region": "Jakarta", "lat": -6.10, "lon": 106.88, "silos": ["PCC", "OPC"]},
    {"id": "PP C", "region": "South Kalimantan", "lat": -3.33, "lon": 114.58, "silos": ["PCC", "PCC", "OPC"]},
    {"id": "PP D", "region": "South Sulawesi", "lat": -5.13, "lon": 119.41, "silos": ["PCC", "PCC"]},
    {"id": "PP E", "region": "East Kalimantan", "lat": -1.27, "lon": 116.82, "silos": ["PCC", "OPC", "PCC"]},
    {"id": "PP F", "region": "Bali", "lat": -8.19, "lon": 114.83, "silos": ["PCC", "PCC"]},
    {"id": "PP G", "region": "East Nusa Tenggara", "lat": -10.17, "lon": 123.58, "silos": ["PCC", "PCC"]},
    {"id": "PP H", "region": "North Sulawesi", "lat": 1.44, "lon": 125.19, "silos": ["PCC", "OPC", "PCC"]},
    {"id": "PP I", "region": "West Papua", "lat": -0.88, "lon": 131.25, "silos": ["PCC", "PCC"]},
]
PLANT_IDS = [p["id"] for p in PLANTS]
PLANT_BY_ID = {p["id"]: p for p in PLANTS}
VESSEL_NAMES = [f"Ship {c}" for c in "ABCDEFGHIJKLMNOPQRS"]  # 19 vessels

SEA_ROUTE_FACTOR = 1.15  # straight-line to sea-route distance (assumption)
LOW_STOCK_PCT = 0.25     # proposal: low stock event below 25 %
DEAD_STOCK_PCT = 0.08    # dead stock share of silo capacity (assumption)
WAVE_LIMIT_M = 2.5       # sailing not advised above this wave height (assumption)
FAILURE_RISK_WARN = 0.30 # Weibull 14-day failure risk warning threshold (assumption)
