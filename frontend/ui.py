"""Dispatch Manifest design system: ruled form stock, navy ink, printed state marks, authorisation stamps.
Direction contract: .impeccable/surfaces/frontend-app-py.md. Tokens are mirrored in frontend/charts.py."""
import html

import pandas as pd
import streamlit as st

from client import denied, role
from shared.rbac import ROLES

CSS = """
<style>
:root {
  --ink:#0b1b33; --ink2:#3b4a63; --ink3:#5c6b82; --ground:#f3f5f8; --stock:#ffffff; --rule:#c9d2de; --rule2:#e3e8ef;
  --act:#1d4ed8; --live:#0e7490; --live-fill:#0891b2; --alarm:#b91c1c; --ok:#15803d; --wait:#b45309; --appr:#5b21b6;
  --hl:#fff4d6;
}
::selection {background:#cfe3ff; color:var(--ink);}
html {scrollbar-color: #9aa8bb var(--ground);}
.block-container {padding-top:2.3rem; padding-bottom:3rem; max-width:1600px;}
[data-testid="stAppViewContainer"] * {font-variant-numeric: tabular-nums;}
h1 {font-size:1.6rem !important; font-weight:750 !important; letter-spacing:-0.02em; font-stretch:92%; padding:0 !important; margin:0 !important;}
h2, h3 {font-weight:700 !important; letter-spacing:-0.01em;}
h3 {font-size:1rem !important;}
a {text-underline-offset:3px;}
:focus-visible {outline:2px solid var(--act) !important; outline-offset:2px;}

/* page head */
.ph {display:flex; align-items:flex-end; justify-content:space-between; gap:16px; border-bottom:2px solid var(--ink); padding-bottom:8px; margin-bottom:14px;}
.ph .sub {font-size:.86rem; color:var(--ink2); margin-top:3px;}
.ph .flag {font-size:.7rem; font-weight:650; letter-spacing:.09em; text-transform:uppercase; color:var(--ink2); border:1px solid var(--rule); padding:2px 8px; background:var(--stock); white-space:nowrap;}

/* section rule */
.sec {display:flex; align-items:baseline; justify-content:space-between; gap:12px; border-bottom:1px solid var(--ink); padding:18px 0 5px; margin-bottom:10px;}
.sec .t {font-size:1rem; font-weight:700; color:var(--ink); letter-spacing:-0.005em;}
.sec .c {font-size:.78rem; color:var(--ink3); text-align:right;}

/* ledger strip (replaces KPI cards): one ruled row of fields */
.ledger {display:grid; grid-auto-flow:column; grid-auto-columns:1fr; border:1px solid var(--ink); background:var(--stock);}
.ledger .f {padding:6px 12px 6px; border-left:1px solid var(--rule); min-width:0;}
.ledger .f:first-child {border-left:0;}
.lbl {font-size:.68rem; font-weight:650; letter-spacing:.08em; text-transform:uppercase; color:var(--ink3); font-stretch:88%; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.ledger .v {display:block; font-size:1.35rem; font-weight:700; line-height:1.2; color:var(--ink); letter-spacing:-0.02em; white-space:nowrap; margin-right:6px;}
.ledger .s {display:block; font-size:.72rem; color:var(--ink3); white-space:normal; line-height:1.25;}
.ledger .f.bad .v {color:var(--alarm);} .ledger .f.warn .v {color:var(--wait);} .ledger .f.appr .v {color:var(--appr);}

/* printed state marks */
.mk {display:inline-block; width:9px; height:9px; border:1.5px solid var(--ink3); margin-right:6px; vertical-align:-1px; flex:0 0 auto;}
.m-ok {background:var(--ink); border-color:var(--ink);}
.m-run {background:var(--live-fill); border-color:var(--live-fill); animation: blink 1.2s steps(2, jump-none) infinite;}
.m-wait {border-color:var(--wait);}
.m-appr {border-color:var(--appr); background: var(--stock); box-shadow: inset 0 0 0 2px var(--stock), inset 0 0 0 5px var(--appr);}
.m-fail {background:var(--alarm); border-color:var(--alarm);}
.m-idle {border-color:#9aa8bb;}
@keyframes blink {50% {opacity:.35;}}
.st {display:inline-flex; align-items:center; font-size:.72rem; font-weight:650; letter-spacing:.06em; text-transform:uppercase; color:var(--ink2); white-space:nowrap;}
.st.s-fail {color:var(--alarm);} .st.s-run {color:var(--live);} .st.s-appr {color:var(--appr);} .st.s-wait {color:var(--wait);}
.struck {text-decoration:line-through; text-decoration-thickness:1px; color:var(--ink3);}

/* enterprise code chips */
.ec {display:inline-block; font-size:.66rem; font-weight:700; letter-spacing:.1em; padding:0 5px; border:1px solid currentColor; line-height:1.5; vertical-align:1px; white-space:nowrap;}
.tag {display:inline-block; white-space:normal; font-size:.68rem; font-weight:650; letter-spacing:.06em; text-transform:uppercase; color:var(--ink2); border:1px solid var(--rule); padding:0 6px; margin-left:6px; vertical-align:2px; background:var(--stock);}

/* docket */
.dk-head {display:flex; flex-wrap:wrap; justify-content:space-between; gap:6px 24px; align-items:baseline; background:var(--ink); color:#fff; padding:10px 14px;}
.dk-head .no {font-size:1.5rem; font-weight:750; letter-spacing:-0.01em; line-height:1.1;}
.dk-head .lbl {color:#9fb2cf;}
.dk-head .meta {display:flex; gap:24px; justify-content:flex-end; flex-wrap:wrap;}
.dk-head .meta > div {display:flex; align-items:baseline; gap:6px;}
.dk-head .meta b {font-size:.92rem; font-weight:650; color:#fff;}
.dk-head .st, .dk-head .st.s-run {color:#bfe9f5;}
.dk-row {display:grid; border:1px solid var(--rule); border-top:0; background:var(--stock);}
.dk-row .box {border:0; border-left:1px solid var(--rule);}
.dk-row .box:first-child {border-left:0;}
.dk-note {font-size:.76rem; color:var(--live); padding:5px 0 10px;}
.box {background:var(--stock); border:1px solid var(--rule); padding:9px 11px 8px; height:100%; display:flex; flex-direction:column; gap:6px; transition: opacity .3s ease-out, box-shadow .3s ease-out;}
.box .bh {border-bottom:1px solid var(--rule2); padding-bottom:6px; display:flex; flex-direction:column; gap:2px;}
.box .bh .top {display:flex; justify-content:space-between; align-items:baseline; gap:8px;}
.bn {font-size:.66rem; font-weight:700; letter-spacing:.1em; color:var(--ink3); margin-right:4px;}
.box.short {height:auto; margin-bottom:8px;}
.auth-h {display:flex; justify-content:space-between; align-items:baseline; border-bottom:1px solid var(--ink); padding-bottom:5px; margin-bottom:2px;}
.auth-h .bt {font-size:.92rem; font-weight:700;}
.auth-row {border-top:1px solid var(--rule2); padding-top:6px; margin-bottom:1.15rem; font-size:.84rem; line-height:1.35;}
.box .bt {font-size:.92rem; font-weight:700; color:var(--ink); line-height:1.2;}
.box .body {font-size:.82rem; color:var(--ink2); line-height:1.45; flex:1;}
.box .body ul {padding-left:16px; margin:0;}
.box .body li {margin:0 0 2px 0;}
.box .sig {border-top:1px dashed var(--rule); padding-top:5px; font-size:.72rem; color:var(--ink3); display:flex; justify-content:space-between; gap:6px; flex-wrap:wrap;}
.box .sig i {font-style:normal; color:var(--ink); font-weight:600;}
.box.empty .body {color:var(--ink3);}
.dim .box:not(.live) {opacity:.5;}
.dk-row .box.live {outline:1px solid var(--live-fill); outline-offset:-1px; position:relative; z-index:1;}
.box.live {border-color:var(--live-fill); box-shadow:0 3px 14px rgba(11,27,51,.16);}
.par-tag {font-size:.66rem; font-weight:700; letter-spacing:.1em; color:var(--live); text-transform:uppercase; border-top:1px solid var(--live-fill); padding-top:3px; margin:6px 0 4px;}

/* ruled tables */
table.rt {border-collapse:collapse; width:100%; font-size:.82rem; background:var(--stock);}
table.rt th {font-size:.66rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--ink3); text-align:left; border-bottom:1px solid var(--ink); padding:5px 8px; font-stretch:88%; white-space:nowrap;}
table.rt td {border-bottom:1px solid var(--rule2); padding:5px 8px; color:var(--ink); vertical-align:top;}
table.rt td.n, table.rt th.n {text-align:right;}
table.rt tr.chg td {background:var(--hl);}
.late {color:var(--alarm); font-weight:650;}

/* stamps */
.stamp {display:inline-block; border:3px double currentColor; padding:2px 10px; font-size:.82rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase;
  transform:rotate(-4deg); color:var(--act); animation: land .45s cubic-bezier(.16,1,.3,1) both;}
.stamp.rej {color:var(--alarm);} .stamp.sup {color:var(--ink3);}
@keyframes land {from {transform:rotate(-4deg) scale(1.6); opacity:0;} to {transform:rotate(-4deg) scale(1); opacity:1;}}
@media (prefers-reduced-motion: reduce) {.stamp, .m-run {animation:none;}}
@media (max-width: 640px) {
  .ledger {grid-auto-flow:row; grid-template-columns:1fr 1fr;}
  .ledger .f {border-left:0; border-top:1px solid var(--rule);}
  .ledger .v {font-size:1.3rem;}
  .ph {flex-direction:column; align-items:flex-start;}
  .dk-head .meta {justify-content:flex-start;}
  .box {min-height:0;}
  .block-container {padding-top:3.6rem !important;}
  .dk-row {grid-template-columns:1fr !important;}
  .dk-row .box {border-left:0; border-top:1px solid var(--rule);}
}

/* manifest log (agent-to-agent messages) */
.log {border-top:1px solid var(--ink);}
.lg {display:grid; grid-template-columns: 58px minmax(0,1fr); gap:10px; padding:6px 2px; border-bottom:1px solid var(--rule2); font-size:.8rem;}
.lg .tm {color:var(--ink3); font-size:.72rem; padding-top:1px;}
.lg .rt2 {color:var(--ink2); font-size:.74rem; margin-bottom:2px;}
.lg .rt2 b {color:var(--ink); font-weight:650;}
.lg .tx {color:var(--ink); line-height:1.4; overflow-wrap:anywhere;}
.lg.negotiation .tx {font-weight:600;}
.lg.error .tx {color:var(--alarm);}

/* registry slips (agents) */
.slips {display:grid; grid-template-columns:repeat(auto-fill, minmax(230px, 1fr)); border-top:1px solid var(--ink); border-left:1px solid var(--rule);}
.slip {border-right:1px solid var(--rule); border-bottom:1px solid var(--rule); background:var(--stock); padding:8px 10px; display:flex; flex-direction:column; gap:4px; min-width:0;}
.slip .nm {font-weight:700; font-size:.86rem; color:var(--ink); line-height:1.25;}
.slip .rl {font-size:.75rem; color:var(--ink3); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.slip .ln {display:flex; justify-content:space-between; gap:6px; font-size:.74rem; color:var(--ink2);}

/* route slip (pipeline) */
.pipe {display:flex; align-items:center; overflow-x:auto; padding:4px 0 8px;}
.pipe .ar {flex:0 0 14px; height:1px; background:var(--ink); margin:0 3px;}
.pipe .par {display:flex; flex-direction:column; gap:4px; padding:16px 5px 5px; border:1px dashed var(--live-fill); position:relative;}
.pipe .par::before {content:"parallel"; position:absolute; top:2px; left:6px; font-size:.62rem; font-weight:700; color:var(--live); text-transform:uppercase; letter-spacing:.1em;}
.step {flex:0 0 auto; min-width:118px; max-width:160px; background:var(--stock); border:1px solid var(--rule); padding:5px 8px; font-size:.75rem; line-height:1.35;}
.step .n {font-weight:700; color:var(--ink); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.step .d {color:var(--ink3); display:flex; justify-content:space-between; gap:6px;}

/* enterprise ledger */
.ent {background:var(--stock); border:1px solid var(--rule); padding:8px 11px; display:flex; flex-direction:column; gap:3px;}
.ent .nm {font-weight:700; font-size:.92rem; color:var(--ink);}
.ent .ln {display:flex; justify-content:space-between; gap:8px; font-size:.76rem; color:var(--ink2);}

/* notices */
.notice {border:1px solid var(--wait); background:#fffaf0; padding:7px 10px; margin-bottom:6px; font-size:.82rem; color:var(--ink);}
.notice.critical {border-color:var(--alarm); background:#fff5f5;}
.notice.info {border-color:var(--rule); background:var(--stock);}
.notice .t {font-weight:700;}

.subtle {color:var(--ink3); font-size:.82rem;}

/* Streamlit widgets in the manifest grammar */
[class*="st-key-auth"] {background:var(--stock); border:1px solid var(--ink); padding:10px 12px 14px !important; gap:6px !important;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:0 !important;}
.stButton button, .stDownloadButton button, [data-testid="stPageLink"] a {border-radius:2px !important; font-weight:650; letter-spacing:.01em;}
.stButton button[kind="secondary"] {background:var(--stock); border:1px solid var(--ink); color:var(--ink);}
.stButton button[kind="primary"] {background:var(--act); border:1px solid var(--act);}
[data-testid="stTabs"] [data-baseweb="tab-list"] {border-bottom:1px solid var(--ink); gap:18px;}
[data-testid="stTabs"] button p {font-weight:600; font-size:.88rem;}
[data-testid="stMetric"] {background:var(--stock); border:1px solid var(--rule); padding:8px 12px;}
[data-testid="stExpander"] details {border-radius:0 !important; background:var(--stock);}
[data-testid="stAlert"] {border-radius:0 !important;}
[data-testid="stDataFrame"] {border:1px solid var(--rule);}
[data-testid="stButtonGroup"] > div {flex-wrap:wrap !important; overflow:visible !important;}
[data-testid="stButtonGroup"] button {border-radius:0 !important;}
.ph h1 {font-size:1.95rem !important; letter-spacing:-0.03em;}

/* sidebar */
section[data-testid="stSidebar"] [data-testid="stNavSectionHeader"] {color:#8ea3c4; font-size:.68rem; text-transform:uppercase; letter-spacing:.12em; font-weight:700;}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {border-radius:0 !important;}
section[data-testid="stSidebar"] a[aria-current="page"] {background:#1d3a66 !important;}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#a9bbd6;}
.brand {border-bottom:1px solid #24406b; padding-bottom:10px; margin-bottom:6px;}
.brand .w {font-size:1.05rem; font-weight:800; letter-spacing:.04em; color:#fff; font-stretch:90%;}
.brand .d {font-size:.74rem; color:#a9bbd6;}
</style>
"""

