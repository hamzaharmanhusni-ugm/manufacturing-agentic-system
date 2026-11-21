"""Draw the report/deck diagrams as SVG: system architecture, agentic loop schema, agent roster.

python scripts/make_diagrams.py   ->  docs/diagrams/*.svg   (PNG export: scripts/render_diagrams.mjs or any browser)
Content mirrors the code: AGENTS registry in backend/global_orchestrator/main.py, ports in shared/config.py."""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "docs" / "diagrams"
NAVY, INK, MUTED, RULE, PAPER = "#0b1b33", "#0b1b33", "#5b6b82", "#c9d3e1", "#f6f8fb"
ENT = {"GLB": NAVY, "MFG": "#1d4ed8", "SHP": "#0e7490", "DST": "#92400e", "SUP": "#5b21b6", "HUM": "#b45309"}
FONT = "Archivo, 'Segoe UI', Arial, sans-serif"


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.p = w, h, []

    def add(self, s):
        self.p.append(s)

    def rect(self, x, y, w, h, fill="#fff", stroke=RULE, sw=1.5, r=6, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, t, size=14, weight=400, fill=INK, anchor="start", ls=None, italic=False):
        lines = t if isinstance(t, list) else [t]
        ls = ls or size * 1.3
        st = ' font-style="italic"' if italic else ""
        for i, line in enumerate(lines):
            self.add(f'<text x="{x}" y="{y + i * ls}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{st}>{escape(line)}</text>')

    def chip(self, x, y, code, label=None):
        c = ENT[code]
        self.rect(x, y, 44, 20, "#fff", c, 1.5, 3)
        self.text(x + 22, y + 14.5, code, 11, 700, c, "middle")
        if label:
            self.text(x + 52, y + 15, label, 15, 700)

    def arrow(self, x1, y1, x2, y2, color=NAVY, sw=2, dash=None, label=None, lx=None, ly=None, head=True):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#ah)"' if head else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d}{m}/>')
        if label:
            self.text(lx if lx is not None else (x1 + x2) / 2 + 8, ly if ly is not None else (y1 + y2) / 2, label, 12, 600, MUTED)

    def path(self, d, color=NAVY, sw=2, dash=None, head=True, fill="none"):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#ah)"' if head else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{sw}"{da}{m}/>')

    def save(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">'
                '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{NAVY}"/></marker></defs>'
                f'<rect width="{self.w}" height="{self.h}" fill="{PAPER}"/>')
        (OUT / name).write_text(head + "".join(self.p) + "</svg>", encoding="utf-8")
        print("wrote", OUT / name)


def robot(s, cx, cy, color, scale=1.0, human=False):
    """Small robot glyph (or a person for the human approver)."""
    k = scale
    if human:
        s.add(f'<circle cx="{cx}" cy="{cy - 14 * k}" r="{13 * k}" fill="{color}"/>')
        s.add(f'<path d="M{cx - 24 * k},{cy + 30 * k} Q{cx},{cy - 4 * k} {cx + 24 * k},{cy + 30 * k} Z" fill="{color}"/>')
        s.rect(cx + 14 * k, cy + 4 * k, 18 * k, 14 * k, "#fff", color, 2, 2)
        s.text(cx + 23 * k, cy + 15 * k, "OK", 8 * k, 800, color, "middle")
        return
    s.add(f'<line x1="{cx}" y1="{cy - 34 * k}" x2="{cx}" y2="{cy - 24 * k}" stroke="{color}" stroke-width="{3 * k}"/>')
    s.add(f'<circle cx="{cx}" cy="{cy - 36 * k}" r="{4 * k}" fill="{color}"/>')
    s.rect(cx - 22 * k, cy - 24 * k, 44 * k, 30 * k, color, color, 1, 8 * k)
    s.add(f'<circle cx="{cx - 9 * k}" cy="{cy - 10 * k}" r="{5 * k}" fill="#fff"/><circle cx="{cx + 9 * k}" cy="{cy - 10 * k}" r="{5 * k}" fill="#fff"/>')
    s.add(f'<circle cx="{cx - 9 * k}" cy="{cy - 10 * k}" r="{2.2 * k}" fill="#22d3ee"/><circle cx="{cx + 9 * k}" cy="{cy - 10 * k}" r="{2.2 * k}" fill="#22d3ee"/>')
    s.rect(cx - 16 * k, cy + 9 * k, 32 * k, 24 * k, "#fff", color, 2.5 * k, 5 * k)
    s.rect(cx - 8 * k, cy + 15 * k, 16 * k, 8 * k, color, color, 1, 2)


