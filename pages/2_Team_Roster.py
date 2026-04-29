"""Module 2 — Team Roster Analysis: position-by-position breakdown with $/WAR overlay."""

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
from scoutiq.salary import add_dollar_per_war, fmt_salary  # noqa: E402
from scoutiq.score import compute_score  # noqa: E402

st.set_page_config(page_title="Team Roster — ScoutIQ", page_icon="⚾", layout="wide")
render_sidebar()

st.title("Team Roster Analysis")
st.caption("Position-by-position breakdown: surface stats, Statcast quality, and salary efficiency.")

season = st.session_state["season"]
team = st.session_state["team"]
weights = st.session_state["weights"]

# Load data
scored = data_loader.load_players_scored(season)
rosters = data_loader.load_rosters()
salaries = data_loader.load_salaries()

if scored.empty:
    st.error(f"No `players_scored_{season}.parquet`. Run `python scripts/refresh_data.py --season {season}`.")
    st.stop()

if rosters.empty:
    st.warning("No roster data yet. Run `python scripts/refresh_data.py` to fetch 40-man rosters.")
    # Fall back to players tagged to this team in scored data
    if "Team" in scored.columns:
        roster_ids = scored[scored["Team"].str.upper().str.contains(team, na=False)]["MLBAMID"].tolist()
    else:
        roster_ids = []
else:
    roster_ids = rosters[rosters["Team"] == team]["MLBAMID"].tolist()

# Filter scored frame to this team's roster
if roster_ids:
    team_df = scored[scored["MLBAMID"].isin(roster_ids)].copy()
    # Attach position labels from the roster parquet
    if not rosters.empty and "Pos" in rosters.columns:
        pos_map = rosters[rosters["Team"] == team][["MLBAMID", "Pos"]].drop_duplicates("MLBAMID")
        team_df = team_df.merge(pos_map, on="MLBAMID", how="left")
else:
    # Fallback: match by Team string
    team_df = scored[scored.get("Team", pd.Series(dtype=str)).str.upper().str.contains(team, na=False)].copy()

if team_df.empty:
    st.warning(f"No players found for **{team}** in {season} data. They may not have enough PA in the qualified pool.")
    st.info("Tip: lower the Min PA slider in the sidebar to see more players.")
    st.stop()

# Attach salary if available
if not salaries.empty and "Name" in salaries.columns and "Salary" in salaries.columns:
    team_df = team_df.merge(
        salaries[["Name", "Salary"]].drop_duplicates("Name"),
        on="Name", how="left"
    )
else:
    team_df["Salary"] = float("nan")

# Recompute score with current sidebar weights
team_df["undervalued_score"] = compute_score(team_df, weights)

# Add $/WAR if WAR column present
if "WAR" in team_df.columns:
    team_df = add_dollar_per_war(team_df)
    team_df["Salary_fmt"] = team_df["Salary"].apply(fmt_salary)
    team_df["DPW_fmt"] = team_df.get("dollar_per_war", pd.Series(dtype=float)).apply(
        lambda v: f"${v/1e6:.1f}M/WAR" if pd.notna(v) else "—"
    )

# ── Position heatmap ──────────────────────────────────────────────────────────
st.subheader("Position overview")

POS_ORDER = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH", "OF", "UTIL"]

pos_col = next((c for c in ("Pos", "position", "POS") if c in team_df.columns), None)

# League-wide averages used for all absolute comparisons
league_avg_xwoba = scored["xwOBA"].mean()
league_avg_woba = scored["wOBA"].mean()

if pos_col and not team_df[pos_col].dropna().empty:
    pos_summary = (
        team_df.groupby(pos_col, as_index=False)
        .agg(
            Players=("Name", "count"),
            avg_wOBA=("wOBA", "mean"),
            avg_xwOBA=("xwOBA", "mean"),
            avg_score=("undervalued_score", "mean"),
        )
    )
    # Color by xwOBA vs league average — this directly answers "is this position strong?"
    # Undervalued Score is a regression/luck signal, not a production signal.
    pos_summary["xwOBA_vs_avg"] = pos_summary["avg_xwOBA"] - league_avg_xwoba

    fig_heat = px.bar(
        pos_summary.sort_values("xwOBA_vs_avg"),
        x=pos_col, y="xwOBA_vs_avg",
        color="xwOBA_vs_avg",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        title=f"{team} {season} — xwOBA vs league average by position",
        labels={pos_col: "Position", "xwOBA_vs_avg": "xwOBA above/below avg"},
        hover_data={"avg_xwOBA": ":.3f", "avg_wOBA": ":.3f", "avg_score": ":.0f"},
        height=320,
    )
    fig_heat.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="league avg")
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption(
        f"League avg xwOBA: **{league_avg_xwoba:.3f}**  ·  "
        "Green = above average production  ·  Red = below average production  ·  "
        "Undervalued Score (luck/regression) shown in the table below."
    )
