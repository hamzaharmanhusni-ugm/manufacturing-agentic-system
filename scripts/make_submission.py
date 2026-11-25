"""Package the course submission into one ZIP next to the project folder.

python scripts/make_submission.py
Contents: 01 report (DOCX, PDF), 02 presentation (PPTX, PDF), 03 source code (git archive of HEAD, so .venv,
local databases and third-party design references are excluded), 04 documentation and screenshots, BACA_DULU.txt."""
import io
import subprocess
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT.parent / "Manufacturing-Agentic-System_Pengumpulan.zip"
REPO = "https://github.com/hamzaharmanhusni-ugm/manufacturing-agentic-system"

README = f"""MANUFACTURING AGENTIC SYSTEM
Global Manufacturing & Cement Supply Chain: Multi-Enterprise Agentic AI Decision Support System
Mata kuliah: AI Agentic Technology Systems for Digital Enterprise Ecosystem
Dikemas: {date.today():%d-%m-%Y}

ISI
01_Laporan       Laporan ringkas (DOCX dan PDF): landasan teori, perancangan, demonstrasi aplikasi,
                 pengujian, dan proses agentic coding.
02_Presentasi    Slide presentasi kelas (PPTX dan PDF) beserta catatan pembicara.
03_Source_Code   Kode sumber lengkap: 4 API enterprise, Global Orchestrator, dashboard Streamlit,
                 decision engine, model ML, data sintetis, uji otomatis, agent dan skill Claude Code.
04_Dokumentasi   Arsitektur, dokumentasi API, panduan pengguna, skrip demo, proses agentic coding,
                 peta kode agent (SVG), diagram arsitektur, skema sistem,
                 ilustrasi agent, dan tangkapan layar aplikasi.

MENJALANKAN (Windows, Python 3.10 atau lebih baru)
  cd 03_Source_Code
  python -m venv .venv
  .venv\\Scripts\\pip install -r requirements.txt
  .venv\\Scripts\\python run_all.py              (Docker Desktop opsional; tanpa Docker otomatis menggunakan penyimpanan lokal)
  Buka http://localhost:3000
  Uji: .venv\\Scripts\\python -m pytest -q tests  dan  .venv\\Scripts\\python scripts\\smoke_test.py

DEMO YANG DISARANKAN
  Halaman "Live Operations 3D": Reset story, kecepatan 2 h/s, Play, lalu Approve pada strip Box 8.
  Urutan lengkap ada di 04_Dokumentasi/demo-script.md.

REPOSITORI PUBLIK
  {REPO}  (branch main: aplikasi, branch docs: dokumentasi)

CATATAN
  Seluruh data bersifat sintetis. Distribution dan Supplier adalah ekstensi prototipe.
  Aset pihak ketiga dan lisensinya tercantum di 03_Source_Code/frontend/static/THIRD_PARTY.md.
"""

DOCS = ["README.md", "ROADMAP.md", "docs/architecture.md", "docs/api.md", "docs/user-guide.md",
        "docs/demo-script.md", "docs/agentic-coding-process.md", "docs/public-api-research.md", "docs/agent-code-map.svg"]


def main():
    archive = subprocess.run(["git", "archive", "--format=zip", "HEAD"], cwd=ROOT, capture_output=True, check=True).stdout
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("BACA_DULU.txt", README.replace("\n", "\r\n"))
        for f in sorted((ROOT / "docs" / "report").glob("Laporan-*.*")):
            if f.suffix.lower() in (".docx", ".pdf"):
                z.write(f, f"01_Laporan/{f.name}")
        for f in sorted((ROOT / "docs" / "presentation").glob("Manufacturing-Agentic-System*.*")):
            z.write(f, f"02_Presentasi/{f.name}")
        with zipfile.ZipFile(io.BytesIO(archive)) as src:
            for info in src.infolist():
                # ponytail: docs media already sit in 01/02/04, skip the duplicate copy inside the source tree
                if not info.is_dir() and not info.filename.startswith(("docs/screenshots/", "docs/report/", "docs/presentation/", "docs/diagrams/")):
                    z.writestr(f"03_Source_Code/{info.filename}", src.read(info))
        for rel in DOCS:
            z.write(ROOT / rel, f"04_Dokumentasi/{Path(rel).name}")
        for f in sorted((ROOT / "docs" / "diagrams").glob("*.*")):
            z.write(f, f"04_Dokumentasi/diagrams/{f.name}")
        for f in sorted((ROOT / "Penjelasan Agentic").glob("*.*")):
            z.write(f, f"05_Penjelasan_Agentic/{f.name}")
        for f in sorted((ROOT / "docs" / "screenshots").glob("*.png")):
            if not f.name.startswith("before-"):
                z.write(f, f"04_Dokumentasi/screenshots/{f.name}")
    with zipfile.ZipFile(OUT) as z:
        names = z.namelist()
    tops = sorted({n.split("/")[0] for n in names})
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB, {len(names)} files): {', '.join(tops)}")
    missing = [d for d in ("01_Laporan", "02_Presentasi") if d not in tops]
    if missing:
        print("WARNING: missing", missing)


if __name__ == "__main__":
    main()
