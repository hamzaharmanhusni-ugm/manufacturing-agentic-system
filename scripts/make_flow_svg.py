"""Beginner-friendly flow explainer: one dispatch cycle in 8 steps, with a real example and where to see it in the app.

python scripts/make_flow_svg.py  ->  docs/diagrams/alur-kerja-sistem.svg"""
from make_diagrams import ENT, INK, MUTED, NAVY, Svg, robot

WORLD = "#64748b"


def wrap(text, n):
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + 1 > n:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + [cur]


STEPS = [
    ("WORLD", "Dunia nyata berubah", "Setiap jam plant menjual semen, sehingga isi silo terus turun. Kapal juga terus bergerak di laut.",
     "Isi silo PCC di PP C turun sampai 24%, cukup untuk sekitar 1,6 hari.", "Live Operations 3D: gauge silo di peta", "isi silo terus turun"),
    ("MFG", "Sensor membunyikan alarm", "Begitu isi silo di bawah 25%, sensor mengirim event secara otomatis. Tidak ada orang yang menekan tombol.",
     "Event: sensor silo PP C PCC 24% (aturan: di bawah 25%).", "Suar oranye berkedip, langkah 1 di bilah bawah", "event: silo PP C 24%"),
    ("GLB", "Orchestrator membagi tugas", "Orchestrator bekerja seperti manajer proyek: membaca event, lalu menugaskan empat agent sekaligus.",
     "Tugas dikirim bersamaan ke Stock Monitoring, ML Forecasting, Demand & Priority, dan Fleet Tracking.", "Amplop terbang dari robot navy ke robot lain", "empat tugas dikirim paralel"),
    ("MFG", "Empat agent bekerja bersamaan", "Setiap agent menjawab satu pertanyaan dari data enterprise-nya sendiri:",
     "PP C menjadi plant paling mendesak, dan Ship N siap di load port.", "Layar di atas robot, Kotak 2 sampai 5 di docket", "jawaban keempat agent"),
    ("GLB", "Dispatch Planner memilih kapal", "Semua jawaban digabung. Kapal yang tidak layak dibuang (maintenance, gelombang di atas 2,5 m), lalu sisanya diberi skor SAW.",
     "Rekomendasi: Ship N ke PP C membawa 4.957 ton PCC.", "Kotak 6 Dispatch plan", "rencana dispatch"),
    ("GLB", "Narrator menjelaskan", "Angka diubah menjadi kalimat yang mudah dibaca manusia. Narrator tidak boleh membuat angka baru.",
     "Penjelasan: alasan PP C diprioritaskan dan alasan Ship N dipilih, menggunakan angka dari langkah sebelumnya.", "Kotak 7 Narrator remarks", "rencana dan penjelasan"),
    ("HUM", "Manusia memutuskan", "Jam simulasi berhenti. Pengguna berwenang membaca rencana, lalu menekan Approve atau Reject.",
     "Global Administrator menekan Approve; keputusan tercatat di audit trail.", "Strip Box 8 Authorisation", "keputusan: disetujui"),
    ("SHP", "Kapal berlayar, silo terisi", "Shipping menerima tugas. Kapal memuat 12 jam, berlayar, lalu membongkar 18 jam di plant tujuan.",
     "Ship N membongkar 4.957 ton PCC di PP C, dan gauge silo naik kembali.", "Kapal bergerak di peta, gauge silo naik", None),
]
QUESTIONS = [("MFG", "Stock Monitoring", "Berapa hari lagi stok habis?"), ("MFG", "ML Forecasting", "Berapa permintaan 14 hari ke depan?"),
             ("MFG", "Demand & Priority", "Plant mana yang paling mendesak?"), ("SHP", "Fleet Tracking", "Kapal mana yang siap, dan kapan tiba?")]


