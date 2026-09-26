# BTC-CONVEX-TREND-CAPTURE-001 — V0.2 FORWARD DETERMINISM AUDIT — 2026-09-25

**Authority:** PROSPECTIVE_SHADOW_AUTHORITY_V0.2_AGGRESSIVE  
**Scientific contract:** UNCHANGED  
**Audit type:** technical / evidence integrity only  
**Result:** **PASS**

## Objective

Verify that the deterministic V0.2 shadow engine reproduces the same scientific state when re-executed inside the same completed 1h-bar set, before any V0.2 trade has closed.

No rule, parameter, asset, cost, direction, timeframe, causal boundary or data source was changed.

## Compared executions

GitHub Actions run: **36043505670**

### Attempt 7
- job: **107947466538**
- snapshot time: **2026-09-25T04:45:30.051147Z**
- artifact: **10847566541**
- artifact ZIP SHA-256: **2ab310a666cf360787ccc84470c797486288deb9d98c6adb3eae9d8c44e32a45**
- inner JSON SHA-256: **16d2652f7be1f89480e2d0dabffab99e1a16c34b129af1f83423d08c0f21f4f5**

### Attempt 8
- job: **107948129256**
- snapshot time: **2026-09-25T04:48:46.369938Z**
- artifact: **10846992604**
- artifact ZIP SHA-256: **663c6968adaa46bb1378f948e0227095e41147143147db81ca1abdfc816c5c4a**
- inner JSON SHA-256: **3dc9e30664c453c821537392e49db51b7e8f0f82e88f138b527f21dc281499c9**

## Normalization

The full JSON objects were compared after removing only fields that are expected to vary with wall-clock/request timing and do not alter scientific state:

1. `snapshot_time_utc`
2. `family.collection_age_days`
3. `source_manifest` — request URLs/endTime and raw payload hashes can differ because the request is made at a different wall-clock instant and can include the then-current incomplete bar before the script filters incomplete bars.

No symbol result, signal, position, stop, funding cashflow, trade record, equity field, drawdown field, checkpoint field, source status or causal state was excluded.

## Result

**NORMALIZED SCIENTIFIC STATE: IDENTICAL**

The two executions reproduced the same:
- completed forward bars;
- signal history;
- pending-entry state;
- open-position state;
- entry prices and quantities;
- peaks;
- initial and active stops;
- funding cashflows;
- marked/realized equity;
- trade ledger;
- closed-trade counts;
- family checkpoint state;
- source PASS state;
- causal-integrity state.

## Governance interpretation

This PASS is operational evidence only. It does **not** create edge evidence, a promotion, a checkpoint, or live-trading authority.

It strengthens the prospective evidence chain by demonstrating repeatability of the frozen V0.2 implementation before the first resolved trade.
