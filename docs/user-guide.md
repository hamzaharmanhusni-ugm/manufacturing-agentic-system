# Panduan Pengguna

## Masuk sebagai peran

Pilih peran di sidebar (**Signed in as**). Peran menentukan halaman yang terlihat, tab yang terbuka, kunci API yang digunakan dashboard, serta hak menjalankan skenario dan menyetujui dispatch.

| Peran | Halaman | Menyetujui | Menjalankan skenario |
|---|---|---|---|
| Global Administrator | semua | ya | ya |
| Manufacturer Manager | Global, Manufacturer | ya | ya |
| Marketing Planner | Manufacturer (tab pemasaran) | tidak | tidak |
| Operations Planner | Manufacturer (tab operasi) | tidak | tidak |
| Shipping Manager | Global, Shipping | ya | ya |
| Distributor Manager | Distribution | tidak | tidak |
| Supplier Manager | Supplier | tidak | tidak |

## Membaca dispatch docket

Satu docket mewakili satu run orkestrasi.

| Kotak | Isi | Pengisi |
|---|---|---|
| 1 Event | Kejadian pemicu | Event bus / Orchestrator |
| 2 sampai 5 | Hasil empat agent pekerja, diisi bersamaan | Agent di API enterprise masing-masing |
| 6 Dispatch plan | Peringkat plant, kapal terpilih, kuantitas, kedatangan, skor SAW, alternatif | Dispatch Planner Agent |
| 7 Narrator remarks | Penjelasan singkat dari angka terverifikasi | Narrator Agent |
| 8 Authorisation | Approve atau Reject per keputusan | Manusia dengan peran berwenang |

Tanda status: kotak hitam berarti selesai, kotak cyan berkedip berarti sedang berjalan, kotak ungu berarti menunggu persetujuan, kotak merah berarti gagal, kotak kosong berarti belum berjalan. Kode enterprise: **GLB** global, **MFG** manufacturer, **SHP** shipping, **DST** distribution, **SUP** supplier.

Pada Kotak 6, angka kedatangan berwarna merah berarti kapal diperkirakan tiba setelah stok habis. Baris kuning menandai rencana yang berubah setelah disrupsi, dengan nama kapal lama dicoret.

## Halaman lain

- **Simulation Center**: memilih dan menjalankan enam skenario, melihat docket, linimasa paralel, serta tujuh bagian hasil (kondisi awal, event, agent, penalaran, keputusan, perubahan dashboard, dampak KPI).
- **KPI & Analytics**: KPI terkini, sebelum dan sesudah AI, operasi normal dan disrupsi, rencana awal dan adaptif.
- **Dashboard enterprise**: data dan agent milik masing-masing enterprise; tombol **Run** menjalankan agent langsung pada API enterprise tersebut.
- **Architecture**: representasi E_i dan tabel heterogenitas teknologi.
- **Governance & Security**: RBAC, kebijakan berbagi data, audit trail, log API, dan uji autentikasi langsung.
