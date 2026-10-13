# PAYOFF-40-10-BTC-001 — ECONOMIC HISTORICAL CLOSEOUT — 2026-10-13

**Final verified state:** `HISTORICAL_MODEL_POSITIVE_BASE_AND_STRESS / PARENT_OUTPERFORMS_ON_RAW_RETURN / ZERO_FORWARD_PROMOTION / NO_MICROLIVE_GO`.

Source: [GitHub Actions run 38354594319](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38354594319) — **SUCCESS**, 12/12 synthetic tests PASS; public archive/source, BASE & STRESS causal replay, receipts, all steps SUCCESS. Result artifact [#11792017263](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38354594319/artifacts/11792017263), `diagnostic.json` SHA256 `8f46df78cd363cf4bd8c5e1b789807e0d91787abddc88c3ab3d9d6d2625eb0fe`, full downloaded archive ZIP SHA256 `b0145ebf8d939bd8cc29865ba85d324048df67d4a3acd3f057f2f69fb584dad3`; raw runner `source.json` SHA256 `7f4a7f7e4e3c8c062fb6ef2c04f0974c0304067da090a278c4e18f854b07f7b9`. 2026 outcomes were NOT opened.

## Data coverage: verified and strict

- Official public Binance BTCUSDT USD-M archives, Feb 2020–Dec 2025, **51,864 consecutive 1h price candles** and **51,864 consecutive 1h markPrice candles**.
- **6,483 funding settlement records**; 2,868 public timestamps normalized by ≤1s to nearest UTC hour; maximum actual adjustment **47 milliseconds**, zero colliding rates.
- **221 ZIPs with official SHA256 CHECKSUM**: 213 monthly (71 each market / mark / funding) and **8 verified daily mark-price archives**, resolving exactly **192 missing mark hours**; no interpolation, no post-PnL choice. Source gate PASS.
- Two pre-price-outcome **source-only technical amendments** are recorded: [daily exact-gap coverage](SOURCE_COVERAGE_AMENDMENT_001_2026-10-13.md) and [subsecond timestamp precision](../../audits/PAYOFF_40_10_BTC_SOURCE_TIMESTAMP_AMENDMENT_002_2026-10-13.md). Prior runs [38353963429](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38353963429), [38354295249](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38354295249) were `SOURCE_BLOCKED` before outcomes. They are preserved, not erased.

## Causal matched-exposure comparison, 2020-03-01 .. 2025-12-31

Both strategies used **20% of evolving equity as entry notional**, initial equity 10,489.94 USDT, LONG-only BTC hourly original Quant Trailing v5 signal, one active slot. This is a **normalized exposure comparison**, NOT the previously published Original Parent 95%-equity exposure curve. Parent retains its original 4% price stop + nonlatched 12% peak trailing on confirmed close. PAYOFF replaces ONLY the exit with price-equivalent +40% / −10% on **initial position margin at 2× before funding/slippage**, and a 60-day time exit; margin is 10% of current account equity.

| Metric | PARENT BASE | PAYOFF BASE | PARENT STRESS | PAYOFF STRESS |
|---|---:|---:|---:|---:|
| Closed trades | 89 | 111 | 89 | 111 |
| Winners / losers | 21 / 68 | 30 / 81 | 21 / 68 | 30 / 81 |
| Win rate | 23.60% | 27.03% | 23.60% | 27.03% |
| Equity return, realized cash (open final excluded) | **+32.46%** | +28.33% | **+30.59%** | +26.32% |
| Profit factor | **1.447** | 1.277 | **1.418** | 1.256 |
| Max DD on closed equity | −10.79% | **−10.06%** | −11.05% | **−10.27%** |
| Approx DD with 1h MTM sampling | −14.06% | **−10.92%** | −14.33% | **−11.04%** |
| Total funding cashflow USD | −1,656.74 | −1,222.75 | −1,646.19 | −1,213.40 |
| Mark low crossing illustrative liquidation-threshold hours | 0 | 0 | 0 | 0 |
| Open position at right edge | 1 | 1 | 1 | 1 |

BASE = fee 0.08% per notional leg and fixed adverse 2bps slippage per leg; STRESS = fee 0.10% per leg and fixed adverse 5bps per leg; official Binance funding-rate archive with public mark hourly open proxy. Actual paid taker fees, executable BBO, spread, future funding and fill quality are NOT established.

## Exact PAYOFF outcome resolution

PAYOFF: **29 `TARGET` closes, 81 `STOP` closes, 1 positive `TIME_EXIT`, zero censored closed trades**; one separate open position at 2025 cutoff (not counted as win/loss). No `STOP_GAP` or same-bar ambiguous event occurred on this historical dataset (but QA explicitly covers both conservatively). The 30 wins give 27.03% completed-trade win rate.

At BASE the **realized mean winning return per initial position margin** is **+37.9353%**; mean loser **−10.6458%**; payout ratio **3.5634:1**; effective 2-outcome break-even win frequency **21.9135%**. At STRESS those are +37.7627% / −10.7768%, 3.5041:1 and **22.2021%** break-even. These exceed 20% because real funding/slippage lower the +40% nominal and deepen −10% nominal. **ZERO of the 111 exits realized ≥+40% on initial margin after BASE funding + assumed slippage**, because +40% had been an ideal before-funding/zero-slip *price barrier*, not an executable all-cost pay-off guarantee; all 81 STOP losses exceeded nominal −10% (14 exceeded −11% in BASE). This does not mean there were no substantial winners.

The Parent average historical win/loss as a fraction of its *notional margin* is +21.5291% / −4.3253%, a different margin convention, not directly comparable as raw percentages to 2× PAYOFF. Parent has an unrestricted right tail; PAYOFF's fixed target clips strong bull trends. The Parent captured more absolute return in **2021** (+20.62% vs PAYOFF +11.60%) and **2024** (+19.70% vs +7.97%). The PAYOFF was better in 2020, 2022, 2023 and 2025, notably **2023** +14.26% vs Parent +2.58%. BOTH were negative in 2022 and 2025.

| Year | Parent BASE cash equity change | PAYOFF BASE cash equity change |
|---|---:|---:|
| 2020 (from Mar) | +5.16% | +6.04% |
| 2021 | +20.62% | +11.60% |
| 2022 | −9.10% | −6.63% |
| 2023 | +2.58% | +14.26% |
| 2024 | +19.70% | +7.97% |
| 2025 | −6.45% | −5.86% |

**Tail concentration (descriptive, NOT a valid re-optimized portfolio replay):** sum of the three largest closed-trade profit amounts accounts for **34.53% of Parent gross positive closed PnL**, compared with **11.51% of PAYOFF gross positive PnL**. This supports a less top-heavy historical PAYOFF, NOT independent robustness proof. Removing past top winners ex post is not a forward performance result.

**Righthand censoring:** both systems had one open trade at the 2025-12-31 23:00 UTC boundary (entry 2025-12-22 20:00 UTC); excluded from closed-trade win/loss statistics and with separate hypothetical mark-exit PnL −22.15 USD Parent / −21.46 USD PAYOFF in BASE. No price paths from 2026 were fetched to resolve it.

## Economic interpretation and adversarial limitations

- **Working mechanism in historical model**: many small losses can be offset by fewer large wins; PAYOFF 27.03% wins, mean payout 3.56× losses, positive in both BASE and STRESS scenarios. This rejects the claim that the idea is mathematically impossible; it does *not* establish a repeatable real market edge.
- **Relative comparator**: original exit mechanism generates higher historical gross-on-equity returns and PF at identical notional exposure, while PAYOFF has lower approximate MTM DD, less concentration in the three biggest winners, and a more uniform year profile (still losing in 2022/2025). None is universally better based on this already observed history.
- **Model constraints**: actual bid/ask and fill probability absent; modeled fixed slip not observed execution; 1h OHLC cannot guarantee first-touch intrabar order or stop fills; exact private venue rate / order type / tick & quantity minima and funding settlement mark not independently verified; liquidation threshold uses an illustrative maintenance assumption rather than historical tier models; returns before later cutoff open position is resolved, and 1h MTM misses intrahour risk. Binance public source is a **proxy** for user's MEXC execution, no apples-to-apples venue GO.
- **Statistical limits**: hypothesis, target, stop and time-expiry were designed after reading the original history; 2020–2025 are NOT independent OOS. Historical source completeness and robust synthetic code QA do NOT award forward edge authority. Do not fit a third variant to 2021/2024 winning segments retrospectively.

## Finite decision / next step

**COMPLETE for historical model**: exact source receipts, frozen causal 1h two-exit comparison, exhaustive outcomes including red years, full available public funding, risk and costs modeled, and deterministic unit tests. **NO GO for actual trading or automated orders**, and no independent liquid diamond established.

**Recommended next research**: run the two *unchanged* exits in a pre-registered **paired read-only forward shadow**, using genuinely future BTC 1h bars, venue-specific achievable bid/ask and fees plus funding, with per-trade ledger, execution eligibility, margin/lot rules and no use of the original sealed 2026 holdout. Before activation lock an observation horizon/power requirement; never use these historical results to re-pick time exits, stop, targets or best years. The original 95% equity Parent is NOT a sensible account risk target at small capital; any later live authorization would need a new independent approval.

No main merge, no orders, no private exchange API, no wallet or balance access, no user capital spent, no science tuning after observed historical outcomes.