STATUS = {"Completed": "ok", "online": "ok", "Approved": "ok", "synced": "ok", "Running": "run", "Waiting for response": "wait",
          "Requires human approval": "appr", "stale": "wait", "degraded": "wait", "Failed": "fail", "offline": "fail",
          "Rejected": "fail", "Idle": "idle", "Superseded": "idle", "not synced": "idle"}
ENT = {"manufacturer": ("MFG", "#1d4ed8"), "shipping": ("SHP", "#0e7490"), "distribution": ("DST", "#92400e"),
       "supplier": ("SUP", "#5b21b6"), "global": ("GLB", "#0b1b33"), "orchestrator": ("GLB", "#0b1b33"),
       "management": ("MGT", "#3b4a63"), "event-bus": ("EVT", "#b45309")}
ENT_NAME = {"manufacturer": "Cement Manufacturing", "shipping": "Shipping & Logistics", "distribution": "Distribution",
            "supplier": "Supplier & Procurement", "global": "Global Orchestrator", "orchestrator": "Global Orchestrator",
            "management": "Management", "event-bus": "Event bus"}
PARALLEL = {"Stock Monitoring Agent", "ML Forecasting Agent", "Fleet Tracking Agent", "Demand & Priority Agent",
            "Distribution Agent (extension)", "Procurement Agent (extension)"}


