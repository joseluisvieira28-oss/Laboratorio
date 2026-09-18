# CED-1D-V1 — 2025 TRANSFERRED REPLICATION / CONFIRMATION FREEZE — V0.1 — 2026-09-18

**Status:** FROZEN BEFORE 2025 MARKET OUTCOMES  
**Child:** MVE-CED1D-MOMENTUM-01  
**Mode:** TRANSFERRED_REPLICATION / ONE-SHOT 2025 CONFIRMATION  
**Branch:** ced-1d-v3-byte-recovery-2026-09-17

## 1. Scientific lineage

Historical parent: CED-1D-V1 Discovery 2021-2024.

Controlling V3 re-adjudication authority:
- implementation freeze commit: 102ee494ea2b46c0d29b48f5cfcae6e6cc28f1ca
- closeout commit: 2927172d237d7aa188e7f191eda005d18c694545
- authority precedence correction: governance/CED_1D_V3_AUTHORITY_PRECEDENCE_CORRECTION_2026-09-18.md
- canonical Phase 1 V0.2 contract SHA256: 4a6ee27a8b6fd66dcc89e3d2b4211d3f5d5c8020c151f8908f081108803acfb4
- canonical repaired Phase 2 dataset fingerprint: 0b3de834cf5a126cb348596a466ce191e956640f4e7c3d8d3fbc8f38e1c5ad93
- historical derived 1D fingerprint: b92741d682a704a237cc1ab1a4d1fb0beb13798b11993ddde9ef54bcd4f3ab20

Historical verdicts remain immutable. This child is a transferred replication, not a second Discovery.

## 2. Exact frozen population

All three controlling survivors must be evaluated in the same one-shot 2025 run. None may be dropped after outcomes.

1. CED1D-0031 — AVAXUSDT — A_MOMENTUM — lookback 20 valid completed daily bars — CONTINUATION — horizon 1 calendar day.
2. CED1D-0241 — SOLUSDT — A_MOMENTUM — lookback 20 valid completed daily bars — CONTINUATION — horizon 1 calendar day.
3. CED1D-0251 — SOLUSDT — A_MOMENTUM — lookback 60 valid completed daily bars — CONTINUATION — horizon 1 calendar day.

No additional symbol, lookback, horizon, direction, filter, regime, threshold, or neighbour may enter the confirmation population.

## 3. Exact inherited signal/execution semantics

The implementation must reuse CED-1D-V1 RUNNER FREEZE V0.3 semantics without interpretation drift:

- daily UTC candles are derived from canonical Binance USD-M Futures 1m data;
- a valid UTC day requires exactly 1,440 unique 1m bars and zero duplicate minutes;
- Momentum lookback uses the original valid-observation semantics:
  log(close[t] / close[t-lookback]);
- reference direction = sign of the frozen lookback return;
- CONTINUATION uses that sign unchanged;
- zero lookback return produces no signal;
- entry day = signal day + 1 calendar day;
- entry reference = exact 1m OPEN at 00:01 UTC on entry day;
- exit day = signal day + 2 calendar days for the frozen 1D horizon;
- exit reference = exact 1m OPEN at 00:01 UTC on exit day;
- every calendar day in the entry-to-exit path must be locally valid;
- no nearest-neighbour timestamp substitution;
- one active event per symbol/config; later signal is OVERLAP_BLOCKED only when entry < prior active exit;
- no 2026 price byte may be opened to complete a 2025 event.

Signals requiring entry/exit/path outside 2025 are DATA_UNAVAILABLE and remain visible in the ledger.

## 4. Temporal firewall

Confirmation price period: 2025-01-01 through 2025-12-31 UTC only.

Warm-up price data:
- AVAXUSDT and SOLUSDT 2024-11 and 2024-12 may be read solely to establish pre-2025 lookback state.
- warm-up outcomes are not Confirmation observations and do not enter 2025 metrics.

2026+: HARD BLOCK.

Complete-week inference rule:
- UTC week = Monday 00:00 UTC to next Monday 00:00 UTC;
- anchor = signal completion day;
- only complete signal weeks wholly inside 2025 enter inference;
- first inference week starts 2025-01-06;
- inference week end is 2025-12-29 exclusive;
- split-edge rows remain in the append-only ledger but are excluded from sample, costs, stability, concentration, bootstrap and confirmatory routing.

## 5. Source identity / source-only gate

Price source: official Binance public archive, USD-M Futures monthly 1m klines.

Frozen route pattern:
https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM}.zip

