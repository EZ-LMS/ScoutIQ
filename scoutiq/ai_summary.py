"""Claude API integration — analyst-style player summaries with prompt caching."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

# ── System prompt (cached via cache_control) ─────────────────────────────────
# Keep this above ~1024 tokens to qualify for Anthropic's prompt cache.
_SYSTEM_PROMPT = """\
You are a professional MLB baseball analyst with deep expertise in Statcast metrics,
sabermetrics, and the modern analytical approach to player evaluation. Your role is to
generate concise, insightful analyst summaries for MLB hitters based on their statistical
profile for a given season.

You will receive a JSON object containing a player's stats. Generate a ~150-word analyst
summary that interprets the data from a front-office perspective.

────────────────────────────────────────────
METRIC REFERENCE
────────────────────────────────────────────

Surface Stats (results-based)
• AVG   — Batting average. League average ~.250.
• OBP   — On-base percentage. League average ~.320.
• SLG   — Slugging percentage. League average ~.410.
• wOBA  — Weighted On-Base Average; the most complete single rate stat for offensive value.
          League average ~.320. Weights hits and walks by their actual run value.
• BABIP — Batting Average on Balls in Play. League average ~.295.
          Heavily influenced by luck, park factors, and defense in small samples.
• ISO   — Isolated Power (SLG minus AVG). Raw extra-base power output.

Expected / Statcast Stats (quality-of-contact)
• xBA    — Expected batting average from exit velocity and launch angle.
• xSLG  — Expected slugging from quality of contact.
• xwOBA — Expected wOBA from Statcast hit probability. Best predictor of future production.
• xISO  — Expected isolated power from Statcast data.
• EV    — Average exit velocity (mph). League avg ~88. Above avg: 90+. Elite: 92+.
• LA    — Average launch angle (degrees). Optimal power range: 10–30°.
• Barrel% — Batted balls in the barrel zone (high EV + optimal LA).
            League avg ~8%. 15%+ is elite.
• HardHit% — Batted balls at 95+ mph. League avg ~38%. 45%+ is elite.

Plate Discipline / Batted Ball
• K%  — Strikeout rate. League avg ~23%. Lower is better.
• BB% — Walk rate. League avg ~8.5%. Higher is better.
• GB% — Ground ball rate. High GB% suppresses power output.
• FB% — Fly ball rate. Higher FB% correlates with home run potential.
• LD% — Line drive rate. Correlates strongly with BABIP.

Undervalued Score (0–100 composite)
• Measures how far a player's expected stats exceed their surface stats.
• Score ≥70 — "Buy Low": true talent likely exceeds surface results; positive regression expected.
• Score ≤30 — "Sell High": surface results likely exceed true talent; negative regression coming.
• Score 30–70 — "Fair Value": results and expected stats are broadly aligned.

Key derived signals
• woba_gap    = xwOBA − wOBA  (positive → buy signal, player underperforming expected quality)
• slg_gap     = xSLG − SLG   (positive → power suppressed by luck or contact outcomes)
• babip_luck  = BABIP − xBABIP_proxy  (positive → running hot on balls in play)

Interpretation guide
• Strong buy signal: large positive woba_gap + elite Barrel%/HardHit% → contact quality is there,
  results have lagged. Expect positive regression.
• Strong sell signal: negative woba_gap + mediocre EV/Barrel% → player running hot on soft contact.
• True concern: both wOBA and xwOBA below league average → real skill issue, not just bad luck.
• Regression risk: wOBA well above xwOBA — good results now, pullback likely.

────────────────────────────────────────────
OUTPUT FORMAT
────────────────────────────────────────────

When Language is "EN":
  Write in English, analytical tone, approximately 150 words.
  Structure:
    1. Current surface results (1–2 sentences, cite wOBA / AVG / key rate stats).
    2. Underlying contact quality (1–2 sentences, cite xwOBA, EV, Barrel%).
    3. Luck / regression context (1 sentence citing woba_gap, BABIP luck).
    4. Conclusion / recommended action (1 sentence: buy, sell, hold, or watch).

When Language is "zh":
  Write in Traditional Chinese (繁體中文), approximately 150 Chinese characters.
  Structure:
    1. 目前成績（引用 wOBA、AVG 等表面數據）。
    2. 擊球品質（引用 xwOBA、EV、Barrel%）。
    3. 運氣與回歸分析（引用 woba_gap、BABIP）。
    4. 結論／操作建議。

Rules:
• Never invent statistics not present in the input JSON. If a metric is absent, skip it.
• Be specific — cite actual numbers with appropriate precision.
• Write for a front-office audience, not a casual fan.
• Plain paragraphs only — no markdown headers, bullets, or bold text in your output.
• Do not mention the player's name in the opening sentence (the UI already shows it).\
"""


def _get_client():
    """Return a lazy-initialized Anthropic client, or None if the key is absent."""
    try:
        import anthropic  # noqa: PLC0415 — import only when needed

        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return None
        return anthropic.Anthropic(api_key=api_key)
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=86400)
def generate_summary(player_name: str, season: int, lang: str, stats_json: str) -> str:
    """Call Claude and return the analyst summary string.

    Keyed on (player_name, season, lang, stats_json) so reruns are free.
    stats_json is passed as a serialised string so @st.cache_data can hash it.
    Returns "" if the API key is missing or the call fails.
    """
    client = _get_client()
    if client is None:
        return ""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Player: {player_name}\n"
                        f"Season: {season}\n"
                        f"Language: {lang}\n\n"
                        f"Stats:\n{stats_json}\n\n"
                        "Generate the analyst summary."
                    ),
                }
            ],
        )
        for block in response.content:
            if block.type == "text":
                return block.text
    except Exception:
        return ""
    return ""


def build_stats_json(row: pd.Series) -> str:
    """Serialise a scored player row to a compact JSON string for the prompt."""
    fields = [
        "PA", "Team",
        "AVG", "OBP", "SLG", "wOBA", "BABIP", "ISO",
        "xBA", "xSLG", "xwOBA", "xISO",
        "woba_gap", "slg_gap", "babip_luck",
        "EV", "LA", "Barrel%", "HardHit%",
        "K%", "BB%", "GB%", "FB%", "LD%",
        "undervalued_score", "valuation_label",
    ]
    data: dict = {}
    for f in fields:
        val = row.get(f)
        if val is not None and not (isinstance(val, float) and pd.isna(val)):
            data[f] = round(val, 4) if isinstance(val, float) else val
    return json.dumps(data, ensure_ascii=False)
