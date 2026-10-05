# OPTIONS-VOL-FWD-001 V0.2 — SOURCE CALIBRATION CONTINUATION FREEZE E–H

Date: 2026-10-05
Status: PRE-COLLECTION / SOURCE-ONLY / NO OUTCOMES

## Authority

Unchanged parent:
- `OPTIONS_VOL_SOURCE_CALIBRATION_FREEZE_V02.md`
- source algorithm: Deribit public source only
- one source round per UTC minute
- no retry inside a minute
- nearest active expiry in [7,30] days
- actual-delta matched put/call selection unchanged
- canonical skew = put mark IV - call mark IV
- threshold rule = nearest-rank P95 of |skew| after the full minimum calibration
- no MEXC data and no Event Futures outcomes during calibration

Completed frozen calibration chunks:

- A: 180 observed minutes / BTC 166 valid / ETH 172 valid
- B: 180 observed minutes / BTC 166 valid / ETH 160 valid
- C: 180 observed minutes / BTC 171 valid / ETH 171 valid
- D: 180 observed minutes / BTC 179 valid / ETH 179 valid

Cumulative after D:
- 720 unique observed minutes per symbol
- BTC valid matched pairs: 682
- ETH valid matched pairs: 682
- no frozen-window overlap

Chunk D final minute:
`1791184980000`

## Continuation plan

Collect four additional bounded source-only chunks E, F, G and H.

Each chunk:
- observes exactly 180 future UTC minutes per symbol;
- starts only after the preceding chunk job has completed;
- computes its first target as the next future UTC minute;
- must have first minute strictly greater than the prior chunk's last recorded minute;
- preserves every raw source response and source-calibration row;
- treats missing/invalid minutes as missing, never imputed;
- opens zero MEXC/Event Futures outcomes;
- commits no numeric threshold.

If any chunk fails its non-overlap gate or collection job, later dependent chunks do not run.

## Final merge gate

After successful H completion, merge A+B+C+D+E+F+G+H using the already frozen
`options_vol_source_calibration_merge_v02.py`.

Activation readiness requires, per symbol:
- >=1440 unique observed UTC minutes;
- >=1200 valid matched-pair minutes;
- zero conflicting duplicate rows.

Only the merged source-only ledger may calculate the sole allowed nearest-rank P95 threshold.

The merge output may say:
- `READY_FOR_NUMERIC_ACTIVATION_FREEZE`
- `SOURCE_CALIBRATION_INCOMPLETE`
- `BLOCKED_CONFLICT`

Even if READY, the workflow does NOT open outcomes and does NOT activate V0.2 automatically.
A separate pre-outcome activation freeze containing exact numeric thresholds, source hashes and
a new future boundary remains mandatory before any Event Futures shadow outcome.

## Prohibitions

No MEXC payout access.
No MEXC index access.
No returns.
No Event Futures outcomes.
No login/API key.
No private/account endpoints.
No orders.
No wallet/spending.
No live trading.
No post-outcome tuning.
No merge/change to main.
