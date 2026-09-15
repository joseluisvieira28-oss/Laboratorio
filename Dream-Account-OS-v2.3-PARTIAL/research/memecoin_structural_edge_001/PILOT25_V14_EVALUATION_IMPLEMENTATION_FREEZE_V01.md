# MSEL-001 — Pilot25 V14 Evaluation Implementation Freeze V0.1

Status: PRE-V14-RUN / RESEARCH-ONLY / FAIL-CLOSED
Date: 2026-09-15

## Authority

V13F binding passed before this implementation freeze:

- V13F binding SHA-256: `0a02806c2795f4e308fcd88aba0dcfb69c9c6e064dcc6fa1d5b976e872d5f7ec`
- entry authority: V12A T+5 Pump curve gross 0.01 SOL
- entry coverage: 25/25
- sealed future transactions: 904
- no future raw transaction decoded by V13F
- no returns or labels computed by V13F

## Frozen V14 implementation

`pilot/evaluate_pilot25_outcomes_v14.py` may now open the sealed V13 future transaction bytes exactly under the already-frozen V11 + V12/V12A rules.

The evaluator must:

1. re-verify the V13F binding, V13 manifest, V11 risk order, V03 pre-T+5 TradeEvents and cohort hashes;
2. reconstruct the V12A 0.01 SOL entry reference from the latest reconciled Pump TradeEvent state at or before T+5;
3. verify all 904 sealed raw transaction hashes before using them;
4. decode historical Pump TradeEvent records only under the frozen May-2025 schema;
5. apply the frozen >=0.01 SOL future SELL floor and mechanically exclude same-transaction equal-token Pump buy/sell atomic round-trip components;
6. compute +15m/+1h/+6h/+24h SELL-only returns, -80% catastrophe, +100% winner, liquidity-absence catastrophe and the fixed 3% stress sensitivity;
7. join only to the already-frozen V11 risk order and 5/13/5 slices;
8. report the already-frozen Pilot25 partial gate diagnostics without claiming full `SURVIVES_MVE`.

## Mandatory migration fail-closed rule

This first V14 implementation is authorized to complete the economic evaluation only if the sealed 24h source contains no Pump migration instruction and no historical PumpSwap BuyEvent, SellEvent or CreatePoolEvent.

If any such migration/PumpSwap evidence is present, V14 must stop **before labels or slice statistics** with:

`PUMPSWAP_PATH_PRESENT_REQUIRES_CANONICAL_MIGRATION_DECODER`

This is not a failed hypothesis and not a negative outcome. It is a technical/source-continuity block requiring the already-frozen canonical Pump→PumpSwap migration-link implementation. PumpSwap evidence may never be ignored or treated as liquidity absence.

## Governance

- no live trading;
- no exchange mutation;
- no main merge;
- no threshold tuning after outcomes;
- no rescue by dropping tokens;
- Pilot25 alone cannot satisfy the full temporal-OOS MVE gate.
