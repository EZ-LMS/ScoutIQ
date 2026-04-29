"""Undervalued Score: 0–100 composite blending xwOBA-wOBA gap, xSLG-SLG gap, and BABIP luck."""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_WEIGHTS = {"woba_gap": 60.0, "slg_gap": 25.0, "babip_luck": 15.0}

BUY_LOW_THRESHOLD = 70.0
SELL_HIGH_THRESHOLD = 30.0


def _z(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    std = s.std(ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.mean()) / std


def compute_components(df: pd.DataFrame) -> pd.DataFrame:
    """Add raw component columns. Expects: wOBA, xwOBA, SLG, xSLG, BABIP, GB%."""
    out = df.copy()
    out["woba_gap"] = out["xwOBA"] - out["wOBA"]
    out["slg_gap"] = out["xSLG"] - out["SLG"]

    # xBABIP proxy: league average BABIP within GB% deciles. Players with very
    # high GB% naturally suppress BABIP a little less than expected on contact —
    # this is a coarse but defensible proxy without a regression model.
    if "GB%" in out.columns:
        out["_gb_decile"] = pd.qcut(out["GB%"], 10, labels=False, duplicates="drop")
        league_babip_by_gb = out.groupby("_gb_decile")["BABIP"].transform("mean")
        out["babip_luck"] = out["BABIP"] - league_babip_by_gb
        out = out.drop(columns="_gb_decile")
    else:
        out["babip_luck"] = out["BABIP"] - out["BABIP"].mean()
    return out


def compute_score(df: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.Series:
    """Return the Undervalued Score (0–100) for each row.

    Each component is z-scored, weighted, summed, and added to baseline 50.
    Sum of weights is normalized to 100 so the user can retune relative weights
    without warping the overall scale. Scaling factor (1/4) keeps ±2σ players
    in roughly the [0, 100] range without heavy clipping.
    """
    w = weights or DEFAULT_WEIGHTS
    total_w = w["woba_gap"] + w["slg_gap"] + w["babip_luck"]
    if total_w <= 0:
        return pd.Series(50.0, index=df.index)
    norm = 100.0 / total_w
    z_woba = _z(df["woba_gap"])
    z_slg = _z(df["slg_gap"])
    z_luck = _z(df["babip_luck"])
    raw = (
        50.0
        + z_woba * w["woba_gap"] * norm * 0.25
        + z_slg * w["slg_gap"] * norm * 0.25
        + z_luck * w["babip_luck"] * norm * 0.25
    )
    return raw.clip(0, 100)


def label(score: float) -> str:
    if score >= BUY_LOW_THRESHOLD:
        return "Buy Low"
    if score <= SELL_HIGH_THRESHOLD:
        return "Sell High"
    return "Fair Value"


def annotate(df: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Convenience: add components, score, and label columns."""
    out = compute_components(df)
    out["undervalued_score"] = compute_score(out, weights)
    out["valuation_label"] = out["undervalued_score"].map(label)
    return out
