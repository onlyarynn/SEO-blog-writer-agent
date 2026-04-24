from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import os
import re
import zipfile
from datetime import date
from io import BytesIO
from typing import Any, Dict, Iterator, List, Optional, Tuple

import pandas as pd
import streamlit as st

from backend.graph import app, State

OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Page config — MUST be first Streamlit call
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BlogForge AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# Global CSS — Dark Professional SaaS Theme
# ─────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
/* ── Root Variables ── */
:root {
    --bg-primary:    #0d0f14;
    --bg-secondary:  #13161e;
    --bg-card:       #181c26;
    --bg-card-hover: #1e2333;
    --border:        #252a38;
    --border-light:  #2e3547;
    --accent:        #4f8ef7;
    --accent-glow:   rgba(79,142,247,0.18);
    --accent-2:      #22d3a5;
    --accent-3:      #f97316;
    --accent-warn:   #f59e0b;
    --text-primary:  #e8eaf0;
    --text-secondary:#8b92a8;
    --text-muted:    #555d72;
    --success:       #22c55e;
    --danger:        #ef4444;
    --radius:        10px;
    --radius-lg:     16px;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background: var(--bg-primary) !important;
}

/* ── Hide Streamlit Branding ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 0 !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}

[data-testid="stSidebarContent"] {
    padding: 0 !important;
}

/* ── Sidebar Logo Area ── */
.sidebar-brand {
    padding: 24px 20px 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 8px;
}

.sidebar-brand h1 {
    font-family: 'Syne', sans-serif !important;
    font-size: 22px !important;
    font-weight: 800 !important;
    color: var(--text-primary) !important;
    margin: 0 !important;
    letter-spacing: -0.5px;
}

.sidebar-brand span {
    font-size: 11px;
    color: var(--text-muted);
    font-weight: 400;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.brand-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: var(--accent);
    border-radius: 50%;
    margin-right: 8px;
    box-shadow: 0 0 10px var(--accent);
}

/* ── Sidebar Sections ── */
.sidebar-section-label {
    font-size: 10px !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding: 16px 20px 6px !important;
    display: block;
}

/* ── Inputs ── */
.stTextArea textarea,
.stTextInput input,
[data-testid="stDateInput"] input {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}

.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
    outline: none !important;
}

/* ── Labels ── */
.stTextArea label, .stTextInput label,
[data-testid="stDateInput"] label,
.stSelectbox label {
    color: var(--text-secondary) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0.3px !important;
    margin-bottom: 4px !important;
}

/* ── Primary Button ── */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #4f8ef7 0%, #3b6fd4 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    letter-spacing: 0.2px !important;
    box-shadow: 0 4px 20px rgba(79,142,247,0.3) !important;
    transition: all 0.2s !important;
    width: 100% !important;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(79,142,247,0.45) !important;
}

/* ── Secondary Buttons ── */
.stButton > button:not([kind="primary"]) {
    background: var(--bg-card) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}

.stButton > button:not([kind="primary"]):hover {
    background: var(--bg-card-hover) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* ── Download Buttons ── */
.stDownloadButton > button {
    background: var(--bg-card) !important;
    color: var(--accent) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    width: 100% !important;
    transition: all 0.2s !important;
}

.stDownloadButton > button:hover {
    background: var(--accent-glow) !important;
    border-color: var(--accent) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] {
    background: transparent !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0 !important;
    padding: 6px 6px 0 6px !important;
    gap: 2px !important;
    border-bottom: 1px solid var(--border) !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 18px !important;
    border: none !important;
    transition: all 0.2s !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;
    background: var(--bg-card) !important;
}

.stTabs [aria-selected="true"] {
    background: var(--bg-card) !important;
    color: var(--accent) !important;
    font-weight: 600 !important;
    border-bottom: 2px solid var(--accent) !important;
}

.stTabs [data-baseweb="tab-panel"] {
    background: var(--bg-card) !important;
    border-radius: 0 0 var(--radius-lg) var(--radius-lg) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    padding: 28px !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 16px !important;
}

[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
}

[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 22px !important;
    font-weight: 700 !important;
}

[data-testid="stMetricDelta"] {
    font-size: 11px !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
}

.dvn-scroller { background: var(--bg-secondary) !important; }

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    margin-bottom: 8px !important;
}

[data-testid="stExpander"] summary {
    color: var(--text-secondary) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 12px 16px !important;
}

