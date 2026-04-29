"""ScoutIQ — Streamlit entry point and global sidebar."""

from __future__ import annotations

import datetime as dt

import streamlit as st

from scoutiq import data_loader
from scoutiq.score import DEFAULT_WEIGHTS

st.set_page_config(page_title="ScoutIQ", page_icon="⚾", layout="wide")

MLB_TEAMS = [
    "ARI", "ATL", "BAL", "BOS", "CHC", "CWS", "CIN", "CLE", "COL", "DET",
    "HOU", "KC",  "LAA", "LAD", "MIA", "MIL", "MIN", "NYM", "NYY", "OAK",
    "PHI", "PIT", "SD",  "SEA", "SF",  "STL", "TB",  "TEX", "TOR", "WSH",
]


def _init_state() -> None:
    today = dt.datetime.utcnow().year
    seasons = data_loader.available_seasons() or [today]
    st.session_state.setdefault("season", seasons[0])
    st.session_state.setdefault("team", "SF")
    st.session_state.setdefault("min_pa", 200)
    st.session_state.setdefault("weights", dict(DEFAULT_WEIGHTS))


def render_sidebar() -> None:
    _init_state()

    with st.sidebar:
        st.title("⚾ ScoutIQ")

        seasons = data_loader.available_seasons() or [dt.datetime.utcnow().year]
        st.selectbox("Season", seasons, key="season")
        st.selectbox("Home team", MLB_TEAMS, key="team")
        st.slider("Min PA", min_value=50, max_value=600, step=10, key="min_pa")

        with st.expander("Undervalued Score weights", expanded=False):
            st.caption("Defaults: 60 / 25 / 15. Sum is normalized internally.")
            w = st.session_state["weights"]
            w["woba_gap"] = st.slider("xwOBA − wOBA gap", 0, 100, int(w["woba_gap"]))
            w["slg_gap"] = st.slider("xSLG − SLG gap", 0, 100, int(w["slg_gap"]))
            w["babip_luck"] = st.slider("BABIP luck", 0, 100, int(w["babip_luck"]))

        status = data_loader.load_status()
        if status:
            st.caption(f"Data refreshed: {status.get('last_run_utc', '—')}")
            stages = status.get("stages", {})
            broken = [k for k, v in stages.items() if not str(v).startswith("ok")]
            if broken:
                st.warning(f"Stale stages: {', '.join(broken)}")
        else:
            st.caption("No data on disk yet. Run `python scripts/refresh_data.py`.")


def render_home() -> None:
    st.title("ScoutIQ")
    st.subheader("MLB player intelligence — surface vs. underlying performance")

    season = st.session_state["season"]
    df = data_loader.load_players_scored(season)

    if df.empty:
        st.error(
            "No data found. Run the refresh job first:\n\n"
            "```bash\npython scripts/refresh_data.py --season "
            f"{season}\n```"
        )
        return

    df = df[df.get("PA", 0) >= st.session_state["min_pa"]] if "PA" in df.columns else df

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Players in pool", f"{len(df):,}")
    col_b.metric("Median xwOBA", f"{df['xwOBA'].median():.3f}")
    col_c.metric("Buy Low (≥70)", int((df["undervalued_score"] >= 70).sum()))
    col_d.metric("Sell High (≤30)", int((df["undervalued_score"] <= 30).sum()))

    st.markdown(
        """
        **Modules**
        - **League Intelligence** — league-wide xwOBA vs. wOBA scatter with Buy Low / Sell High top 10.
        - **Player Deep Dive** — full metric panel and trend chart for any qualified hitter.
        - *(Phase 2)* Team Roster, Free Agent Finder.
        - *(Phase 3)* Call-Up Evaluator, AI summary.
        """
    )


def main() -> None:
    render_sidebar()
    render_home()


if __name__ == "__main__":
    main()
