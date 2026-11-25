"""Annotated, step-by-step screenshots of the running app (the app itself is not restyled).

python scripts/make_annotations.py  ->  "Penjelasan Agentic/NN-*.png"
Raw captures: docs/screenshots/walk-*.png and data-governance-audit-trail.png (taken from the running app with Playwright)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "screenshots"
OUT = ROOT / "Penjelasan Agentic"
F = lambda n, b=False: ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if b else "C:/Windows/Fonts/segoeui.ttf", n)
NAVY, INK, MUTED, PAPER = (11, 27, 51), (15, 23, 42), (71, 85, 105), (246, 248, 251)
COL = {"GLB": (11, 27, 51), "MFG": (29, 78, 216), "SHP": (14, 116, 144), "DST": (146, 64, 14), "SUP": (91, 33, 182), "HUM": (217, 119, 6), "RED": (185, 28, 28), "SKY": (2, 132, 199)}
PANEL = 760


def wrap(d, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) > width:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + [cur]


def make(name, shot, step, title, subtitle, marks, concept, crop=None):
    """marks: list of (x, y, w, h, colour, heading, text) on the 1600x1000 screenshot."""
    im = Image.open(SHOTS / shot).convert("RGB")
    if crop:
        im = im.crop((0, 0, im.width, crop))  # ponytail: keep only the part the marks explain
    W, H = im.width, 1000
    canvas = Image.new("RGB", (W + PANEL, H), PAPER)
    canvas.paste(im, (0, 0))
    over = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    for i, (x, y, w, h, c, _, _) in enumerate(marks):
        col = COL[c]
        od.rectangle([x, y, x + w, y + h], fill=col + (28,), outline=col + (255,), width=5)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), over).convert("RGB")
    d = ImageDraw.Draw(canvas)
    for i, (x, y, w, h, c, _, _) in enumerate(marks):
        cx, cy = max(x + 2, 22), max(y + 2, 22)
        d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=COL[c], outline="white", width=3)
        d.text((cx, cy), str(i + 1), fill="white", font=F(24, True), anchor="mm")
    # side panel
    px = W + 32
    d.rectangle([W, 0, W + PANEL, H], fill=PAPER)
    d.line([W, 0, W, H], fill=(203, 213, 225), width=2)
    d.text((px, 30), step if isinstance(step, str) else f"LANGKAH {step}", fill=COL["SKY"], font=F(17, True))
    y = 56
    for line in wrap(d, title, F(30, True), PANEL - 64):
        d.text((px, y), line, fill=NAVY, font=F(30, True))
        y += 38
    for line in wrap(d, subtitle, F(17), PANEL - 64):
        d.text((px, y + 4), line, fill=MUTED, font=F(17))
        y += 24
    y += 22
    for i, (_, _, _, _, c, head, text) in enumerate(marks):
        d.ellipse([px, y, px + 34, y + 34], fill=COL[c])
        d.text((px + 17, y + 17), str(i + 1), fill="white", font=F(18, True), anchor="mm")
        d.text((px + 48, y + 2), head, fill=NAVY, font=F(18, True))
        yy = y + 28
        for line in wrap(d, text, F(16), PANEL - 112):
            d.text((px + 48, yy), line, fill=INK, font=F(16))
            yy += 22
        y = yy + 14
    # concept box at the bottom
    lines = wrap(d, concept, F(16), PANEL - 104)
    bh = 52 + 22 * len(lines)
    by = max(y + 6, H - bh - 28)
    d.rounded_rectangle([px, by, W + PANEL - 32, by + bh], 14, fill=NAVY)
    d.text((px + 20, by + 16), "KONSEP AGENTIC", fill=(125, 211, 252), font=F(15, True))
    for k, line in enumerate(lines):
        d.text((px + 20, by + 42 + 22 * k), line, fill=(228, 235, 245), font=F(16))
    if by + bh > H:
        raise SystemExit(f"{name}: panel text too long")
    OUT.mkdir(exist_ok=True)
    canvas.save(OUT / name)
    print("wrote", name)


def main():
    make("01-dashboard-control-center.png", "walk-01-control.png", 1, "Pusat kendali ekosistem",
         "Halaman pertama: Control Center. Semua enterprise dan agent terlihat dari satu tempat.",
         [(356, 132, 1158, 66, "GLB", "Ringkasan ekosistem", "4 enterprise, 9 agent, pesanan, kapal, plant berisiko, dan indeks kesehatan rantai pasok."),
          (356, 256, 1158, 100, "MFG", "Empat enterprise terpisah", "Manufacturer, Shipping, Distribution, dan Supplier masing-masing memiliki API, basis data, dan agent sendiri. ONLINE berarti Orchestrator dapat menghubunginya."),
          (356, 388, 884, 40, "HUM", "Pilih event, lalu Run", "Di sini event dipilih secara manual untuk simulasi. Di Live Operations, event datang sendiri dari sensor."),
          (356, 442, 1158, 64, "GLB", "Dispatch docket", "Satu lembar kerja untuk satu siklus agent. Lembar ini terisi Box 1 sampai Box 8 setelah Run."),
          (356, 532, 1158, 466, "SHP", "Kondisi dunia nyata", "Stok setiap plant dan posisi kapal di peta. Inilah yang diamati para agent sebelum bertindak.")],
         "Lingkungan (environment) dan para agent berada pada satu layar. Agent mengamati kondisi ini, lalu bertindak melalui API enterprise masing-masing.")

    make("02-event-dan-agent-paralel.png", "walk-02-docket.png", 2, "Event memicu empat agent sekaligus",
         "Satu run orkestrasi selesai dalam 3,35 detik; empat agent paralel hanya butuh sekitar 1 detik.",
         [(356, 38, 241, 194, "GLB", "Box 1: Event", "Sensor silo melaporkan PP C PCC di bawah 25%. Orchestrator menugaskan 4 agent."),
          (598, 38, 228, 194, "MFG", "Box 2: Stock Monitoring", "Menghitung kapan stok habis: PP C tinggal 1,18 hari."),
          (827, 38, 229, 194, "MFG", "Box 3: ML Forecasting", "Meramal permintaan 14 hari; WAPE LightGBM 0,0735 lebih baik daripada TFT."),
          (1057, 38, 228, 194, "SHP", "Box 4: Fleet Tracking", "12 dari 19 kapal tersedia, tidak ada rute badai, tiga kapal berisiko rusak."),
          (1286, 38, 229, 194, "MFG", "Box 5: Demand & Priority", "Mengurutkan plant: PP C peringkat 1 dengan skor 4,6.")],
         "Pola orchestrator-worker: satu orchestrator membagi tugas, empat worker dari dua enterprise bekerja bersamaan, dan setiap hasil ditandatangani agent pemiliknya.")

    make("03-rencana-penjelasan-persetujuan.png", "walk-02-docket.png", 3, "Rencana, penjelasan, dan tanda tangan manusia",
         "Hasil keempat agent digabung menjadi rencana, dijelaskan, lalu menunggu keputusan manusia.",
         [(356, 268, 771, 257, "GLB", "Box 6: Dispatch Planner", "Memilih kapal terbaik per plant dengan skor SAW. PP C mendapat Ship N (5.250 t), lengkap dengan kapal alternatif."),
          (1143, 268, 372, 204, "GLB", "Box 7: Narrator", "Mengubah angka menjadi kalimat. Ia jujur menyebut Ship N tiba sesudah perkiraan stok habis."),
          (1143, 483, 372, 307, "HUM", "Box 8: Authorisation", "Manusia menekan Approve atau Reject. Stempel APPROVED mencatat siapa dan kapan.")],
         "Code decides, AI explains, people act: kode menghitung rencana, AI menjelaskan, dan manusia memegang keputusan akhir (human-in-the-loop).")

    make("04-registry-dan-pesan-antar-agent.png", "walk-03-messages.png", 4, "Siapa bekerja dan apa yang mereka katakan",
         "Bagian bawah Control Center merekam status setiap agent dan setiap pesan antar-agent.",
         [(356, 274, 644, 536, "GLB", "Agent registry", "Status sembilan agent: selesai, menunggu persetujuan, atau idle, lengkap dengan durasi kerja."),
          (1024, 274, 490, 516, "SKY", "Log pesan lintas enterprise", "Setiap pesan tercatat dengan pengirim, penerima, dan jenisnya: request, response, recommendation, decision, execution."),
          (356, 880, 1158, 76, "GLB", "Tanya Narrator", "Pengguna dapat bertanya, misalnya kapal mana ke PP C dan mengapa. Jawaban hanya dari rencana yang sudah diverifikasi."),
          (20, 720, 241, 34, "HUM", "Notifikasi", "Peringatan untuk peran terkait, misalnya stok rendah untuk Operations Planner.")],
         "Komunikasi antar-agent memakai format pesan baku, sehingga kerja sama lintas enterprise dapat diaudit.".replace("memakai", "menggunakan"))

    bar, stage, mapp = (356, 193, 1159, 56), (357, 266, 659, 732), (1025, 266, 497, 732)
    make("05-live-dunia-berjalan.png", "walk-live-1.png", 5, "Dunia berjalan sendiri",
         "Halaman Live Operations 3D. Jam simulasi berjalan 2 jam per detik.",
         [(*bar, "GLB", "Jam simulasi", "Play, Pause, kecepatan, dan Reset story. Status menunjukkan bahwa plant sedang menjual semen."),
          (*stage, "GLB", "Kantor agent 3D", "Setiap robot adalah satu agent di atas platform enterprise-nya. Layar di atas robot menampilkan hasil kerja terakhir."),
          (*mapp, "SHP", "Dunia nyata", "Gauge silo di setiap plant turun setiap jam, dan kapal bergerak di perairan Indonesia.")],
         "Environment terus berubah tanpa campur tangan agent. Agent belum bertindak selama belum ada percept yang melampaui ambang.")

    make("06-live-sensor-memicu-agent.png", "walk-live-2.png", 6, "Sensor membangunkan agent",
         "Day 2 pukul 05.00: silo PCC di PP C turun di bawah 25%. Tidak ada yang menekan tombol.",
         [(*bar, "RED", "Jam berhenti", "Status berubah menjadi Clock waiting: agent sedang bekerja, dunia menunggu rencana."),
          (*stage, "MFG", "Agent mulai bekerja", "Orchestrator mengirim tugas; robot Stock Monitoring, ML Forecasting, Demand & Priority, dan Fleet Tracking aktif bersamaan."),
          (*mapp, "SHP", "Pemicu dari dunia nyata", "Gauge silo PP C di peta sudah di bawah ambang 25%.")],
         "Otonomi event-driven: run dimulai oleh perubahan lingkungan, bukan oleh perintah manusia.")

    bar2, appr, stage2, map2 = (356, 193, 1159, 56), (356, 257, 1159, 154), (357, 420, 659, 578), (1025, 420, 497, 578)
    make("07-live-menunggu-persetujuan.png", "walk-live-3.png", 7, "Rencana menunggu tanda tangan",
         "Agent selesai bekerja. Jam tetap berhenti sampai manusia memutuskan.",
         [(*appr, "HUM", "Strip Box 8", "Tiga rekomendasi: Ship N ke PP C membawa 4.901 t PCC (prioritas High), Ship J ke PP F, Ship K ke PP I."),
          (*stage2, "GLB", "Layar kerja agent", "Forecast 14 hari, prioritas plant, ranking SAW, ketersediaan armada, dan penjelasan Narrator tampil di atas robot."),
          (*map2, "SHP", "Dunia ikut menunggu", "Kapal dan silo diam selama keputusan belum diambil.")],
         "Tingkat otonomi Approve (human-in-the-loop): agent mengusulkan, manusia memutuskan. Dispatch Planner bersifat deliberatif dan utility-based.")

    make("08-live-kapal-berlayar.png", "walk-live-4.png", 8, "Tindakan dijalankan",
         "Setelah Approve, Shipping menerima tugas dan Manufacturer menerima jadwal kedatangan.",
         [(*bar, "SHP", "Jam berjalan lagi", "Clock running: dunia kembali bergerak setelah keputusan diambil."),
          (*mapp, "SHP", "Kapal berlayar", "Ship N memuat 12 jam di load port, lalu berlayar menuju PP C mengikuti garis putus-putus di peta."),
          (*stage, "GLB", "Hasil kerja tetap terlihat", "Layar di atas robot masih menampilkan rencana yang sedang dijalankan.")],
         "Act: keputusan berubah menjadi tindakan nyata melalui API Shipping dan Manufacturer.")

    make("09-live-badai-replanning.png", "walk-live-5.png", 9, "Badai memicu perencanaan ulang",
         "Layanan cuaca melaporkan gelombang 3,4 m di rute PP F.",
         [(*bar, "RED", "Event baru", "Clock waiting lagi: agent bekerja ulang tanpa perintah manusia."),
          (*mapp, "RED", "Rute badai", "Rute ke PP F ditandai tidak aman; kapal bermuatan di rute itu melambat sekitar 14 jam."),
          (*stage, "GLB", "Agent menyusun rencana baru", "Fleet Tracking menandai sailing not advised, lalu Dispatch Planner mengeluarkan kapal yang harus melewati gelombang di atas 2,5 m.")],
         "Adaptive replanning dan feedback loop: rencana tidak dianggap final, melainkan dievaluasi ulang ketika lingkungan berubah.")

    make("10-live-kapal-tiba-silo-terisi.png", "walk-live-6.png", 10, "Kapal tiba, silo terisi",
         "Day 3 pukul 09.00: Ship N membongkar muatan di PP C.",
         [(*mapp, "SHP", "Dampak fisik", "Gauge silo PP C naik kembali setelah muatan dibongkar (bongkar sekitar 18 jam)."),
          (*bar, "GLB", "Siklus berlanjut", "Jam terus berjalan; sensor membaca kondisi baru setiap jam."),
          (*stage, "GLB", "Agent kembali memantau", "Agent siap bekerja lagi apabila ada silo lain yang turun di bawah ambang.")],
         "Loop perceive, reason, act tertutup: tindakan yang disetujui mengubah lingkungan, dan pembacaan sensor berikutnya mencerminkan perubahan itu.")

    make("11-audit-trail-governance.png", "data-governance-audit-trail.png", 11, "Semua tercatat dan dapat diaudit",
         "Halaman Governance & Security, tab Audit trail.",
         [(357, 484, 1168, 32, "RED", "Run otonom", "Orchestrator mencatat run yang dipicu sensor: silo PP C 24%, sisa stok 1,62 hari."),
          (357, 418, 1168, 32, "HUM", "Persetujuan manusia", "Global Administrator menyetujui Ship N ke PP C; waktu dan pelaku tercatat."),
          (357, 319, 1168, 32, "RED", "Run karena badai", "Event cuaca di rute PP F juga memicu run otonom."),
          (357, 623, 1168, 101, "GLB", "Riwayat aktivitas agent", "Setiap run memiliki nomor, judul, status, waktu mulai dan selesai, serta durasi.")],
         "Trust dan akuntabilitas: setiap tindakan agent dan setiap keputusan manusia dapat ditelusuri kembali.")


def menus():
    tabs = (356, 138, 1170, 26)
    make("12-simulation-center-skenario.png", "walk-sim-1.png", "MENU · SIMULATION CENTER", "Menguji enam skenario kejadian",
         "Simulation Center digunakan untuk mencoba kejadian tertentu secara sengaja, lalu melihat cara para agent menanggapinya. Docket yang tampil adalah run terakhir.",
         [(370, 145, 795, 33, "HUM", "Pilihan skenario", "Enam kejadian siap uji: operasi normal, stok rendah PP C, lonjakan permintaan PP F, kapal terlambat (replanning), cuaca buruk, dan gangguan pemasok. Setiap skenario mengubah data enterprise terkait."),
          (370, 190, 360, 40, "HUM", "Deskripsi event", "Menjelaskan kejadian yang akan dikirim ke Orchestrator dan dampaknya pada data, misalnya silo turun atau kapal tertunda."),
          (1204, 145, 297, 93, "GLB", "Run scenario dan Reset ecosystem", "Run mengirim event ke Orchestrator sehingga agent bekerja. Reset mengembalikan keempat enterprise ke data awal agar setiap uji dimulai dari kondisi yang sama."),
          (356, 267, 1159, 271, "MFG", "Docket run: Box 1 sampai 5", "Judul run menunjukkan event yang diproses, di sini badai di rute PP F dengan gelombang 3,4 m. Empat agent dari dua enterprise mengisi Box 2 sampai 5 secara bersamaan; Fleet Tracking menandai PP F sailing not advised."),
          (356, 571, 1159, 381, "HUM", "Box 6 sampai 8: rencana, penjelasan, persetujuan", "Dispatch Planner hanya merekomendasikan dua kapal karena rute PP F ditutup. Narrator menjelaskan, lalu kedua rekomendasi disetujui dan diberi stempel APPROVED.")],
         "Pengujian berbasis skenario: event yang sama selalu menghasilkan alur agent yang sama, sehingga perilaku sistem dapat diperiksa dan dibandingkan antar-kejadian.")

    make("13-simulation-center-tujuh-tab.png", "walk-sim-2.png", "MENU · SIMULATION CENTER", "Membaca hasil run secara rinci",
         "Di bawah docket, satu run dapat ditelusuri dari kondisi awal sampai dampaknya pada KPI.",
         [(356, 777, 1159, 36, "GLB", "Timeline eksekusi paralel", "Dapat dibuka untuk melihat kapan setiap agent mulai dan selesai. Batangnya saling tumpang tindih, bukti bahwa keempat agent bekerja bersamaan, bukan bergantian."),
          (356, 833, 620, 32, "SKY", "Tujuh tab analisis", "1 Kondisi awal, 2 Event, 3 Agent yang terlibat, 4 Penalaran (negosiasi antar-enterprise), 5 Keputusan, 6 Perubahan dashboard, dan 7 Dampak KPI."),
          (356, 880, 1159, 55, "MFG", "Kondisi awal sebelum agent bertindak", "Rata-rata days of cover 7,58 hari, 1 series berisiko stock-out, on-time 67%, dan 1 kapal terlambat. Angka ini dibandingkan dengan kondisi sesudah run pada tab 7."),
          (356, 100, 1159, 670, "GLB", "Docket yang sama dengan Control Center", "Kotak 1 sampai 8 identik dengan Control Center; Simulation Center menambahkan konteks analisis di bawahnya.")],
         "Explainability: setiap keputusan dapat ditelusuri ke data awal, event, penalaran setiap agent, dan dampaknya, sehingga manusia dapat menilai apakah agent bekerja dengan benar.")

    make("14-kpi-dan-analytics.png", "walk-kpi.png", "MENU · KPI & ANALYTICS", "Mengukur kinerja sistem agentic",
         "Semua indikator dihitung langsung dari API enterprise setiap kali halaman dibuka. Data bersifat sintetis.",
         [(356, 132, 1159, 68, "MFG", "KPI prediksi dan stok", "WAPE forecast LightGBM 0,073 (semakin kecil semakin akurat), MAE ETA 2,82 jam dari Random Forest, 1 series berisiko stock-out, rata-rata days of cover 7,61 hari, on-time delivery 74%, dan waktu respons dispatch 4,7 detik."),
          (356, 214, 1159, 68, "GLB", "KPI sistem agent", "Keberhasilan agent dan API 100%, sinkronisasi enterprise 100%, jumlah replanning, tingkat persetujuan manusia 100%, dan 0 keputusan yang masih menunggu."),
          (356, 292, 1159, 334, "SHP", "Sebelum AI dan sesudah AI", "Lima grafik membandingkan proses manual (abu-abu, asumsi ilustratif spreadsheet) dengan sistem agentic (biru): respons dispatch dari 240 menit menjadi kurang dari 1 menit, WAPE dari 0,0937 ke 0,0735, plant berisiko dari 3 menjadi 1, dan days of cover dari 4,5 menjadi 7,61 hari.")],
         "Evaluasi agent: kinerja diukur dari hasil (akurasi, ketepatan waktu, stok aman) dan dari perilaku sistem (keberhasilan agent, sinkronisasi, persetujuan manusia).", crop=640)

    make("15-manufacturer-executive.png", "data-manufacturer-executive.png", "MENU · CEMENT MANUFACTURING", "Dashboard pabrik semen",
         "Enterprise 1: PostgreSQL, REST port 8001. Pengguna: Manufacturer Manager, Marketing Planner, Operations Planner.",
         [(*tabs, "MFG", "Sembilan tab sesuai departemen", "Executive, Marketing, Operations, Forecasting, Silo Monitoring, Packing Plants, Stock-out, Agents, dan Decision History. Tab yang terlihat bergantung pada peran (RBAC)."),
          (356, 184, 1170, 68, "MFG", "Ringkasan pabrik", "9 packing plant, 22 silo yang dipantau sensor IIoT, usable stock 48.803 t, permintaan harian 6.583 t, kiriman yang sedang menuju plant, dan stok load port."),
          (356, 256, 564, 314, "MFG", "Skor prioritas (Demand & Priority Agent)", "Setiap plant diberi grade 1 sampai 5 pada lima kriteria berbobot (Pers. 14). Batang terpanjang adalah plant yang paling mendesak untuk dikirim."),
          (950, 256, 576, 314, "MFG", "Days of cover vs ARIMA (Stock Monitoring Agent)", "Setiap titik adalah satu series plant dan jenis semen. Sumbu datar: berapa hari stok cukup; sumbu tegak: perkiraan hari sampai habis dari ARIMA. Area merah muda menandai series berisiko.")],
         "Perceive dan reason di dalam enterprise: agent Manufacturer membaca data milik pabrik sendiri dan hanya mengirim hasilnya (skor dan risiko) ke Orchestrator, bukan data mentah.")

    make("16-manufacturer-forecasting.png", "data-manufacturer-forecasting.png", "MENU · CEMENT MANUFACTURING", "Peramalan permintaan 14 hari",
         "Tab Forecasting menampilkan kerja ML Forecasting Agent.",
         [(356, 184, 1170, 68, "MFG", "Champion dan challenger", "LightGBM (champion) dengan WAPE 0,074 dibandingkan TFT (challenger, mode simulasi) dengan WAPE 0,095 dan ensemble 0,079. Coverage P10 sampai P90 sebesar 70%. Model dengan galat terkecil yang digunakan."),
          (356, 290, 1170, 56, "MFG", "Pilih series", "Setiap kombinasi plant dan jenis semen memiliki forecast sendiri; di sini PP C OPC."),
          (356, 366, 1170, 314, "SKY", "Forecast dengan rentang ketidakpastian", "Garis tengah adalah P50 (nilai paling mungkin), pita biru muda adalah rentang P10 sampai P90. Penurunan tajam menandai hari libur atau akhir pekan yang dipelajari dari riwayat penjualan 400 hari.")],
         "Learning agent: model belajar dari data historis, dan metrik backtest (WAPE) berperan sebagai critic yang menentukan model mana yang dipercaya.")

    make("17-manufacturer-agents.png", "data-manufacturer-agents.png", "MENU · CEMENT MANUFACTURING", "Agent yang tinggal di dalam enterprise",
         "Tab Agents memperlihatkan bahwa ketiga agent Manufacturer berjalan di dalam API Manufacturer sendiri.",
         [(356, 184, 1158, 290, "MFG", "Tiga agent Manufacturer", "Stock Monitoring, ML Forecasting, dan Demand & Priority, lengkap dengan status COMPLETED, ringkasan hasil terakhir, waktu run, dan durasi (sekitar 640 ms)."),
          (356, 514, 1158, 42, "HUM", "Menjalankan agent secara langsung", "Setiap agent dapat dijalankan dari halaman ini tanpa melalui Orchestrator, berguna untuk memeriksa satu agent secara terpisah."),
          (356, 584, 1158, 414, "SKY", "Log eksekusi A2A", "Pesan antara Orchestrator dan agent Manufacturer: request berisi tugas (misalnya forecast 14 hari P10/P50/P90), lalu response berisi hasilnya (misalnya champion tetap LightGBM).")],
         "Otonomi data dan komunikasi A2A: agent tinggal bersama data enterprise-nya, dan Orchestrator hanya berkomunikasi melalui pesan request dan response yang tercatat.")

    make("18-shipping-live-tracking.png", "data-shipping-live-vessel-tracking.png", "MENU · SHIPPING & LOGISTICS", "Melacak 19 kapal",
         "Enterprise 2: anak perusahaan pelayaran, MongoDB, REST port 8002. Hanya GPS, status, ETA, dan riwayat voyage yang dibagikan.",
         [(356, 138, 970, 26, "SHP", "Sembilan tab armada", "Fleet Overview, Live Vessel Tracking, Vessel Availability, Voyage History, ETA Prediction, Ship Ranking, Shipping Assignment, Maintenance Status, dan Agents."),
          (356, 260, 1158, 564, "SHP", "Peta posisi kapal", "Titik kapal di perairan Indonesia, load port (merah), dan packing plant. Garis menunjukkan kapal yang sedang menuju plant tujuan."),
          (356, 876, 1158, 124, "SHP", "Status geofence dan DBSCAN", "Fleet Tracking Agent menentukan status setiap kapal (sailing, anchored, berthed) dengan dua cara: aturan geofence dari proposal dan klaster DBSCAN dari titik GPS. Keduanya ditampilkan berdampingan.")],
         "Perceive dari sensor GPS: agent mengubah titik koordinat mentah menjadi status kapal yang bermakna bagi perencanaan dispatch.")

    make("19-shipping-eta-prediction.png", "data-shipping-eta-prediction.png", "MENU · SHIPPING & LOGISTICS", "Memprediksi waktu tiba kapal",
         "Tab ETA Prediction menampilkan model Random Forest milik Fleet Tracking Agent.",
         [(356, 184, 1170, 68, "SHP", "Kualitas model", "Random Forest 200 pohon, MAE 2,86 jam pada 20% data uji, dilatih dari 225 voyage. Weibull shape 1,751 (lebih dari 1 berarti risiko rusak naik seiring pemakaian mesin).".replace("pemakaian", "penggunaan")),
          (356, 256, 568, 288, "SHP", "Fitur paling berpengaruh", "Plant tujuan dan jarak tempuh paling menentukan ETA, disusul kecepatan rata-rata, tinggi gelombang, bulan, dan muatan."),
          (950, 256, 576, 288, "SKY", "ETA dengan rentang", "Setiap batang adalah perkiraan jam tiba untuk kapal yang sedang berlayar; garis hitam adalah rentang dari sebaran antar-pohon. Rentang lebar berarti prediksi kurang pasti.")],
         "Agen rasional yang jujur tentang ketidakpastian: prediksi selalu disertai rentang, sehingga Dispatch Planner dan manusia mengetahui seberapa yakin agent.")

    make("20-shipping-ship-ranking.png", "data-shipping-ship-ranking.png", "MENU · SHIPPING & LOGISTICS", "Ranking kapal dengan SAW",
         "Tab Ship Ranking membuka perhitungan Dispatch Planner untuk setiap plant yang membutuhkan kiriman.",
         [(356, 184, 1170, 206, "SHP", "PP H membutuhkan OPC", "Kandidat diurutkan berdasarkan skor SAW. Ship I terpilih (0,8845) karena kapasitas 5.500 t dan 3 proven calls, meskipun waktu tibanya lebih lama daripada Ship L."),
          (356, 414, 1170, 206, "SHP", "PP G membutuhkan PCC", "Ship P terpilih (0,8983). Kolom risiko kerusakan 14 hari dari model Weibull ikut ditampilkan; risiko di atas 30% diberi peringatan."),
          (600, 456, 926, 30, "GLB", "Cara membaca skor", "Setiap kriteria dinormalkan (benefit: nilai dibagi maksimum; cost: minimum dibagi nilai), lalu dijumlahkan dengan bobot: arrival time 0,35, capacity 0,20, proven calls 0,20, evidence 0,15, gelombang 0,10.")],
         "Utility-based agent: pilihan kapal adalah alternatif dengan nilai utilitas tertinggi, dan seluruh perhitungannya terbuka untuk diperiksa manusia.")

    make("21-distribution.png", "data-distribution-regional-demand.png", "MENU · DISTRIBUTION", "Permintaan di tingkat wilayah",
         "Enterprise 3 (ekstensi prototipe): SQLite, REST port 8003, satuan sak 50 kg.",
         [(356, 50, 1170, 56, "DST", "Identitas enterprise", "Distribution adalah ekstensi untuk memenuhi syarat empat enterprise. Teknologinya sengaja berbeda (SQLite, satuan sak) untuk menunjukkan heterogenitas."),
          (356, 138, 770, 26, "DST", "Tujuh tab distribusi", "Regional Inventory, Distributor Orders, Regional Demand, Order Fulfillment, Distribution Performance, Stock Alerts, dan Agents."),
          (356, 184, 1170, 346, "DST", "Permintaan mingguan per wilayah", "Setiap garis adalah satu wilayah (Banten, Jakarta, Bali, dan lainnya) dalam satuan sak. Distribution Agent memantau lonjakan dan mengirim sinyal ke Orchestrator, yang menormalkan satuannya menjadi ton (20 sak = 1 t).")],
         "Interoperabilitas semantik: data dengan satuan dan format berbeda tetap dapat digabung karena Orchestrator menormalkannya.")

    make("22-supplier-procurement.png", "data-supplier-procurement-risk.png", "MENU · SUPPLIER & PROCUREMENT", "Risiko pasokan bahan baku",
         "Enterprise 4 (ekstensi prototipe): PostgreSQL dari ekspor CSV ERP, REST port 8004.",
         [(356, 138, 830, 26, "SUP", "Tujuh tab pengadaan", "Supplier Overview, Raw Material Inventory, Procurement Orders, Supplier Performance, Supply Availability, Procurement Risk, dan Agents."),
          (356, 184, 1170, 396, "SUP", "Risiko per material", "Procurement Agent menghitung cakupan pasokan setiap material (clinker, gypsum, limestone, fly ash, batu bara, kantong kertas) dan menandai material yang kritis bagi produksi. Hijau berarti risiko rendah."),
          (356, 600, 1170, 300, "RED", "Saat pemasok terganggu", "Dalam skenario gangguan pemasok, ketersediaan clinker turun ke 30%. Agent mengusulkan pemasok alternatif, dan Orchestrator membatasi kapasitas produksi sehingga kuantitas dispatch ikut menyesuaikan.")],
         "Koordinasi lintas enterprise: masalah di hulu (pemasok) memengaruhi keputusan di hilir (dispatch kapal) melalui Orchestrator.")

    make("23-architecture.png", "walk-arch.png", "MENU · ARCHITECTURE", "Arsitektur dan representasi enterprise",
         "Halaman ini membaca langsung dari API setiap enterprise, sehingga isinya selalu sesuai dengan sistem yang berjalan.",
         [(365, 140, 1142, 222, "GLB", "Diagram alur panggilan", "Kotak navy adalah Global Orchestrator (Dispatch Planner, Orchestrator, Narrator, Human approval). Panah padat adalah panggilan tugas A2A melalui HTTP dengan API key; panah putus-putus adalah hasil yang dikembalikan."),
          (356, 384, 860, 22, "SKY", "Cara membaca panah", "Hasil keempat worker digabung sekali oleh Dispatch Planner, lalu diteruskan ke Narrator dan persetujuan manusia."),
          (356, 462, 1160, 538, "MFG", "E_i = (U, M, D, A, P, G)", "Setiap enterprise dijelaskan dengan enam unsur: U pengguna dan peran, M modul aplikasi, D data lokal, A agent, P protokol dan API, G kebijakan berbagi data. Label PROPOSAL atau PROTOTYPE EXTENSION menunjukkan asalnya.")],
         "Multi-Agent System lintas organisasi: setiap enterprise adalah lingkungan mandiri dengan data, agent, dan aturannya sendiri, dan hanya terhubung melalui protokol yang disepakati.")

    make("24-governance-rbac.png", "walk-gov-rbac.png", "MENU · GOVERNANCE & SECURITY", "Siapa boleh melakukan apa (RBAC)",
         "Tab Roles menampilkan tujuh peran pengguna dan hak masing-masing.",
         [(357, 138, 600, 32, "GLB", "Enam tab tata kelola", "Roles (RBAC), Data-sharing policies, Audit trail, API access logs, Authentication test, dan Guardrails."),
          (357, 185, 410, 268, "GLB", "Peran dan halaman", "Setiap peran hanya melihat halaman yang relevan. Contoh: Marketing Planner hanya melihat Manufacturer dan beberapa tab saja."),
          (948, 185, 360, 268, "HUM", "Hak menyetujui dan menjalankan", "Hanya Global Administrator, Manufacturer Manager, dan Shipping Manager yang dapat menyetujui dispatch dan menjalankan skenario. Peran lain melihat tombol Approve dalam keadaan nonaktif."),
          (1308, 185, 218, 268, "SKY", "API key per peran", "Dashboard menggunakan kunci yang berbeda untuk setiap peran, sehingga API enterprise mengetahui siapa yang meminta data.")],
         "Bounded autonomy dan akuntabilitas: wewenang manusia dan agent dibatasi sesuai peran, sehingga keputusan penting hanya diambil oleh pihak yang berhak.")

    make("25-governance-kebijakan-data.png", "walk-gov-policy.png", "MENU · GOVERNANCE & SECURITY", "Kebijakan berbagi data G_i",
         "Tab Data-sharing policies: setiap enterprise menentukan sendiri data apa yang boleh dibaca pihak lain.",
         [(357, 183, 845, 22, "GLB", "Prinsip", "Contohnya, Orchestrator tidak dapat membaca harga dan margin mentah Manufacturer atau data mesin Shipping."),
          (357, 222, 282, 248, "MFG", "Kebijakan Manufacturer", "global-orchestrator memperoleh scope agents, execute, dan read:shared, tetapi tidak finance. Portal enterprise lain hanya read:shared."),
          (652, 222, 874, 214, "SHP", "Kebijakan tiga enterprise lain", "Shipping, Distribution, dan Supplier masing-masing memiliki daftar principal dan scope sendiri. Permintaan di luar scope ditolak dengan HTTP 403, dan kunci yang tidak valid ditolak dengan 401.")],
         "Kepercayaan antar-organisasi: kerja sama agent tidak membutuhkan berbagi seluruh data, cukup scope minimal yang ditegakkan oleh kode di setiap API.")


if __name__ == "__main__":
    main()
    menus()