# ------------------------------------------------------------------ 1 architecture
def architecture():
    s = Svg(1600, 1060)
    s.text(40, 52, "Arsitektur Sistem: Manufacturing Agentic System", 28, 800)
    s.text(40, 80, "Empat enterprise independen, satu Global Orchestrator, sembilan agent. Setiap kotak sesuai dengan layanan nyata di repositori.", 15, 400, MUTED)

    # users
    s.rect(40, 100, 1520, 70, "#fff", RULE)
    s.text(60, 128, "PENGGUNA · 7 PERAN RBAC", 12, 700, MUTED)
    roles = ["Global Administrator", "Manufacturer Manager", "Marketing Planner", "Operations Planner", "Shipping Manager", "Distributor Manager", "Supplier Manager"]
    for i, r in enumerate(roles):
        x = 60 + i * 212
        robot(s, x + 14, 152, ENT["HUM"], 0.45, human=True)
        s.text(x + 34, 158, r, 14, 600)

    s.arrow(800, 172, 800, 196, label="memilih peran, menyetujui keputusan", lx=812, ly=190)

    # presentation
    s.rect(40, 200, 1520, 92, "#fff", NAVY, 2)
    s.text(60, 228, "LAPISAN PRESENTASI · Dashboard Streamlit :3000", 13, 800, NAVY)
    pages = ["Control Center", "Live Operations 3D", "Simulation Center", "KPI & Analytics", "4 dashboard enterprise", "Architecture", "Governance & Security"]
    for i, pg in enumerate(pages):
        x = 60 + i * 212
        s.rect(x, 240, 196, 36, PAPER, RULE, 1, 4)
        s.text(x + 98, 263, pg, 13, 600, INK, "middle")

    s.arrow(800, 294, 800, 322, label="REST/JSON", lx=812, ly=314)

    # orchestrator
    s.rect(40, 326, 1520, 210, "#eef2f8", NAVY, 2.5)
    s.chip(60, 340, "GLB", "Global Orchestrator :8000  (FastAPI)")
    agents = [("Orchestrator Agent", ["menerima event, menyusun task plan,", "memanggil worker secara paralel"]),
              ("Dispatch Planner Agent", ["filter keras, ranking SAW,", "assignment greedy"]),
              ("Narrator Agent", ["menjelaskan angka terverifikasi,", "tidak pernah membuat angka"])]
    for i, (n, d) in enumerate(agents):
        x = 60 + i * 330
        s.rect(x, 376, 310, 92, "#fff", NAVY, 1.5)
        robot(s, x + 36, 420, NAVY, 0.7)
        s.text(x + 70, 404, n, 15, 700)
        s.text(x + 70, 426, d, 13, 400, MUTED, ls=17)
    s.rect(1050, 376, 230, 92, "#fff8ec", ENT["HUM"], 2)
    robot(s, 1084, 420, ENT["HUM"], 0.7, human=True)
    s.text(1116, 404, "Human approval", 15, 700)
    s.text(1116, 426, ["Box 8: Approve atau", "Reject per keputusan"], 13, 400, MUTED, ls=17)
    s.rect(1300, 376, 240, 92, "#fff", RULE)
    s.text(1316, 400, "Layanan pendukung", 14, 700)
    s.text(1316, 420, ["jam Live World dan alur cerita", "event bus, audit trail, KPI", "RBAC dan notifikasi"], 12.5, 400, MUTED, ls=16)
    s.text(60, 498, "Prinsip: code decides, AI explains, people act. Orchestrator tidak membaca basis data enterprise; ia hanya memanggil endpoint agent dengan API key.", 13, 500, MUTED)
    s.text(60, 520, "Agent tidak saling memanggil langsung. Semua pesan antar-agent tercatat di log pesan orchestrator.", 13, 500, MUTED)

    # A2A
    for x in (230, 610, 990, 1370):
        s.arrow(x, 538, x, 590, sw=2.2)
    s.text(420, 558, ["A2A HTTP paralel", "header X-API-Key"], 13, 700, NAVY, "middle", ls=18)
    s.text(800, 558, ["POST /agents/<nama>/run", "satu endpoint per agent"], 13, 700, NAVY, "middle", ls=18)
    s.text(1180, 558, ["scope dari kebijakan G_i", "401 atau 403 di luar scope"], 13, 700, NAVY, "middle", ls=18)

    ents = [("MFG", "Cement Manufacturing :8001", ["Stock Monitoring Agent", "ML Forecasting Agent", "Demand & Priority Agent"],
             "PostgreSQL (Docker)", "LightGBM, TFT, ARIMA", "harga dan margin tidak dibagikan mentah"),
            ("SHP", "Shipping & Logistics :8002", ["Fleet Tracking Agent"], "MongoDB (Docker)", "Random Forest ETA, Weibull, DBSCAN",
             "data mesin dan biaya charter internal"),
            ("DST", "Distribution :8003 (ekstensi)", ["Distribution Agent"], "SQLite", "agregasi permintaan regional", "data distributor rinci internal"),
            ("SUP", "Supplier & Procurement :8004 (ekstensi)", ["Procurement Agent"], "PostgreSQL dari CSV ERP", "cakupan pasokan, pemasok alternatif",
             "purchase order internal")]
    for i, (code, name, ags, db, ml, g) in enumerate(ents):
        x, c = 40 + i * 380, ENT[code]
        s.rect(x, 594, 360, 290, "#fff", c, 2.5)
        s.chip(x + 16, 608, code)
        s.text(x + 68, 623, name, 14.5, 700)
        for j, a in enumerate(ags):
            robot(s, x + 36, 680 + j * 52, c, 0.55)
            s.text(x + 62, 682 + j * 52, a, 14, 600)
        y = 812
        s.rect(x + 16, y - 6, 328, 66, PAPER, RULE, 1, 4)
        s.text(x + 28, y + 12, f"D · {db}", 12.5, 600)
        s.text(x + 28, y + 30, f"Model · {ml}", 12.5, 400, MUTED)
        s.text(x + 28, y + 48, f"G · {g}", 12.5, 400, MUTED)

    # world
    for x in (230, 610, 990, 1370):
        s.arrow(x - 40, 940, x - 40, 888, color=MUTED, dash="5 4")
        s.arrow(x + 40, 888, x + 40, 940, color=MUTED, dash="5 4")
    s.text(160, 920, "sensor dan data", 12, 600, MUTED, "end")
    s.text(1430, 920, "aksi yang disetujui", 12, 600, MUTED)
    s.rect(40, 944, 1520, 90, "#fff", RULE, 1.5, 6, dash="6 4")
    s.text(60, 972, "LINGKUNGAN (SIMULASI) · Live World", 13, 800, MUTED)
    s.text(60, 996, "22 silo di 9 packing plant (PP A sampai PP I) · 1 load port · 19 kapal (Ship A sampai Ship S) · cuaca laut dan gelombang · pemasok clinker", 14, 500)
    s.text(60, 1018, "Jam simulasi menguras silo setiap jam, menggerakkan kapal, dan memicu event. Assignment yang disetujui mengubah lingkungan: kapal berlayar dan silo terisi.", 13, 400, MUTED)
    s.save("architecture.svg")