def e(x):
    return html.escape(str(x if x is not None else ""))


def mark(status):
    return f'<span class="mk m-{STATUS.get(status, "idle")}"></span>'


def badge(text):
    return f'<span class="st s-{STATUS.get(text, "idle")}">{mark(text)}{e(text)}</span>'


def chip(enterprise):
    code, color = ENT.get(enterprise, (str(enterprise or "")[:3].upper(), "#3b4a63"))
    return f'<span class="ec" style="color:{color}" title="{e(ENT_NAME.get(enterprise, enterprise))}">{code}</span>'


def stamp(status):
    cls = {"Approved": "", "Rejected": "rej"}.get(status, "sup")
    return f'<span class="stamp {cls}">{e(status)}</span>'


def hhmmss(ts):
    ts = str(ts or "")
    return ts[11:19] if len(ts) > 11 else (ts or "-")


def header(title, subtitle="", synthetic=True):
    flag = '<span class="flag">Synthetic data</span>' if synthetic else ""
    st.markdown(f'<div class="ph"><div><h1>{e(title)}</h1><div class="sub">{subtitle}</div></div>{flag}</div>', unsafe_allow_html=True)


def kpis(items, cols=None):
    """Ledger strip. items: (label, value, sub, tone[, icon]); tone bad | warn | appr, anything else plain."""
    cells = []
    for it in items:
        label, value, sub, tone = (list(it) + ["", ""])[:4]
        cells.append(f'<div class="f {e(tone)}"><div class="lbl" title="{e(label)}">{e(label)}</div>'
                     f'<div class="v">{e(value)}</div><div class="s" title="{e(sub)}">{e(sub)}</div></div>')
    st.markdown(f'<div class="ledger">{"".join(cells)}</div>', unsafe_allow_html=True)