The exact 28 warm-up/Confirmation ZIP SHA256 values must be copied from the already-recovered canonical target_registry_R1.json into a separate source manifest before any 2025 economic statistic is computed.

Every ZIP must pass:
- exact frozen SHA256;
- ZIP CRC;
- expected CSV member name;
- 12-column Binance kline schema;
- exact UTC month timestamp bounds;
- ascending timestamps;
- zero duplicates;
- positive finite OHLC;
- structural volume/trade checks;
- 1,440 unique bars for every complete UTC day;
- zero 2026 timestamps.

Any source mismatch => SOURCE_GATE_FAIL / no outcomes.

## 6. Frozen costs and funding

Canonical V0.2 Confirmation nonfunding floor:
- BASE = 14 bps round-trip;
- STRESS = 20 bps round-trip.

No lower fee/cost scenario may control Confirmation.

These are floor sensitivities, not a claim of historical executable fills. The exact 00:01 bar opens remain REFERENCE_PRICE_ONLY until independent quote/fill evidence exists.

Funding provenance:
- official Binance USD-M public market-data endpoint:
  GET https://fapi.binance.com/fapi/v1/fundingRate
- symbols: AVAXUSDT, SOLUSDT;
- requested interval: only funding records needed for frozen 2025 positions;
- fundingTime and fundingRate from the official response are preserved raw and hashed.

Funding PnL contribution for a position direction d in {+1 long, -1 short}:
- funding_bps = -d * fundingRate * 10,000
for each actual funding record with fundingTime inside the open position interval [entry_timestamp, exit_timestamp).

No fixed 8h schedule is assumed when an actual official record is available.

If complete funding provenance cannot be verified, funded economics = NOT_TESTABLE. Nonfunding BASE14/STRESS20 results may still be reported but cannot be represented as funded Confirmation.

## 7. V0.2 Confirmation gates

Per fixed cell, using only inference-week-eligible 2025 events:

Sample minimums:
- events >= 300;
- active days >= 120;
- active complete UTC week clusters >= 39;
- active months >= 9.

Primary economic/statistical metric:
- mean BASE14 net bps per event.

Frozen null/alternative:
- H0: mean BASE14 net <= +2 bps;
- H1: mean BASE14 net > +2 bps.

Bootstrap:
- complete UTC weeks jointly;
- preserve within-week event rows;
- 9,999 resamples;
- seed 20260908;
- centered-null bootstrap at +2 bps;
- plus-one p correction;
- uncentered percentile 95% CI;
- >1% zero-count invalid resamples blocks inference.

Multiplicity:
- Holm FWER 0.05 across the three fixed primary cells.
- all three remain in the family even if one fails.

Per-cell economic/statistical replication gate requires all:
- sample gates PASS;
- BASE14 mean > +2 bps;
- 95% bootstrap lower bound > 0;
- Holm-adjusted p <= 0.05;
- STRESS20 mean >= 0;
- temporal stability gates;
- concentration gates;
- complete lineage and ledger.

Execution-quality gate:
- historical 1m bar-open reference is not sufficient to substantiate executable fills;
- until independent quote/fill evidence exists, execution gate = BLOCKED_REFERENCE_PRICE_ONLY.

Therefore a cell may receive:
- OOS_ECONOMIC_STATISTICAL_REPLICATION_PASS__EXECUTION_BLOCKED, or
- OOS_CONFIRMATION_FAIL, or
- INSUFFICIENT_SAMPLE / SOURCE_OR_INFERENCE_BLOCKED.

It may NOT receive CANDIDATE, TIER 2, micro-live, or production authority from this one-shot alone.

## 8. Family adjudication

All three fixed cells are reported individually.

A passing cell is not allowed to erase losing siblings. Family reporting must state the complete 3-cell result vector.

No family-wide PASS is claimed unless all three independently satisfy the economic/statistical replication gate. If only a subset passes, only those exact cells may remain as replication survivors, explicitly labeled as pre-registered cell-level survivors rather than a family-wide confirmation.

No post-outcome selection or parameter rescue is allowed.

## 9. Stop rule

After the one-shot 2025 closeout:
- STOP.
- 2026 remains closed.
- no second 2025 shot;
- no asset/lookback/horizon/direction rescue;
- no fee reduction;
- no regime selection;
- no live orders;
- no exchange mutation;
- no wallet use;
- no alerts/webhooks;
- no merge to main.

A separate authority would be required for any execution-quality study, Final Holdout assignment, shadow program, or micro-live work.
