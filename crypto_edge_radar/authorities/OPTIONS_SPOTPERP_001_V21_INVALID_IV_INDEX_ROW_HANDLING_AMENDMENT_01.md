# OPTIONS-SPOTPERP-001 / V2.1 — INVALID IV/INDEX ROW HANDLING AMENDMENT 01

**Status:** FROZEN BEFORE TECHNICAL REMEDIATION  
**Scope:** source-adapter semantics only; no scientific rule change.

## Recovered authority

The canonical historical Source/Data Audit explicitly established that invalid Deribit IV/index rows are rejected from frozen eligibility coverage and disclosed as source-quality counters; they are not a corpus-wide structural failure. Structural/provenance failures remain fail-closed.

## Technical defect

The prospective live-shadow adapter currently raises `OptionsV21SourceError("Deribit trade has invalid IV/index")` on the first invalid IV/index row and aborts the entire UTC source window. This is stricter than the already-reconciled source semantics and creates an operational false blocker.

## Frozen remediation

For a Deribit trade row that:
- is an object;
- contains the frozen required fields;
- has a valid in-window timestamp;
- has a non-empty trade_id;
- has a structurally valid BTC option instrument;

but whose IV or index_price is non-numeric, non-finite, or <= 0:

1. reject that row from signal eligibility;
2. increment an explicit invalid-IV/index source counter;
3. continue processing the same immutable source window.

All other structural/provenance failures remain fail-closed, including:
- missing frozen fields;
- invalid/out-of-window timestamp;
- missing trade_id;
- malformed BTC option instrument;
- trade_id collision with different payload;
- pagination/saturation failure.

## Scientific invariants

Unchanged:
- signal = CALL_IV_MINUS_PUT_IV;
- DTE = 30–120 calendar days;
- call moneyness = 1.05–1.20;
- put moneyness = 0.80–0.95;
- median IV per instrument then median per side;
- minimum 5 distinct valid instruments per side;
- direction mapping;
- RV20 state, expanding-median baseline and weight;
- execution timing;
- BASE10 / STRESS20 costs;
- prospective boundary;
- no backfill rescue;
- no parameter tuning.

This amendment is technical/source-quality reconciliation only. It grants no live trading, orders, exchange mutation, capital, Tier-1 promotion, or main merge.
