"""Render docs/agent-code-map.svg: real code excerpts (read from the files, with line numbers) marking where each agent lives.
Re-run after code changes:  python scripts/make_agent_code_svg.py"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "agent-code-map.svg"

ENT = {"GLB": "#0b1b33", "MFG": "#1d4ed8", "SHP": "#0e7490", "DST": "#92400e", "SUP": "#5b21b6"}

# (agent, enterprise code, origin, file, function signature to find, lines to show, one-line role)
PANELS = [
    ("Orchestrator Agent", "GLB", "proposal", "backend/global_orchestrator/main.py", "def pipeline(", 16,
     "Receives the event, writes the task plan, fans out to all workers in parallel (ThreadPoolExecutor)."),
    ("A2A call to a worker agent", "GLB", "proposal", "backend/global_orchestrator/main.py", "def run_agent(", 13,
     "Each worker is called over HTTP on its own enterprise API, with an API key."),
    ("Stock Monitoring Agent", "MFG", "proposal", "backend/manufacturer_api/main.py", '@app.post("/agents/stock-monitoring/run"', 16,
     "Re-measures 22 silos, ARIMA stock-out time, low-stock events fired once."),
    ("ML Forecasting Agent", "MFG", "proposal", "backend/manufacturer_api/main.py", '@app.post("/agents/ml-forecasting/run"', 12,
     "LightGBM P10/P50/P90 for 14 days; champion vs TFT challenger (simulation mode)."),
    ("Demand & Priority Agent", "MFG", "proposal", "backend/manufacturer_api/main.py", '@app.post("/agents/demand-priority/run"', 11,
     "Eq. 14 priority grades; price and margin leave the enterprise only as grades."),
    ("Fleet Tracking Agent", "SHP", "proposal", "backend/shipping_api/main.py", '@app.post("/agents/fleet-tracking/run"', 16,
     "GPS, geofence + DBSCAN status, Random Forest ETA, Weibull failure risk per vessel."),
    ("Dispatch Planner Agent", "GLB", "proposal", "backend/global_orchestrator/main.py", "def plan_dispatch(", 14,
     "Combines priority and fleet options: SAW ship ranking and greedy assignment (deterministic)."),
    ("Narrator Agent", "GLB", "proposal", "backend/global_orchestrator/main.py", "def narrate(", 16,
     "Explains verified numbers; an optional LLM rewrite is rejected if it adds any number."),
    ("Distribution Agent", "DST", "extension", "backend/distribution_api/main.py", '@app.post("/agents/distribution/run"', 11,
     "Prototype extension: regional stock and orders at risk, bags converted to tons."),
    ("Procurement Agent", "SUP", "extension", "backend/supplier_api/main.py", '@app.post("/agents/procurement/run"', 13,
     "Prototype extension: supply coverage, alternative suppliers, production impact."),
]

W, COLS, PW, GAP, X0 = 1600, 2, 770, 20, 20
LH, HEAD = 15.5, 64


def excerpt(path, needle, n):
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    i = next(k for k, line in enumerate(lines) if line.lstrip().startswith(needle))
    return i + 1, lines[i:i + n]


def panel(x, y, agent, code, origin, path, needle, n, role):
    start, lines = excerpt(path, needle, n)
    h = HEAD + len(lines) * LH + 16
    c = ENT[code]
    out = [f'<g transform="translate({x},{y})">',
           f'<rect width="{PW}" height="{h}" fill="#ffffff" stroke="#c9d2de"/>',
           f'<rect width="{PW}" height="3" fill="{c}"/>',
           f'<rect x="14" y="14" width="40" height="17" fill="none" stroke="{c}"/>',
           f'<text x="34" y="27" text-anchor="middle" class="code" fill="{c}">{code}</text>',
           f'<text x="64" y="28" class="agent">{escape(agent)}</text>']
    if origin != "proposal":
        out.append(f'<text x="{PW - 14}" y="28" text-anchor="end" class="ext">PROTOTYPE EXTENSION</text>')
    else:
        out.append(f'<text x="{PW - 14}" y="28" text-anchor="end" class="ext">PROPOSAL AGENT</text>')
    out.append(f'<text x="14" y="48" class="role">{escape(role)}</text>')
    out.append(f'<text x="{PW - 14}" y="48" text-anchor="end" class="file">{escape(path)}:{start}</text>')
    out.append(f'<line x1="0" y1="{HEAD - 6}" x2="{PW}" y2="{HEAD - 6}" stroke="#e3e8ef"/>')
    # the agent's entry line gets the enterprise colour band
    out.append(f'<rect x="0" y="{HEAD - 2}" width="{PW}" height="{LH + 2}" fill="{c}" fill-opacity="0.09"/>')
    out.append(f'<rect x="0" y="{HEAD - 2}" width="3" height="{len(lines) * LH + 4}" fill="{c}"/>')
    for k, line in enumerate(lines):
        ty = HEAD + 10 + k * LH
        shown = line if len(line) <= 104 else line[:101] + "..."
        out.append(f'<text x="14" y="{ty}" class="ln">{start + k}</text>')
        out.append(f'<text x="52" y="{ty}" class="src" xml:space="preserve">{escape(shown)}</text>')
    out.append("</g>")
    return "\n".join(out), h


def main():
    parts, y_col = [], [150, 150]
    for i, p in enumerate(PANELS):
        col = i % COLS
        svg, h = panel(X0 + col * (PW + GAP), y_col[col], *p)
        parts.append(svg)
        y_col[col] += h + GAP
    H = max(y_col) + 40
    legend = "".join(f'<rect x="{X0 + 560 + i * 120}" y="96" width="34" height="16" fill="none" stroke="{c}"/>'
                     f'<text x="{X0 + 577 + i * 120}" y="108" text-anchor="middle" class="code" fill="{c}">{k}</text>'
                     f'<text x="{X0 + 600 + i * 120}" y="108" class="leg">{n}</text>'
                     for i, (k, c, n) in enumerate([("GLB", ENT["GLB"], "Global"), ("MFG", ENT["MFG"], "Manufacturer"),
                                                     ("SHP", ENT["SHP"], "Shipping"), ("DST", ENT["DST"], "Distribution"),
                                                     ("SUP", ENT["SUP"], "Supplier")]))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Archivo, 'Segoe UI', Arial, sans-serif">
<style>
.title {{font-size:28px; font-weight:800; fill:#0b1b33; letter-spacing:-0.5px;}}
.sub {{font-size:14px; fill:#3b4a63;}}
.agent {{font-size:16px; font-weight:700; fill:#0b1b33;}}
.role {{font-size:12px; fill:#3b4a63;}}
.file {{font-size:11px; fill:#5c6b82; font-family:Consolas, 'Courier New', monospace;}}
.ext {{font-size:10px; font-weight:700; letter-spacing:1.2px; fill:#5c6b82;}}
.code {{font-size:10px; font-weight:700; letter-spacing:1.2px;}}
.leg {{font-size:12px; fill:#3b4a63;}}
.ln {{font-size:11px; fill:#9aa8bb; font-family:Consolas, 'Courier New', monospace;}}
.src {{font-size:11.5px; fill:#0b1b33; font-family:Consolas, 'Courier New', monospace;}}
</style>
<rect width="{W}" height="{H}" fill="#f3f5f8"/>
<rect width="{W}" height="6" fill="#0b1b33"/>
<text x="{X0}" y="52" class="title">Where the agents live in the code</text>
<text x="{X0}" y="78" class="sub">Manufacturing Agentic System · each panel is a real excerpt (file:line) of one agent. Worker agents run inside their own enterprise API; the Global Orchestrator calls them over HTTP.</text>
<text x="{X0}" y="108" class="leg">Enterprise that hosts the agent:</text>
{legend}
<line x1="{X0}" y1="128" x2="{W - X0}" y2="128" stroke="#0b1b33"/>
{chr(10).join(parts)}
</svg>"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
