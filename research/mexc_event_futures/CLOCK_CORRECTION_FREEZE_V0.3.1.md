# MEXC EVENT FUTURES LAB — CLOCK CORRECTION FREEZE V0.3.1

Date: 2026-10-02
Status: PRE-CORRECTION OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## Reason for correction

The V0.3 Min5 proxy used each K-line `close` at the K-line timestamp itself.

A live source observation during the source probe showed that, at approximately 14:52 UTC, the latest Min5 K-line timestamp was 14:50 UTC while the live index timestamp was approximately 14:52 UTC. This is consistent with the Min5 timestamp identifying the beginning of the current 5-minute bucket, not the instant at which its final close is known.

Therefore using a historical Min5 close at its raw bucket timestamp risks up to 5 minutes of look-ahead.

V0.3 produced zero discovery passers, so no candidate was promoted and August OOS was not evaluated. Nevertheless V0.3 is not used as the final scientific verdict.

## Frozen technical correction

For every Min5 K-line with raw timestamp `s`:
- the close is mapped to observable proxy time `s + 300 seconds`;
- a decision at time `t` may use only close values mapped to times <= `t`;
- future outcome price at `t + H` uses the close mapped exactly to `t + H`.

All strategy rules, mappings, partitions, gates, horizons, lookbacks, and payout assumptions remain identical to SOURCE_TRANSFER_FREEZE_V0.3.

No September 2026 data may be fetched.
No new signal family is introduced.
No threshold is changed.
No live trading or authenticated exchange mutation.

## V0.3 status

V0.3 = CLOCK_AMBIGUOUS / NOT FINAL.

V0.3.1 supersedes V0.3 for the simple CONTINUATION / REVERSAL Min5 proxy family.