[data-testid="stExpander"] summary:hover {
    color: var(--text-primary) !important;
}

/* ── Code blocks ── */
.stCodeBlock, code {
    background: var(--bg-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    color: var(--accent-2) !important;
}

/* ── Info / Warning / Error ── */
[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-secondary) !important;
}

.stAlert[data-baseweb="notification"] {
    background: var(--bg-secondary) !important;
}

/* ── Status box ── */
[data-testid="stStatus"] {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}

/* ── Radio buttons (past blogs) ── */
[data-testid="stRadio"] label {
    color: var(--text-secondary) !important;
    font-size: 12px !important;
}

[data-testid="stRadio"] label:hover {
    color: var(--text-primary) !important;
}

/* ── Divider ── */
hr {
    border-color: var(--border) !important;
    margin: 20px 0 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Custom Cards ── */
.stat-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 20px;
    margin-bottom: 10px;
}

.stat-card-label {
    font-size: 10px;
    font-weight: 600;
    color: var(--text-muted);
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 4px;
}

.stat-card-value {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: var(--text-primary);
}

/* ── API Status Pills ── */
.api-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 6px;
    font-size: 12px;
    color: var(--text-secondary);
}

.api-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}
.api-dot.ok   { background: var(--success); box-shadow: 0 0 6px var(--success); }
.api-dot.warn { background: var(--accent-warn); }
.api-dot.err  { background: var(--danger); }

/* ── Page Header ── */
.page-header {
    padding: 32px 0 24px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
}

.page-header h2 {
    font-family: 'Syne', sans-serif !important;
    font-size: 28px !important;
    font-weight: 800 !important;
    color: var(--text-primary) !important;
    margin: 0 0 4px 0 !important;
    letter-spacing: -0.5px !important;
}

.page-header p {
    color: var(--text-muted) !important;
    font-size: 13px !important;
    margin: 0 !important;
}

