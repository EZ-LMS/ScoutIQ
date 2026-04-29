"""Scrape MLB.com 40-man rosters for all 30 teams.

MLB.com team slug examples: bos, nyy, sf, lad, hou ...
We use the Stats API endpoint which returns JSON — far more reliable than HTML scraping.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

# MLB Stats API endpoint for 40-man rosters (rosterType=40Man)
ROSTER_URL = "https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=40Man"
TEAMS_URL = "https://statsapi.mlb.com/api/v1/teams?sportId=1"

HEADERS = {"User-Agent": "ScoutIQ/1.0 (portfolio project; ezchen0919@gmail.com)"}
DELAY_SECS = 1.0  # polite rate-limiting


def fetch_teams() -> pd.DataFrame:
    """Return all 30 MLB team IDs and abbreviations."""
    r = requests.get(TEAMS_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    teams = r.json()["teams"]
    rows = [
        {
            "team_id": t["id"],
            "team_abbrev": t.get("abbreviation", ""),
            "team_name": t.get("teamName", ""),
            "full_name": t.get("name", ""),
        }
        for t in teams
    ]
    return pd.DataFrame(rows)


def fetch_roster(team_id: int, team_abbrev: str) -> pd.DataFrame:
    """Return 40-man roster for one team with position and MLBAM player id."""
    url = ROSTER_URL.format(team_id=team_id)
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    roster = r.json().get("roster", [])
    rows = []
    for p in roster:
        person = p.get("person", {})
        pos = p.get("position", {})
        rows.append({
            "MLBAMID": person.get("id"),
            "Name": person.get("fullName", ""),
            "Team": team_abbrev,
            "Pos": pos.get("abbreviation", ""),
            "PosType": pos.get("type", ""),
            "Status": p.get("status", {}).get("description", ""),
        })
    return pd.DataFrame(rows)


def scrape_all_rosters() -> pd.DataFrame:
    """Fetch 40-man rosters for all 30 teams."""
    teams = fetch_teams()
    frames = []
    for _, row in teams.iterrows():
        try:
            df = fetch_roster(row["team_id"], row["team_abbrev"])
            frames.append(df)
            time.sleep(DELAY_SECS)
        except Exception as e:
            print(f"  ⚠ {row['team_abbrev']} failed: {e}")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data" / "rosters.parquet"
    print("Fetching 40-man rosters...")
    df = scrape_all_rosters()
    if not df.empty:
        df.to_parquet(out, index=False)
        print(f"✓ wrote {out.name} ({len(df):,} rows, {df['Team'].nunique()} teams)")
    else:
        print("⚠ No data returned")
