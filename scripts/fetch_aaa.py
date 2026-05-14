"""Fetch Triple-A batting stats from the MLB Stats API.

Builds an affiliate map (AAA team_id → MLB team abbreviation) dynamically,
then pulls season-level hitting stats for all AAA players.

wOBA is approximated from counting stats using 2024 linear weights.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

STATS_URL = (
    "https://statsapi.mlb.com/api/v1/stats"
    "?stats=season&group=hitting&gameType=R"
    "&season={season}&sportId=11&limit=500&offset={offset}"
)
TEAMS_MLB_URL = "https://statsapi.mlb.com/api/v1/teams?sportId=1&season={season}"
TEAMS_AAA_URL = "https://statsapi.mlb.com/api/v1/teams?sportId=11&season={season}"

HEADERS = {"User-Agent": "ScoutIQ/1.0 (portfolio project; ezchen0919@gmail.com)"}

# 2024 linear weights (FanGraphs guts page)
_LW_BB = 0.690
_LW_1B = 0.888
_LW_2B = 1.271
_LW_3B = 1.616
_LW_HR = 2.101


def _build_affiliate_map(season: int) -> dict[int, str]:
    """Return {aaa_team_id: mlb_team_abbreviation} using Stats API team data."""
    mlb_r = requests.get(TEAMS_MLB_URL.format(season=season), headers=HEADERS, timeout=15)
    mlb_r.raise_for_status()
    org_to_abbrev: dict[int, str] = {
        t["id"]: t.get("abbreviation", "")
        for t in mlb_r.json().get("teams", [])
    }

    time.sleep(0.5)
    aaa_r = requests.get(TEAMS_AAA_URL.format(season=season), headers=HEADERS, timeout=15)
    aaa_r.raise_for_status()
    affiliate_map: dict[int, str] = {}
    for t in aaa_r.json().get("teams", []):
        parent_id = t.get("parentOrgId")
        if parent_id and parent_id in org_to_abbrev:
            affiliate_map[t["id"]] = org_to_abbrev[parent_id]
    return affiliate_map


def _approx_woba(row: dict) -> float | None:
    """Compute wOBA from counting stats using linear weights."""
    pa = row.get("plateAppearances", 0) or 0
    if pa < 1:
        return None
    bb = row.get("baseOnBalls", 0) or 0
    h = row.get("hits", 0) or 0
    d = row.get("doubles", 0) or 0
    t = row.get("triples", 0) or 0
    hr = row.get("homeRuns", 0) or 0
    singles = max(0, h - d - t - hr)
    num = _LW_BB * bb + _LW_1B * singles + _LW_2B * d + _LW_3B * t + _LW_HR * hr
    return num / pa


def _fetch_all_splits(season: int) -> list[dict]:
    """Page through the stats endpoint and return all splits."""
    splits: list[dict] = []
    offset = 0
    while True:
        r = requests.get(
            STATS_URL.format(season=season, offset=offset),
            headers=HEADERS, timeout=30,
        )
        r.raise_for_status()
        data = r.json().get("stats", [])
        if not data:
            break
        batch = data[0].get("splits", [])
        if not batch:
            break
        splits.extend(batch)
        if len(batch) < 500:
            break
        offset += 500
        time.sleep(0.5)
    return splits


def fetch_aaa_batting(season: int) -> pd.DataFrame:
    """Return a DataFrame of Triple-A hitters with computed rate stats and affiliate."""
    affiliate_map = _build_affiliate_map(season)
    splits = _fetch_all_splits(season)

    rows = []
    for split in splits:
        player = split.get("player", {})
        team = split.get("team", {})
        stat = split.get("stat", {})

        pa = stat.get("plateAppearances", 0) or 0
        ab = stat.get("atBats", 0) or 0
        h = stat.get("hits", 0) or 0
        d = stat.get("doubles", 0) or 0
        t = stat.get("triples", 0) or 0
        hr = stat.get("homeRuns", 0) or 0
        k = stat.get("strikeOuts", 0) or 0
        bb = stat.get("baseOnBalls", 0) or 0
        sf = stat.get("sacFlies", 0) or 0

        avg_raw = stat.get("avg", None)
        obp_raw = stat.get("obp", None)
        slg_raw = stat.get("slg", None)
        babip_raw = stat.get("babip", None)

        def _flt(v):
            try:
                return float(v) if v not in (None, ".---", "-.--") else None
            except (TypeError, ValueError):
                return None

        avg = _flt(avg_raw)
        obp = _flt(obp_raw)
        slg = _flt(slg_raw)
        babip = _flt(babip_raw)

        # Derive stats from counting stats where possible (more reliable than API strings)
        if ab > 0:
            avg = h / ab
        if pa > 0:
            k_pct = k / pa
            bb_pct = bb / pa
        else:
            k_pct = bb_pct = None

        iso = (slg - avg) if (slg is not None and avg is not None) else None

        babip_denom = ab - k - hr + sf
        if babip is None and babip_denom > 0:
            babip = (h - hr) / babip_denom

        woba = _approx_woba(stat)

        aaa_team_id = team.get("id")
        mlb_aff = affiliate_map.get(aaa_team_id, "")

        rows.append({
            "MLBAMID": player.get("id"),
            "Name": player.get("fullName", ""),
            "AAATeam": team.get("abbreviation", team.get("name", "")),
            "MLBAff": mlb_aff,
            "PA": pa,
            "AVG": avg,
            "OBP": obp,
            "SLG": slg,
            "ISO": iso,
            "wOBA": woba,
            "BABIP": babip,
            "K%": k_pct,
            "BB%": bb_pct,
            "HR": hr,
            "H": h,
            "2B": d,
            "3B": t,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Attach primary position from a separate roster-level call if possible,
    # but for now default to empty — Module 3 will use name matching to MLB rosters.
    df["MLBAMID"] = pd.to_numeric(df["MLBAMID"], errors="coerce").astype("Int64")
    return df.sort_values("PA", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    import argparse, datetime as dt  # noqa: E401

    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=dt.datetime.utcnow().year)
    args = parser.parse_args()

    out = Path(__file__).resolve().parent.parent / "data" / f"aaa_batting_{args.season}.parquet"
    print(f"Fetching Triple-A batting stats for {args.season}…")
    df = fetch_aaa_batting(args.season)
    if not df.empty:
        df.to_parquet(out, index=False)
        print(f"✓ wrote {out.name} ({len(df):,} rows, {df['MLBAff'].nunique()} affiliates)")
    else:
        print("⚠ No data returned")
