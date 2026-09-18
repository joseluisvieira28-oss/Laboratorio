# LL-0017 — TRADER-RATIO POSITIONING — PRE-SOURCE AUTHORITY V0.1

Date: 2026-09-18
Status: **FROZEN PRE-SOURCE / OUTCOME-BLIND / RESEARCH-ONLY**
Branch: `ll-0017-positioning-ratio-v0.1`

## 1. Lineage and anti-duplication

Archaeology ID: ARQ-006 / legacy LL-0017.

Recovered lineage:
- LL-0016-C subsequently closed NO EDGE under its own frozen crowd-unwind hypothesis.
- LL-0017 remained IDEA ONLY as a distinct follow-up using trader-ratio / positioning information.
- Drive/GitHub searches on 2026-09-18 found no dedicated LL-0017 branch, frozen protocol, execution receipt or closeout.
- Generic taker-flow, funding, OI and flow-imbalance families already have substantial negative/saturated evidence and must not be silently retested here.

Materially distinct source question:
Can official Binance historical positioning archives reproducibly provide **top-trader account ratio, top-trader position ratio and global account ratio** as separate state variables across 2021-2024?

This authority does not claim that any ratio predicts direction.

## 2. First source MVE

Lab ID: `LL-0017-POSITIONING-RATIO-001`
Source MVE: `LL17-BTCUSDT-METRICS-SCHEMA-001`

Venue/instrument:
- Binance USDⓈ-M Futures
- BTCUSDT only

Canonical source candidate:
`https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/`

Frozen deterministic probe dates:
- 2021-01-15
- 2022-06-15
- 2023-06-15
- 2024-12-15

Expected archive naming:
`BTCUSDT-metrics-YYYY-MM-DD.zip`
with matching `.CHECKSUM` sidecar.

No 2025 or 2026 object may be requested.

## 3. Allowed inspection

Source Gate may inspect only:
- HTTP accessibility;
- archive and sidecar bytes;
- provider checksum;
- ZIP member identity;
- CSV header/schema;
- row count;
- timestamp column only;
- unique timestamp count;
- timestamp cadence/gap diagnostics.

Required positioning schema candidates:
- a top-trader account long/short ratio field;
- a top-trader position long/short ratio field;
- a global account long/short ratio field.

Column names are not guessed as authority. The probe records the provider header and classifies semantics based on exact header names.

## 4. Explicitly forbidden at this stage

Do NOT parse, persist, summarize or inspect:
- ratio numeric values;
- open-interest numeric values;
- taker-volume ratio values;
- OHLC/mark/index prices;
- funding values;
- returns;
- future price direction;
- PnL;
- PF;
- win rate;
- drawdown;
- threshold performance;
- asset comparison;
- 2025/2026 data.

No trading rule, sign, threshold, lookback, event definition, entry, exit or cost model is authorized.

## 5. Frozen source adequacy gate

`SOURCE_SCHEMA_PASS` requires ALL:

1. all 4 frozen ZIP objects return successfully;
2. all 4 CHECKSUM sidecars return successfully;
3. provider SHA-256 verification passes on all 4 ZIPs;
4. each ZIP contains exactly one CSV member;
5. all 4 CSVs expose an identical header;
6. the header contains distinct fields semantically corresponding to:
   - top-trader account long/short ratio;
   - top-trader position long/short ratio;
   - global account long/short ratio;
7. each probe day has at least 200 unique valid timestamps;
8. median timestamp interval <= 10 minutes on every probe day;
9. no duplicate timestamps within a probe file;
10. no timestamp falls outside its requested UTC calendar day;
11. no 2025/2026 object is requested or opened.

Permitted terminal states:
- `SOURCE_SCHEMA_PASS`
- `SOURCE_ACCESS_BLOCKED`
- `SOURCE_CHECKSUM_FAILURE`
- `SOURCE_SCHEMA_INADEQUATE`
- `SOURCE_TEMPORAL_COVERAGE_INADEQUATE`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `PROVENANCE_FAILURE`

No source-stage state is NO_EDGE.

## 6. Post-pass authority

A Source Schema PASS authorizes only a separately frozen historical coverage census for 2021-01-01 through 2024-12-31.

It does NOT authorize:
- a predictor;
- a directional sign;
- market outcomes;
- Discovery;
- 2025/2026;
- paper/live trading.

Any later mechanism must prove material distinction from prior generic taker-flow/funding/OI failures and must be frozen before ratio values or future outcomes are opened.

## 7. Safety

Research only.
Fail closed.
No exchange authentication.
No account access.
No orders.
No wallets.
No alerts/webhooks.
No live capital.
No merge to main.
No post-outcome tuning.