def section(title, caption=""):
    st.markdown(f'<div class="sec"><span class="t">{e(title)}</span><span class="c">{caption}</span></div>', unsafe_allow_html=True)


def alert(title, body="", source="", severity="warning"):
    sev = severity if severity in ("critical", "info") else ""
    st.markdown(f'<div class="notice {sev}"><span class="t">{e(title)}</span> {e(body)} <span class="subtle">{e(source)}</span></div>',
                unsafe_allow_html=True)


def agent_card(a):
    ext = '<span class="tag">extension</span>' if a.get("origin") not in (None, "", "proposal") else ""
    ms = a.get("last_duration_ms")
    note = a.get("last_log") or a.get("role")
    return (f'<div class="slip"><div class="ln"><span>{chip(a.get("host"))}{ext}</span>{badge(a.get("status") or "Idle")}</div>'
            f'<div class="nm">{e(a.get("name"))}</div><div class="rl" title="{e(note)}">{e(note)}</div>'
            f'<div class="ln"><span>Last run {e(hhmmss(a.get("last_run")))}</span>'
            f'<span>{f"{ms:,.0f} ms" if isinstance(ms, (int, float)) else "not run"}</span></div></div>')


def agent_grid(agents):
    return '<div class="slips">' + "".join(agent_card(a) for a in agents) + "</div>"


