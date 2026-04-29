"""Parquet readers for the Streamlit app. All reads are cached and cheap."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_TTL = 3600  # 1 hour; nightly job invalidates by file mtime anyway


@st.cache_data(ttl=CACHE_TTL)
def load_players_scored(season: int) -> pd.DataFrame:
    """League-wide hitters with merged FanGraphs + Statcast + Undervalued Score components."""
    path = DATA_DIR / f"players_scored_{season}.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(ttl=CACHE_TTL)
def load_batting(season: int) -> pd.DataFrame:
    path = DATA_DIR / f"batting_{season}.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(ttl=CACHE_TTL)
def load_statcast_expected(season: int) -> pd.DataFrame:
    path = DATA_DIR / f"statcast_expected_{season}.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(ttl=CACHE_TTL)
def load_statcast_quality(season: int) -> pd.DataFrame:
    path = DATA_DIR / f"statcast_quality_{season}.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(ttl=CACHE_TTL)
def load_status() -> dict:
    """Returns nightly job metadata: last_run_utc, errors per stage, etc."""
    path = DATA_DIR / "_status.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def available_seasons() -> list[int]:
    """All seasons present on disk, newest first."""
    seasons = []
    for f in DATA_DIR.glob("players_scored_*.parquet"):
        try:
            seasons.append(int(f.stem.split("_")[-1]))
        except ValueError:
            continue
    return sorted(seasons, reverse=True)
