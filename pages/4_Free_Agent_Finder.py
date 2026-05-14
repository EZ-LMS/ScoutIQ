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
from scoutiq.help_link import help_link  # noqa: E402
from scoutiq.score import compute_score  # noqa: E402

st.set_page_config(page_title="Free Agent Finder — ScoutIQ", page_icon="⚾", layout="wide")
render_sidebar()

st.title("Free Agent Finder")
help_link("module_fa")
st.caption("Market-undervalued players available for signing — filtered by position need.")

weights = st.session_state["weights"]

# ── Load FA list ──────────────────────────────────────────────────────────────
fa_list = data_loader.load_free_agents()
rosters = data_loader.load_rosters()

if fa_list.empty:
    # No FA parquet: fall back to full scored pool for current season
    season = st.session_state["season"]
    scored = data_loader.load_players_scored(season)
    if scored.empty:
        st.error(f"No `players_scored_{season}.parquet`. Run the refresh job first.")
        st.stop()
    fa_scored = scored.copy()
    fa_scored["undervalued_score"] = compute_score(fa_scored, weights)
    fa_scored["valuation_label"] = fa_scored["undervalued_score"].apply(
        lambda s: "Buy Low" if s >= 70 else ("Sell High" if s <= 30 else "Fair Value")
    )
    st.warning(
        "No `free_agents.parquet` on disk. Run the refresh job to fetch the current FA list. "
        "Showing all qualified hitters as a proxy."
    )
else:
    # ── Use fa_season to pick the right stats year ────────────────────────────
    # FA players signed in the off-season after fa_season — score them against
    # that season's full stats, not the current (potentially partial) season.
    fa_season = int(fa_list["fa_season"].mode()[0]) if "fa_season" in fa_list.columns else st.session_state["season"]
    scored = data_loader.load_players_scored(fa_season)

    if scored.empty:
        # Try sidebar season as fallback
        fa_season = st.session_state["season"]
        scored = data_loader.load_players_scored(fa_season)

    if scored.empty:
        st.error("No scored player data found. Run the refresh job first.")
        st.stop()

    st.caption(f"Scoring FA candidates against **{fa_season}** season stats (most recent full season).")

    # ── Merge scored stats into FA list ──────────────────────────────────────
    score_cols = ["Name", "wOBA", "xwOBA", "SLG", "xSLG", "BABIP",
                  "woba_gap", "slg_gap", "babip_luck",
                  "Barrel%", "HardHit%", "K%", "BB%", "AVG", "xBA", "MLBAMID"]
    score_cols = [c for c in score_cols if c in scored.columns]

    fa_scored = fa_list.merge(scored[score_cols], on="Name", how="inner")

    if fa_scored.empty:
        # No name matches — show full scored pool with warning
        fa_scored = scored.copy()
        st.info(
            f"FA list loaded ({len(fa_list)} players) but no name matches with {fa_season} scored data. "
            "Showing full qualified-hitter pool instead."
        )
    else:
        matched = len(fa_scored)
        st.caption(f"Matched **{matched}** of {len(fa_list)} FA names to {fa_season} Statcast data.")

    fa_scored["undervalued_score"] = compute_score(fa_scored, weights)
    fa_scored["valuation_label"] = fa_scored["undervalued_score"].apply(
        lambda s: "Buy Low" if s >= 70 else ("Sell High" if s <= 30 else "Fair Value")
    )

    # ── Attach position from rosters (FA list has no position column) ─────────
    if not rosters.empty and "MLBAMID" in fa_scored.columns and "Pos" in rosters.columns:
        pos_map = (
            rosters[["MLBAMID", "Pos"]]
            .dropna(subset=["MLBAMID", "Pos"])
            .drop_duplicates("MLBAMID")
        )
        fa_scored = fa_scored.merge(pos_map, on="MLBAMID", how="left")

# ── Detect position column ────────────────────────────────────────────────────
pos_col_name = next((c for c in ("Pos", "PosType", "position") if c in fa_scored.columns), None)

# ── Filters ───────────────────────────────────────────────────────────────────
filter_col, main_col = st.columns([1, 3])

with filter_col:
    st.subheader("Filters")

    pos_options = ["All"]
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
        st.info("No players match the current filters. Try adjusting position, valuation, or score threshold.")
    else:
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
