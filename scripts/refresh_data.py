"""Nightly orchestrator: fetch FanGraphs + Statcast, score players, write Parquet.

Phase 1 scope: batting stats, expected stats, quality of contact, and the
joined `players_scored_{season}.parquet`. Roster/salary/free-agent scrapers
arrive in Phase 2.

Run:
    python scripts/refresh_data.py [--season 2025]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import traceback
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))

from scoutiq.score import annotate  # noqa: E402


def _safe_write(df: pd.DataFrame, path: Path) -> bool:
    """Only overwrite if df has rows; never clobber a good file with empty data."""
    if df is None or df.empty:
        print(f"  ⚠ skipping {path.name}: empty frame")
        return False
    df.to_parquet(path, index=False)
    print(f"  ✓ wrote {path.name} ({len(df):,} rows)")
    return True


def fetch_batting(season: int) -> pd.DataFrame:
    """Baseball Reference season batting stats (FanGraphs is currently 403'd).

    Returns the major-league subset with raw counts that we use to derive
    BABIP, K%, and BB%. wOBA comes from Statcast's expected_stats table.
    """
    from pybaseball import batting_stats_bref

    df = batting_stats_bref(season)
    if "Lev" in df.columns:
        df = df[df["Lev"].str.startswith("Maj", na=False)].copy()
    return df


def fetch_expected(season: int) -> pd.DataFrame:
    """Baseball Savant expected stats: xBA, xSLG, xwOBA, xISO."""
    from pybaseball import statcast_batter_expected_stats

    df = statcast_batter_expected_stats(season, minPA="q")
    return df


def fetch_quality(season: int) -> pd.DataFrame:
    """Baseball Savant quality of contact: barrel%, hard hit%, EV, LA."""
    from pybaseball import statcast_batter_exitvelo_barrels

    df = statcast_batter_exitvelo_barrels(season, minBBE="q")
    return df


def _coerce_pct(s: pd.Series) -> pd.Series:
    """FanGraphs returns percent strings ('25.4%') for some columns; coerce to floats."""
    if s.dtype == object:
        return s.astype(str).str.rstrip("%").astype(float) / 100.0
    return s


def join_and_score(batting: pd.DataFrame, expected: pd.DataFrame, quality: pd.DataFrame) -> pd.DataFrame:
    """Merge BR batting + Statcast expected + Statcast quality, then score.

    Merge key: MLBAM player id ('mlbID' on BR, 'player_id' on Statcast).
    """
    bat = batting.rename(columns={"mlbID": "MLBAMID", "Tm": "Team", "BA": "AVG"}).copy()
    bat["MLBAMID"] = pd.to_numeric(bat["MLBAMID"], errors="coerce").astype("Int64")

    # Derived rate stats from BR raw counts
    pa = bat["PA"].astype(float)
    ab = bat["AB"].astype(float)
    h = bat["H"].astype(float)
    hr = bat["HR"].astype(float)
    so = bat["SO"].astype(float)
    bb = bat["BB"].astype(float)
    sf = bat.get("SF", pd.Series(0, index=bat.index)).astype(float).fillna(0)
    bat["K%"] = (so / pa).where(pa > 0)
    bat["BB%"] = (bb / pa).where(pa > 0)
    babip_denom = ab - so - hr + sf
    bat["BABIP"] = ((h - hr) / babip_denom).where(babip_denom > 0)
    bat["ISO"] = bat["SLG"] - bat["AVG"]

    exp = expected.rename(columns={
        "player_id": "MLBAMID",
        "est_ba": "xBA",
        "est_slg": "xSLG",
        "est_woba": "xwOBA",
        "woba": "wOBA",
    }).copy()
    exp["xISO"] = exp["xSLG"] - exp["xBA"]
    exp_cols = ["MLBAMID", "wOBA", "xBA", "xSLG", "xwOBA", "xISO"]
    exp = exp[[c for c in exp_cols if c in exp.columns]]

    qual = quality.rename(columns={
        "player_id": "MLBAMID",
        "brl_percent": "Barrel%",
        "ev95percent": "HardHit%",
        "avg_hit_speed": "EV",
        "avg_hit_angle": "LA",
    }).copy()
    # GB% from raw counts: gb / (gb + fbld) where fbld = FB+LD count
    if {"gb", "fbld"}.issubset(qual.columns):
        denom = qual["gb"] + qual["fbld"]
        qual["GB%"] = (qual["gb"] / denom).where(denom > 0)
    qual_cols = ["MLBAMID", "Barrel%", "HardHit%", "EV", "LA", "GB%"]
    qual = qual[[c for c in qual_cols if c in qual.columns]]

    merged = bat.merge(exp, on="MLBAMID", how="inner")
    merged = merged.merge(qual, on="MLBAMID", how="left")

    # Statcast HardHit% / Barrel% come back as percentages (e.g. 42.1) — convert to fractions
    for col in ("Barrel%", "HardHit%"):
        if col in merged.columns and merged[col].dropna().max() > 1:
            merged[col] = merged[col] / 100.0

    required = ["wOBA", "xwOBA", "SLG", "xSLG", "BABIP"]
    missing = [c for c in required if c not in merged.columns]
    if missing:
        raise RuntimeError(f"Missing required columns after join: {missing}")
    merged = merged.dropna(subset=required)

    return annotate(merged)


def write_status(stages: dict[str, str], season: int) -> None:
    payload = {
        "last_run_utc": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "season": season,
        "stages": stages,
    }
    (DATA_DIR / "_status.json").write_text(json.dumps(payload, indent=2))


def main(season: int) -> int:
    print(f"\n=== ScoutIQ refresh for season {season} ===")
    stages: dict[str, str] = {}

    try:
        print("[1/4] FanGraphs batting…")
        batting = fetch_batting(season)
        _safe_write(batting, DATA_DIR / f"batting_{season}.parquet")
        stages["batting"] = f"ok ({len(batting)} rows)"
    except Exception as e:
        stages["batting"] = f"error: {e}"
        traceback.print_exc()
        batting = pd.DataFrame()

    try:
        print("[2/4] Statcast expected stats…")
        expected = fetch_expected(season)
        _safe_write(expected, DATA_DIR / f"statcast_expected_{season}.parquet")
        stages["expected"] = f"ok ({len(expected)} rows)"
    except Exception as e:
        stages["expected"] = f"error: {e}"
        traceback.print_exc()
        expected = pd.DataFrame()

    try:
        print("[3/4] Statcast quality of contact…")
        quality = fetch_quality(season)
        _safe_write(quality, DATA_DIR / f"statcast_quality_{season}.parquet")
        stages["quality"] = f"ok ({len(quality)} rows)"
    except Exception as e:
        stages["quality"] = f"error: {e}"
        traceback.print_exc()
        quality = pd.DataFrame()

    if batting.empty or expected.empty:
        print("[4/4] Skipping score join — required inputs missing.")
        stages["scored"] = "skipped (missing inputs)"
        write_status(stages, season)
        return 1

    try:
        print("[4/4] Joining and scoring…")
        scored = join_and_score(batting, expected, quality)
        _safe_write(scored, DATA_DIR / f"players_scored_{season}.parquet")
        stages["scored"] = f"ok ({len(scored)} rows)"
    except Exception as e:
        stages["scored"] = f"error: {e}"
        traceback.print_exc()

    write_status(stages, season)
    print("\nStages:", json.dumps(stages, indent=2))
    return 0 if all(v.startswith("ok") for v in stages.values()) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=dt.datetime.utcnow().year)
    args = parser.parse_args()
    raise SystemExit(main(args.season))