def main():
    W, X0, CW = 1400, 60, 1220
    s = Svg(W, 2560)
    s.text(X0, 60, "Cara Kerja Sistem dalam 8 Langkah", 34, 800)
    s.text(X0, 94, "Contoh nyata dari aplikasi: silo semen di PP C hampir kosong. Baca dari atas ke bawah; setiap warna menunjukkan siapa yang bekerja.", 16, 400, MUTED)
    legend = [("WORLD", "Dunia nyata"), ("MFG", "Manufacturer"), ("SHP", "Shipping"), ("GLB", "Global Orchestrator"), ("HUM", "Manusia")]
    lx = X0
    for code, name in legend:
        c = WORLD if code == "WORLD" else ENT[code]
        s.add(f'<circle cx="{lx + 9}" cy="128" r="9" fill="{c}"/>')
        s.text(lx + 26, 133, name, 15, 600)
        lx += 60 + len(name) * 9

    y = 170
    for i, (code, title, what, example, where, handoff) in enumerate(STEPS):
        c = WORLD if code == "WORLD" else ENT[code]
        h = 300 if i == 3 else 220
        s.rect(X0, y, CW, h, "#fff", c, 2.5, 12)
        s.add(f'<circle cx="{X0 + 50}" cy="{y + 52}" r="30" fill="{c}"/>')
        s.text(X0 + 50, y + 62, str(i + 1), 28, 800, "#fff", "middle")
        gx, gy = X0 + 50, y + 150
        if code == "WORLD":
            s.add(f'<rect x="{gx - 22}" y="{gy - 40}" width="20" height="56" rx="4" fill="{c}"/><rect x="{gx + 4}" y="{gy - 28}" width="20" height="44" rx="4" fill="{c}" opacity="0.6"/>')
            s.add(f'<path d="M{gx - 34},{gy + 30} q12,-10 24,0 t24,0 t24,0" fill="none" stroke="{c}" stroke-width="3"/>')
        else:
            robot(s, gx, gy, c, 0.9, human=(code == "HUM"))
        tx = X0 + 110
        s.text(tx, y + 48, title, 24, 800)
        lines = wrap(what, 70)
        s.text(tx, y + 80, lines, 16, 400, INK, ls=23)
        if i == 3:
            for j, (qc, qn, qq) in enumerate(QUESTIONS):
                qy = y + 80 + 23 * len(lines) + 6 + j * 30
                s.add(f'<circle cx="{tx + 8}" cy="{qy - 5}" r="6" fill="{ENT[qc]}"/>')
                s.text(tx + 22, qy, qn, 15, 700, ENT[qc])
                s.text(tx + 190, qy, qq, 15, 400)
        # example box on the right
        ex, ew = X0 + 740, 450
        s.rect(ex, y + 22, ew, h - 44 - 46, "#f1f5f9", "#f1f5f9", 0, 8)
        s.text(ex + 18, y + 50, "CONTOH NYATA", 12, 800, c)
        s.text(ex + 18, y + 76, wrap(example, 48), 15, 500, INK, ls=21)
        # where in the app
        s.rect(ex, y + h - 62, ew, 40, "#fff", c, 1.5, 20)
        s.text(ex + 18, y + h - 36, "Di aplikasi: " + where, 13.5, 600, c)
        y += h
        if handoff:
            s.arrow(X0 + 50, y + 4, X0 + 50, y + 52, color=MUTED, sw=3)
            s.text(X0 + 80, y + 34, handoff, 14, 600, MUTED, italic=True)
            y += 58

    # loop back arrow on the right edge
    top, bot = 170 + 110, y - 110
    s.path(f"M{X0 + CW},{bot} C{X0 + CW + 70},{bot} {X0 + CW + 70},{top} {X0 + CW + 8},{top}", "#0e7490", 3, dash="9 6")
    s.add(f'<text x="{X0 + CW + 44}" y="{(top + bot) / 2}" font-size="15" font-weight="700" fill="#0e7490" text-anchor="middle" transform="rotate(-90 {X0 + CW + 44} {(top + bot) / 2})">Sensor membaca dunia yang sudah berubah, lalu siklus dimulai lagi</text>')

    y += 40
    bw = (CW - 30) / 2
    s.rect(X0, y, bw, 190, "#fff", "#b91c1c", 2.5, 12)
    s.text(X0 + 24, y + 38, "Bagaimana jika ada badai?", 20, 800, "#b91c1c")
    s.text(X0 + 24, y + 70, wrap("Layanan cuaca melaporkan gelombang 3,4 m di rute PP F. Kapal bermuatan melambat sekitar 14 jam. Kejadian ini menjadi event baru: sistem kembali ke langkah 3, agent menyusun rencana baru, dan manusia menyetujuinya di langkah 7.", 62), 15, 400, INK, ls=22)
    x2 = X0 + bw + 30
    s.rect(x2, y, bw, 190, NAVY, NAVY, 1, 12)
    s.text(x2 + 24, y + 38, "Cukup ingat tiga kalimat ini", 20, 800, "#fff")
    rows = [("Kode memutuskan", "langkah 4 dan 5: model ML dan SAW menghitung angka"), ("AI menjelaskan", "langkah 6: Narrator merangkai kalimat"), ("Manusia bertindak", "langkah 7: tidak ada kapal berangkat tanpa Approve")]
    for j, (a, b) in enumerate(rows):
        s.text(x2 + 24, y + 78 + j * 36, a, 17, 800, "#7dd3fc")
        s.text(x2 + 210, y + 78 + j * 36, b, 14.5, 400, "#e4ebf5")
    s.h = int(y + 230)
    s.save("alur-kerja-sistem.svg")


