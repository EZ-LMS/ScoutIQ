"""Module 0 — ScoutIQ Guide: product overview, bilingual metric explainer, and module docs."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import render_sidebar  # noqa: E402
from scoutiq.guide_content import SECTIONS, SECTION_MAP  # noqa: E402

st.set_page_config(page_title="Guide — ScoutIQ", page_icon="📖", layout="wide")
render_sidebar()

lang = st.session_state.get("lang", "EN")
lang_key = "zh" if lang == "zh" else "en"

# ── Hero banner ───────────────────────────────────────────────────────────────
HERO_EN = (
    "Stop chasing box scores. Chase quality."
)
HERO_ZH = (
    "別再追逐比分欄，追求的是真實擊球品質。"
)
TAGLINE_EN = (
    "ScoutIQ surfaces market inefficiencies in MLB player evaluation by comparing "
    "Statcast expected stats to surface results — helping front offices find "
    "buy-low targets, flag regression risks, and evaluate call-up candidates."
)
TAGLINE_ZH = (
    "ScoutIQ 透過比較 Statcast 預期數據與表面成績，找出 MLB 球員評估中的市場效率失靈——"
    "協助球隊管理層找到低估球員、標記回歸風險，並評估召喚候選人。"
)

st.markdown(
    f"""
    <div style="
        background: linear-gradient(135deg, #0d1b2a 0%, #1b3a5c 100%);
        border-radius: 12px;
        padding: 2.5rem 3rem 2rem 3rem;
        margin-bottom: 1.5rem;
    ">
        <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.4rem;">
            <span style="font-size:2rem;">⚾</span>
            <span style="font-size:2rem; font-weight:800; color:#ffffff; letter-spacing:-0.5px;">ScoutIQ</span>
            <span style="font-size:0.85rem; color:#7ec8e3; background:#1b3a5c;
                         border:1px solid #2e6a9a; padding:2px 10px; border-radius:20px;
                         margin-left:0.5rem; font-weight:600;">MLB Player Intelligence</span>
        </div>
        <p style="font-size:1.45rem; font-weight:700; color:#f0f4f8; margin:0.6rem 0 0.5rem 0;
                  line-height:1.3;">
            "{HERO_EN if lang_key == "en" else HERO_ZH}"
        </p>
        <p style="font-size:1rem; color:#a8c8e8; margin:0; line-height:1.6; max-width:720px;">
            {TAGLINE_EN if lang_key == "en" else TAGLINE_ZH}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Language toggle + nav ─────────────────────────────────────────────────────
col_lang, col_note = st.columns([1, 5])
with col_lang:
    if st.button("🌐  中文" if lang_key == "en" else "🌐  English", use_container_width=True):
        st.session_state["lang"] = "zh" if lang_key == "en" else "EN"
        st.rerun()
with col_note:
    if lang_key == "en":
        st.caption("Jump to any section from the table of contents below, or via ❓ links on each module page.")
    else:
        st.caption("從下方目錄跳到任何章節，或透過各模組頁面的 ❓ 連結直接進入。")

st.divider()

# ── Stats row ──────────────────────────────────────────────────────────────────
if lang_key == "en":
    labels = ["Modules", "Data sources", "Refresh cadence", "AI summaries"]
    values = ["5", "5", "Nightly", "Claude API"]
    captions = ["league → team → callup → FA → player", "Statcast · BR · MLB API · Cot's · BREF FA",
                "09:00 UTC · GitHub Actions", "Player Deep Dive · Sonnet 4.6 · prompt-cached"]
else:
    labels = ["分析模組", "資料來源", "更新頻率", "AI 摘要"]
    values = ["5", "5", "每晚", "Claude API"]
    captions = ["全聯盟→陣容→召喚→自由球員→球員", "Statcast · BR · MLB API · Cot's · BREF FA",
                "09:00 UTC · GitHub Actions 自動執行", "球員分析 · Sonnet 4.6 · 提示快取"]

c1, c2, c3, c4 = st.columns(4)
for col, lbl, val, cap in zip([c1, c2, c3, c4], labels, values, captions):
    col.markdown(
        f"""<div style="background:#f0f7ff; border-left:4px solid #1f77b4;
                        padding:0.9rem 1rem; border-radius:6px; height:100%;">
            <div style="font-size:1.7rem; font-weight:800; color:#1f77b4; line-height:1;">{val}</div>
            <div style="font-size:0.9rem; font-weight:600; color:#333; margin-top:0.2rem;">{lbl}</div>
            <div style="font-size:0.75rem; color:#666; margin-top:0.3rem; line-height:1.3;">{cap}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Module cards ──────────────────────────────────────────────────────────────
if lang_key == "en":
    st.subheader("Five modules, one decision workflow")
    modules = [
        ("1", "League Intelligence", "Which hitters league-wide have the biggest xwOBA vs wOBA gap right now?", "#e8f5e9", "#2e7d32", "/League_Intelligence"),
        ("2", "Team Roster", "Position-by-position health check — genuine weak spots vs. bad luck.", "#fff3e0", "#e65100", "/Team_Roster"),
        ("3", "Call-Up Evaluator", "Does our AAA system have someone ready to upgrade a weak position?", "#f3e5f5", "#6a1b9a", "/Call_Up_Evaluator"),
        ("4", "Free Agent Finder", "Undervalued FA targets filtered by position need and Undervalued Score.", "#e3f2fd", "#1565c0", "/Free_Agent_Finder"),
        ("5", "Player Deep Dive", "Full metric panel, multi-season trend, and Claude AI analyst summary.", "#fce4ec", "#880e4f", "/Player_Deep_Dive"),
    ]
else:
    st.subheader("五個模組，一套決策工作流")
    modules = [
        ("1", "全聯盟概覽", "當前哪些打者的 xwOBA vs wOBA 落差最大？", "#e8f5e9", "#2e7d32", "/League_Intelligence"),
        ("2", "球隊陣容分析", "逐守備位置健康檢查——真正的弱點 vs. 只是運氣差。", "#fff3e0", "#e65100", "/Team_Roster"),
        ("3", "召喚評估", "我們的 3A 農場有沒有人準備好補強弱項？", "#f3e5f5", "#6a1b9a", "/Call_Up_Evaluator"),
        ("4", "自由球員搜尋", "按守備位置需求和 Undervalued Score 篩選的低估自由球員。", "#e3f2fd", "#1565c0", "/Free_Agent_Finder"),
        ("5", "單一球員分析", "完整指標面板、多季趨勢圖，以及 Claude AI 分析師摘要。", "#fce4ec", "#880e4f", "/Player_Deep_Dive"),
    ]

cols = st.columns(5)
for col, (num, name, desc, bg, accent, link) in zip(cols, modules):
    col.markdown(
        f"""<a href="{link}" target="_self" style="text-decoration:none;">
        <div style="background:{bg}; border-top:4px solid {accent}; border-radius:8px;
                    padding:1rem; height:140px; cursor:pointer;
                    transition:box-shadow 0.2s; box-shadow:0 1px 3px rgba(0,0,0,0.08);">
            <div style="font-size:1.6rem; font-weight:900; color:{accent}; line-height:1;">{num}</div>
            <div style="font-size:0.88rem; font-weight:700; color:#222; margin-top:0.3rem;">{name}</div>
            <div style="font-size:0.75rem; color:#555; margin-top:0.4rem; line-height:1.4;">{desc}</div>
        </div></a>""",
        unsafe_allow_html=True,
    )

st.divider()

# ── Table of contents ─────────────────────────────────────────────────────────
toc_label = "📋 Table of Contents" if lang_key == "en" else "📋 目錄"
with st.expander(toc_label, expanded=False):
    cols = st.columns(2)
    for i, section in enumerate(SECTIONS):
        cols[i % 2].markdown(
            f"- [{section['title'][lang_key]}](#{section['id']})"
        )

# ── Auto-open section from query param (?section=id) ─────────────────────────
active_section = st.query_params.get("section", "")

# ── Render all sections ───────────────────────────────────────────────────────
SECTION_ICONS = {
    "overview": "🏟️",
    "undervalued_score": "📊",
    "metrics_expected": "🔬",
    "metrics_surface": "📋",
    "metrics_quality": "💥",
    "metrics_plate": "🎯",
    "metrics_war": "💰",
    "flags": "🚩",
    "data_sources": "🗄️",
    "module_league": "🌐",
    "module_roster": "👥",
    "module_callup": "⬆️",
    "module_fa": "🤝",
    "module_player": "🔍",
}

for section in SECTIONS:
    sid = section["id"]
    icon = SECTION_ICONS.get(sid, "•")
    title = section["title"][lang_key]
    content = section[lang_key]

    st.markdown(f'<div id="{sid}"></div>', unsafe_allow_html=True)

    expanded = (sid == active_section)
    with st.expander(f"{icon}  {title}", expanded=expanded):
        st.markdown(content)
        if sid == active_section and active_section:
            other_key = "zh" if lang_key == "en" else "en"
            other_label = "🔄 中文版本" if lang_key == "en" else "🔄 English version"
            with st.expander(other_label, expanded=False):
                st.markdown(section[other_key])