# ------------------------------------------------------------------ 2 agentic loop
def loop():
    s = Svg(1600, 1080)
    s.text(40, 52, "Skema Sistem: Satu Siklus Agentic dari Event sampai Dampak di Dunia Nyata", 28, 800)
    s.text(40, 80, "Tujuh langkah ini sama dengan bilah langkah di halaman Live Operations 3D. Lingkungan yang berubah dibaca lagi oleh sensor, sehingga siklus tertutup.", 15, 400, MUTED)
    import math
    cx, cy, R = 800, 520, 330
    steps = [
        ("1", "EVENT", "Sensor IIoT: silo PP C 24%", ["aturan < 25% memicu event", "badai, pemasok, lonjakan"], "GLB", "Perceive"),
        ("2", "PLAN", "Orchestrator Agent", ["menyusun task plan", "memilih agent yang dipanggil"], "GLB", "Reason"),
        ("3", "WORK", "4 agent bekerja paralel", ["Stock, Forecast, Priority (MFG)", "Fleet Tracking (SHP)"], "MFG", "Reason"),
        ("4", "DECIDE", "Dispatch Planner Agent", ["filter keras, SAW, greedy", "kapal terbaik per plant"], "GLB", "Reason"),
        ("5", "EXPLAIN", "Narrator Agent", ["kalimat dari angka terverifikasi", "LLM opsional, dijaga"], "GLB", "Reason"),
        ("6", "ACT", "Manusia menyetujui (Box 8)", ["Approve atau Reject", "jam menunggu tanda tangan"], "HUM", "Act"),
        ("7", "WORLD", "Kapal berlayar, silo terisi", ["Shipping /assignments", "Manufacturer /incoming"], "SHP", "Act"),
    ]
    pos = []
    for i in range(7):
        a = -math.pi / 2 + i * 2 * math.pi / 7
        pos.append((cx + R * 1.32 * math.cos(a), cy + R * math.sin(a)))
    # ring arrows
    for i in range(7):
        x1, y1 = pos[i]; x2, y2 = pos[(i + 1) % 7]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        bx, by = cx + (mx - cx) * 1.18, cy + (my - cy) * 1.18
        T0, T1 = (0.40, 0.60) if i in (0, 3, 6) else (0.28, 0.72)
        s.path(f"M{x1 + (x2 - x1) * T0:.0f},{y1 + (y2 - y1) * T0:.0f} Q{bx:.0f},{by:.0f} {x1 + (x2 - x1) * T1:.0f},{y1 + (y2 - y1) * T1:.0f}",
               NAVY if i != 6 else ENT["SHP"], 2.5, dash=None if i != 6 else "7 5")
    for (n, k, title, desc, code, phase), (x, y) in zip(steps, pos):
        c = ENT[code]
        w, h = 300, 112
        s.rect(x - w / 2, y - h / 2, w, h, "#fff", c, 2.5)
        s.rect(x - w / 2, y - h / 2, 36, h, c, c, 1, 6)
        s.text(x - w / 2 + 18, y + 8, n, 22, 800, "#fff", "middle")
        s.text(x - w / 2 + 48, y - h / 2 + 24, k if k == phase.upper() else f"{k} · {phase.upper()}", 11.5, 800, c)
        s.text(x - w / 2 + 48, y - h / 2 + 46, title, 15, 700)
        s.text(x - w / 2 + 48, y - h / 2 + 68, desc, 12.5, 400, MUTED, ls=17)
    # centre
    s.rect(cx - 210, cy - 95, 420, 190, NAVY, NAVY, 1, 10)
    s.text(cx, cy - 52, "PERCEIVE  ›  REASON  ›  ACT", 20, 800, "#fff", "middle")
    s.text(cx, cy - 18, ["Closed loop: tindakan yang disetujui mengubah", "lingkungan, lalu sensor membaca perubahan itu.", "Jam simulasi berhenti saat agent bekerja dan", "saat keputusan menunggu manusia."],
           14, 400, "#e4ebf5", "middle", ls=21)
    # replanning
    s.rect(40, 960, 640, 96, "#fff", "#b91c1c", 2, 6)
    s.text(60, 988, "ADAPTIVE REPLANNING", 12, 800, "#b91c1c")
    s.text(60, 1012, ["Badai di rute PP F (gelombang 3,4 m) atau kapal terlambat menjadi event baru:", "kapal bermuatan melambat sekitar 14 jam, siklus berjalan ulang, rencana lama diganti."], 13.5, 400, INK, ls=19)
    s.rect(920, 960, 640, 96, "#fff", RULE, 1.5)
    s.text(940, 988, "KONSEP KULIAH PADA SIKLUS INI", 12, 800, MUTED)
    s.text(940, 1012, ["orchestrator-worker dan eksekusi paralel (Materi 4.2), utility function (4.7),", "LLM sebagai explainer (5.5), human-in-the-loop (2.6), feedback loop (3.8)"], 13.5, 400, INK, ls=19)
    s.save("agentic-loop.svg")


