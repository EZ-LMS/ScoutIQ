"""Contextual help link rendered at the top-right of module pages."""

from __future__ import annotations

import streamlit as st


def help_link(section: str) -> None:
    """Render a small ❓ link that jumps to the Guide page at the specified section."""
    lang = st.session_state.get("lang", "EN")
    label = "❓ 指標說明" if lang == "zh" else "❓ Metric guide"
    st.markdown(
        f'<div style="text-align:right; margin-top:-1.5rem; margin-bottom:0.5rem;">'
        f'<a href="/Guide?section={section}" target="_self" '
        f'style="font-size:0.85rem; color:#888; text-decoration:none;">{label}</a>'
        f"</div>",
        unsafe_allow_html=True,
    )
