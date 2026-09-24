# ETF-CME-INSTFLOW-001 — DIAMOND TEST V1 AUTHORITY RECONCILIATION — 2026-09-24

Status: `CORRECTED_BEFORE_ANY_ETF_DIAMOND_OUTCOME_ACCESS`

Parent: `ETF-CME-INSTFLOW-001`

## Authority conflict discovered and resolved

The 2026-09-24 draft originally proposed a new first-50 resolved-observation Diamond block.

That proposal is **void and must not be used** because a stricter, earlier prospectively frozen authority already exists:

- `ETF-CME-INSTFLOW-001 — FORWARD SHADOW Q4 2026 — FINAL EVALUATION CONTRACT V0.1A`
- frozen: **2026-09-15**
- study: `ETF-CME-INSTFLOW-001-FORWARD-SHADOW-Q4-2026-V0.1A`

Earlier authority takes precedence.

No ETF-CME BTC forward outcome has been opened by the 2026-09-24 Diamond work.

## Governing Q4 authority — inherited exactly

The Diamond Test may observe **source-only** CFTC state and operational timing/friction diagnostics during Q4, but must not fetch, inspect, log, summarize, infer or use BTC forward-outcome prices before the frozen one-shot evaluation.

Frozen window:
- first allowed prospective CFTC as-of: 2026-09-15;
- last allowed prospective CFTC as-of: 2026-12-15;
- latest allowed exit: 2026-12-31;
- target maximum weeks: 14;
- minimum evaluable weeks: 12.

Frozen one-shot evaluation:
- may execute only **after 2027-01-01T00:00:00Z**;
- exactly one final economic evaluation;
- no interim PnL;
- no sequential testing;
- no early promotion/demotion;
- no partial-sample verdict;
- all eligible prospective observations included.

## Frozen scientific rule

Unchanged:
- CFTC dataset `6dca-aqww`;
- contract code `133741`;
- signal = delta(non-commercial long - non-commercial short) / current open interest;
- positive signal = LONG BTC;
- negative signal = SHORT BTC;
- zero = no position/no cost;
- entry = first Binance BTCUSDT Spot daily 00:00 UTC open at/after as-of + 8 calendar days;
- exit = entry + 7 calendar days;
- BASE round-trip cost = 10 bps;
- STRESS round-trip cost = 20 bps;
- no threshold / z-score / winsorization / regime filter / alternate COT category.

Frozen outcome source:
- **Binance Vision BTCUSDT Spot 1d official archive bytes only**;
- source archive hashes must be preserved;
- REST ticker, TradingView, exchange UI, alternate venue, mark/index, interpolation or reconstructed candle are forbidden substitutes.

## Frozen final success criteria

`FORWARD_SHADOW_PASS` requires all simultaneously:

- evaluable observations >= 12;
- BASE NET10 mean > 0;
- BASE PF >= 1.0;
- STRESS20 NET mean >= 0;
- STRESS20 PF >= 1.0;
- OLS beta sign positive;
- leave-one-trade-out minimum BASE NET mean > 0;
- max single-trade share of positive gross PnL <= 40%;
- absolute additive max drawdown < 0.50;
- clean provenance / no leakage / no technical or source-path failure.

At final evaluation:
- pass => `DIAMOND_TEST_ETF_EVIDENCE_LAYER_PASS__TIER_EFFECT_NONE_AUTOMATIC`;
- scientific/economic fail with >=12 => `DIAMOND_TEST_FAIL__EXACT_ETF_CME_NO_RESCUE`;
- legitimate evaluable sample <12 => `DIAMOND_TEST_INSUFFICIENT_SAMPLE`;
- technical/provenance failure => `DIAMOND_TEST_BLOCKED`.

A Q4 forward pass is strong independent evidence but is **not automatically** `DIAMOND_TEST_SURVIVES`; Diamond V1 still requires a separate post-evaluation reconciliation of operational realism and the complete evidence chain, without changing the frozen Q4 result.

## What is allowed before 2027-01-01

Allowed:
- CFTC source-only checkpointing;
- exact timing receipts;
- missed-observation receipts;
- public execution-friction diagnostics;
- source health;
- persistence/idempotency checks;
- evidence-chain integrity;
- verification that no BTC outcomes were opened.

Forbidden:
- BTC forward price fetch for Q4 observations;
- forward return;
- PnL;
- PF;
- drawdown;
- interim winner/loser view;
- partial-sample performance;
- threshold/horizon/cost/sign/category/regime rescue.

## Preserved runtime fact

The information-safe observation expected on 2026-09-23 was missed under the exact runtime and is immutable as `MISSED_EXPECTED_OBSERVATION_NO_CHASE`.

It must not be reconstructed as a prospective observed signal.

The older Q4 V0.1A source-only study remains the scientific authority for inclusion and final one-shot evaluation semantics.

## Governance

- research-only;
- no live trading from this document;
- no orders;
- no exchange mutation;
- no wallets;
- no capital;
- no main merge;
- no interim outcome peeking;
- no post-outcome rescue.