# ------------------------------------------------------------------ 3 agent roster
ROSTER = [
    ("Orchestrator Agent", "GLB", "Koordinator", "event sensor, cuaca, pemasok", "menyusun task plan, memilih agent", "memanggil 4 agent paralel, menggabungkan hasil"),
    ("Stock Monitoring Agent", "MFG", "Reaktif + model-based", "level 22 silo, dead stock, kedatangan", "usable stock, days of cover, ARIMA", "low-stock event, dikirim sekali"),
    ("ML Forecasting Agent", "MFG", "Learning agent", "riwayat penjualan 400 hari, S&OP", "LightGBM quantile, TFT challenger", "forecast 14 hari P10/P50/P90, WAPE"),
    ("Demand & Priority Agent", "MFG", "Utility-based", "forecast, stock-out, harga, margin", "grade 1 sampai 5, bobot Pers. 14", "ranking packing plant"),
    ("Fleet Tracking Agent", "SHP", "Model-based + learning", "GPS 19 kapal, cuaca, riwayat voyage", "geofence, DBSCAN, RF ETA, Weibull", "ketersediaan armada, peringatan risiko"),
    ("Dispatch Planner Agent", "GLB", "Deliberatif, utility-based", "ranking plant, opsi kapal, stok port", "filter keras, SAW, greedy", "rencana dispatch dan 3 alternatif"),
    ("Narrator Agent", "GLB", "LLM explainer", "angka yang sudah diverifikasi", "template atau LLM dengan penjaga angka", "penjelasan di Box 7"),
    ("Distribution Agent", "DST", "Reaktif (ekstensi)", "stok regional, pesanan distributor", "pesanan berisiko, lonjakan", "sinyal permintaan ke orchestrator"),
    ("Procurement Agent", "SUP", "Deliberatif (ekstensi)", "stok clinker, PO, pemasok", "cakupan pasokan, pemasok alternatif", "faktor kapasitas produksi"),
    ("Human approver", "HUM", "Human in the loop", "rencana, narasi, peringatan", "penilaian manusia sesuai peran", "Approve atau Reject di Box 8"),
]


