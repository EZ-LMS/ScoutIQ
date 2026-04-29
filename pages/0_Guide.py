"""Module 0 — ScoutIQ Guide: bilingual metric explainer and module documentation."""

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

# ── Language toggle ───────────────────────────────────────────────────────────
lang = st.session_state.get("lang", "EN")
col_title, col_lang = st.columns([6, 1])
with col_title:
    st.title("📖 ScoutIQ Guide")
with col_lang:
    st.write("")  # spacing
    if st.button("中文" if lang == "EN" else "English", use_container_width=True):
        st.session_state["lang"] = "zh" if lang == "EN" else "EN"
        st.rerun()

lang_key = "zh" if lang == "zh" else "en"

if lang_key == "en":
    st.caption(
        "Complete reference for every metric, scoring formula, and module in ScoutIQ. "
        "Jump to any section from the table of contents or via the ❓ links on each page."
    )
else:
    st.caption(
        "ScoutIQ 所有指標、評分公式與模組的完整說明。"
        "可從下方目錄跳到對應章節，或從各頁面的 ❓ 連結直接跳入。"
    )

st.divider()

# ── Table of contents ─────────────────────────────────────────────────────────
toc_label = "Table of Contents" if lang_key == "en" else "目錄"
with st.expander(f"📋 {toc_label}", expanded=True):
    cols = st.columns(2)
    for i, section in enumerate(SECTIONS):
        cols[i % 2].markdown(
            f"- [{section['title'][lang_key]}](#{section['id']})"
        )

st.divider()

# ── Auto-open section from query param (?section=id) ─────────────────────────
active_section = st.query_params.get("section", "")

# ── Render all sections ───────────────────────────────────────────────────────
for section in SECTIONS:
    sid = section["id"]
    title = section["title"][lang_key]
    content = section[lang_key]

    # Use anchor div so the # link works
    st.markdown(f'<div id="{sid}"></div>', unsafe_allow_html=True)

    expanded = (sid == active_section) or (active_section == "")
    with st.expander(f"### {title}", expanded=expanded):
        st.markdown(content)
        # Show both language versions for the active section
        if sid == active_section and active_section:
            other_key = "zh" if lang_key == "en" else "en"
            other_label = "中文版本" if lang_key == "en" else "English version"
            with st.expander(f"🔄 {other_label}", expanded=False):
                st.markdown(section[other_key])
