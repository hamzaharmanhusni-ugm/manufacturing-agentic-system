# Roadmap Checklist: Manufacturing Agentic System

Prototipe akademik **Global Manufacturing & Cement Supply Chain, Multi-Enterprise Agentic AI Decision Support System**.
Mata kuliah: AI Agentic Technology Systems for Digital Enterprise Ecosystem.

Status: `[x]` selesai, `[ ]` belum, `[~]` berjalan dalam mode simulasi.

> Catatan sumber: berkas `Agentic-AI-Cement-Distribution.pptx` dan `Agentic-AI-Cement-Supply-Chain-Management-ID.docx` belum tersedia di repositori ini. Arsitektur mengikuti spesifikasi tugas (7 agent, model ML, bobot SAW). Saat dokumen tersedia, bagian yang berbeda dicatat di `docs/architecture.md`.

## Fase 0. Persiapan tim agent pengembang
- [x] Agent Claude Code proyek (`.claude/agents/`): backend-api-builder, streamlit-dashboard-builder, decision-engine-auditor, demo-qa-tester
- [x] Skill proyek (`.claude/skills/`): run-mas-stack, saw-decision-engine, add-scenario

## Fase 1. Analisis dan arsitektur
- [x] Representasi enterprise `E_i = (U_i, M_i, D_i, A_i, P_i, G_i)` untuk 4 enterprise
- [x] Pola Orchestrator-Worker, 7 agent inti + 2 agent ekstensi (Distribution, Procurement)
- [x] Prinsip "Code decides, AI explains, people act"
- [x] Pemisahan: komponen proposal, komponen tambahan prototipe, data sintetis

## Fase 2. Struktur folder, skema, dan data sintetis
- [x] 9 packing plant (PP A sampai PP I), 22 silo, 19 kapal, 282 voyage historis
- [x] Riwayat penjualan 400 hari, rencana S&OP, harga jual, contribution margin
- [x] GPS ping, prakiraan cuaca, inventori distributor, inventori pemasok, purchase order
- [x] Relasi konsisten (silo milik plant, voyage merujuk kapal dan plant yang valid)

## Fase 3. Empat API enterprise independen
- [x] Manufacturer API :8001 (PostgreSQL di Docker melalui SQLAlchemy)
- [x] Shipping API :8002 (MongoDB di Docker, dokumen camelCase bersarang)
- [x] Distribution API :8003 (SQLite, SQL mentah, satuan sak 50 kg)
- [x] Supplier API :8004 (PostgreSQL di Docker, dimuat dari ekspor CSV ERP)
- [x] Mode cadangan tanpa Docker (`run_all.py --no-docker`): SQLite dan JSON lokal
- [x] Autentikasi API key per pemanggil, scope per kebijakan G_i, log request, health check

## Fase 4. Global Orchestrator dan kerangka agent
- [x] Global Orchestrator :8000 memanggil agent di setiap API melalui HTTP (A2A)
- [x] Eksekusi paralel 4 agent worker (ThreadPoolExecutor), log, durasi, input, output
- [x] Status agent: Idle, Running, Completed, Waiting for response, Failed, Requires human approval

## Fase 5. Decision engine dan model ML
- [x] SAW prioritas plant (0,35 / 0,20 / 0,20 / 0,15 / 0,10)
- [x] SAW ranking kapal (0,35 / 0,20 / 0,20 / 0,15 / 0,10)
- [x] LightGBM kuantil P10/P50/P90, horizon 14 hari, WAPE (dilatih pada data sintetis)
- [~] TFT challenger: mode simulasi (proksi seasonal-naive), bukan TFT terlatih
- [x] Random Forest ETA + rentang prediksi
- [x] ARIMA waktu stock-out silo
- [x] DBSCAN deteksi aktivitas kapal (sailing, anchored, berthed)

## Fase 6. Simulasi berbasis event
- [x] Skenario 1 Normal, 2 Low Stock PP C, 3 Demand Surge PP F
- [x] Skenario 4 Shipping Disruption (adaptive replanning + negosiasi)
- [x] Skenario 5 Weather Disruption (sailing not advised)
- [x] Skenario 6 Supplier Disruption
- [x] Tombol trigger dan reset, 7 bagian hasil per skenario

## Fase 7. Dashboard Streamlit end-to-end
- [x] Global Agentic Control Center (overview, peta ekosistem, monitoring, agent, timeline, decision center)
- [x] Dashboard Manufacturer, Shipping, Distribution, Supplier
- [x] Simulation Center dengan alur agent langsung
- [x] KPI dan Analytics (Before vs After AI, Normal vs Disruption, Original vs Adaptive)
- [x] Governance: RBAC, audit trail, log akses API, izin berbagi data
- [x] Arsitektur E_i per enterprise dan tabel heterogenitas

## Fase 8. Pengujian dan dokumentasi
- [x] Uji unit decision engine (SAW, days of cover)
- [x] Uji end-to-end: jalankan semua layanan, picu skenario, approve keputusan
- [x] README instalasi dan eksekusi, dokumentasi API (`docs/api.md` dan Swagger `/docs` setiap layanan)
- [x] Arsitektur (`docs/architecture.md`), panduan pengguna (`docs/user-guide.md`), peta kode agent (`docs/agent-code-map.svg`)
- [x] Presentasi kelas (`docs/presentation/`)
- [x] Skrip demo presentasi (`docs/demo-script.md`)

## Fase 8b. Redesign antarmuka
- [x] Agent desainer dan skill desain (impeccable): wawancara produk, undian arah visual, kontrak arah
- [x] Arah visual "Dispatch Manifest": run agent sebagai docket bernomor, ditandatangani agent, distempel manusia
- [x] Dua putaran review independen, detektor pola desain bersih, `DESIGN.md` dicatat dari build

## Fase 9. Repositori
- [x] Repositori GitHub publik
- [x] Branch `main` (aplikasi) dan `docs` (dokumentasi)

## Batasan yang disadari
- Semua data sintetis. Angka performa model tidak mewakili performa model nyata.
- TFT tidak dilatih (butuh PyTorch dan data nyata); ditampilkan sebagai mode simulasi.
- Narrator memakai template deterministik; LLM (Claude) aktif bila `ANTHROPIC_API_KEY` diisi, dan hanya merangkai angka yang sudah dihitung kode.
- Penyimpanan PostgreSQL/MongoDB diganti padanan lokal agar prototipe langsung berjalan; adapter siap ditukar.
