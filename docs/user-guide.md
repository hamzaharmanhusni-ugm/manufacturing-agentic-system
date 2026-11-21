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

## Live Operations 3D

Halaman ini memperlihatkan kasus nyata dari awal sampai akhir pada satu jam simulasi. Panel kiri adalah kantor agent (siapa yang sedang berpikir); panel kanan adalah dunia nyata (silo dan kapal di peta laut Indonesia).

Alur yang terjadi setelah tombol **Play** ditekan:

1. Setiap jam simulasi plant menjual semen sehingga silo terkuras sesuai permintaan harian masing-masing plant.
2. Saat sebuah silo turun di bawah 25%, sensor IIoT memicu event dan Orchestrator menjalankan agent tanpa perintah manusia.
3. Jam berhenti selama agent bekerja, lalu menunggu tanda tangan pada strip **Box 8 Authorisation** di bagian atas.
4. Setelah disetujui, kapal memuat di load port, berlayar menuju plant (garis putus-putus cyan di peta), lalu membongkar muatan sehingga gauge silo naik kembali.
5. Alur cerita menambahkan disrupsi: badai di rute PP F pada jam ke-30 (rute memerah, kapal bermuatan melambat sekitar 14 jam, agent merencanakan ulang), badai reda pada jam ke-54, dan gangguan pemasok clinker pada jam ke-66.

Kecepatan jam dapat diatur (0,5 sampai 4 jam simulasi per detik). **Reset story** mengembalikan seluruh enterprise ke kondisi awal. **Screens** menampilkan atau menyembunyikan layar kerja di atas robot.

Setiap platform berwarna di panel kiri adalah satu enterprise; platform navy di tengah adalah Global Orchestrator. Di atas setiap robot muncul layar kerja berisi keluaran agent itu sendiri: level silo, forecast 14 hari, ranking prioritas, ketersediaan armada, hasil SAW, atau kalimat Narrator.

| Yang terlihat | Artinya |
|---|---|
| Suar oranye berkedip | Event masuk (sensor silo, penjualan, keterlambatan kapal, cuaca) |
| Robot berjalan dengan cincin cyan berdenyut | Agent sedang bekerja di API enterprise-nya |
| Amplop terbang antar-platform | Pesan antar-agent yang tercatat di orchestrator |
| Robot mengacungkan jempol | Agent selesai dan menandatangani hasilnya |
| Robot melambai, cincin ungu | Keputusan menunggu persetujuan manusia |
| Figur manusia memberi stempel | Persetujuan atau penolakan oleh peran berwenang |
| Gauge silo merah di peta | Level silo di bawah 25% |
| Rute merah di peta | Badai, pelayaran tidak disarankan |

Klik robot atau figur manusia untuk membuka panel berisi status, tanggung jawab, keluaran terakhir, dan konsep agentic yang diperankan (misalnya orchestrator-worker, perceive-reason-act, human in the loop). Bilah di bawah menandai langkah yang sedang berlangsung, dari event sampai dampak di dunia nyata, dan log cerita mencatat setiap kejadian dengan waktu simulasinya.

## Halaman lain

- **Simulation Center**: memilih dan menjalankan enam skenario, melihat docket, linimasa paralel, serta tujuh bagian hasil (kondisi awal, event, agent, penalaran, keputusan, perubahan dashboard, dampak KPI).
- **KPI & Analytics**: KPI terkini, sebelum dan sesudah AI, operasi normal dan disrupsi, rencana awal dan adaptif.
- **Dashboard enterprise**: data dan agent milik masing-masing enterprise; tombol **Run** menjalankan agent langsung pada API enterprise tersebut.
- **Architecture**: representasi E_i dan tabel heterogenitas teknologi.
- **Governance & Security**: RBAC, kebijakan berbagi data, audit trail, log API, dan uji autentikasi langsung.
