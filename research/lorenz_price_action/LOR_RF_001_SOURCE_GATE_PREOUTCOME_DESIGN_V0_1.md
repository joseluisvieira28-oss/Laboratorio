# LOR-RF-001 — SOURCE GATE + PRE-OUTCOME SIGNAL DESIGN V0.1
Date: 2026-10-09
Status: SIGNAL_DESIGN_FROZEN / ECONOMIC_TEST_BLOCKED_PENDING_SOURCE_AND_EXECUTION_GATE
Branch: research/lorenz-price-action-source-gate-2026-10-09
Authority: RESEARCH_ONLY, NO_TRADING
Relationship to author: lab's explicitly mechanical adaptation of publicly attributed Realização Frustrada, NOT a claim of literal replication of the paid lecture.

## Question
Does the three-bar countertrend correction / failed correction signal add positive causal continuation expectancy over a simple moving-average trend baseline, and is any advantage materially larger than actual round-trip execution costs?

## Primary economic mechanism hypothesis
Temporary countertrend participation stalls inside an existing EMA/SMA trend, then price breaks the three-bar opposite extreme, prompting continuation. This is a price-action hypothesis; actual stop/flow involvement is not observed from OHLCV alone.

## What is fixed from source
Sequence, trend-conditioned direction, EMA9/SMA21 alignment, SMA200 obstacle veto, entry above highest of three / below lowest, opposite extreme stop, and target 1R.
Publicly accessible third-party transcription:
https://pt.scribd.com/document/874836582/Estrategias
Official source confirms lesson title but not all literal rules:
https://lorenzfabricio.com.br/epa-tp-a/

## What the lab MUST define before price/outcome access
All items here are DECISIONS TO FREEZE, NOT inferred author claims:
- asset and tradable venue; timeframe and clock;
- EMA9/SMA21 favorable definition and SMA200 intersection rule;
- treatment of flat candles and market gaps;
- point-in-time tick size and stop-trigger fill model;
- entry validity/cancellation window, same-minute target vs stop tie-break;
- timeout, settlement mark and costs;
- causal indicator warmup, overlap serialization, per-trade/date gates;
- matched/simple trend-only counterfactual and inferential method.

All choices must be committed in a versioned immutable economic freeze. No outcomes may be read until then. This document intentionally does NOT lock economically arbitrary choices or assert that a complete trading strategy already exists.

## Prospective boundary recommendation
Recommended for a future formal freeze: first full UTC 1h bar after 2026-10-10T00:00:00Z, provided the complete freeze and source-integrity gates are committed BEFORE that boundary. If not committed and verified beforehand, this suggested boundary is INVALID and must move strictly forward BEFORE outcome opening. Under no circumstances retroactively date the freeze.

## Source path / feasibility
- Official Binance Spot `GET /api/v3/klines` supports BTCUSDT and 1h/1m intervals, public, no authenticated account request needed; documentation:
  https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md
- Binance public-data archive may be used with its official checksum; documentation:
  https://github.com/binance/binance-public-data
- Spot 1h candles may identify a pattern; spot 1m (or public trades) needed to adjudicate stop/target order conservatively.
- A Binance spot price signal is NOT proof of executable MEXC perpetual entry, spread, position size or fill priority.
- Documentation existence is `SOURCE_DOCS_PASS`; exact availability, continuity, timestamp/unit and checksum probe for the intended window are `SOURCE_GATE_NOT_RUN`.

## Anti-duplication gates
1. Compare against Donchian/EMA-structure/pattern family freezes; event-level equivalence requires causal feature mapping only, not opening outcomes.
2. Keep `ABSORPTION-FAILED-AUCTION-001` and its historically separate sibling untouched; RF does NOT use aggTrade extreme imbalance or POC.
3. Keep closed scalp/sweep/geometry/liquidation tests terminal; do not relabel their outcomes as RF.
4. Do not claim a fresh edge merely from a source-authored 3-candle definition.

## Counterfactual requirement
Before any signal outcomes:
- choose a trend-only baseline with same venue, side, timeframe, entry/exit cost authority and exposure budget;
- compare RF incremental economic uplift vs that baseline, not vs zero gross return alone;
- preserve overlap/correlation by clustered UTC-week or date resampling;
- report size, date concentration, gross and both base/stress cost results, with source receipts.

## Stop conditions
* A complete mechanical rule set cannot be validated from accessible material and cannot be fixed objectively without discretionary after-the-fact chart fitting -> `DEFINITION_BLOCKED`.
* Source integrity / 1m execution resolution unavailable -> `SOURCE_BLOCKED`.
* Same exact MVE already studied or merely rebranded -> `DUPLICATE_CLOSED`.
* Fees/spread/funding route impossible or state fails cost bounds -> `EXECUTION_BLOCKED`.
* Otherwise and ONLY after economic freeze / data source check: `READY_FOR_DEVELOPMENT_OR_PROSPECTIVE_COLLECTION`, NOT `EDGE`.

## Before first economic run — required receipts
[ ] Versioned pre-outcome FREEZE.json with all mechanics, costs and terminal gates
[ ] Rule-code unit tests on SYNTHETIC candles only (bull/bear/flat/gap/intra-minute ambiguity)
[ ] Source receipt with timestamp units, continuity, duplicate/gap checks, checksum/authority
[ ] Non-duplication memo for same MVE vs existing Donchian/EMA/candle studies
[ ] Independent reviewer confirms datasets and times not peeked
[ ] Exact executable venue cost & notional preflight (READ-ONLY, no accounts)
[ ] Separate PR or commit documenting eligibility before any outcome-run dispatch

## CURRENT VERDICT
`RESEARCH_CANDIDATE / SIGNAL_DESIGN_ONLY`.
Zero economic tests, zero validated earnings, zero trading authority.
