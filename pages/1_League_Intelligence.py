"""Module 1 — League Intelligence: xwOBA vs wOBA scatter + Buy Low / Sell High lists."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import render_sidebar  # noqa: E402
from scoutiq import data_loader  # noqa: E402
from scoutiq.help_link import help_link  # noqa: E402
from scoutiq.score import compute_score  # noqa: E402

st.set_page_config(page_title="League Intelligence — ScoutIQ", page_icon="⚾", layout="wide")
render_sidebar()

st.title("League Intelligence")
help_link("module_league")
st.caption("How far does each hitter's surface wOBA stray from their xwOBA?")

season = st.session_state["season"]
min_pa = st.session_state["min_pa"]
weights = st.session_state["weights"]

df = data_loader.load_players_scored(season)
if df.empty:
    st.error(f"No `players_scored_{season}.parquet` on disk. Run `python scripts/refresh_data.py --season {season}`.")
    st.stop()

if "PA" in df.columns:
    df = df[df["PA"] >= min_pa].copy()

# Allow runtime reweighting from sidebar without rerunning the nightly job
df["undervalued_score"] = compute_score(df, weights)

left, right = st.columns([3, 2])

with left:
    fig = px.scatter(
        df,
        x="xwOBA",
        y="wOBA",
        color="undervalued_score",
        color_continuous_scale="RdYlGn",
        range_color=(0, 100),
        size="PA" if "PA" in df.columns else None,
        size_max=18,
        hover_data={
            "Name": True,
            "Team": True if "Team" in df.columns else False,
            "PA": True if "PA" in df.columns else False,
            "xwOBA": ":.3f",
            "wOBA": ":.3f",
            "woba_gap": ":.3f",
            "undervalued_score": ":.0f",
        },
        title=f"{season} qualified hitters — xwOBA vs wOBA",
        height=620,
    )
    # Diagonal reference line: wOBA == xwOBA (no gap)
    lo = float(min(df["xwOBA"].min(), df["wOBA"].min()))
    hi = float(max(df["xwOBA"].max(), df["wOBA"].max()))
    fig.add_shape(
        type="line", x0=lo, y0=lo, x1=hi, y1=hi,
        line=dict(color="gray", dash="dash", width=1),
    )
    fig.update_layout(coloraxis_colorbar=dict(title="Undervalued"))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Top 10 Buy Low")
    cols = [c for c in ["Name", "Team", "PA", "wOBA", "xwOBA", "woba_gap", "undervalued_score"] if c in df.columns]
    buy_low = df.nlargest(10, "undervalued_score")[cols].reset_index(drop=True)
    st.dataframe(buy_low, use_container_width=True, height=380)

    st.subheader("Top 10 Sell High")
    sell_high = df.nsmallest(10, "undervalued_score")[cols].reset_index(drop=True)
    st.dataframe(sell_high, use_container_width=True, height=380)

st.caption(
    f"Pool: {len(df):,} hitters · Min PA: {min_pa} · "
    f"Weights — wOBA gap: {weights['woba_gap']}, SLG gap: {weights['slg_gap']}, BABIP luck: {weights['babip_luck']}"
)
