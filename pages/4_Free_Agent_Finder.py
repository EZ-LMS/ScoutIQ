"""Module 4 — Free Agent Finder: Undervalued Score applied to the FA market."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import render_sidebar  # noqa: E402
from scoutiq import data_loader  # noqa: E402
from scoutiq.score import compute_score, DEFAULT_WEIGHTS  # noqa: E402

st.set_page_config(page_title="Free Agent Finder — ScoutIQ", page_icon="⚾", layout="wide")
render_sidebar()

st.title("Free Agent Finder")
st.caption("Market-undervalued players available for signing — filtered by position need.")

season = st.session_state["season"]
weights = st.session_state["weights"]

# Read the pre-scored league-wide frame and the free-agent list
scored = data_loader.load_players_scored(season)
fa_list = data_loader.load_free_agents()

if scored.empty:
    st.error(f"No `players_scored_{season}.parquet`. Run `python scripts/refresh_data.py --season {season}`.")
    st.stop()

# ── Merge: attach Statcast quality scores to free agent list ─────────────────
if not fa_list.empty and "Name" in fa_list.columns:
    fa_scored = fa_list.merge(
        scored[["Name", "wOBA", "xwOBA", "SLG", "xSLG", "BABIP",
                "woba_gap", "slg_gap", "babip_luck",
                "Barrel%", "HardHit%", "K%", "BB%", "AVG", "xBA", "MLBAMID"]],
        on="Name", how="inner"
    )
    if not fa_scored.empty:
        fa_scored["undervalued_score"] = compute_score(fa_scored, weights)
        fa_scored["valuation_label"] = fa_scored["undervalued_score"].apply(
            lambda s: "Buy Low" if s >= 70 else ("Sell High" if s <= 30 else "Fair Value")
        )
    else:
        fa_scored = scored.copy()
        fa_scored["undervalued_score"] = compute_score(fa_scored, weights)
        st.info("Free agent list loaded but no name matches with scored data — showing full league pool instead.")
else:
    # No FA parquet yet: show scored pool with a banner
    fa_scored = scored.copy()
    fa_scored["undervalued_score"] = compute_score(fa_scored, weights)
    st.warning(
        "No `free_agents.parquet` on disk. Run the refresh job to fetch the current FA list. "
        "Showing all qualified hitters as a proxy."
    )

# ── Filters ──────────────────────────────────────────────────────────────────
filter_col, main_col = st.columns([1, 3])

with filter_col:
    st.subheader("Filters")

    # Position filter (pre-populated from Module 2 cross-link via query param)
    pos_options = ["All"]
    pos_col_name = next((c for c in ("Pos", "PosType", "position") if c in fa_scored.columns), None)
    if pos_col_name:
        pos_options += sorted(fa_scored[pos_col_name].dropna().unique().tolist())
    qp_pos = st.query_params.get("pos", "All")
    default_pos = qp_pos if qp_pos in pos_options else "All"
    pos_filter = st.selectbox("Position", pos_options, index=pos_options.index(default_pos))

    label_filter = st.multiselect(
        "Valuation",
        ["Buy Low", "Fair Value", "Sell High"],
        default=["Buy Low"],
    )
    min_score = st.slider("Min Undervalued Score", 0, 100, 50)

with main_col:
    filtered = fa_scored.copy()
    if pos_filter != "All" and pos_col_name:
        filtered = filtered[filtered[pos_col_name] == pos_filter]
    if label_filter:
        filtered = filtered[filtered["valuation_label"].isin(label_filter)]
    filtered = filtered[filtered["undervalued_score"] >= min_score]

    st.subheader(f"{len(filtered)} players match")

    if filtered.empty:
        st.info("No players match the current filters. Try adjusting position or score threshold.")
    else:
        # Scatter: xwOBA vs wOBA colored by score
        fig = px.scatter(
            filtered,
            x="xwOBA", y="wOBA",
            color="undervalued_score",
            color_continuous_scale="RdYlGn",
            range_color=(0, 100),
            hover_data={
                "Name": True,
                pos_col_name: True if pos_col_name else False,
                "xwOBA": ":.3f",
                "wOBA": ":.3f",
                "woba_gap": ":.3f",
                "undervalued_score": ":.0f",
            },
            title="Free Agent pool — xwOBA vs wOBA",
            height=420,
        )
        lo = float(min(filtered["xwOBA"].min(), filtered["wOBA"].min()))
        hi = float(max(filtered["xwOBA"].max(), filtered["wOBA"].max()))
        fig.add_shape(type="line", x0=lo, y0=lo, x1=hi, y1=hi,
                      line=dict(color="gray", dash="dash", width=1))
        st.plotly_chart(fig, use_container_width=True)

        display_cols = [c for c in [
            "Name", pos_col_name, "wOBA", "xwOBA", "woba_gap",
            "Barrel%", "HardHit%", "K%", "BB%", "undervalued_score", "valuation_label"
        ] if c and c in filtered.columns]
        st.dataframe(
            filtered[display_cols].sort_values("undervalued_score", ascending=False).reset_index(drop=True),
            use_container_width=True, height=400,
        )
