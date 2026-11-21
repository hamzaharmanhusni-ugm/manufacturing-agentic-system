# Proses Agentic Coding

Dokumen ini mencatat bagaimana prototipe dibangun dengan bantuan sistem agentic, yaitu Claude Code (model Claude Opus) sebagai *coding agent* utama yang mengatur sejumlah subagent, skill, dan alat. Proses ini sendiri merupakan contoh penerapan materi kuliah: agen yang memiliki tujuan, menggunakan tools, bekerja dalam feedback loop, berkolaborasi dalam pola orchestrator-worker, dan tetap berada di bawah kendali manusia.

## 1. Peran

| Peran | Pelaku | Tanggung jawab |
|---|---|---|
| Pemilik produk (manusia) | Mahasiswa | Memberi brief tugas dan proposal, menjawab pertanyaan keputusan, menghentikan atau melanjutkan pekerjaan, menyetujui tindakan publik (repositori publik, login layanan) |
| Coding agent utama | Claude Code | Merencanakan, menulis kode, menjalankan dan menguji layanan, mendelegasikan pekerjaan ke subagent, melaporkan hasil |
| Subagent spesialis | Agen Claude terpisah dengan konteks sendiri | Riset API publik, pengunduhan referensi desain, desain antarmuka, review independen, pencatatan sistem desain, pembuatan presentasi |
| Alat (tools) | Shell, editor berkas, Playwright, browser aplikasi, Docker, GitHub CLI | Tindakan nyata terhadap lingkungan pengembangan |

## 2. Urutan kerja

| Tahap | Yang dikerjakan agen | Bukti di repositori |
|---|---|---|
| Memahami tugas | Membaca brief dan dua dokumen proposal (DOCX dan PPTX) sebelum menulis kode | `PRODUCT.md`, `docs/architecture.md` |
| Merencanakan | Menyusun roadmap checklist per fase | `ROADMAP.md` |
| Menyiapkan tim agen pengembang | Membuat agent dan skill Claude Code khusus proyek | `.claude/agents/`, `.claude/skills/` |
| Membangun | Generator data sintetis, empat API enterprise, Global Orchestrator, decision engine, model ML, dashboard | `backend/`, `shared/`, `frontend/`, `data/generate.py` |
| Menguji | Uji unit, smoke test end-to-end, pengujian sebagai pengguna dengan Playwright | `tests/`, `scripts/smoke_test.py`, `docs/screenshots/` |
| Mendesain ulang | Wawancara produk, undian arah visual, kontrak arah, dua putaran review independen | `.impeccable/surfaces/`, `DESIGN.md` |
| Memperdalam kasus nyata | Jam simulasi, dunia fisik (silo dan kapal), kantor agent 3D | `frontend/office3d.html`, endpoint `/world` |
| Mendokumentasikan | README, arsitektur, API (dihasilkan dari OpenAPI), panduan, skrip demo, peta kode agent, presentasi | `docs/` |
| Merilis | Repositori GitHub publik dengan branch `main` dan `docs` | riwayat commit |

## 3. Agent dan skill proyek

| Nama | Jenis | Fungsi |
|---|---|---|
| backend-api-builder | Agent | Aturan membangun API enterprise: data store terpisah, kebijakan G_i, endpoint agent |
| streamlit-dashboard-builder | Agent | Aturan halaman dashboard: angka dari API, label data sintetis, RBAC |
| decision-engine-auditor | Agent | Memeriksa rumus Pers. 1, 2, 14 sampai 18 dan label model, tanpa mengubah kode |
| demo-qa-tester | Agent | Menjalankan stack dan smoke test sebelum presentasi |
| ui-designer | Agent | Menentukan dan menerapkan sistem desain |
| run-mas-stack | Skill | Prosedur menyalakan, memeriksa, dan mereset stack |
| saw-decision-engine | Skill | Referensi rumus decision engine |
| add-scenario | Skill | Prosedur menambah skenario disrupsi |

## 4. Delegasi ke subagent (orchestrator-worker dalam pengembangan)

Coding agent utama berperan sebagai orchestrator: memecah pekerjaan, menjalankan subagent secara paralel di latar belakang, lalu menggabungkan hasilnya. Contoh nyata dari proyek ini:

