# Skrip Demo Presentasi

Durasi sekitar 12 menit. Jalankan `python run_all.py`, buka http://localhost:3000, lalu tekan **Reset ecosystem** di Simulation Center agar semua enterprise kembali ke kondisi awal.

## 0. Pembuka (1 menit), Control Center

- Tunjukkan ledger di bagian atas: empat enterprise terhubung, sembilan agent, pesanan, kapal, dan indeks kesehatan rantai pasok.
- Tunjukkan buku besar enterprise: setiap enterprise memiliki API, port, basis data, dan agent sendiri. Klik salah satu tautan untuk membuka dashboard enterprise.
- Sampaikan prinsip: *code decides, AI explains, people act*.

## 0b. Agent Office 3D (1 menit, opsional untuk pembukaan)

Buka **Agent Office 3D**, pilih **2. Low stock at PP C**, tekan **Run and watch**. Tunjukkan suar event, amplop yang dikirim Orchestrator ke empat robot sekaligus, robot yang berjalan saat bekerja, lalu Dispatch Planner yang melambai menunggu persetujuan. Klik figur manusia untuk menampilkan konsep human in the loop. Lanjutkan ke Control Center untuk menandatangani docket.

## 1. Operasi normal (1 menit)

Pilih **1. Normal operation**, tekan **Run**. Docket terisi kotak demi kotak: Kotak 1 event, Kotak 2 sampai 5 diisi bersamaan oleh empat agent dari dua enterprise, Kotak 6 rencana dispatch, Kotak 7 penjelasan Narrator, Kotak 8 persetujuan.

Poin bicara: agent tidak saling memanggil; hanya Orchestrator yang mengatur urutan. Waktu paralel (sekitar satu detik) jauh lebih pendek daripada jumlah waktu keempat agent.

## 2. Low stock PP C (2 menit)

Jalankan **2. Low stock at PP C**. Silo PCC di PP C turun ke 20%.

- Kotak Stock Monitoring menampilkan stock-out PP C dalam hitungan hari dan event low stock (dikirim sekali).
- Panel notifikasi di sidebar menerima peringatan untuk Operations Planner.
- Rencana dispatch menempatkan PP C di peringkat 1. Bila kapal tiba setelah perkiraan stock-out, angka kedatangan diberi warna merah dan Narrator menyatakannya terus terang.

## 3. Demand surge PP F (1,5 menit)

Jalankan **3. Demand surge at PP F**. Distribution Agent (ekstensi) ikut dipanggil.

- ML Forecasting memperbarui proyeksi 14 hari, Demand & Priority menaikkan peringkat PP F.
- Buka dashboard Distribution untuk melihat pesanan wilayah Bali yang melonjak.

## 4. Gangguan pengiriman dan adaptive replanning (3 menit)

Jalankan **4. Shipping disruption (adaptive replanning)**.

- Siklus pertama menghasilkan rencana, lalu kapal yang direkomendasikan mengalami keterlambatan 60 jam.
- Siklus kedua berjalan otomatis. Pada Kotak 6, baris yang berubah disorot dengan nama kapal lama dicoret, sampai pengguna menekan **Acknowledge plan changes**.
- Buka Simulation Center, tab **4 Reasoning**, untuk menunjukkan linimasa negosiasi antara Manufacturer, Shipping, dan Dispatch Planner.
- Di Kotak 8, tekan **Approve** pada satu keputusan (stempel APPROVED muncul) dan **Reject** pada keputusan lain.
- Ganti peran ke **Marketing Planner** di sidebar: tombol persetujuan nonaktif. Kembalikan ke Global Administrator.

## 5. Cuaca buruk (1 menit)

Jalankan **5. Weather disruption**. Gelombang 3,4 m di rute PP F: kapal ke PP F dikeluarkan dengan alasan *sailing not advised*, terlihat pada catatan rencana dan notifikasi Shipping Manager.

## 6. Gangguan pemasok (1 menit)

Jalankan **6. Supplier disruption**. Procurement Agent (ekstensi) menghitung cakupan clinker, mengusulkan pemasok alternatif, dan Orchestrator membatasi kapasitas produksi sehingga stok load port turun. Kuantitas dispatch ikut dibatasi.

## 7. Penutup (1,5 menit)

- **KPI & Analytics**: perbandingan sebelum dan sesudah AI, operasi normal dan disrupsi, serta rencana awal dan adaptif.
- **Governance & Security**: matriks RBAC, kebijakan berbagi data per enterprise, audit trail, log API, dan uji autentikasi (kirim permintaan dengan kunci orchestrator ke `/marketing/prices` untuk menunjukkan 403).
- **Architecture**: representasi E_i = (U, M, D, A, P, G) untuk keempat enterprise.

## Pertanyaan yang sering muncul

| Pertanyaan | Jawaban singkat |
|---|---|
| Apakah LLM yang menentukan kapal? | Tidak. SAW dan assignment greedy di `shared/decision_engine.py` yang menentukan; Narrator hanya menjelaskan. |
| Apakah modelnya benar-benar dilatih? | LightGBM, Random Forest, ARIMA, Weibull, dan DBSCAN dilatih pada data sintetis saat API menyala. TFT ditampilkan dalam mode simulasi. |
| Mengapa ada empat enterprise padahal proposal hanya dua perusahaan? | Distribution dan Supplier adalah ekstensi prototipe untuk memenuhi syarat minimal empat enterprise, dan diberi label jelas. |
| Bagaimana komunikasi antar-enterprise terjadi? | Panggilan HTTP dengan API key ke endpoint agent setiap enterprise; semua tercatat di log pesan dan log API. |
