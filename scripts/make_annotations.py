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
PANEL = 620


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


def make(name, shot, step, title, subtitle, marks, concept):
    """marks: list of (x, y, w, h, colour, heading, text) on the 1600x1000 screenshot."""
    im = Image.open(SHOTS / shot).convert("RGB")
    W, H = im.size
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
    d.text((px, 30), f"LANGKAH {step}", fill=COL["SKY"], font=F(17, True))
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


if __name__ == "__main__":
    main()
