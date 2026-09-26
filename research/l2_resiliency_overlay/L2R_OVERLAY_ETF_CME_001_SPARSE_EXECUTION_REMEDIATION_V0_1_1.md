# L2R-OVERLAY-ETF-CME-001 — SPARSE EXECUTION REMEDIATION V0.1.1

Date: 2026-09-26  
Status: **FROZEN BEFORE ANY COMBINED 2025 OUTCOME ACCESS**  
Parent protocol: `L2R_OVERLAY_ETF_CME_001_2025_DEVELOPMENT_PROTOCOL_V0_1.md`  
Parent one-shot authority: `L2R_OVERLAY_ETF_CME_001_2025_DEVELOPMENT_ONE_SHOT_AUTHORIZATION_V0_1.md`

## Trigger

The exact V0.1 full-corpus runner was byte-verified and prepared with the canonical 2025 L2 corpus and immutable ETF-CME parent artifact. The chat runtime could not launch the long-lived full scan because its streaming execution facility was unavailable before the Python process started.

**No combined L2 × ETF-CME residual/outcome was opened.**

The prospectively frozen one-shot authority permits a technical correction before another outcome-bearing run only when the correction is implementation-only, documented, re-QA'd and re-locked.

## Scientific contract unchanged

V0.1.1 changes no scientific rule:
- same LAB_ID: `L2R-OVERLAY-ETF-CME-001`;
- same 50-row immutable ETF-CME parent ledger;
- same parent position/direction and T0;
- same canonical Hyperliquid BTC 2025 corpus;
- same source-clock normalization V0.1B;
- same sweep definition;
- same RR threshold: WEAK iff RR < 1.0;
- same maximum lateness: 1,100 ms;
- same six frozen cells;
- same ALIGNED / OPPOSED / NO_ACTIVE_WEAK / SOURCE_GATED definitions;
- same residual formula;
- same sample viability and five support gates;
- same classification routing;
- no parent weekly PnL filtering;
- 2026 remains CLOSED;
- no orders, live trading, exchange mutation, wallet mutation, main merge or post-outcome rescue.

## Sparse equivalence boundary

Every frozen causal cell has maximum Y horizon = 60 seconds.

An event can be ACTIVE_WEAK_AT_T0 only if its Y target is strictly after T0. Therefore every event capable of affecting the overlay classification must satisfy:

`event_env > T0 - 60 seconds`.

V0.1.1 reads only:
1. the complete prior UTC hour for normalization/state warm-up; and
2. the complete T0 UTC hour for the causal window and all R/Y observations.

This is sufficient because T0 is exactly 00:00:00 UTC for every immutable ETF-CME parent row.

### Normalization-state equivalence proof

Before the causal cutoff `T0 - 60s`, V0.1.1 requires a non-future payload row satisfying:

`payload_ms >= previous_hour_start_ms`.

Any canonical non-future `last_payload` inherited from an earlier hour must be strictly less than `previous_hour_start_ms`, because its envelope precedes the prior-hour boundary and payload may not exceed envelope for a non-future row.

Thus that qualifying row is necessarily accepted by the full runner and deterministically synchronizes:
- `last_payload`;
- accepted current book state;
- `prev` state.

After that synchronization row, the sparse replay and full runner receive the same remaining bytes in the same envelope order and apply the same future-payload and stale-late rules. Any omitted transition occurs before `T0-60s` and cannot enter a frozen active-event cell.

If synchronization is not proven before the causal cutoff, V0.1.1 fails closed.

## Pre-outcome QA / source preflight

Implementation:
- V0.1.1 sparse runner SHA256: `ed17bbc54afede0888b5b4cea56b2d5c6396bede46a7c723bfd2ca0c6a07cc63`
- original V0.1 runner SHA256: `495129040193b01218d867bd8a29f50039e5229203d118571f38445746942b2a`
- canonical manifest SHA256: `767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`
- ETF parent artifact SHA256: `40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1`

QA:
- Python compile: PASS
- synthetic self-test: PASS
- sparse-equivalence preflight: PASS
- parent rows: 50
- parent non-zero rows: 49
- source-evaluable T0 rows: 46
- source-gated rows: 3
- byte-bound RAW objects required by sparse replay: 92
- 92 / 92 RAW objects SHA256 + MD5 + length verified
- minimum normalization stabilization margin before causal cutoff: 3,455.382308889 seconds
- outcomes opened during preflight: false
- 2026 accessed: false
- preflight receipt SHA256: `0a8469490c6ecbc26df34050a0d0b44d151bb3996cab41438303d066d7f02a58`

Source-gated parent entry dates are frozen by the canonical manifest:
- 2025-10-22
- 2025-11-18
- 2025-11-26

## One-shot continuation authority

After this freeze, exactly **one** combined outcome-bearing V0.1.1 execution is authorized.

The first scientifically valid terminal classification is final for this identity:
- `DEVELOPMENT_OVERLAY_SIGNAL_SUPPORTED`
- `DEVELOPMENT_OVERLAY_NO_SUPPORT`
- `DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE`

No rerun for a different sign, cell mix, sample count or economic interpretation is authorized.