/* ── Section Headers inside tabs ── */
.tab-section-title {
    font-family: 'Syne', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 20px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

.tab-section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── SEO Keyword Pills ── */
.kw-pill {
    display: inline-block;
    background: var(--accent-glow);
    border: 1px solid rgba(79,142,247,0.3);
    color: var(--accent);
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    margin: 3px;
    font-weight: 500;
}

/* ── Past blog items ── */
.blog-item {
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.15s;
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.blog-item:hover {
    background: var(--bg-card);
    border-color: var(--border);
    color: var(--text-primary);
}

/* ── Progress node badges ── */
.node-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
    margin: 3px;
    font-weight: 500;
}

/* ── Evidence URL links ── */
a { color: var(--accent) !important; text-decoration: none !important; }
a:hover { text-decoration: underline !important; }

/* ── Text area dark ── */
.stTextArea [data-baseweb="textarea"] {
    background: var(--bg-card) !important;
    border-color: var(--border-light) !important;
}

/* Markdown content inside preview */
.stMarkdown h1 {
    font-family: 'Syne', sans-serif !important;
    font-size: 28px !important;
    font-weight: 800 !important;
    color: var(--text-primary) !important;
    border-bottom: 1px solid var(--border) !important;
    padding-bottom: 12px !important;
}

.stMarkdown h2 {
    font-family: 'Syne', sans-serif !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    margin-top: 32px !important;
}

.stMarkdown h3 {
    font-family: 'Syne', sans-serif !important;
    font-size: 16px !important;
    color: var(--text-secondary) !important;
}

.stMarkdown p {
    color: var(--text-secondary) !important;
    line-height: 1.75 !important;
    font-size: 15px !important;
}

.stMarkdown strong { color: var(--text-primary) !important; }

.stMarkdown li {
    color: var(--text-secondary) !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
}

/* Date input dark */
[data-testid="stDateInput"] > div > div {
    background: var(--bg-card) !important;
    border-color: var(--border-light) !important;
    border-radius: var(--radius) !important;
}

/* JSON viewer */
[data-testid="stJson"] {
    background: var(--bg-primary) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
}

/* Sidebar padding fix */
section[data-testid="stSidebar"] .block-container {
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────

def safe_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"


def bundle_zip(md_text: str, md_filename: str, images_dir: Path) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(md_filename, md_text.encode("utf-8"))
        if images_dir.exists() and images_dir.is_dir():
            for p in images_dir.rglob("*"):
                if p.is_file():
                    z.write(p, arcname=str(p))
    return buf.getvalue()


def images_zip(images_dir: Path) -> Optional[bytes]:
    if not images_dir.exists():
        return None
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in images_dir.rglob("*"):
            if p.is_file():
                z.write(p, arcname=str(p))
    return buf.getvalue()


def try_stream(graph_app, inputs: Dict[str, Any]) -> Iterator[Tuple[str, Any]]:
    try:
        for step in graph_app.stream(inputs, stream_mode="updates"):
            yield ("updates", step)
        out = graph_app.invoke(inputs)
        yield ("final", out)
        return
    except Exception:
        pass
    try:
        for step in graph_app.stream(inputs, stream_mode="values"):
            yield ("values", step)
        out = graph_app.invoke(inputs)
        yield ("final", out)
        return
    except Exception:
        pass
    out = graph_app.invoke(inputs)
    yield ("final", out)


def extract_latest_state(current: Dict[str, Any], payload: Any) -> Dict[str, Any]:
    if isinstance(payload, dict):
        if len(payload) == 1 and isinstance(next(iter(payload.values())), dict):
            current.update(next(iter(payload.values())))
        else:
            current.update(payload)
    return current


_MD_IMG_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)")
_CAPTION_LINE_RE = re.compile(r"^\*(?P<cap>.+)\*$")


def render_markdown_with_local_images(md: str):
    matches = list(_MD_IMG_RE.finditer(md))
    if not matches:
        st.markdown(md, unsafe_allow_html=False)
        return
    parts: List[Tuple[str, str]] = []
    last = 0
    for m in matches:
        before = md[last: m.start()]
        if before:
            parts.append(("md", before))
        parts.append(("img", f"{(m.group('alt') or '').strip()}|||{(m.group('src') or '').strip()}"))
        last = m.end()
    tail = md[last:]
    if tail:
        parts.append(("md", tail))
    i = 0
    while i < len(parts):
        kind, payload = parts[i]
        if kind == "md":
            st.markdown(payload, unsafe_allow_html=False)
            i += 1
            continue
        alt, src = payload.split("|||", 1)
        caption = None
        if i + 1 < len(parts) and parts[i + 1][0] == "md":
            nxt = parts[i + 1][1].lstrip()
            if nxt.strip():
                first_line = nxt.splitlines()[0].strip()
                mcap = _CAPTION_LINE_RE.match(first_line)
                if mcap:
                    caption = mcap.group("cap").strip()
                    parts[i + 1] = ("md", "\n".join(nxt.splitlines()[1:]))
        if src.startswith("http://") or src.startswith("https://"):
            st.image(src, caption=caption or alt or None, use_container_width=True)
        else:
            img_path = Path(src.strip().lstrip("./")).resolve()
            if img_path.exists():
                st.image(str(img_path), caption=caption or alt or None, use_container_width=True)
            else:
                st.warning(f"Image not found: `{src}`")
        i += 1


def list_past_blogs() -> List[Path]:
    files = [p for p in OUTPUTS_DIR.glob("*.md") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def read_md_file(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def extract_title_from_md(md: str, fallback: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    # Brand
    st.markdown("""
    <div class="sidebar-brand">
        <h1><span class="brand-dot"></span>BlogForge AI</h1>
        <span>Powered by Claude · LangGraph · Tavily</span>
    </div>
    """, unsafe_allow_html=True)

    # Generate section
    st.markdown('<span class="sidebar-section-label">Generate</span>', unsafe_allow_html=True)

    topic = st.text_area(
        "Topic",
        placeholder="e.g. 'Self Attention in Transformers'\nor 'AI news this week'",
        height=110,
        label_visibility="collapsed",
    )
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

    col_date, _ = st.columns([1, 0.01])
    with col_date:
        as_of_date = st.date_input("As-of date", value=date.today())

    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
    run_btn = st.button("⚡  Generate Blog", type="primary", use_container_width=True)

    # API Status
    st.markdown('<span class="sidebar-section-label">API Status</span>', unsafe_allow_html=True)

    anthropic_ok = bool(os.getenv("ANTHROPIC_API_KEY"))
    tavily_ok    = bool(os.getenv("TAVILY_API_KEY"))
    gemini_ok    = bool(os.getenv("GOOGLE_API_KEY"))

    def api_pill(name: str, ok: bool, optional: bool = False) -> str:
        cls  = "ok" if ok else ("warn" if optional else "err")
        label = "Connected" if ok else ("Optional" if optional else "Missing")
        return f"""<div class="api-status">
            <span class="api-dot {cls}"></span>
            <span style="flex:1;font-weight:500">{name}</span>
            <span style="color:{'#22c55e' if ok else ('#f59e0b' if optional else '#ef4444')};font-size:11px">{label}</span>
        </div>"""

    st.markdown(
        api_pill("Anthropic (LLM)", anthropic_ok, False) +
        api_pill("Tavily (Research)", tavily_ok, True) +
        api_pill("Gemini (Images)", gemini_ok, True),
        unsafe_allow_html=True,
    )

    # Past Blogs
    st.markdown('<span class="sidebar-section-label">Past Blogs</span>', unsafe_allow_html=True)
    past_files = list_past_blogs()
    if not past_files:
        st.markdown('<p style="font-size:12px;color:var(--text-muted);padding:0 12px">No saved blogs yet.</p>', unsafe_allow_html=True)
    else:
        options: List[str] = []
        file_by_label: Dict[str, Path] = {}
        for p in past_files[:30]:
            try:
                md_text = read_md_file(p)
                title = extract_title_from_md(md_text, p.stem)
            except Exception:
                title = p.stem
            label = title[:42] + ("…" if len(title) > 42 else "")
            full_label = f"{title}  ·  {p.name}"
            options.append(full_label)
            file_by_label[full_label] = p

        selected_label = st.radio(
            "Past blogs",
            options=options,
            index=0,
            label_visibility="collapsed",
        )
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        if st.button("Load Selected Blog", use_container_width=True):
            if selected_label and file_by_label.get(selected_label):
                md_text = read_md_file(file_by_label[selected_label])
                st.session_state["last_out"] = {
                    "plan": None, "evidence": [], "image_specs": [], "seo_meta": {}, "final": md_text
                }

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:10px;color:var(--text-muted);padding:0 12px;line-height:1.5">Google E-E-A-T Optimised · SEO Ready · Structured Output</p>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────
if "last_out" not in st.session_state:
    st.session_state["last_out"] = None
if "logs" not in st.session_state:
    st.session_state["logs"] = []


# ─────────────────────────────────────────────────────────────
# Main Page Header
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>⚡ Blog Content Studio</h2>
    <p>AI-powered · E-E-A-T Optimised · Google Helpful Content Aligned</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────
tab_plan, tab_evidence, tab_preview, tab_seo, tab_images, tab_logs = st.tabs([
    "🧩  Plan",
    "🔎  Evidence",
    "📝  Preview",
    "🎯  SEO",
    "🖼️  Images",
    "🧾  Logs",
])

logs: List[str] = []


# ─────────────────────────────────────────────────────────────
# Run Agent
# ─────────────────────────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.warning("Please enter a topic first.")
        st.stop()
    if not anthropic_ok:
        st.error("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
        st.stop()

    inputs: Dict[str, Any] = {
        "topic": topic.strip(), "as_of": as_of_date.isoformat(),
        "mode": "", "needs_research": False, "queries": [], "recency_days": 7,
        "evidence": [], "plan": None, "sections": [],
        "merged_md": "", "md_with_placeholders": "", "image_specs": [],
        "final": "", "seo_meta": {},
    }

    st.session_state["logs"] = []

    with st.container():
        status = st.status("⚡ Agent running…", expanded=True)
        progress_area = st.empty()

    current_state: Dict[str, Any] = {}
    last_node = None
    nodes_done: List[str] = []

    for kind, payload in try_stream(app, inputs):
        if kind in ("updates", "values"):
            node_name = None
            if isinstance(payload, dict) and len(payload) == 1 and isinstance(next(iter(payload.values())), dict):
                node_name = next(iter(payload.keys()))
            if node_name and node_name != last_node:
                nodes_done.append(node_name)
                badges = " ".join(f'<span class="node-badge">✓ {n}</span>' for n in nodes_done)
                status.markdown(f'<div style="padding:8px 0">{badges}</div>', unsafe_allow_html=True)
                last_node = node_name

            current_state = extract_latest_state(current_state, payload)
            plan_obj = current_state.get("plan")

            # Live metrics row
            ev_count  = len(current_state.get("evidence") or [])
            sec_count = len(current_state.get("sections") or [])
            img_count = len(current_state.get("image_specs") or [])
            mode_val  = current_state.get("mode") or "—"
            task_count = (
                len(plan_obj.tasks) if hasattr(plan_obj, "tasks") else
                (len(plan_obj.get("tasks", [])) if isinstance(plan_obj, dict) else 0)
            )

            progress_area.markdown(f"""
            <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:12px">
                <div class="stat-card" style="flex:1;min-width:100px">
                    <div class="stat-card-label">Mode</div>
                    <div class="stat-card-value" style="font-size:16px">{mode_val}</div>
                </div>
                <div class="stat-card" style="flex:1;min-width:100px">
                    <div class="stat-card-label">Evidence</div>
                    <div class="stat-card-value">{ev_count}</div>
                </div>
                <div class="stat-card" style="flex:1;min-width:100px">
                    <div class="stat-card-label">Sections</div>
                    <div class="stat-card-value">{sec_count}/{task_count or '?'}</div>
                </div>
                <div class="stat-card" style="flex:1;min-width:100px">
                    <div class="stat-card-label">Images</div>
                    <div class="stat-card-value">{img_count}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            logs.append(f"[{kind}] node={node_name} | {json.dumps(payload, default=str)[:800]}")

        elif kind == "final":
            st.session_state["last_out"] = payload
            status.update(label="✅ Blog generated successfully!", state="complete", expanded=False)
            progress_area.empty()
            logs.append("[final] received final output")

    st.session_state["logs"].extend(logs)


# ─────────────────────────────────────────────────────────────
# Render Output Tabs
# ─────────────────────────────────────────────────────────────
out = st.session_state.get("last_out")

if out:
    # ── PLAN TAB ─────────────────────────────────────────────
    with tab_plan:
        st.markdown('<div class="tab-section-title">Blog Structure Plan</div>', unsafe_allow_html=True)
        plan_obj = out.get("plan")
        if not plan_obj:
            st.info("No plan available for this blog.")
        else:
            plan_dict = plan_obj.model_dump() if hasattr(plan_obj, "model_dump") else (plan_obj if isinstance(plan_obj, dict) else {})

            # Header metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Blog Kind",   plan_dict.get("blog_kind", "—").replace("_", " ").title())
            col2.metric("Sections",    len(plan_dict.get("tasks", [])))
            col3.metric("Audience",    plan_dict.get("audience", "—")[:20])
            col4.metric("Tone",        plan_dict.get("tone", "—")[:20])

            st.markdown(f"""
            <div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:var(--radius);
                        padding:16px 20px;margin:20px 0 16px">
                <div style="font-size:10px;color:var(--text-muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:6px">Blog Title</div>
                <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:700;color:var(--text-primary)">{plan_dict.get('blog_title','Untitled')}</div>
            </div>
            """, unsafe_allow_html=True)

            tasks = plan_dict.get("tasks", [])
            if tasks:
                df = pd.DataFrame([{
                    "#":       t.get("id"),
                    "Section": t.get("title"),
                    "Words":   t.get("target_words"),
                    "Research":"✅" if t.get("requires_research") else "",
                    "Cite":    "✅" if t.get("requires_citations") else "",
                    "Code":    "✅" if t.get("requires_code") else "",
                    "Tags":    ", ".join(t.get("tags") or []),
                } for t in tasks]).sort_values("#")
                st.dataframe(df, use_container_width=True, hide_index=True)
                with st.expander("📋 Raw JSON"):
                    st.json(tasks)

    # ── EVIDENCE TAB ─────────────────────────────────────────
    with tab_evidence:
        st.markdown('<div class="tab-section-title">Research Evidence</div>', unsafe_allow_html=True)
        evidence = out.get("evidence") or []
        if not evidence:
            st.markdown("""
            <div style="text-align:center;padding:40px 20px;color:var(--text-muted)">
                <div style="font-size:32px;margin-bottom:12px">🔎</div>
                <div style="font-size:15px;font-weight:500;color:var(--text-secondary)">No evidence collected</div>
                <div style="font-size:13px;margin-top:6px">Topic ran in closed_book mode or Tavily key not connected</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:12px;color:var(--text-muted);margin-bottom:12px">{len(evidence)} sources found</div>', unsafe_allow_html=True)
            rows = []
            for e in evidence:
                ed = e.model_dump() if hasattr(e, "model_dump") else e
                rows.append({"Title": ed.get("title"), "Published": ed.get("published_at"), "URL": ed.get("url")})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown('<div style="margin-top:16px"></div>', unsafe_allow_html=True)
            for row in rows:
                if row["URL"]:
                    st.markdown(f"→ [{row['Title']}]({row['URL']})")

    # ── PREVIEW TAB ──────────────────────────────────────────
    with tab_preview:
        st.markdown('<div class="tab-section-title">Blog Preview</div>', unsafe_allow_html=True)
        final_md = out.get("final") or ""
        if not final_md:
            st.markdown("""
            <div style="text-align:center;padding:60px 20px;color:var(--text-muted)">
                <div style="font-size:40px;margin-bottom:16px">📝</div>
                <div style="font-size:16px;font-weight:500;color:var(--text-secondary)">No blog generated yet</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            plan_obj = out.get("plan")
            blog_title = (
                plan_obj.blog_title if hasattr(plan_obj, "blog_title") else
                (plan_obj.get("blog_title", "blog") if isinstance(plan_obj, dict) else
                 extract_title_from_md(final_md, "blog"))
            )
            md_filename = f"{safe_slug(blog_title)}.md"

            # Download bar
            dl1, dl2, _ = st.columns([1, 1, 2])
            with dl1:
                st.download_button("⬇️ Markdown", data=final_md.encode("utf-8"), file_name=md_filename, mime="text/markdown", use_container_width=True)
            with dl2:
                bundle = bundle_zip(final_md, md_filename, OUTPUTS_DIR / "images")
                st.download_button("📦 Full Bundle", data=bundle, file_name=f"{safe_slug(blog_title)}_bundle.zip", mime="application/zip", use_container_width=True)

            st.markdown('<hr>', unsafe_allow_html=True)
            render_markdown_with_local_images(final_md)

            with st.expander("📄 Raw Markdown"):
                st.code(final_md, language="markdown")

    # ── SEO TAB ──────────────────────────────────────────────
    with tab_seo:
        st.markdown('<div class="tab-section-title">SEO & Google Optimisation</div>', unsafe_allow_html=True)
        meta = out.get("seo_meta") or {}
        if not meta:
            st.markdown("""
            <div style="text-align:center;padding:40px 20px;color:var(--text-muted)">
                <div style="font-size:32px;margin-bottom:12px">🎯</div>
                <div style="font-size:15px;color:var(--text-secondary)">Generate a blog to see SEO metadata</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            title_len = len(meta.get("title_tag", ""))
            desc_len  = len(meta.get("meta_description", ""))
            faq_count = len(meta.get("faq_items", []))

            # Score row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Title Tag",   f"{title_len}/60 chars",  delta="✅ Good" if title_len <= 60 else "⚠️ Long",  delta_color="normal")
            col2.metric("Meta Desc",   f"{desc_len}/160 chars",  delta="✅ Good" if desc_len <= 160 else "⚠️ Long",  delta_color="normal")
            col3.metric("FAQ Items",   faq_count)
            col4.metric("Keywords",    len(meta.get("semantic_keywords", [])))

            st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown('<div style="font-size:11px;color:var(--text-muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:8px">Title Tag</div>', unsafe_allow_html=True)
                st.code(meta.get("title_tag", ""), language=None)

                st.markdown('<div style="font-size:11px;color:var(--text-muted);letter-spacing:1px;text-transform:uppercase;margin:12px 0 8px">Meta Description</div>', unsafe_allow_html=True)
                st.code(meta.get("meta_description", ""), language=None)

                st.markdown('<div style="font-size:11px;color:var(--text-muted);letter-spacing:1px;text-transform:uppercase;margin:12px 0 8px">Focus Keyword</div>', unsafe_allow_html=True)
                st.code(meta.get("focus_keyword", ""), language=None)

                st.markdown('<div style="font-size:11px;color:var(--text-muted);letter-spacing:1px;text-transform:uppercase;margin:12px 0 8px">Canonical Slug</div>', unsafe_allow_html=True)
                st.code(f"/{meta.get('canonical_slug', '')}/", language=None)

            with col_b:
                st.markdown('<div style="font-size:11px;color:var(--text-muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:10px">Semantic Keywords</div>', unsafe_allow_html=True)
                kws_html = " ".join(f'<span class="kw-pill">{kw}</span>' for kw in meta.get("semantic_keywords", []))
                st.markdown(f'<div>{kws_html}</div>', unsafe_allow_html=True)

                st.markdown('<div style="font-size:11px;color:var(--text-muted);letter-spacing:1px;text-transform:uppercase;margin:20px 0 10px">E-E-A-T Notes</div>', unsafe_allow_html=True)
                for note in meta.get("eeat_notes", []):
                    st.markdown(f'<div style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:6px;font-size:13px;color:var(--text-secondary)">→ {note}</div>', unsafe_allow_html=True)

            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:11px;color:var(--text-muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:12px">FAQ Schema — People Also Ask</div>', unsafe_allow_html=True)
            faq_items = meta.get("faq_items", [])
            if faq_items:
                for i, faq in enumerate(faq_items, 1):
                    with st.expander(f"Q{i}:  {faq.get('question', '')}"):
                        st.markdown(f'<p style="color:var(--text-secondary);font-size:14px;line-height:1.6">{faq.get("answer","")}</p>', unsafe_allow_html=True)

                jsonld = {
                    "@context": "https://schema.org", "@type": "FAQPage",
                    "mainEntity": [{"@type": "Question", "name": f.get("question"), "acceptedAnswer": {"@type": "Answer", "text": f.get("answer")}} for f in faq_items]
                }
                st.download_button(
                    "⬇️ Download FAQ JSON-LD",
                    data=json.dumps(jsonld, indent=2).encode("utf-8"),
                    file_name="faq_schema.json",
                    mime="application/json",
                )

    # ── IMAGES TAB ───────────────────────────────────────────
    with tab_images:
        st.markdown('<div class="tab-section-title">Generated Images</div>', unsafe_allow_html=True)
        specs = out.get("image_specs") or []
        images_dir = OUTPUTS_DIR / "images"
        if not specs:
            st.markdown("""
            <div style="text-align:center;padding:40px 20px;color:var(--text-muted)">
                <div style="font-size:32px;margin-bottom:12px">🖼️</div>
                <div style="font-size:15px;color:var(--text-secondary)">No images generated for this blog</div>
                <div style="font-size:12px;margin-top:6px">Add GOOGLE_API_KEY to enable AI image generation</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for spec in specs:
                sd = spec if isinstance(spec, dict) else spec
                with st.expander(f"{sd.get('placeholder','?')}  —  {sd.get('alt','')}"):
                    st.markdown(f'<p style="color:var(--text-secondary);font-size:13px"><strong>Caption:</strong> {sd.get("caption","")}</p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="color:var(--text-muted);font-size:12px"><strong>Prompt:</strong> {sd.get("prompt","")}</p>', unsafe_allow_html=True)

            if images_dir.exists():
                files = sorted(p for p in images_dir.iterdir() if p.is_file())
                if files:
                    cols = st.columns(min(len(files), 3))
                    for col, p in zip(cols, files):
                        col.image(str(p), caption=p.name, use_container_width=True)
                    z = images_zip(images_dir)
                    if z:
                        st.download_button("⬇️ Download All Images", data=z, file_name="blog_images.zip", mime="application/zip")

    # ── LOGS TAB ─────────────────────────────────────────────
    with tab_logs:
        st.markdown('<div class="tab-section-title">Agent Execution Logs</div>', unsafe_allow_html=True)
        all_logs = st.session_state.get("logs", [])
        if all_logs:
            st.text_area(
                "Event log",
                value="\n\n".join(all_logs[-80:]),
                height=500,
                label_visibility="collapsed",
            )
        else:
            st.markdown("""
            <div style="text-align:center;padding:40px 20px;color:var(--text-muted)">
                <div style="font-size:32px;margin-bottom:12px">🧾</div>
                <div style="font-size:15px;color:var(--text-secondary)">Logs will appear here after generation</div>
            </div>
            """, unsafe_allow_html=True)

else:
    # Empty state
    with tab_preview:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px">
            <div style="font-size:56px;margin-bottom:20px">⚡</div>
            <div style="font-family:Syne,sans-serif;font-size:24px;font-weight:700;color:var(--text-primary);margin-bottom:10px">
                Ready to write
            </div>
            <div style="font-size:15px;color:var(--text-muted);max-width:420px;margin:0 auto;line-height:1.6">
                Enter a topic in the sidebar and click <strong style="color:var(--accent)">Generate Blog</strong> to start your AI-powered content pipeline.
            </div>
        </div>
        """, unsafe_allow_html=True)