| Subagent | Tugas | Hasil |
|---|---|---|
| Riset API publik | Mencari dan memanggil langsung API cuaca laut, jarak rute, hari libur, kurs, geofence pelabuhan | `docs/public-api-research.md`, endpoint diberi status terverifikasi atau tidak |
| Pengunduh referensi | Mengambil referensi desain Dribbble | Diblokir CAPTCHA; agen tidak menembus CAPTCHA dan melaporkannya, lalu gambar diambil melalui browser aplikasi |
| Desainer UI | Menyusun komponen kartu agent, pipeline, dan timeline pesan | Helper di `frontend/ui.py` |
| Reviewer independen | Menilai hasil redesign tanpa mewarisi konteks pembuat | Putusan *recapture*, lalu *fix* dua kali, dengan daftar perbaikan bernomor |
| Dokumenter | Mencatat sistem desain dari kode yang sudah selesai dibangun | `DESIGN.md`, `.impeccable/design.json` |
| Pembuat presentasi | Menyusun deck 16 slide dan memeriksa setiap slide sebagai gambar | `docs/presentation/` |

## 5. Feedback loop dan verifikasi

Setiap perubahan melewati loop *act, observe, correct*:

1. **Uji otomatis.** Tujuh uji unit decision engine dan 21 pemeriksaan smoke test end-to-end (enam skenario, eksekusi paralel, replanning, approve dan reject, autentikasi 401/403, dunia langsung, perubahan KPI, reset).
2. **Agen sebagai pengguna.** Playwright membuka dashboard, menekan tombol, menyetujui keputusan, lalu mengambil tangkapan layar. Cacat yang ditemukan dengan cara ini antara lain: alur agent terpotong, keputusan lama menumpuk, canvas 3D berukuran nol, basemap yang meminta kunci API, dan area utama yang ambruk saat strip persetujuan hilang.
3. **Review independen.** Hasil desain dinilai agen lain yang tidak ikut membangun, dengan batas dua putaran perbaikan.
4. **Detektor pola.** Pemeriksaan otomatis terhadap pola desain generik ("AI slop") menghasilkan nol temuan.

## 6. Manusia tetap memegang kendali

Pemilik produk memutuskan hal-hal yang memang wewenangnya: audiens dan bahasa antarmuka, fokus tampilan, arah desain (diserahkan kepada agen dengan peran pengguna), cakupan "kasus nyata", serta kapan pekerjaan dihentikan dan dilanjutkan. Tindakan berdampak keluar, seperti membuat repositori publik, dilakukan karena diminta secara eksplisit.

## 7. Guardrail yang dijalankan agen

| Guardrail | Contoh dalam proyek |
|---|---|
| Tidak menembus mekanisme keamanan | CAPTCHA Dribbble tidak dilewati |
| Lisensi diperiksa | Model robot CC0, three.js MIT, Leaflet BSD 2-Clause, dicatat di `frontend/static/THIRD_PARTY.md` |
| Hak cipta dihormati | Gambar referensi Dribbble tidak diunggah ke repositori publik |
| Privasi | Skrip pembuat deck yang memuat path lokal komputer tidak ikut dipublikasikan |
| Kejujuran data | Semua data diberi label sintetis; TFT ditandai mode simulasi; angka performa tidak diklaim sebagai performa nyata |
| Diagnosis, bukan tebakan | Kegagalan Docker Desktop dilacak sampai log backend (socket Unix yang tidak dapat diakses) sebelum langkah perbaikan |

## 8. Kaitan dengan materi kuliah

| Materi | Wujud dalam proses pengembangan |
|---|---|
| 1.5 sampai 1.6 AI Agents dan Agentic AI | Coding agent menerima tujuan ("bangun prototipe"), bukan instruksi baris per baris |
| 2.4 Perception and Action | Agen membaca keluaran perintah, log, dan tangkapan layar sebelum bertindak |
| 3.7 Tools, Functions, APIs | Shell, editor, Playwright, Docker, GitHub CLI sebagai aktuator |
| 3.8 Agentic execution dan feedback loop | Siklus tulis, jalankan, uji, perbaiki |
| 3.10 Coding Agents | Claude Code sebagai agen pembuat perangkat lunak |
| 4.2 Arsitektur MAS | Orchestrator dengan subagent spesialis yang bekerja paralel |
| 4.10 Keamanan dan Trust | Reviewer independen, guardrail lisensi dan privasi |
| 2.6 Autonomous Agents | Otonomi bertingkat: agen bebas menulis kode lokal, tetapi keputusan produk dan tindakan publik tetap pada manusia |
