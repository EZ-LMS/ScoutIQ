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

st.set_page_config(page_title="Player Deep Dive — ScoutIQ", page_icon="⚾", layout="wide")
render_sidebar()

st.title("Player Deep Dive")
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

# 3-season trend (wOBA vs xwOBA) — pulled from any available historical Parquet
st.subheader("Multi-season trend (wOBA vs xwOBA)")
trend_rows = []
for s in sorted(data_loader.available_seasons()):
    hist = data_loader.load_players_scored(s)
    if hist.empty:
        continue
    hit = hist[hist["Name"] == chosen]
    if hit.empty:
        continue
    h = hit.iloc[0]
    trend_rows.append({"season": s, "wOBA": h.get("wOBA"), "xwOBA": h.get("xwOBA")})

if trend_rows:
    trend = pd.DataFrame(trend_rows)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["season"], y=trend["wOBA"], mode="lines+markers", name="wOBA"))
    fig.add_trace(go.Scatter(x=trend["season"], y=trend["xwOBA"], mode="lines+markers", name="xwOBA"))
    fig.update_layout(height=380, xaxis_title="Season", yaxis_title="wOBA / xwOBA")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Only one season of data on disk — trend chart needs ≥2 seasons.")

st.caption("Phase 3 will add a Claude-generated analyst summary here.")
