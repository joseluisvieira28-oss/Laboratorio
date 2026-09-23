# L2-RESILIENCY-001 — 2025 SOURCE CLOCK NORMALIZATION AMENDMENT V0.1B

Date: 2026-09-23
Status: **FROZEN PRE-OUTCOME SOURCE NORMALIZATION AMENDMENT**
Authority: source-clock diagnostic V0.1A + previously frozen 2025 validation protocol.
Scientific outcomes opened before this freeze: **false**.

## Why an amendment is required

The canonical V0.1/V0.1.1 normalizer fails closed whenever:

`raw.data.time * 1e6 > envelope_ns`

The full-corpus source-only diagnostic found 109 such rows across 53,647,758 records. Only 9 are <=1ms; 100 exceed 1ms and the maximum lead is 42.609667ms. Therefore the already-frozen complete-sub-1ms quantization route is rejected.

At the same time:

- envelope backwards = 0;
- envelope outside key hour = 0;
- source/schema fallback = 0;
- the 2025 validation protocol already freezes the top-level envelope timestamp as the archive availability/order clock and the event anchor.

## V0.1B normalization rule

No fitted or observed-value clock threshold is introduced.

For each record, in contiguous PRESENT-segment envelope order:

1. Envelope timestamp must remain inside the object's UTC hour.
2. Envelope timestamp must be non-decreasing.
3. Raw l2Book schema/book validity rules remain unchanged.
4. Define `future_clock_skew = payload_ms * 1e6 > envelope_ns`.
5. Maintain a payload monotonicity watermark using **accepted non-future payload timestamps only**.
6. If `payload_ms < payload_watermark`, classify `STALE_LATE_PAYLOAD`, preserve raw evidence, quarantine the state from continuity, and do not update the watermark.
7. Equal payload timestamps remain preserved in envelope order.
8. If the row is future-clock-skew and not stale:
   - accept the book state in envelope order;
   - preserve the original payload timestamp unchanged;
   - record it in a dedicated future-clock ledger;
   - **do not advance the payload watermark**.
9. If the row is non-future and not stale:
   - accept the book state;
   - update the payload watermark to `payload_ms`.

No timestamp is clamped, shifted, winsorized, rounded, replaced, or fitted.

## Why this is outcome-independent

The rule depends only on:
- envelope ordering;
- payload timestamp ordering;
- the sign of the already-defined future-clock relation.

It does not inspect:
- sweep direction;
- replenishment;
- midpoint response;
- returns;
- PnL;
- month/subperiod performance;
- validation sign.

No clock-skew magnitude observed in 2025 is used as a threshold.

## 2024 exact-equivalence proof

The frozen 2024 source/schema closeout records:

- future payload rows: 0;
- stale-late payload rows: 80;
- envelope backwards: 0.

V0.1B differs from the prior normalizer only inside the future-clock branch. With zero future rows, that branch is unreachable.

Therefore for the canonical 2024 corpus:

- accepted/quarantined state sequence is identical;
- payload watermark evolution is identical;
- stale-late decisions are identical;
- equal-timestamp handling is identical;
- event anchors are identical.

Classification:

`2024_NORMALIZATION_EQUIVALENCE_PASS_BY_UNREACHABLE_BRANCH_PROOF`

This amendment inherits **no new promotion credit** from that proof.

## Validation invariants

Everything downstream remains frozen exactly as before:

- BTC only;
- 2025 only;
- missing-hour segmentation unchanged;
- sweep definition unchanged;
- event anchor remains envelope time;
- horizons 1s/5s/15s/60s unchanged;
- max lateness 1,100ms unchanged;
- replenishment RR rule unchanged;
- WEAK/STRONG threshold RR <1 / >=1 unchanged;
- six causal cells unchanged;
- UTC-day contrast method unchanged;
- bootstrap 10,000 / seed 20260919 unchanged;
- minimum 300 eligible days unchanged;
- VALIDATION_PASS gate unchanged.

## Required implementation behavior

Schema audit and validation must share the same V0.1B normalization semantics.

The schema receipt must expose:
- future payload clock-skew count;
- stale-late count;
- equal count;
- dedicated future-clock normalization ledger hash.

The validation receipt must expose the future-clock count actually traversed by the frozen validation.

## Firewalls

- 2026: forbidden
- economic feasibility/PnL/costs/Sharpe/leverage: forbidden
- live trading/orders/exchange mutation: forbidden
- post-outcome retuning: forbidden
- main merge: forbidden without separate authority

Once the V0.1B runner hash is implementation-locked, the previously authorized one-shot independent 2025 validation may execute on the exact canonical 8,400-object corpus.
