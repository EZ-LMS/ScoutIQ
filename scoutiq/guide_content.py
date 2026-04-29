"""Bilingual (EN / 中文) content for the ScoutIQ Guide page.

Structure: SECTIONS is an ordered list of section dicts.
Each section has: id, title, en (markdown), zh (markdown).
"""

from __future__ import annotations

SECTIONS: list[dict] = [
    # ── Overview ──────────────────────────────────────────────────────────────
    {
        "id": "overview",
        "title": {"en": "What is ScoutIQ?", "zh": "ScoutIQ 是什麼？"},
        "en": """
ScoutIQ is a baseball player intelligence platform built for MLB front-office analysts and scouts.

**The core thesis:** A player's *surface statistics* (the numbers in the box score) often diverge from
their *underlying quality* (what Statcast says about how hard and well they hit the ball).
That divergence — caused by luck, sequencing, and sample noise — creates **market inefficiencies**:
players who are undervalued (surface looks bad, underlying is strong) or overvalued (surface looks
good, underlying is weak).

ScoutIQ surfaces these inefficiencies using an **Undervalued Score** (0–100) and applies it to four
decision contexts:
1. **League-wide** buy-low / sell-high signals
2. **Team roster** position-by-position health check
3. **Free agent market** CP value search
4. **Single player** deep-dive with trend analysis
""",
        "zh": """
ScoutIQ 是一個棒球球員分析平台，專為 MLB 球隊的分析師與球探設計。

**核心理念：** 球員的*表面數據*（打擊率、上壘率等出現在比分欄的數字）往往和他們的*底層品質*（Statcast 測量的擊球速度、角度等）存在落差。
這個落差由運氣、時機與樣本誤差造成，形成**市場效率失靈**：被低估的球員（表面看起來差，但擊球品質很好）或被高估的球員（表面好看，但擊球品質不支撐）。

ScoutIQ 透過 **Undervalued Score（0–100 分）** 找出這些落差，並應用在四個決策場景：
1. **全聯盟**買入低估 / 賣出高估信號
2. **球隊陣容**逐位置健康檢查
3. **自由球員市場**性價比搜尋
4. **單一球員**完整分析與趨勢圖
""",
    },
    # ── Undervalued Score ─────────────────────────────────────────────────────
    {
        "id": "undervalued_score",
        "title": {"en": "Undervalued Score", "zh": "Undervalued Score（低估分數）"},
        "en": """
**Range:** 0–100 · **Buckets:** Buy Low ≥ 70 · Fair Value 30–70 · Sell High ≤ 30

### Formula

```
Score = 50
      + z(xwOBA − wOBA)  × 60 × 0.25   # how much better true quality is than surface
      + z(xSLG  − SLG )  × 25 × 0.25   # power-specific luck signal
      + z(BABIP_luck    ) × 15 × 0.25   # sequencing / park / speed luck
  clipped to [0, 100]
```

Each component is **z-scored** (how many standard deviations from the league mean) so the weights
stay stable across seasons regardless of run-environment changes.

### Component weights

| Component | Weight | Why |
|-----------|--------|-----|
| xwOBA − wOBA | 60 | Strongest single predictor of year-over-year regression; xwOBA captures *all* batted-ball quality |
| xSLG − SLG | 25 | Isolates power-specific luck (HR/extra-base hit variance is high) |
| BABIP luck | 15 | Captures sequencing luck not already in xwOBA |

> **Why no xBA − AVG?**
> xwOBA already incorporates batting-average-like information. Including xBA−AVG would
> double-count the same signal and inflate scores for contact hitters.

### What the score means

| Score | Label | Interpretation |
|-------|-------|----------------|
| ≥ 70 | 🟢 Buy Low | True quality substantially exceeds surface stats. Numbers likely to improve. Good buy target. |
| 30–70 | ⚪ Fair Value | Surface and underlying roughly aligned. Performance is about right. |
| ≤ 30 | 🔴 Sell High | Surface stats exceed true quality. **Does not mean the player is bad** — just that regression is likely. (e.g. a .475 wOBA hitter with .444 xwOBA is still elite; they're just a regression risk.) |
""",
        "zh": """
**範圍：** 0–100 · **分類：** Buy Low（買入）≥ 70 · Fair Value（符合市場）30–70 · Sell High（賣出）≤ 30

### 計算公式

```
分數 = 50
      + z(xwOBA − wOBA)  × 60 × 0.25   # 底層品質優於表面數據的程度
      + z(xSLG  − SLG )  × 25 × 0.25   # 長打力的運氣信號
      + z(BABIP_luck    ) × 15 × 0.25   # 時機/球場/跑速的運氣修正
  截斷於 [0, 100]
```

每個組件都經過 **z 標準化**（距離聯盟平均幾個標準差），確保跨季度的分數尺度一致。

### 各組件權重設計理由

| 組件 | 權重 | 理由 |
|------|------|------|
| xwOBA − wOBA | 60 | 最強的跨年回歸預測指標；xwOBA 捕捉所有擊球品質 |
| xSLG − SLG | 25 | 分離長打力的運氣（全壘打/多壘打的方差很高） |
| BABIP luck | 15 | 補捉 xwOBA 尚未涵蓋的時機運氣 |

> **為什麼不包含 xBA − AVG？**
> xwOBA 已包含類打擊率的資訊。加入 xBA−AVG 會對相同信號重複計算，並高估接觸型打者的分數。

### 分數的意義

| 分數 | 標籤 | 解讀 |
|------|------|------|
| ≥ 70 | 🟢 Buy Low（低估） | 真實品質遠優於表面數據。數字很可能改善。值得關注的低買目標。 |
| 30–70 | ⚪ Fair Value（符合預期） | 表面與底層大致吻合。表現合理。 |
| ≤ 30 | 🔴 Sell High（高估） | 表面數據超越真實品質。**不代表這個球員差** — 只是回歸風險高。（例如 wOBA .475 但 xwOBA .444 的球員仍是頂尖打者，只是表現略超出底層支撐。） |
""",
    },
    # ── Expected Stats ────────────────────────────────────────────────────────
    {
        "id": "metrics_expected",
        "title": {"en": "Expected Stats (Statcast)", "zh": "預期數據（Statcast 底層指標）"},
        "en": """
Expected stats are computed by MLB's Statcast system. For every batted ball, a machine-learning
model predicts the *expected outcome* based on **exit velocity** and **launch angle** alone,
then averages across all balls in play.

| Metric | Full name | Meaning |
|--------|-----------|---------|
| **xBA** | Expected Batting Average | What AVG *should* be based on how hard & at what angle the ball was hit. Strips out defender positioning and park factors. |
| **xSLG** | Expected Slugging | What SLG *should* be based on contact quality. High gap = power is being suppressed (or aided) by luck. |
| **xwOBA** | Expected Weighted On-Base Average | The single most important expected stat. Combines all batted-ball quality into one number. A player with high xwOBA but low wOBA is a prime regression candidate. |
| **xISO** | Expected Isolated Power | xSLG − xBA. True power quality stripped of luck. |

### Why these matter more than surface stats

A player who hits the ball at 105 mph at 25° every time will eventually produce elite numbers —
*even if this week his hard-hit balls are landing at defenders.* Expected stats smooth out that
positioning luck and give a forward-looking quality estimate.

> **Year-over-year correlation of xwOBA ≈ 0.55 vs wOBA ≈ 0.35.**
> xwOBA is substantially more stable — it's a better predictor of *future* performance.
""",
        "zh": """
預期數據由 MLB 的 Statcast 系統計算。對每一顆被擊出的球，機器學習模型根據**出棒速度**和**擊球角度**預測*預期結果*，再取所有打席的平均。

| 指標 | 全名 | 意義 |
|------|------|------|
| **xBA** | 預期打擊率 | 根據擊球品質「應該有」的打擊率，排除守備位置和球場因素的影響。 |
| **xSLG** | 預期長打率 | 根據接觸品質「應該有」的長打率。落差大 = 長打力被運氣壓制（或虛增）。 |
| **xwOBA** | 預期加權上壘率 | 最重要的單一預期指標。將所有擊球品質整合成一個數字。xwOBA 高但 wOBA 低的球員是典型的低買候選人。 |
| **xISO** | 預期純長打率 | xSLG − xBA。排除運氣後的真實長打力。 |

### 為什麼這些指標比表面數據更重要

一個每次都以時速 105 英里、25 度角擊球的打者，最終會產出頂尖數據 —
*即使本週他的強勁打球恰好落在守備員的正面。*預期數據平滑掉這種守備位置運氣，提供前瞻性的品質估計。

> **年際相關性：xwOBA ≈ 0.55，wOBA ≈ 0.35。**
> xwOBA 的穩定性大幅優於 wOBA，是更好的**未來**表現預測指標。
""",
    },
    # ── Surface Stats ─────────────────────────────────────────────────────────
    {
        "id": "metrics_surface",
        "title": {"en": "Surface Stats", "zh": "表面數據"},
        "en": """
These are the traditional statistics visible in any box score. They reflect *actual results* —
which means they include all luck, sequencing, and random variation.

| Metric | Formula | Meaning |
|--------|---------|---------|
| **AVG** | H / AB | Batting average. Simple but ignores walks and extra-base hits. Low predictive value year-over-year. |
| **OBP** | (H + BB + HBP) / PA | On-base percentage. Better than AVG — getting on base in any way counts. |
| **SLG** | Total Bases / AB | Slugging. Weights hits by bases earned, but treats a home run as only 4× a single. |
| **wOBA** | Weighted sum of outcomes / PA | The best single surface offensive stat. Each outcome (BB, 1B, 2B, 3B, HR) is weighted by its true run value. League-average wOBA is typically ~.320. |
| **ISO** | SLG − AVG | Isolated Power. Measures extra-base power by removing singles from slugging. |
| **BABIP** | (H − HR) / (AB − SO − HR + SF) | Batting Average on Balls in Play. The luck meter — league average is ~.295–.300. High BABIP often means a player got lucky; low often means bad luck. Context matters (fast players sustain higher BABIP). |
| **OPS** | OBP + SLG | Convenient but mathematically flawed (adds two different denominators). wOBA is strictly better. |
""",
        "zh": """
這些是出現在任何比分欄的傳統統計數據。它們反映*實際結果* — 也就是包含了所有運氣、時機和隨機變異。

| 指標 | 計算公式 | 意義 |
|------|---------|------|
| **AVG（打擊率）** | 安打 / 打數 | 最基本的打擊數據，但忽略保送和多壘打的價值。跨年預測力低。 |
| **OBP（上壘率）** | （安打 + 保送 + 觸身球）/ 打席 | 比打擊率更好 — 任何方式上壘都算。 |
| **SLG（長打率）** | 壘打數 / 打數 | 按壘打數加權的打擊數據，但把全壘打算成單安的 4 倍並不精確。 |
| **wOBA（加權上壘率）** | 各結果加權總和 / 打席 | 最好的單一進攻表面指標。每種結果（保送、一安、二安、三安、全打）按真實得分價值加權。聯盟平均 wOBA 約 .320。 |
| **ISO（純長打率）** | 長打率 − 打擊率 | 從長打率中去除一壘安打，衡量真正的長打力。 |
| **BABIP（場內球安打率）** | （安打 − 全打）/ （打數 − 三振 − 全打 + 高飛犧牲打）| 運氣計量表 — 聯盟平均約 .295–.300。高 BABIP 通常代表運氣好；低代表運氣差。但脈絡很重要（速度快的球員能維持較高 BABIP）。 |
| **OPS** | 上壘率 + 長打率 | 方便但數學上有缺陷（把兩個不同分母的數字相加）。wOBA 嚴格來說更好。 |
""",
    },
    # ── Quality of Contact ────────────────────────────────────────────────────
    {
        "id": "metrics_quality",
        "title": {"en": "Quality of Contact (Statcast)", "zh": "擊球品質（Statcast）"},
        "en": """
These metrics come from Statcast's radar tracking of every batted ball and describe *how well*
a batter is making contact — independent of whether the ball found a hole or a glove.

| Metric | Meaning | Elite threshold |
|--------|---------|-----------------|
| **EV** (Exit Velocity) | Average speed off the bat in mph. Higher = harder contact. | ≥ 92 mph |
| **LA** (Launch Angle) | Average vertical angle at which the ball leaves the bat. Sweet spot is roughly 10°–30°. | ~15°–20° for power hitters |
| **Hard Hit%** | % of batted balls with EV ≥ 95 mph. Best single indicator of raw contact quality. | ≥ 40% |
| **Barrel%** | % of batted balls in the "barrel" zone: EV ≥ 98 mph AND launch angle 26°–30°. These produce a ≥.500 BA and ≥1.500 SLG. | ≥ 10% |
| **GB%** | Ground ball rate. High GB% suppresses BABIP (grounders have lower BA than fly balls) and power. | Context-dependent |

### Barrel explained

A **barrel** is the ideal combination of exit velocity and launch angle. MLB defines it as
exit velocity ≥ 98 mph *and* launch angle between 26° and 30°. As EV increases above 98, the
optimal angle range widens. Barrels produce batting averages over .500 and slugging over 1.500
— they are almost always hits, and often home runs.

> Barrel% is one of the best leading indicators of future power production.
""",
        "zh": """
這些指標來自 Statcast 的雷達追蹤系統，記錄每顆被擊出球的*擊球品質* — 與球有沒有落在空檔或落在守備員手套無關。

| 指標 | 意義 | 頂尖門檻 |
|------|------|---------|
| **EV（出棒速度）** | 平均出棒英里速，越高代表越強的接觸。 | ≥ 92 mph |
| **LA（擊球角度）** | 球離開球棒時的平均垂直角度。甜蜜區約 10°–30°。 | 長打型約 15°–20° |
| **Hard Hit%（強勁打球率）** | 出棒速度 ≥ 95 mph 的打球比例。衡量原始接觸品質最好的單一指標。 | ≥ 40% |
| **Barrel%（最佳擊球率）** | 落在「桶區」的打球比例：出棒速度 ≥ 98 mph 且角度 26°–30°。這類打球產生 ≥.500 打擊率和 ≥1.500 長打率。 | ≥ 10% |
| **GB%（滾地球率）** | 滾地球比例。高 GB% 會壓制 BABIP（滾地球打擊率低於飛球）和長打力。 | 視脈絡而定 |

### Barrel（最佳擊球）的定義

**Barrel** 是出棒速度與擊球角度的理想組合。MLB 定義為出棒速度 ≥ 98 mph *且* 擊球角度介於 26° 至 30° 之間（速度越高，角度範圍越寬）。桶區打球的打擊率超過 .500、長打率超過 1.500 —— 幾乎必定是安打，且往往是全壘打。

> Barrel% 是預測未來長打產出最好的領先指標之一。
""",
    },
    # ── Plate Discipline ──────────────────────────────────────────────────────
    {
        "id": "metrics_plate",
        "title": {"en": "Plate Discipline", "zh": "打席控制力"},
        "en": """
Plate discipline metrics describe *how a batter behaves* at the plate — their approach,
selectivity, and ability to make contact. These are largely skills (not luck) and tend to be
more stable year-over-year than outcome stats.

| Metric | Formula | Meaning |
|--------|---------|---------|
| **K%** | Strikeouts / PA | Strikeout rate. High K% limits upside; < 20% is generally good. |
| **BB%** | Walks / PA | Walk rate. Measures pitch selection and eye. Elite hitters often post BB% ≥ 12%. |
| **BB/K** | BB% / K% | Walk-to-strikeout ratio. > 1.0 is excellent discipline. |
| **GB%** | Ground balls / Batted balls | Ground ball rate. Influences BABIP and power ceiling. |
| **FB%** | Fly balls / Batted balls | Fly ball rate. Positively correlated with power. |
| **LD%** | Line drives / Batted balls | Line drive rate. Highest BABIP type. |

### The K% and BABIP interaction

A batter with **high K%** will have a naturally lower BABIP — because strikeouts are the
*worst* outcome and remove balls from play entirely. This is one reason you can't judge BABIP
luck without also checking K% and sprint speed.

> **Sprint speed** (ft/s) and **hp_to_1b** (home-to-first time) explain a significant portion
> of BABIP variance — fast players beat out more ground balls.
""",
        "zh": """
打席控制力指標描述打者*在打席中的行為* — 他們的選球、耐心和接觸能力。這些指標主要是技能（非運氣），跨年穩定性通常比結果統計高。

| 指標 | 計算 | 意義 |
|------|------|------|
| **K%（三振率）** | 三振 / 打席 | 三振率。高 K% 限制上限；低於 20% 通常算好。 |
| **BB%（保送率）** | 保送 / 打席 | 保送率。衡量選球能力和打擊眼光。頂尖打者通常 BB% ≥ 12%。 |
| **BB/K** | BB% / K% | 保送 / 三振比。> 1.0 代表優秀的選球紀律。 |
| **GB%（滾地球率）** | 滾地球 / 被擊打球 | 影響 BABIP 和長打上限。 |
| **FB%（飛球率）** | 飛球 / 被擊打球 | 與長打力正相關。 |
| **LD%（平飛球率）** | 平飛球 / 被擊打球 | BABIP 最高的擊球型態。 |

### K% 與 BABIP 的關係

高 **K%** 的打者天然 BABIP 較低 — 因為三振是最差的結果，完全不讓球進入守備範圍。
這也是為什麼評估 BABIP 運氣時必須同時看 K% 和跑速。

> **跑速**（英尺/秒）和 **home-to-first 時間**可以解釋大部分 BABIP 的變異 — 快腳球員能跑過更多滾地球。
""",
    },
    # ── WAR & Salary ─────────────────────────────────────────────────────────
    {
        "id": "metrics_war",
        "title": {"en": "WAR & Salary Efficiency", "zh": "WAR 與薪資效益"},
        "en": """
### WAR — Wins Above Replacement

**WAR** (Wins Above Replacement) is the single number that tries to capture a player's total
contribution — offense, defense, and positional value — in terms of wins added over a
replacement-level (freely available) player.

| WAR level | Interpretation |
|-----------|----------------|
| < 0 | Below replacement level |
| 0–1 | Bench / roster filler |
| 2–3 | Solid regular starter |
| 4–5 | All-Star caliber |
| 6+ | MVP candidate |

> ScoutIQ currently uses **fWAR** (FanGraphs WAR) where available via the Statcast expected
> stats tables. FanGraphs WAR uses UZR for defense; Baseball Reference uses DRS.
> They often disagree — neither is definitively correct.

### $/WAR — Salary Efficiency

**$/WAR** = Annual Salary ÷ WAR

The **2025 free-agent market rate** is approximately **$9.5M per WAR** — meaning a player
producing 3 WAR at fair market value earns ~$28.5M/year.

| $/WAR | Interpretation |
|-------|----------------|
| < $5M/WAR | Exceptional value (often pre-arb players on minimum salary) |
| $5–9.5M/WAR | Good value |
| ~$9.5M/WAR | Market rate |
| > $15M/WAR | Overpaid (or on a long-term deal signed when older) |

**Surplus value** = (WAR × $9.5M) − Salary. Positive = team is getting more than they're paying.
""",
        "zh": """
### WAR — 勝場貢獻值

**WAR**（Wins Above Replacement，超越替補級的勝場數）試圖將球員的全部貢獻 — 進攻、守備、守備位置價值 — 整合成一個數字，以超越替補級（隨時可在市場找到的）球員的勝場數衡量。

| WAR 水準 | 解讀 |
|---------|------|
| < 0 | 低於替補水準 |
| 0–1 | 替補 / 替代球員 |
| 2–3 | 穩健的先發球員 |
| 4–5 | 全明星水準 |
| 6+ | MVP 候選 |

> ScoutIQ 目前使用 **fWAR**（FanGraphs WAR）。FanGraphs WAR 用 UZR 計算守備；Baseball Reference 用 DRS。兩者常有分歧，各有優缺點。

### $/WAR — 薪資效益

**$/WAR** = 年薪 ÷ WAR

**2025 年自由球員市場行情**約為每 WAR **$950 萬美元** — 意思是一個貢獻 3 WAR 的球員市場合理年薪約 $2,850 萬。

| $/WAR | 解讀 |
|-------|------|
| < $500 萬/WAR | 超值（通常是仲裁前、領最低薪的球員） |
| $500–950 萬/WAR | 划算 |
| ~$950 萬/WAR | 市場行情 |
| > $1,500 萬/WAR | 薪資偏高（或長約簽訂時年齡較大） |

**剩餘價值** = (WAR × $950 萬) − 年薪。正數 = 球隊付出小於產出。
""",
    },
    # ── Actionable Flags ─────────────────────────────────────────────────────
    {
        "id": "flags",
        "title": {"en": "Actionable Flags Explained", "zh": "行動建議旗標說明"},
        "en": """
The Team Roster page generates three types of flags. Each requires a **different response**:

### 📊 Hold / Watch
- **Condition:** wOBA below league avg **AND** xwOBA above league avg
- **Meaning:** The player is producing below their actual skill level. Bad luck (BABIP, sequencing) is suppressing surface numbers. The underlying quality is fine.
- **Action:** Do *not* bench or trade. Monitor for regression toward true ability over the next 30–60 PA.

### 🔴 True Concern
- **Condition:** Both wOBA *and* xwOBA below league average
- **Meaning:** Surface stats are bad *and* the underlying quality confirms it. This is a genuine skill/approach issue, not luck.
- **Action:** Consider roster change. Look at Free Agent Finder for replacements at the same position.

### ⚠️ Regression Risk
- **Condition:** wOBA significantly above xwOBA (gap < −0.025) even though xwOBA is above average
- **Meaning:** The player is performing *above* their true skill level. They're still good — but the gap suggests some luck is embedded in their numbers. Expect some pullback.
- **Action:** Don't extend or overpay based on current surface numbers alone. Use xwOBA for contract valuation.
""",
        "zh": """
陣容分析頁面生成三種旗標，各自需要**不同的回應方式**：

### 📊 Hold / Watch（觀察等待）
- **條件：** wOBA 低於聯盟平均 **且** xwOBA 高於聯盟平均
- **意義：** 球員的實際產出低於真實能力。BABIP、時機等壞運氣壓制了表面數字，但底層品質沒問題。
- **行動：** *不要*讓他坐板凳或交易。後續 30–60 個打席觀察是否往真實能力回歸。

### 🔴 True Concern（真正的問題）
- **條件：** wOBA 和 xwOBA 都低於聯盟平均
- **意義：** 表面數字差，底層品質也確認了問題存在。這是真正的技術或打法問題，不是運氣。
- **行動：** 考慮陣容調整。在自由球員搜尋頁面找同守備位置的替代人選。

### ⚠️ Regression Risk（回歸風險）
- **條件：** wOBA 明顯高於 xwOBA（gap < −0.025），但 xwOBA 仍高於平均
- **意義：** 球員目前表現超越真實能力。他們仍然是好球員 — 但落差顯示數字中帶有一些運氣，預期會有所回落。
- **行動：** 不要只看當前表面數字就簽長約或付高薪。合約估值應以 xwOBA 為基準。
""",
    },
    # ── Module guides ─────────────────────────────────────────────────────────
    {
        "id": "module_league",
        "title": {"en": "Module 1 — League Intelligence", "zh": "Module 1 — 全聯盟概覽"},
        "en": """
**Question answered:** Across the entire league, which hitters have the biggest gap between
true quality and surface production?

### The scatter chart
- **X-axis:** xwOBA (true underlying quality)
- **Y-axis:** wOBA (actual surface production)
- **Diagonal reference line:** where xwOBA = wOBA (no luck gap)
- **Color:** Undervalued Score (green = buy low, red = sell high)
- **Point size:** Plate appearances (larger = larger sample, more reliable)

**Above the diagonal** → wOBA > xwOBA → player got lucky → Sell High candidate
**Below the diagonal** → wOBA < xwOBA → player got unlucky → Buy Low candidate

### How to use it
1. Identify players far below the diagonal with large bubbles (big sample, undervalued)
2. Check their BABIP and GB% — high BABIP + high GB% = sustainable, not luck
3. Click a point to open that player's Deep Dive page
""",
        "zh": """
**解答的問題：** 整個聯盟中，哪些打者的真實品質和表面產出落差最大？

### 散點圖說明
- **X 軸：** xwOBA（真實底層品質）
- **Y 軸：** wOBA（實際表面產出）
- **對角線：** xwOBA = wOBA 的地方（沒有運氣落差）
- **顏色：** Undervalued Score（綠色 = 買入，紅色 = 賣出）
- **點大小：** 打席數（越大代表樣本越大，越可靠）

**對角線上方** → wOBA > xwOBA → 球員運氣好 → 賣出候選人
**對角線下方** → wOBA < xwOBA → 球員運氣差 → 買入候選人

### 如何使用
1. 找對角線下方、氣泡大的球員（大樣本、被低估）
2. 檢查他們的 BABIP 和 GB% — 高 BABIP + 高 GB% = 可持續，非純運氣
3. 點擊氣泡跳到該球員的 Deep Dive 頁面
""",
    },
    {
        "id": "module_roster",
        "title": {"en": "Module 2 — Team Roster Analysis", "zh": "Module 2 — 球隊陣容分析"},
        "en": """
**Question answered:** On my team, which positions are genuinely strong, which are genuinely
weak, and which just look bad due to luck?

### Position heatmap
Colored by **xwOBA vs league average** — not Undervalued Score.
Green = above-average production at this position.
Red = below-average production (genuine concern).

> ⚠️ A "Sell High" player (regression risk) can be at a *green* position. High Undervalued Score
> means the player is undervalued; red on the position map means the position is genuinely weak.
> These are independent signals.

### The three flags
See **Actionable Flags Explained** for full detail. In short:
- 📊 Watch: bad luck, underlying is fine
- 🔴 Concern: both surface and underlying are weak
- ⚠️ Regression: surface exceeds underlying (still good, but expect pullback)

### Cross-link to Free Agent Finder
The "Positions below league avg xwOBA" link pre-filters the Free Agent page to that position.
""",
        "zh": """
**解答的問題：** 我的球隊中，哪個守備位置是真正的強項，哪個是弱項，哪個只是因為運氣差而看起來不好？

### 位置熱力圖
以 **xwOBA 相對聯盟平均**上色 — 不是 Undervalued Score。
綠色 = 這個位置的產出高於聯盟平均。
紅色 = 產出低於聯盟平均（真正需要關注）。

> ⚠️ 「Sell High」（回歸風險）的球員所在位置可能是*綠色*的。Undervalued Score 衡量的是球員估值；位置熱力圖衡量的是絕對生產力。這是兩個獨立信號。

### 三種旗標
詳見**行動建議旗標說明**。簡要說明：
- 📊 觀察等待：運氣差，底層沒問題
- 🔴 真正問題：表面和底層都弱
- ⚠️ 回歸風險：表面超越底層（仍然是好球員，但預期回落）

### 跨模組連結
「低於聯盟平均 xwOBA 的位置」連結會預篩選自由球員頁面，直接顯示該守備位置的候選人。
""",
    },
    {
        "id": "module_fa",
        "title": {"en": "Module 4 — Free Agent Finder", "zh": "Module 4 — 自由球員搜尋"},
        "en": """
**Question answered:** In the free-agent market, which available players are undervalued
because of recent bad luck — not a true skill decline?

### Workflow
1. Use Module 2 to identify your team's weakest position (by xwOBA)
2. Click the "Find free agents" link — it pre-fills the position filter
3. Set Valuation filter to "Buy Low" to see undervalued FA candidates
4. Sort by Undervalued Score — top candidates have the biggest positive gap

### Salary data caveat
Salary data comes from Cot's Baseball Contracts (scraped nightly). Free-agent contract values
shown are from the most recent off-season. In-season releases and minor-league signings may
not be reflected immediately.
""",
        "zh": """
**解答的問題：** 自由球員市場中，哪些可簽球員因為最近的壞運氣而被低估 — 而非真正的能力衰退？

### 使用流程
1. 用 Module 2 找出球隊最弱的守備位置（按 xwOBA）
2. 點擊「Find free agents」連結 — 會自動預填守備位置篩選條件
3. 將估值篩選設為「Buy Low」查看被低估的自由球員候選人
4. 按 Undervalued Score 排序 — 最上面的候選人有最大的正向落差

### 薪資資料說明
薪資資料來自 Cot's Baseball Contracts（每晚自動抓取）。顯示的自由球員合約價值來自最近一個休賽季。賽季中的釋出與小聯盟簽約可能無法立即反映。
""",
    },
    {
        "id": "module_player",
        "title": {"en": "Module 5 — Player Deep Dive", "zh": "Module 5 — 單一球員分析"},
        "en": """
**Question answered:** For a specific hitter, is their current performance driven by skill or luck?
Are they a buy at their current market value?

### Metric panel
Side-by-side comparison of:
- **Surface stats** (AVG, SLG, OBP, BABIP, wOBA) — what happened
- **Statcast quality** (xBA, xSLG, xwOBA, Barrel%, Hard Hit%) — what the underlying quality says
- **Plate discipline** (K%, BB%, GB%) — approach and contact tendencies

### Multi-season trend
wOBA vs xwOBA plotted over available seasons. A player whose wOBA consistently
tracks *below* their xwOBA is structurally unlucky (high GB%, slow runner, extreme launch angle).
A sustained xwOBA advantage is more meaningful than a single-season gap.

### Deep-link
You can link directly to any player's page with `?player=Name` in the URL.
""",
        "zh": """
**解答的問題：** 對於某位特定打者，目前的表現是技術還是運氣驅動的？以當前市場價值來說值不值得簽？

### 指標面板
並排比較：
- **表面數據**（打擊率、長打率、上壘率、BABIP、wOBA）— 實際發生的結果
- **Statcast 品質**（xBA、xSLG、xwOBA、Barrel%、Hard Hit%）— 底層品質說了什麼
- **打席控制力**（三振率、保送率、滾地球率）— 打法與接觸傾向

### 多季趨勢圖
在可取得的賽季中繪製 wOBA vs xwOBA 趨勢。一個 wOBA 持續*低於* xwOBA 的球員可能是結構性的運氣差（高滾地球率、跑速慢、極端擊球角度）。持續的 xwOBA 優勢比單賽季落差更有意義。

### 深度連結
可以在 URL 中加上 `?player=Name` 直接跳到任何球員的頁面。
""",
    },
]

# Quick lookup by id
SECTION_MAP: dict[str, dict] = {s["id"]: s for s in SECTIONS}