PHASES = [
    ("MFG", "AMATI", "Perceive", "Dunia berubah: silo terkuras, kapal bergerak, cuaca berganti. Sensor dan agent pemantau membaca perubahan itu dan mengirim event.",
     ["Sensor silo IIoT", "Stock Monitoring", "Fleet Tracking", "Distribution, Procurement"], "Gauge silo dan kapal di peta"),
    ("GLB", "PIKIRKAN", "Reason", "Orchestrator membagi tugas. Agent menghitung forecast, prioritas plant, dan ranking kapal, lalu Narrator menjelaskan hasilnya.",
     ["Orchestrator", "ML Forecasting, Demand & Priority", "Dispatch Planner (SAW)", "Narrator"], "Box 1 sampai 7 di docket"),
    ("HUM", "PUTUSKAN", "Decide", "Manusia membaca rencana beserta penjelasannya, lalu menekan Approve atau Reject. Tanpa persetujuan, tidak ada kapal yang berangkat.",
     ["Global Administrator", "Manufacturer Manager", "Shipping Manager"], "Box 8 Authorisation"),
    ("SHP", "BERTINDAK", "Act", "Rencana dikirim ke API Shipping dan Manufacturer. Kapal memuat, berlayar, dan membongkar muatan, sehingga silo terisi kembali.",
     ["Shipping API (assignment)", "Manufacturer API (jadwal tiba)", "Kapal di dunia nyata"], "Kapal berlayar, gauge silo naik"),
]


def overview():
    s = Svg(1600, 960)
    s.text(60, 64, "Alur Kerja Secara Garis Besar", 34, 800)
    s.text(60, 98, "Empat tahap yang terus berulang. Setiap tahap dikerjakan oleh pihak yang berbeda, dan manusia selalu memegang keputusan.", 17, 400, MUTED)
    cw, gap, y0, ch = 335, 60, 140, 520
    for i, (code, name, en, what, who, where) in enumerate(PHASES):
        x, c = 60 + i * (cw + gap), ENT[code]
        s.rect(x, y0, cw, ch, "#fff", c, 2.5, 14)
        s.rect(x, y0, cw, 86, c, c, 1, 14)
        s.rect(x, y0 + 70, cw, 16, c, c, 1, 0)
        s.text(x + 24, y0 + 54, f"{i + 1}  {name}", 28, 800, "#fff")
        s.text(x + cw - 22, y0 + 54, en, 16, 600, "#e4ebf5", "end")
        robot(s, x + cw / 2, y0 + 150, c, 1.1, human=(code == "HUM"))
        s.text(x + 24, y0 + 222, "APA YANG TERJADI", 12, 800, c)
        s.text(x + 24, y0 + 246, wrap(what, 36), 15.5, 400, INK, ls=22)
        s.text(x + 24, y0 + 352, "SIAPA", 12, 800, c)
        for j, w in enumerate(who):
            s.add(f'<circle cx="{x + 30}" cy="{y0 + 372 + j * 24}" r="4" fill="{c}"/>')
            s.text(x + 42, y0 + 377 + j * 24, w, 14.5, 600)
        s.rect(x + 16, y0 + ch - 50, cw - 32, 34, PAPER_TINT, PAPER_TINT, 0, 17)
        s.text(x + cw / 2, y0 + ch - 28, "Di aplikasi: " + where, 13, 700, c, "middle")
        if i < 3:
            s.arrow(x + cw + 8, y0 + 150, x + cw + gap - 8, y0 + 150, color=NAVY, sw=4)
    # loop back
    yl = y0 + ch + 30
    s.path(f"M{60 + 3 * (cw + gap) + cw / 2},{y0 + ch + 4} L{60 + 3 * (cw + gap) + cw / 2},{yl + 40} L{60 + cw / 2},{yl + 40} L{60 + cw / 2},{y0 + ch + 8}", "#0e7490", 3, dash="9 6")
    s.rect(560, yl + 22, 480, 36, "#f6f8fb", "#f6f8fb", 0, 0)
    s.text(800, yl + 46, "Dunia sudah berubah, sensor membaca lagi, siklus berulang", 15, 700, "#0e7490", "middle")
    yb = yl + 80
    s.rect(60, yb, 700, 120, "#fff", "#b91c1c", 2.5, 12)
    s.text(84, yb + 34, "Ada badai atau kapal terlambat?", 18, 800, "#b91c1c")
    s.text(84, yb + 62, wrap("Kejadian itu masuk sebagai event baru di tahap AMATI. Sistem kembali ke tahap PIKIRKAN dan menyusun rencana baru, lalu manusia menyetujuinya lagi.", 78), 15, 400, INK, ls=21)
    s.rect(790, yb, 750, 120, NAVY, NAVY, 1, 12)
    s.text(814, yb + 34, "Pembagian peran", 18, 800, "#fff")
    s.text(814, yb + 66, "Kode memutuskan", 16, 800, "#7dd3fc")
    s.text(990, yb + 66, "angka dihitung model ML dan SAW di tahap PIKIRKAN", 14.5, 400, "#e4ebf5")
    s.text(814, yb + 96, "Manusia bertindak", 16, 800, "#7dd3fc")
    s.text(990, yb + 96, "tidak ada tindakan tanpa persetujuan di tahap PUTUSKAN", 14.5, 400, "#e4ebf5")
    s.h = yb + 150
    s.save("alur-kerja-garis-besar.svg")


PAPER_TINT = "#f1f5f9"

if __name__ == "__main__":
    main()
    overview()
