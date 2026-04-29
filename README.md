# ScoutIQ — MLB Player Intelligence Platform

A Streamlit web app that surfaces undervalued and overvalued MLB hitters by comparing surface stats (wOBA, AVG, SLG) to underlying Statcast quality (xwOBA, xBA, xSLG, Barrel%, Hard Hit%).

Built for MLB front-office analysts and scouts; deployable on Streamlit Cloud free tier.

## Quick start

```bash
pip install -r requirements.txt
python scripts/refresh_data.py        # builds data/*.parquet (~3-5 min)
streamlit run app.py
```

## How it works

- **Nightly data refresh** (GitHub Actions, 09:00 UTC): pulls FanGraphs + Baseball Savant via `pybaseball`, scrapes salaries from Cot's Contracts and free agents from MLB Trade Rumors, computes the Undervalued Score, commits Parquet files to `data/`.
- **Streamlit app** reads pre-computed Parquet — no live API calls on the hot path.

## Undervalued Score

```
score = 50
      + z(xwOBA - wOBA) × 60 × 0.5
      + z(xSLG  - SLG ) × 25 × 0.5
      + z(BABIP_luck  ) × 15 × 0.5     →  clipped to [0, 100]
```

Weights drop the xBA-AVG term that the spec originally proposed: it is largely redundant with xwOBA-wOBA. Buckets: Buy Low ≥70, Fair Value 30–70, Sell High <30.

## AAA → MLB translation

Stat-specific Davenport multipliers (used in Module 3):

| Stat | Mult | Stat | Mult |
|------|------|------|------|
| wOBA | 0.82 | AVG  | 0.81 |
| OBP  | 0.80 | K%   | 1.10 |
| SLG  | 0.78 | BB%  | 0.95 |
| ISO  | 0.75 |      |      |

## Modules

1. **League Intelligence** — league scatter (xwOBA vs wOBA) + Top 10 Buy Low / Sell High.
2. **Team Roster Analysis** — 40-man broken out by position, with $/WAR.
3. **Call-Up / Send-Down Evaluator** — MLB roster vs AAA candidates with MLE translation.
4. **Free Agent Finder** — Undervalued Score applied to FA market.
5. **Player Deep Dive** — full metric panel, 3-yr trend, AI-generated analyst summary.

## Layout

See `/Users/yichen/.claude/plans/scoutiq-baseball-curried-rivest.md` for the full plan.
