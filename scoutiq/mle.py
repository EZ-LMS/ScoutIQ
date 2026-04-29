"""Davenport-style AAA → MLB statistical translations."""

from __future__ import annotations

import pandas as pd

# Stat-specific multipliers. Rate stats (K%, BB%) are inverted by direction:
# AAA hitters strike out less in MLB-equivalent terms? No — they strike out MORE in MLB,
# so we multiply K% UP by 1.10. BB% drops slightly, so 0.95.
MULTIPLIERS = {
    "wOBA": 0.82,
    "OBP": 0.80,
    "SLG": 0.78,
    "AVG": 0.81,
    "ISO": 0.75,
    "K%": 1.10,
    "BB%": 0.95,
}


def translate(aaa_df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with MLB-equivalent versions of any supported stat columns.

    New columns are prefixed with `mle_` (e.g. `mle_wOBA`).
    """
    out = aaa_df.copy()
    for col, mult in MULTIPLIERS.items():
        if col in out.columns:
            out[f"mle_{col}"] = out[col] * mult
    return out
