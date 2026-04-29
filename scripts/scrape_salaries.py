"""Scrape 2025 MLB salary data from Cot's Baseball Contracts (Baseball Prospectus).

Source: https://legacy.baseballprospectus.com/compensation/cots/
Uses pandas.read_html — no API key required. Permitted for non-commercial use.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://legacy.baseballprospectus.com/compensation/cots/"
HEADERS = {"User-Agent": "ScoutIQ/1.0 (portfolio project; ezchen0919@gmail.com)"}
DELAY_SECS = 2.0

# Cot's URL slugs for all 30 teams (al_east, nl_west, etc. subdirectories)
TEAM_SLUGS = [
    "al_east/baltimore_orioles", "al_east/boston_red_sox",
    "al_east/new_york_yankees", "al_east/tampa_bay_rays",
    "al_east/toronto_blue_jays",
    "al_central/chicago_white_sox", "al_central/cleveland_guardians",
    "al_central/detroit_tigers", "al_central/kansas_city_royals",
    "al_central/minnesota_twins",
    "al_west/houston_astros", "al_west/los_angeles_angels",
    "al_west/oakland_athletics", "al_west/seattle_mariners",
    "al_west/texas_rangers",
    "nl_east/atlanta_braves", "nl_east/miami_marlins",
    "nl_east/new_york_mets", "nl_east/philadelphia_phillies",
    "nl_east/washington_nationals",
    "nl_central/chicago_cubs", "nl_central/cincinnati_reds",
    "nl_central/milwaukee_brewers", "nl_central/pittsburgh_pirates",
    "nl_central/st_louis_cardinals",
    "nl_west/arizona_diamondbacks", "nl_west/colorado_rockies",
    "nl_west/los_angeles_dodgers", "nl_west/san_diego_padres",
    "nl_west/san_francisco_giants",
]

# Rough team-name → abbreviation map for joining with our player data
TEAM_NAME_TO_ABBREV = {
    "orioles": "BAL", "red sox": "BOS", "yankees": "NYY", "rays": "TB",
    "blue jays": "TOR", "white sox": "CWS", "guardians": "CLE",
    "tigers": "DET", "royals": "KC", "twins": "MIN", "astros": "HOU",
    "angels": "LAA", "athletics": "OAK", "mariners": "SEA", "rangers": "TEX",
    "braves": "ATL", "marlins": "MIA", "mets": "NYM", "phillies": "PHI",
    "nationals": "WSH", "cubs": "CHC", "reds": "CIN", "brewers": "MIL",
    "pirates": "PIT", "cardinals": "STL", "diamondbacks": "ARI",
    "rockies": "COL", "dodgers": "LAD", "padres": "SD", "giants": "SF",
}


def _parse_salary(val: str) -> float | None:
    """'$3,200,000' or '$3.2M' → float in dollars."""
    if not isinstance(val, str):
        return None
    val = val.strip().lstrip("$").replace(",", "")
    if val.lower().endswith("m"):
        try:
            return float(val[:-1]) * 1_000_000
        except ValueError:
            return None
    try:
        return float(val)
    except ValueError:
        return None


def scrape_team_page(slug: str) -> pd.DataFrame:
    url = BASE_URL + slug
    try:
        tables = pd.read_html(url, flavor="lxml")
    except Exception:
        # Try with requests + header injection
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        tables = pd.read_html(r.text, flavor="lxml")

    if not tables:
        return pd.DataFrame()

    # Cot's puts the active roster salary table first; it has columns like
    # Name, Pos, Salary (or Salary/Year), Yrs, etc.
    # We'll grab the largest table and find salary-looking columns.
    df = max(tables, key=len).copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Identify player name and salary columns heuristically
    name_col = next((c for c in df.columns if "name" in c.lower() or c == "Player"), None)
    if name_col is None and len(df.columns) > 0:
        name_col = df.columns[0]

    salary_col = next(
        (c for c in df.columns
         if any(k in c.lower() for k in ("salary", "aav", "avg ann", "/yr", "value"))),
        None,
    )

    if not salary_col:
        return pd.DataFrame()

    result = pd.DataFrame()
    result["Name"] = df[name_col].astype(str).str.strip()
    result["Salary"] = df[salary_col].apply(_parse_salary)

    # Derive team abbreviation from slug
    team_key = slug.split("/")[-1].replace("_", " ").lower()
    abbrev = next((v for k, v in TEAM_NAME_TO_ABBREV.items() if k in team_key), "UNK")
    result["Team"] = abbrev

    return result.dropna(subset=["Salary"])


def scrape_all_salaries() -> pd.DataFrame:
    frames = []
    for slug in TEAM_SLUGS:
        try:
            df = scrape_team_page(slug)
            if not df.empty:
                frames.append(df)
                print(f"  ✓ {slug.split('/')[-1]} ({len(df)} players)")
            else:
                print(f"  ⚠ {slug.split('/')[-1]}: no salary table found")
        except Exception as e:
            print(f"  ✗ {slug.split('/')[-1]}: {e}")
        time.sleep(DELAY_SECS)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data" / "salaries.parquet"
    print("Scraping Cot's Contracts...")
    df = scrape_all_salaries()
    if not df.empty:
        df.to_parquet(out, index=False)
        print(f"\n✓ wrote {out.name} ({len(df):,} rows)")
    else:
        print("⚠ No data returned")
