---
name: add-scenario
description: Menambah skenario simulasi baru ke Simulation Center Manufacturing Agentic System (event injection ke API enterprise, agent yang aktif, dampak KPI). Gunakan saat diminta menambah atau mengubah skenario disrupsi.
---
# Menambah skenario

1. Tambah event injection di API enterprise terkait: `POST /events/<nama>` dengan scope `simulate`.
2. Daftarkan skenario di `SCENARIOS` pada `backend/global_orchestrator/main.py`: `title`, `description`, `inject` (daftar `(enterprise, path, body)`), `replan` (bool).
3. Orchestrator otomatis: snapshot KPI awal, inject event, jalankan pipeline (4 worker paralel, agent ekstensi bila relevan, Dispatch Planner, Narrator), buat keputusan berstatus `Requires human approval`, snapshot KPI akhir.
4. UI tidak perlu diubah: Simulation Center membaca daftar dari `GET /scenarios`.
5. Tambahkan skenario ke `scripts/smoke_test.py` dan `docs/demo-script.md`.
