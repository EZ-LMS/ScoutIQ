"""Salary efficiency helpers."""

from __future__ import annotations

import pandas as pd

# 2025 market rate: ~$9.5M per WAR in free agency
WAR_MARKET_RATE = 9_500_000.0


def add_dollar_per_war(df: pd.DataFrame, salary_col: str = "Salary", war_col: str = "WAR") -> pd.DataFrame:
    """Add $/WAR and market_value columns. Negative WAR → $/WAR = NaN."""
    out = df.copy()
    if salary_col not in out.columns or war_col not in out.columns:
        return out
    war = pd.to_numeric(out[war_col], errors="coerce")
    sal = pd.to_numeric(out[salary_col], errors="coerce")
    out["dollar_per_war"] = (sal / war).where(war > 0)
    out["market_value"] = war * WAR_MARKET_RATE
    out["surplus_value"] = out["market_value"] - sal
    return out


def fmt_salary(val: float | None) -> str:
    """Format salary as $3.2M or $720K."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    if val >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    return f"${val/1_000:.0f}K"
