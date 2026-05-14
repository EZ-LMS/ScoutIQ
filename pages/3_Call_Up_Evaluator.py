"""Module 3 — Call-Up Evaluator: AAA prospects vs. MLB incumbents with Davenport MLEs."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import render_sidebar  # noqa: E402
from scoutiq import data_loader  # noqa: E402
from scoutiq.help_link import help_link  # noqa: E402
from scoutiq.mle import MULTIPLIERS, translate  # noqa: E402

st.set_page_config(page_title="Call-Up Evaluator — ScoutIQ", page_icon="⚾", layout="wide")
render_sidebar()

st.title("Call-Up Evaluator")
help_link("module_callup")
st.caption("Compare AAA prospects to MLB incumbents using Davenport MLB-equivalent translations.")

st.info(
    "**Caveat:** AAA Statcast expected stats (xwOBA, Barrel%) are not publicly available. "
    "Comparisons use surface stats only — wOBA, OBP, SLG, K%, BB%. "
    "MLE translations apply Davenport multipliers; treat as estimates, not projections.",
    icon="⚠️",
)

season = st.session_state["season"]
team = st.session_state["team"]

# ── Load data ──────────────────────────────────────────────────────────────────
mlb_scored = data_loader.load_players_scored(season)
rosters = data_loader.load_rosters()
aaa_raw = data_loader.load_aaa_batting(season)

if mlb_scored.empty:
    st.error(f"No `players_scored_{season}.parquet`. Run `python scripts/refresh_data.py`.")
    st.stop()

# ── Build MLB team frame ───────────────────────────────────────────────────────
if not rosters.empty:
    roster_ids = rosters[rosters["Team"] == team]["MLBAMID"].tolist()
    team_mlb = mlb_scored[mlb_scored["MLBAMID"].isin(roster_ids)].copy()
    if not rosters.empty and "Pos" in rosters.columns:
        pos_map = (
            rosters[rosters["Team"] == team][["MLBAMID", "Pos"]]
            .drop_duplicates("MLBAMID")
        )
        team_mlb = team_mlb.merge(pos_map, on="MLBAMID", how="left")
else:
    team_mlb = mlb_scored[
        mlb_scored.get("Team", pd.Series(dtype=str)).str.upper().str.contains(team, na=False)
    ].copy()

# ── Build AAA team frame ───────────────────────────────────────────────────────
if aaa_raw.empty:
    aaa_team = pd.DataFrame()
    st.warning(
        f"No `aaa_batting_{season}.parquet` on disk. "
        "Run `python scripts/refresh_data.py` (or `python scripts/fetch_aaa.py`) to fetch Triple-A stats."
    )
else:
    aaa_team = aaa_raw[aaa_raw["MLBAff"] == team].copy()

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.subheader("Call-Up filters")
    min_aaa_pa = st.slider("Min AAA plate appearances", 50, 300, 100, step=25)

# ── Apply Davenport MLEs ───────────────────────────────────────────────────────
if not aaa_team.empty:
    aaa_team = aaa_team[aaa_team["PA"] >= min_aaa_pa].copy()
    aaa_team = translate(aaa_team)

# ── MLE reference card ─────────────────────────────────────────────────────────
with st.expander("Davenport MLE multipliers used in this table"):
    mle_df = pd.DataFrame(
        [{"Stat": k, "Multiplier": v, "Direction": "AAA × mult = MLB-equivalent"}
         for k, v in MULTIPLIERS.items()]
    )
    st.table(mle_df.set_index("Stat"))
    st.caption(
        "Source: Davenport translations via Clay Davenport's work. "
        "K% is multiplied *up* (hitters strike out more vs. MLB pitching); "
        "all others are multiplied down."
    )

# ── Summary metrics ────────────────────────────────────────────────────────────
col_a, col_b, col_c = st.columns(3)
col_a.metric("MLB qualifiers on roster", len(team_mlb))
col_b.metric(
    f"AAA prospects (≥{min_aaa_pa} PA)",
    len(aaa_team) if not aaa_team.empty else "—",
)

if not aaa_team.empty and not team_mlb.empty:
    mlb_avg_woba = team_mlb["wOBA"].mean()
    upgrade_count = (aaa_team["mle_wOBA"] > mlb_avg_woba).sum()
    col_c.metric("Prospects above team avg wOBA (MLE)", upgrade_count)

# ── Position-by-position comparison ───────────────────────────────────────────
st.subheader("Position comparison")

pos_col = next((c for c in ("Pos", "position", "POS") if c in team_mlb.columns), None)

if pos_col and not team_mlb[pos_col].dropna().empty and not aaa_team.empty:
    POS_ORDER = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH", "OF", "P"]

    available_pos = sorted(
        team_mlb[pos_col].dropna().unique().tolist(),
        key=lambda p: POS_ORDER.index(p) if p in POS_ORDER else 99,
    )

    selected_pos = st.selectbox("Filter by position", ["All"] + available_pos)

    mlb_show = team_mlb if selected_pos == "All" else team_mlb[team_mlb[pos_col] == selected_pos]

    mlb_display_cols = [c for c in [
        "Name", pos_col, "PA", "wOBA", "xwOBA", "woba_gap",
        "Barrel%", "HardHit%", "K%", "BB%", "undervalued_score",
    ] if c in mlb_show.columns]

    aaa_display_cols = [c for c in [
        "Name", "AAATeam", "PA", "wOBA", "mle_wOBA", "OBP", "mle_OBP",
        "SLG", "mle_SLG", "K%", "mle_K%", "BB%", "mle_BB%",
    ] if c in aaa_team.columns]

    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown(f"**{team} MLB hitters**")
        if mlb_show.empty:
            st.caption("No qualified hitters at this position.")
        else:
            st.dataframe(
                mlb_show[mlb_display_cols]
                .sort_values("wOBA", ascending=False)
                .reset_index(drop=True),
                use_container_width=True,
                height=380,
            )

    with right_col:
        st.markdown(f"**{team} AAA prospects** (MLE stats)")
        if aaa_team.empty:
            st.caption("No AAA data available.")
        else:
            aaa_sorted = aaa_team[aaa_display_cols].sort_values("mle_wOBA", ascending=False)
            st.dataframe(aaa_sorted.reset_index(drop=True), use_container_width=True, height=380)

    # ── Upgrade flags ──────────────────────────────────────────────────────────
    if not aaa_team.empty and not team_mlb.empty:
        st.subheader("Upgrade candidates")
        st.caption(
            "Prospects whose MLE wOBA exceeds the team's MLB average wOBA at their level. "
            "Not a guaranteed improvement — check K%, BB%, and sample size."
        )

        mlb_avg = team_mlb["wOBA"].mean()
        upgrade_mask = aaa_team["mle_wOBA"] > mlb_avg
        upgrades = aaa_team[upgrade_mask].copy()

        if upgrades.empty:
            st.info("No AAA prospects currently projecting above team average wOBA on an MLE basis.")
        else:
            upgrades["vs_team_avg"] = upgrades["mle_wOBA"] - mlb_avg
            upgrade_cols = [c for c in [
                "Name", "AAATeam", "PA", "wOBA", "mle_wOBA", "vs_team_avg",
                "mle_OBP", "mle_SLG", "mle_K%", "mle_BB%",
            ] if c in upgrades.columns]
            st.dataframe(
                upgrades[upgrade_cols].sort_values("vs_team_avg", ascending=False).reset_index(drop=True),
                use_container_width=True,
            )

            # Scatter: AAA wOBA vs MLE wOBA colored by vs_team_avg
            if "mle_wOBA" in upgrades.columns and "wOBA" in upgrades.columns:
                fig = px.scatter(
                    upgrades,
                    x="wOBA", y="mle_wOBA",
                    color="vs_team_avg",
                    color_continuous_scale="RdYlGn",
                    hover_data={"Name": True, "PA": True, "mle_wOBA": ":.3f", "vs_team_avg": ":.3f"},
                    title=f"{team} AAA upgrade candidates — raw AAA wOBA vs MLE",
                    height=380,
                    labels={"wOBA": "AAA wOBA (raw)", "mle_wOBA": "MLE wOBA (MLB-equivalent)"},
                )
                fig.add_hline(
                    y=mlb_avg, line_dash="dash", line_color="gray",
                    annotation_text=f"team avg wOBA ({mlb_avg:.3f})",
                )
                st.plotly_chart(fig, use_container_width=True)

elif aaa_team.empty:
    st.info("AAA data not yet available for this team. Run the data refresh to populate.")
else:
    st.info("Position data not available — run the roster scraper for position labels.")

# ── Full AAA table ─────────────────────────────────────────────────────────────
if not aaa_team.empty:
    st.subheader(f"All {team} AAA prospects — {season}")
    all_cols = [c for c in [
        "Name", "AAATeam", "PA",
        "AVG", "OBP", "SLG", "wOBA", "BABIP", "ISO",
        "mle_wOBA", "mle_OBP", "mle_SLG", "mle_ISO",
        "K%", "BB%", "mle_K%", "mle_BB%",
    ] if c in aaa_team.columns]
    st.dataframe(
        aaa_team[all_cols].sort_values("mle_wOBA", ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=500,
    )
