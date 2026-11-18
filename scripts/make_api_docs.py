"""Write docs/api.md from the live OpenAPI schemas (stack must be running): python scripts/make_api_docs.py"""
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from shared.config import API_KEYS, SERVICES, url  # noqa: E402

out = ["# Dokumentasi API", "",
       "Dokumen ini dihasilkan dari skema OpenAPI setiap layanan (`python scripts/make_api_docs.py`). "
       "Dokumentasi interaktif tersedia di `http://localhost:<port>/docs` selama stack menyala.", "",
       "## Autentikasi", "",
       "Endpoint enterprise membutuhkan header `X-API-Key` (simulasi autentikasi). Setiap kunci dipetakan ke satu principal, "
       "dan setiap enterprise menentukan scope principal itu dalam kebijakan G_i (`GET /governance`). "
       "Kunci yang tidak dikenal menghasilkan 401; scope yang tidak dimiliki menghasilkan 403.", "",
       "| Kunci (simulasi) | Principal |", "|---|---|"]
out += [f"| `{k}` | {v} |" for k, v in API_KEYS.items()]
out += ["", "Global Orchestrator tidak memakai API key dari dashboard; peran pengguna dikirim di badan permintaan "
        "(`{\"role\": \"Manufacturer Manager\"}`) untuk aksi yang dibatasi (menjalankan skenario, menyetujui keputusan).", "",
        "## Contoh", "", "```bash",
        "curl -X POST localhost:8000/scenarios/low_stock/run -H 'content-type: application/json' -d '{\"role\":\"Global Administrator\"}'",
        "curl localhost:8000/runs/<run_id>",
        "curl -X POST localhost:8000/decisions/<decision_id>/approve -H 'content-type: application/json' -d '{\"role\":\"Manufacturer Manager\"}'",
        "curl localhost:8001/plants -H 'X-API-Key: key-global-orchestrator'",
        "curl localhost:8001/marketing/prices -H 'X-API-Key: key-global-orchestrator'   # 403: margin tidak dibagikan",
        "curl -X POST localhost:8002/agents/fleet-tracking/run -H 'X-API-Key: key-global-orchestrator'",
        "```", ""]
for key, meta in SERVICES.items():
    spec = httpx.get(url(key) + "/openapi.json", timeout=30).json()
    out += [f"## {spec['info']['title']} (port {meta['port']})", "", spec["info"].get("description", ""), "",
            "| Metode | Path | Kelompok | Ringkasan |", "|---|---|---|---|"]
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            out.append(f"| {method.upper()} | `{path}` | {', '.join(op.get('tags', [])) or 'platform'} | {op.get('summary', '')} |")
    out.append("")
(ROOT / "docs" / "api.md").write_text("\n".join(out), encoding="utf-8")
print("wrote docs/api.md")
