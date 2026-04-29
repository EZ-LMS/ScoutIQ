"""Scrape current MLB free agent list from Baseball Reference.

Baseball Reference's free-agent tracker is more stable than MLB Trade Rumors
for programmatic access. URL pattern:
  https://www.baseball-reference.com/leagues/MLB/2025-free-agents.shtml
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pandas as pd
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_free_agents(season: int | None = None) -> pd.DataFrame:
    """Return list of free agents for the given off-season (e.g. season=2025 → 2025-26 FA class).

    Season is the year the FA class was created (typically the year their contract ended).
    Since the 2026 class doesn't exist yet mid-season, we fall back to 2025.
    """
    if season is None:
        season = datetime.datetime.utcnow().year
    # bref FA pages cover completed off-seasons; fall back one year during the active season
    if season >= datetime.datetime.utcnow().year:
        season = season - 1

    url = f"https://www.baseball-reference.com/leagues/MLB/{season}-free-agents.shtml"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()

    # bref embeds its main tables inside HTML comments — extract them first
    from bs4 import BeautifulSoup, Comment
    soup = BeautifulSoup(r.text, "lxml")
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment) and "<table" in t):
        fragment = BeautifulSoup(str(comment), "lxml")
        for tbl in fragment.find_all("table"):
            comment.replace_with(tbl)

    from io import StringIO
    try:
        tables = pd.read_html(StringIO(str(soup)), flavor="lxml")
    except Exception:
        return pd.DataFrame()

    if not tables:
        return pd.DataFrame()

    # Table 0: full FA transaction log — Name, Date, To Team, From Team, Age, Pos, Years, Value
    df = tables[0].copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Drop sub-header rows
    name_col = next((c for c in df.columns if c.lower() == "name"), None)
    if name_col:
        df = df[df[name_col] != name_col].copy()
        df = df.rename(columns={name_col: "Name"})

    rename = {
        "Age": "Age",
        "Pos": "Pos",
        "From Team": "PrevTeam",
        "To Team": "NewTeam",
        "WAR3": "WAR3",
        "Value": "ContractValue",
        "Years": "ContractYears",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    for col in ("Age", "WAR3", "ContractYears"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["fa_season"] = season
    return df.dropna(subset=["Name"]).reset_index(drop=True)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data" / "free_agents.parquet"
    print("Scraping Baseball Reference free agents...")
    df = scrape_free_agents()
    if not df.empty:
        df.to_parquet(out, index=False)
        print(f"✓ wrote {out.name} ({len(df):,} rows)")
        show_cols = [c for c in ["Name", "Pos", "PrevTeam", "NewTeam", "Age"] if c in df.columns]
        print(df.head(5)[show_cols].to_string(index=False))
    else:
        print("⚠ No data returned")