def roster():
    s = Svg(1600, 900)
    s.text(40, 52, "Para Agent sebagai Tim Kerja Digital", 28, 800)
    s.text(40, 80, "Sembilan agent dan satu manusia, masing-masing dengan persepsi, penalaran, dan tindakan sendiri. Warna menunjukkan enterprise pemilik agent.", 15, 400, MUTED)
    W, H = 296, 372
    for i, (name, code, kind, p, r, a) in enumerate(ROSTER):
        x, y = 40 + (i % 5) * (W + 10), 104 + (i // 5) * (H + 16)
        c = ENT[code]
        s.rect(x, y, W, H, "#fff", c, 2.5, 8)
        s.rect(x, y, W, 112, c, c, 1, 8)
        s.rect(x, y + 100, W, 14, c, c, 1, 0)
        s.add(f'<circle cx="{x + 60}" cy="{y + 58}" r="40" fill="#fff" opacity="0.95"/>')
        robot(s, x + 60, y + 60, c, 0.95, human=(code == "HUM"))
        s.text(x + 112, y + 40, "PENGAWAS" if code == "HUM" else code, 12, 800, "#fff")
        s.text(x + 112, y + 62, kind, 13, 600, "#fff")
        s.text(x + 16, y + 142, name, 17, 800)
        for j, (lab, val) in enumerate((("PERCEIVE", p), ("REASON", r), ("ACT", a))):
            yy = y + 172 + j * 64
            s.text(x + 16, yy, lab, 11, 800, c)
            words, lines, cur = val.split(), [], ""
            for wd in words:
                if len(cur) + len(wd) > 32:
                    lines.append(cur); cur = wd
                else:
                    cur = (cur + " " + wd).strip()
            lines.append(cur)
            s.text(x + 16, yy + 20, lines, 13.5, 500, INK, ls=18)
    s.save("agent-roster.svg")


if __name__ == "__main__":
    architecture()
    loop()
    roster()