else:
    st.info("Position data not available — run the roster scraper for position labels.")

# ── Roster table ──────────────────────────────────────────────────────────────
st.subheader(f"{team} qualified hitters — {season}")

display_cols = [c for c in [
    "Name", pos_col, "PA", "AVG", "wOBA", "xwOBA", "woba_gap",
    "BABIP", "Barrel%", "HardHit%", "WAR", "Salary_fmt", "DPW_fmt", "undervalued_score", "valuation_label"
] if c and c in team_df.columns]

st.dataframe(
    team_df[display_cols].sort_values("undervalued_score", ascending=False).reset_index(drop=True),
    use_container_width=True,
    height=500,
)

# ── Actionable flags ──────────────────────────────────────────────────────────
st.subheader("Actionable flags")

# Three distinct buckets — each with a different recommended action:
#
# 1. Hold / watch  : wOBA below league avg, but xwOBA above → pure bad luck, stay patient
# 2. True concern  : BOTH wOBA and xwOBA below league avg   → real skill issue, consider upgrade
# 3. Regression risk: wOBA well above xwOBA (Sell High)     → performing above true skill level,
#                     numbers likely to regress (still may be a good player — see Ben Rice)

flag_watch   = team_df[
    (team_df["wOBA"] < league_avg_woba) & (team_df["xwOBA"] >= league_avg_xwoba)
]
flag_concern = team_df[
    (team_df["wOBA"] < league_avg_woba) & (team_df["xwOBA"] < league_avg_xwoba)
]
flag_regress = team_df[
    (team_df["woba_gap"] < -0.025) & (team_df["xwOBA"] >= league_avg_xwoba)
]

col_watch, col_concern, col_regress = st.columns(3)

with col_watch:
    st.markdown("**📊 Hold / watch** — bad luck, not bad skill")
    st.caption("wOBA < avg, xwOBA ≥ avg. Stay patient.")
    if not flag_watch.empty:
        st.dataframe(
            flag_watch[["Name", "wOBA", "xwOBA", "woba_gap"]].sort_values("woba_gap", ascending=False),
            use_container_width=True,
        )
    else:
        st.caption("None.")

with col_concern:
    st.markdown("**🔴 True concern** — real skill issue")
    st.caption("Both wOBA and xwOBA below league avg. Consider upgrading.")
    if not flag_concern.empty:
        st.dataframe(
            flag_concern[["Name", "wOBA", "xwOBA", "BABIP"]].sort_values("xwOBA"),
            use_container_width=True,
        )
    else:
        st.caption("None.")

with col_regress:
    st.markdown("**⚠️ Regression risk** — outperforming true skill")
    st.caption("wOBA >> xwOBA (gap < −0.025) despite being above avg. Numbers likely to come down.")
    if not flag_regress.empty:
        st.dataframe(
            flag_regress[["Name", "wOBA", "xwOBA", "woba_gap"]].sort_values("woba_gap"),
            use_container_width=True,
        )
    else:
        st.caption("None.")

# Cross-link: weakest positions = xwOBA below league average (absolute production)
# NOT Undervalued Score — a "Sell High" player like Ben Rice is strong, just lucky.
if pos_col and not team_df[pos_col].dropna().empty:
    weak_pos = (
        team_df[team_df["xwOBA"] < league_avg_xwoba]
        .groupby(pos_col)["xwOBA"].mean()
        .sort_values()
        .index.tolist()
    )
    if weak_pos:
        pos_list = ", ".join(weak_pos)
        st.info(f"Positions below league avg xwOBA: **{pos_list}** → [Find free agents](/Free_Agent_Finder)")