def _step(s):
    ms = s.get("duration_ms")
    return (f'<div class="step" title="{e(s.get("agent"))}"><div class="n">{e(s.get("agent"))}</div>'
            f'<div class="d"><span>{chip(s.get("enterprise"))}</span><span>{f"{ms:,.0f} ms" if isinstance(ms, (int, float)) else ""}</span></div>'
            f'{badge(s.get("status") or "Idle")}</div>')


def pipeline(steps):
    """Route slip: Event > Orchestrator > [parallel workers] > Planner > Narrator > Approval."""
    out, group = [], []
    for s in list(steps) + [None]:
        if s is not None and s.get("agent") in PARALLEL:
            group.append(_step(s))
            continue
        if group:
            out.append(f'<div class="par">{"".join(group)}</div>')
            group = []
        if s is not None:
            out.append(_step(s))
    return '<div class="pipe">' + '<div class="ar"></div>'.join(out) + "</div>"


def segments(steps):
    """Split a run's steps into planning cycles (a replanning run has two)."""
    segs, cur = [], []
    for s in steps:
        if s["agent"] == "Event Detected" and any(x["agent"] == "Orchestrator Agent" for x in cur):
            segs.append(cur)
            cur = []
        cur.append(s)
    return segs + ([cur] if cur else [])


def message_bubble(m):
    return (f'<div class="lg {e(m.get("type"))}"><div class="tm">{e(hhmmss(m.get("ts")))}</div><div>'
            f'<div class="rt2">{chip(m.get("from_enterprise"))} <b>{e(m.get("from"))}</b> &rarr; {chip(m.get("to_enterprise"))} '
            f'<b>{e(m.get("to"))}</b> &middot; {e(m.get("type"))}</div><div class="tx">{e(m.get("content"))}</div></div></div>')


def message_log(msgs):
    return '<div class="log">' + "".join(message_bubble(m) for m in msgs) + "</div>"


def guard(view):
    r = role()
    if view not in ROLES[r]["views"]:
        st.warning(f"Role **{r}** is not authorised to view this environment. Switch role in the sidebar.")
        st.stop()


def tab_allowed(name):
    tabs = ROLES[role()]["tabs"]
    return tabs == "all" or name in tabs


def check(data):
    if data is None:
        st.stop()
    if denied(data):
        st.error(f"Access denied by enterprise data-sharing policy: {data['__denied__']}")
        return False
    return True


def df(rows, cols=None):
    d = pd.DataFrame(rows)
    return d[cols] if cols and len(d) else d


def fmt(v, nd=1, pct=False):
    if v is None:
        return "n/a"
    return f"{v * 100:.{nd}f}%" if pct else (f"{v:,.{nd}f}" if isinstance(v, float) else f"{v:,}")
