# Macro Shock Microstructure State Lab V0.1 — Schema & Alignment Spec

Status: **FROZEN PRE-DATA IMPLEMENTATION SPEC / NO EDGE HYPOTHESIS**

## Authority

This specification is downstream of:

- `MACRO_SHOCK_MICROSTRUCTURE_STATE_LAB_V01_PRE_DATA_CHARTER.md`
- `MACRO_SHOCK_MICROSTRUCTURE_STATE_LAB_V01_PROVENANCE_GATE.json`
- `MICROSTRUCTURE_PROVENANCE_SHAKEDOWN_V02_CLOSEOUT.json`

The provenance gate passed using bounded public read-only Binance Spot market-data-only and Coinbase Advanced Spot streams. This document does **not** authorize target-outcome research, a directional H02, live trading, exchange mutation, MEXC access, main merge, or Render deployment.

## Objective

Define deterministic venue-neutral records and clock-alignment rules that can be validated using synthetic fixtures before any event-outcome research.

## Canonical market identity

- `venue`: exact source venue identifier; no venue substitution.
- `market_type`: `SPOT` only at this stage.
- `symbol`: source-native symbol retained.
- `canonical_asset`: `BTC` or `ETH` only for cross-venue identity.
- `quote_asset`: source-native quote asset (`USDT` or `USD`).

Cross-venue mapping is identity-only:

- Binance `BTCUSDT` ↔ canonical asset `BTC`
- Coinbase `BTC-USD` ↔ canonical asset `BTC`
- Binance `ETHUSDT` ↔ canonical asset `ETH`
- Coinbase `ETH-USD` ↔ canonical asset `ETH`

No synthetic FX conversion is authorized in this stage.

## Clock fields

Every normalized observation must retain:

- `exchange_ts_ns` when the venue supplies an exchange timestamp;
- `collector_wall_ns` from the collector wall clock;
- `collector_monotonic_ns` for local ordering/audit;
- source sequence/update identifiers where available;
- source-message SHA-256 or equivalent provenance linkage.

Rules:

1. UTC nanoseconds are the canonical time unit.
2. Exchange timestamps are never replaced by collector time when present.
3. Collector time is provenance/latency metadata, not a substitute event timestamp.
4. Records without an exchange timestamp may be retained for provenance but cannot silently become cross-venue event-time anchors.
5. No future observation may be used to populate an earlier canonical timestamp.

## Canonical observation types

### BBO observation

Required:

- venue
- symbol
- canonical asset
- exchange timestamp if available
- collector timestamps
- best bid price and quantity
- best ask price and quantity
- provenance hash/reference

Derived mechanically:

- mid = `(best_bid + best_ask) / 2`
- spread = `best_ask - best_bid`
- spread_bps = `spread / mid * 10000`

A crossed or locked book is invalid and fails closed.

### L2 state observation

Required:

- same identity/time/provenance fields;
- synchronized book state;
- deterministic ordered bid and ask levels.

No depth band is hard-coded here. Any future research depth band must be prospectively frozen before target-data inspection.

### Trade observation

Required:

- venue
- symbol
- canonical asset
- exchange timestamp
- trade identifier/sequence where available
- price
- quantity
- source-defined aggressor/maker-side field only when unambiguously supported by venue semantics
- provenance hash/reference

No inferred trade direction may be invented when source semantics are ambiguous.

## Cross-venue alignment

The only permitted generic alignment primitive at this stage is **backward as-of alignment**:

For an anchor observation at time `t`, a candidate from another venue is eligible only if its exchange timestamp is `<= t` and it is the latest eligible observation. Future observations are forbidden.

`max_skew_ns` is an explicit caller-supplied parameter in synthetic/offline code. This specification intentionally does not freeze a numeric skew threshold. A future empirical contract must freeze it before target-outcome inspection.

If no eligible observation is within `max_skew_ns`, the aligned value is missing. Missingness is preserved; no interpolation is authorized.

## Deterministic integrity rules

- duplicates with identical provenance hash may be de-duplicated without reordering;
- conflicting payloads sharing an allegedly identical sequence/update ID fail closed;
- sequence regression fails closed where sequence semantics exist;
- book reconstruction must be synchronized before spread/depth metrics are emitted;
- missing venue timestamps remain missing;
- sorting ties must use stable source order, never price-movement outcome.

## Synthetic implementation boundary

Allowed now:

- dataclasses / typed records;
- mechanical BBO metrics;
- deterministic backward as-of alignment;
- synthetic fixtures for BTC and ETH across Binance/Coinbase;
- fail-closed tests for future leakage, crossed books, invalid timestamps, missing alignment and duplicate conflicts.

Forbidden now:

- event-family optimization;
- directional labels;
- returns after macro events;
- continuation/reversal labels;
- profitability, fees or slippage strategy scoring;
- choosing windows/thresholds because real outcomes look favorable.

## Scientific boundary

`H02_STATUS = NOT_AUTHORIZED`

Passing this implementation stage means only that the measurement layer is deterministic and technically suitable for a future separately authorized pre-data contract review.

Final gate: **STOP BEFORE TARGET OUTCOMES OR H02 FREEZE.**
