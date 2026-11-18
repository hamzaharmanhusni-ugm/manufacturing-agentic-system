# Dokumentasi API

Dokumen ini dihasilkan dari skema OpenAPI setiap layanan (`python scripts/make_api_docs.py`). Dokumentasi interaktif tersedia di `http://localhost:<port>/docs` selama stack menyala.

## Autentikasi

Endpoint enterprise membutuhkan header `X-API-Key` (simulasi autentikasi). Setiap kunci dipetakan ke satu principal, dan setiap enterprise menentukan scope principal itu dalam kebijakan G_i (`GET /governance`). Kunci yang tidak dikenal menghasilkan 401; scope yang tidak dimiliki menghasilkan 403.

| Kunci (simulasi) | Principal |
|---|---|
| `key-global-orchestrator` | global-orchestrator |
| `key-global-admin` | global-admin |
| `key-manufacturer-portal` | manufacturer-portal |
| `key-shipping-portal` | shipping-portal |
| `key-distribution-portal` | distribution-portal |
| `key-supplier-portal` | supplier-portal |

Global Orchestrator tidak memakai API key dari dashboard; peran pengguna dikirim di badan permintaan (`{"role": "Manufacturer Manager"}`) untuk aksi yang dibatasi (menjalankan skenario, menyetujui keputusan).

## Contoh

```bash
curl -X POST localhost:8000/scenarios/low_stock/run -H 'content-type: application/json' -d '{"role":"Global Administrator"}'
curl localhost:8000/runs/<run_id>
curl -X POST localhost:8000/decisions/<decision_id>/approve -H 'content-type: application/json' -d '{"role":"Manufacturer Manager"}'
curl localhost:8001/plants -H 'X-API-Key: key-global-orchestrator'
curl localhost:8001/marketing/prices -H 'X-API-Key: key-global-orchestrator'   # 403: margin tidak dibagikan
curl -X POST localhost:8002/agents/fleet-tracking/run -H 'X-API-Key: key-global-orchestrator'
```

## Global Orchestrator (port 8000)

Global Agentic Control Center: orchestration, dispatch planning, narration, approvals, KPIs.

| Metode | Path | Kelompok | Ringkasan |
|---|---|---|---|
| GET | `/health` | platform | Health |
| GET | `/ecosystem` | platform | Ecosystem |
| GET | `/overview` | platform | Overview |
| GET | `/agents` | platform | Agents |
| GET | `/messages` | platform | Messages |
| GET | `/scenarios` | platform | Scenarios |
| POST | `/scenarios/{key}/run` | platform | Run Scenario |
| GET | `/runs` | platform | Runs |
| GET | `/runs/{rid}` | platform | Get Run |
| GET | `/runs/latest/plan` | platform | Latest Plan |
| GET | `/decisions` | platform | Decisions |
| POST | `/decisions/{did}/{verdict}` | platform | Decide |
| GET | `/kpis` | platform | Kpis |
| GET | `/audit` | platform | Get Audit |
| GET | `/notifications` | platform | Notifications |
| GET | `/api-logs` | platform | Api Logs |
| GET | `/governance` | platform | Governance |
| POST | `/reset` | platform | Reset |
| POST | `/ask` | platform | Ask |
| GET | `/architecture` | platform | Architecture |

## Manufacturer API (Enterprise 1) (port 8001)

Cement manufacturer: Marketing + Operations. SYNTHETIC data.

| Metode | Path | Kelompok | Ringkasan |
|---|---|---|---|
| GET | `/health` | platform | Health |
| GET | `/logs` | platform | Logs |
| GET | `/governance` | platform | Governance |
| GET | `/plants` | operations | Plants |
| GET | `/silos` | operations | Silos |
| GET | `/silos/history` | operations | Silo History |
| GET | `/incoming` | operations | Incoming |
| POST | `/incoming` | execution | Add Incoming |
| GET | `/load-port` | operations | Load Port |
| GET | `/alerts` | operations | Alerts |
| GET | `/forecast` | marketing | Forecast |
| GET | `/forecast/metrics` | marketing | Forecast Metrics |
| GET | `/marketing/sales` | marketing | Sales |
| GET | `/marketing/sop` | marketing | Sop |
| GET | `/marketing/prices` | marketing | Prices |
| GET | `/marketing/priority-full` | marketing | Priority Full |
| POST | `/agents/stock-monitoring/run` | agents | Stock Monitoring |
| POST | `/agents/ml-forecasting/run` | agents | Ml Forecasting |
| POST | `/agents/demand-priority/run` | agents | Demand Priority |
| POST | `/events/silo-drop` | simulation | Silo Drop |
| POST | `/events/demand-surge` | simulation | Demand Surge |
| POST | `/events/production-cap` | simulation | Production Cap |
| POST | `/reset` | simulation | Reset |

## Shipping API (Enterprise 2) (port 8002)

Shipment subsidiary: fleet, voyages, ETA. SYNTHETIC data.

| Metode | Path | Kelompok | Ringkasan |
|---|---|---|---|
| GET | `/health` | platform | Health |
| GET | `/logs` | platform | Logs |
| GET | `/governance` | platform | Governance |
| GET | `/vessels` | fleet | Vessels |
| GET | `/vessels/internal` | fleet | Vessels Internal |
| GET | `/vessels/{name}/track` | fleet | Track |
| GET | `/voyages` | voyages | Voyages |
| GET | `/weather` | weather | Weather |
| GET | `/models` | models | Models |
| GET | `/assignments` | execution | Assignments |
| POST | `/assignments` | execution | Assign |
| POST | `/agents/fleet-tracking/run` | agents | Fleet Tracking |
| POST | `/events/vessel-delay` | simulation | Vessel Delay |
| POST | `/events/weather` | simulation | Weather Event |
| POST | `/reset` | simulation | Reset |

## Distribution API (Enterprise 3, prototype extension) (port 8003)

Regional distributors, orders, fulfillment. SYNTHETIC data, quantities in 50 kg bags.

| Metode | Path | Kelompok | Ringkasan |
|---|---|---|---|
| GET | `/health` | platform | Health |
| GET | `/logs` | platform | Logs |
| GET | `/governance` | platform | Governance |
| GET | `/regions` | inventory | Regions |
| GET | `/distributors` | inventory | Distributors |
| GET | `/orders` | orders | Orders |
| GET | `/demand` | demand | Demand |
| POST | `/agents/distribution/run` | agents | Distribution Agent |
| POST | `/events/order-surge` | simulation | Order Surge |
| POST | `/reset` | simulation | Reset |

## Supplier API (Enterprise 4, prototype extension) (port 8004)

Raw materials, suppliers, purchase orders. SYNTHETIC data, CSV store.

| Metode | Path | Kelompok | Ringkasan |
|---|---|---|---|
| GET | `/health` | platform | Health |
| GET | `/logs` | platform | Logs |
| GET | `/governance` | platform | Governance |
| GET | `/materials` | inventory | Materials |
| GET | `/suppliers` | suppliers | Suppliers |
| GET | `/purchase-orders` | procurement | Purchase Orders |
| POST | `/agents/procurement/run` | agents | Procurement Agent |
| POST | `/events/disruption` | simulation | Disruption |
| POST | `/reset` | simulation | Reset |
