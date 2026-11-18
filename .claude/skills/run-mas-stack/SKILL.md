---
name: run-mas-stack
description: Menjalankan, menghentikan, dan memeriksa seluruh stack Manufacturing Agentic System (4 API enterprise, Global Orchestrator, Streamlit). Gunakan saat diminta "jalankan aplikasi", "start semua service", "cek health", atau sebelum demo.
---
# Menjalankan stack

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # sekali saja
.venv/Scripts/python run_all.py                 # 5 API + Streamlit di :3000
.venv/Scripts/python run_all.py --no-ui         # hanya API
```

| Layanan | Port | Swagger |
|---|---|---|
| Global Orchestrator | 8000 | http://localhost:8000/docs |
| Manufacturer API | 8001 | http://localhost:8001/docs |
| Shipping API | 8002 | http://localhost:8002/docs |
| Distribution API | 8003 | http://localhost:8003/docs |
| Supplier API | 8004 | http://localhost:8004/docs |
| Streamlit | 3000 | http://localhost:3000 |

- Cek cepat: `curl localhost:8000/ecosystem` harus menampilkan 4 enterprise `online`.
- Data dibuat dari seed saat store kosong; `POST localhost:8000/reset` mengembalikan semua enterprise ke kondisi awal.
- Uji end-to-end: `.venv/Scripts/python scripts/smoke_test.py`.
- Tampilan lokal: buka http://localhost:3000 lewat Playwright untuk screenshot demo.
