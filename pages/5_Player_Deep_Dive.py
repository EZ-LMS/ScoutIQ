"""Module 5 — Player Deep Dive: full metric panel, multi-season trend."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import render_sidebar  # noqa: E402
from scoutiq import data_loader  # noqa: E402
from scoutiq.ai_summary import build_stats_json, generate_summary  # noqa: E402
from scoutiq.help_link import help_link  # noqa: E402

st.set_page_config(page_title="Player Deep Dive — ScoutIQ", page_icon="⚾", layout="wide")
render_sidebar()

st.title("Player Deep Dive")
help_link("module_player")
st.caption("Surface stats vs. Statcast quality, trend over recent seasons.")

season = st.session_state["season"]
df = data_loader.load_players_scored(season)
if df.empty:
    st.error(f"No `players_scored_{season}.parquet` on disk. Run the refresh job first.")
    st.stop()

names = sorted(df["Name"].dropna().unique().tolist())

# Allow deep-link via ?player=Name. Falls back to selectbox.
qp = st.query_params.get("player")
default_idx = names.index(qp) if qp in names else None
chosen = st.selectbox("Search player", names, index=default_idx, placeholder="Start typing a name…")
if not chosen:
    st.info("Pick a player to see their profile.")
    st.stop()
st.query_params["player"] = chosen

row = df[df["Name"] == chosen].iloc[0]

# Top-line summary metrics
score = float(row["undervalued_score"])
label = row.get("valuation_label", "—")
score_color = "🟢" if score >= 70 else ("🔴" if score <= 30 else "⚪")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Team", row.get("Team", "—"))
c2.metric("PA", int(row.get("PA", 0)) if pd.notna(row.get("PA")) else "—")
c3.metric("wOBA", f"{row['wOBA']:.3f}")
c4.metric("xwOBA", f"{row['xwOBA']:.3f}", delta=f"{row['woba_gap']:+.3f}")
c5.metric(f"{score_color} Score", f"{score:.0f}", help=f"{label}")

# Metric panel
st.subheader("Metric panel")
panel_left, panel_right = st.columns(2)

surface_keys = [("AVG", ".3f"), ("SLG", ".3f"), ("OBP", ".3f"), ("BABIP", ".3f"), ("ISO", ".3f"), ("wOBA", ".3f")]
quality_keys = [
    ("xBA", ".3f"), ("xSLG", ".3f"), ("xwOBA", ".3f"), ("xISO", ".3f"),
    ("Barrel%", ".1%"), ("HardHit%", ".1%"), ("EV", ".1f"), ("LA", ".1f"),
]
plate_keys = [("K%", ".1%"), ("BB%", ".1%"), ("GB%", ".1%"), ("FB%", ".1%"), ("LD%", ".1%")]


def _fmt(val, spec: str) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    try:
        return format(val, spec)
    except (TypeError, ValueError):
        return str(val)


with panel_left:
    st.markdown("**Surface stats**")
    surface_data = {k: _fmt(row.get(k), spec) for k, spec in surface_keys if k in row.index}
    st.table(pd.DataFrame.from_dict(surface_data, orient="index", columns=["value"]))

    st.markdown("**Plate discipline / batted ball**")
    plate_data = {k: _fmt(row.get(k), spec) for k, spec in plate_keys if k in row.index}
    st.table(pd.DataFrame.from_dict(plate_data, orient="index", columns=["value"]))

with panel_right:
    st.markdown("**Statcast quality**")
    quality_data = {k: _fmt(row.get(k), spec) for k, spec in quality_keys if k in row.index}
    st.table(pd.DataFrame.from_dict(quality_data, orient="index", columns=["value"]))

# Multi-season trend (wOBA vs xwOBA)
st.subheader("Multi-season trend (wOBA vs xwOBA)")

import datetime as _dt  # noqa: E402
_CURRENT_YEAR = _dt.datetime.utcnow().year
_CURRENT_MONTH = _dt.datetime.utcnow().month
# A season is considered "partial" if it's the current calendar year and
# we're still in the first half (before Aug 1) — fewer than ~350 PA on avg.
_PARTIAL_SEASONS = {_CURRENT_YEAR} if _CURRENT_MONTH < 8 else set()

trend_rows = []
for s in sorted(data_loader.available_seasons()):
    hist = data_loader.load_players_scored(s)
    if hist.empty:
        continue
    hit = hist[hist["Name"] == chosen]
    if hit.empty:
        continue
    h = hit.iloc[0]
    label = f"{s}*" if s in _PARTIAL_SEASONS else str(s)
    trend_rows.append({
        "season_label": label,
        "season_order": s,
        "wOBA": h.get("wOBA"),
        "xwOBA": h.get("xwOBA"),
    })

if len(trend_rows) >= 2:
    trend = pd.DataFrame(trend_rows).sort_values("season_order")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend["season_label"], y=trend["wOBA"],
        mode="lines+markers", name="wOBA",
        line=dict(color="#1f77b4", width=2),
        marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=trend["season_label"], y=trend["xwOBA"],
        mode="lines+markers", name="xwOBA",
        line=dict(color="#ff7f0e", width=2, dash="dot"),
        marker=dict(size=8),
    ))
    fig.update_layout(
        height=380,
        xaxis_title="Season",
        yaxis_title="wOBA / xwOBA",
        xaxis=dict(type="category"),   # discrete — no interpolation between years
        yaxis=dict(tickformat=".3f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    has_partial = bool(_PARTIAL_SEASONS & {r["season_order"] for r in trend_rows})
    if has_partial:
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "\\* Season marked with \\* is partial (early season — stats based on limited PA). "
            "Treat that data point as preliminary, not a trend signal."
        )
    else:
        st.plotly_chart(fig, use_container_width=True)
elif len(trend_rows) == 1:
    st.info(
        f"Only one season of data on disk for {chosen}. "
        "Trend chart will populate as more historical seasons are added."
    )
else:
    st.info("No historical data found for this player.")

# ── AI Analyst Summary ────────────────────────────────────────────────────────
st.subheader("AI Analyst Summary")

has_key = bool(st.secrets.get("ANTHROPIC_API_KEY", ""))
lang = st.session_state.get("lang", "EN")

if not has_key:
    st.info(
        "Add `ANTHROPIC_API_KEY` to `.streamlit/secrets.toml` (local) or "
        "Streamlit Cloud → App settings → Secrets to enable AI summaries.",
        icon="🔑",
    )
else:
    stats_json = build_stats_json(row)
    with st.spinner("Generating analyst summary…"):
        summary = generate_summary(chosen, season, lang, stats_json)
    if summary:
        st.markdown(
            f'<div style="background:#f8f9fa;border-left:3px solid #1f77b4;'
            f'padding:0.8rem 1rem;border-radius:4px;line-height:1.6;">'
            f"{summary}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption("Generated by Claude · cached 24 h · not a substitute for your own analysis")
