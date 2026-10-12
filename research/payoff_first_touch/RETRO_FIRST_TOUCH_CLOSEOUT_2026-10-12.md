# PAYOFF-FIRST-TOUCH-RETRO-001 — ECONOMIC CLOSEOUT — 2026-10-12

**Final science result:** `TARGET_40_10_NOT_ESTABLISHED` / `NO_MICROLIVE_PROMOTION`.  
**Operational source result:** `RETRO_FIRST_TOUCH_DESCRIPTIVE_READY`.  
**Original BTC-CONVEX family verdict:** unchanged: historical causal diagnostics survive, **independent 4:1 all-cost edge unproven**, other original freezes and closeouts intact. These labels are not `NO_EDGE` for all possible future designs.

## Immutable authority, reproduction and receipts

- Base evidence: [PR #166](https://github.com/joseluisvieira28-oss/Laboratorio/pull/166) commit `98454c4516b69fae54526ed37600895f0b6063a9`, source ledger decoded SHA256 `ca6903faf7d4f42a40d0b76d4e7d106edec36007075d2da4600c4800b08583fa`.
- Branch: `research/payoff-first-touch-identifiability-2026-10-12`, [PR #193](https://github.com/joseluisvieira28-oss/Laboratorio/pull/193), based on PR #166, not main.
- Original pre-archive protocol `RETRO_FIRST_TOUCH_FROZEN_PROTOCOL_V0.1.md` committed `86fc7e063d8aaa64ef19d403ace45034ac6a15ba` before first price-archive attempt.
- First run `38268635390`: stopped at 2019-10 archive 404; no candle outcomes. Second run `38268804917`: source-only HEAD 2019-10 404, 2020/2021/2024/2025 monthly archive samples 200; initial parser still failed closed.
- Availability-only `SOURCE_COVERAGE_AMENDMENT_001_2026-10-12.md` committed `893b773b4426a3ff1fe8dc750300e6cd5391629c` **before any price data were opened**, allowing exclusion solely of entry timestamps before 2020-01-01, and correction to the published ledger's `entry` field. No performance-based subgroup selection.
- [Successful authoritative descriptive run 38269021214](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38269021214), code commit `a24a9591c435eff92d2917fbe779592c4b50e56f`, **7 synthetic tests passed**, artifact **11755773347**, uploaded ZIP SHA256 `44a2d9a48f570c09fc72a426da8661104f15eef7fd74581bec7e1af76479cda4`. Artifact includes full per-trade event ledger and per-month archive SHA256 manifest.
- Run receipt `retro_verdict.json` SHA256 `1cde30028bd5ae450d266f4c1f8542e0e8049ddba3ec7626a479852d2c777b6a`; `retro_events.json` SHA256 `20ee665123663dc8575f66cd50addee52a6fb46c7edbdfa2ed031191214ac804`.
- **70 verified monthly ZIP/CHECKSUM pairs** from **2020-03 to 2025-12** (BTCUSDT USD-M perpetual 1h), archived exchange candles, not an authenticated MEXC historical fill source.
- Seed 101 rows: **89 included**, **6 initial-entry 2019 source-blocked**, **5 2026 closed excluded**, **1 still-open excluded**. No 2026 price archive fetched and no unseen OOS/forward outcome opened.

## Results: the actual historical first-touch evidence

Synthetic initial margin `M`, original ledger entry price, leverage `N/M=2`, taker fees **0.08% per side** hypothetically, target **+40%/M** and stop **−10%/M** if perfectly filled. Corresponding price boundaries:

- Target **+20.17614091273%** from the original entry price.
- Stop **−4.84387510008%** from original entry price.

First-touch measured **only while the original BTC-CONVEX position remained open**, never after the original exit:

| UTC 1h first-touch class | Inclusive entry hour | From NEXT full hour |
|---|---:|---:|
| TARGET_FIRST | **18** | **18** |
| STOP_FIRST | **0** | **0** |
| SAME_BAR_AMBIGUOUS | 0 | 0 |
| GAP_FIRST | 0 | 0 |
| MISSING_PATH | 0 | 0 |
| NEITHER_WITHIN_ORIGINAL_HOLD = CENSORED | **71** | **71** |
| Total | **89** | **89** |

The 18 target touch episodes span original entry years: 2020=3, 2021=5, 2022=3, 2023=3, 2024=3, 2025=1. Median entry-to-price-target **424 hours = 17.67 days** (range 58..1125 hours), meaning funding/time-at-risk are material. Event counts stable when first entry-hour bar is completely omitted. This proves that *price targets sometimes appeared during the original position*, not that stop, funding, fill or prospective economics were satisfied.

**Why zero stops means nothing favorable:** BTC-CONVEX's original frozen stop was **4% price loss** (and it could exit for other reasons). The newly proposed `−10% initial-margin` barrier at 2x is **−4.8439% price**, *wider* than the original stop. By truncating each sampled path at the old exit, trades frequently stopped under the original rule **before the new stop could be observed**. The 71 are **right-censored**. Counting them as losses or as surviving winners would fabricate a model outcome. Thus **18/89=20.22% is NOT a win rate for a +40/−10 trading strategy**; do not report a legitimate PF, PnL, drawdown or capital final for it.

**Price-timing caveat:** 7/89 ledger entry prices differ by over 1% from the public exchange 1h candle *open*, up to +14.65%; entry timestamps may represent intrahour fill times and the public source is a proxy, not exact fills. One target-touch entry (#70) has >1% open/entry mismatch. Matching first-touch categories in the next-completed-hour sensitivity reduces but does not eliminate fill and source-basis uncertainty. There is no verified stop order type, entry fill priority, mark-price liquidation trace, personal fee/funding, min-size or orderbook slippage.

## Economics: no 4:1 strategy promotion

The necessary break-even win probability for exactly +40% / −10% **realized net** is `0.10/(0.40+0.10)=20%`. It requires trade outcomes *fully resolved under the new stop/target* and costs actually included. None were established because 71 are censored, the 18 are **bar touches, not executable closed winners**, and entries come from the already known original strategy with endogenous future entries.

For purely illustrative arithmetic (explicitly **NOT observed PnL**), pretending all 18 touch events fill at +40% and all 71 censored events subsequently fill at −10% yields `18×(+200 USDT) + 71×(−50 USDT) = +50 USDT` over 89 notional occurrences if **500 USDT margin** were available for every position. One misclassified target would change this illustrative total by −250 USDT. This assumption is **not a lower or upper bound** on attainable strategy equity: all-in 500 margin cannot be redeployed at fixed 500 after a loss without extra funds, old exits censor new outcomes, and funding/slippage/margin-liquidation may change fills.

Ten consecutive genuinely realized −10% losses using **100% of evolving equity as margin** would draw down `1−0.9^10=65.13%` of equity. This is risk arithmetic, not observed 2x forward DD. Nothing in the study warrants 5×/10×/20× live leverage, orders, bot activation or a 4:1 edge claim.

## Final adjudication and what would change it

`SOURCE_READY_HISTORICAL_PROXY` / `FIRST_TOUCH_CENSORED` / **`ECONOMIC_EDGE_NOT_DEMONSTRATED`**. This is a final and reproducible scientific **NO-GO for promotion based on present evidence**, not NO_EDGE for the BTC-CONVEX family's distinct original frozen experiments.

To open a *new* GO consideration requires a distinct pre-outcome ID, immutable entry/exit signal specifications, **uncensored causal trade lives**, exact fees/funding/slippage and mark-liquidation/margin constraints, independent untouched OOS/forward results, and sufficient robust trade/sample observations. Reusing these BTC 2020-2025 opened episodes or picking rules from their winners cannot supply that independence.

No exchange private API, balance, login, order, money, production runtime, Render mutation, main merge, alteration to original freeze, 2026 holdout access, or live trading. The GitHub Action does not schedule recurrence (only push/explicit dispatch of this branch) and has read-only repo permission.
