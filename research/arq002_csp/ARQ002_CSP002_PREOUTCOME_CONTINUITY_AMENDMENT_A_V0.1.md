# ARQ-002-CSP-002 — PRE-OUTCOME CONTINUITY AMENDMENT A V0.1

Date: 2026-09-23
State when frozen:
- CSP-002 SOURCE_MASK_PASS.
- 364/366 2024 UTC days source-eligible.
- masked days frozen: 2024-02-16, 2024-10-28.
- no CSP-002 economic outcome, price return, CVD value, OI value or funding value opened.

## Masked day = hard continuity break

A CSP-002 event at minute M is eligible only when every one-minute timestamp required by:
- the 30-minute reference window;
- event minute M;
- the five-minute post-event outcome

belongs either to:
1. a SOURCE_ELIGIBLE 2024 UTC day; or
2. the explicitly authorized 2023-12-31 warm-up boundary for reference-only use.

Therefore:
- no event on a masked day;
- no event immediately before a masked day if its 5m outcome crosses into the masked day;
- after a masked day, no event until its complete 30-minute reference window lies after the mask boundary.

No price outcome crosses a masked-day boundary.

## OI continuity

Both OI_now and OI_prev must:
- come from SOURCE_ELIGIBLE dates;
- be exactly five minutes apart;
- satisfy the frozen causal timestamp rule.

Any masked-day OI row is ignored even if physically present.

No cross-mask OI comparison.

## Funding continuity

Funding observations timestamped on a masked UTC day are not admitted.

For an eligible event:
- latest admitted funding observation timestamp <= event close;
- funding staleness <= 8h05m;
- if masking removes the latest scheduled funding point and the prior admitted point becomes too stale, funding confirmation is unavailable until a new eligible funding observation arrives.

## Kline warm-up

2023-12-31 klines are allowed only to provide the 30-minute reference for early 2024 events.

No 2023 outcome is computed.

## Source byte binding

Discovery must verify every downloaded Binance archive against:
1. its published .CHECKSUM; and
2. the SHA256 observed in the outcome-blind source census receipt for that object.

If the archive has been revised since the census:
- classify SOURCE_PROVENANCE_DRIFT;
- do not silently accept the replacement;
- do not open outcomes from the changed object.

## Scientific invariants

No changes to sweep/reclaim, CVD, OI, funding, reversal direction, five-minute horizon, cost bands, bootstrap or Discovery gates.
