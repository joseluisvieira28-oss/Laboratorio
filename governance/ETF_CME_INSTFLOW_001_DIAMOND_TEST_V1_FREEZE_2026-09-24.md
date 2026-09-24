# ETF-CME-INSTFLOW-001 — DIAMOND TEST V1 PROSPECTIVE FREEZE — 2026-09-24

Status: FROZEN BEFORE DIAMOND-COUNTED FORWARD BLOCK
Parent: ETF-CME-INSTFLOW-001
Diamond authority: DIAMOND-TEST-V1-FROZEN-2026-09-24
Current V3 state: Tier 2 retained — fragile / forward shadow active
Diamond state: DIAMOND_TEST_ARMED

## Scientific identity — unchanged

- CFTC Legacy Futures Only;
- contract code 133741;
- signal = delta(noncommercial_long - noncommercial_short) / current open interest;
- sign determines LONG / SHORT / FLAT;
- information-safe time = CFTC as-of date + 8 calendar days at 00:00 UTC;
- entry = first BTCUSDT daily 00:00 UTC at/after information-safe time;
- exit = entry + 7 calendar days at 00:00 UTC;
- no threshold, category, regime or horizon change.

Exact runtime timing remains:
- arm lead = 60 seconds;
- max technical lateness = 2 seconds;
- no late chase.

## Diamond boundary

The 2026-09-23 missed observation is immutable and excluded from this new Diamond block because it occurred before this freeze.

Only forward observations with information-safe timestamps strictly after this freeze may enter the Diamond block.

No missed or late event after this freeze may be reconstructed.

## Sample

Final Diamond statistical block = first **50 resolved directional forward observations** after this freeze.

Rationale: Promotion Policy V3 defines >=50 genuinely independent validation observations as the normal dense/systematic independent-block minimum. The historical independent OOS also contained 50 weeks. This sample rule is frozen before the new Diamond block.

## Statistical gates at 50

All required:
- BASE10 mean > 0;
- BASE10 PF > 1;
- STRESS20 mean >= 0;
- five consecutive blocks of 10 observations;
- at least 3/5 blocks have non-negative BASE10 mean;
- largest single positive BASE10 observation share <=40%;
- no favourable-week deletion;
- no missed/late observation reconstructed;
- signal provenance and timing identity remain exact.

## Operational gate

The existing candidate-specific readiness contract remains authoritative:
- projected all-in round-trip friction for an intended execution must be <=20 bps;
- exact applicable fees must be measured, never assumed lower after outcomes;
- LONG mapping = unlevered MEXC BTCUSDT Spot;
- SHORT mapping = MEXC BTC_USDT isolated 1x perpetual;
- no stop invention;
- no maker fallback rescue;
- no leverage tuning;
- missed exact entry = no trade.

For Diamond survival, every counted implementation observation must have an immutable pre-entry friction/timing receipt. An observation whose projected friction exceeds 20 bps remains in the scientific ledger but is marked operationally non-executable; it cannot be silently deleted.

## Outcome

At 50:
- statistical gates PASS + no unresolved operational contradiction -> `DIAMOND_TEST_SURVIVES`;
- statistical gate FAIL -> `DIAMOND_TEST_FAIL__EXACT_ETF_CME_NO_RESCUE`;
- source/timing/operational evidence incomplete -> `DIAMOND_TEST_BLOCKED`.

No automatic Tier 1, micro-live, production or capital authority is created.
