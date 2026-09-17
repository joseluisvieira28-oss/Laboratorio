# BINANCE-MARGIN-BORROW-ACCESS-001 — SOURCE TRANSPORT REMEDIATION V0.3

Date: 2026-09-17  
Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND / CURSOR REMEDIATION ONLY**

## Trigger

V0.2 proved that Telegram cursor `before=6900` is not protected-period safe: the first returned page contained at least one timestamp after `2024-12-31T23:59:59Z`. The V0.2 run therefore correctly emitted `PROVENANCE_FAILURE` and opened no market outcome.

## Frozen correction

Narrow the official Binance English announcements Telegram upper cursor by exactly one message boundary:

`before=6899`

No event/outcome information is used in this correction. This is a transport-boundary remediation only.

## Additional end-window coverage gate

A protected-safe cursor is not enough. The first historical page must also prove that the retained traversal reaches the end of the frozen scientific window closely enough to avoid silently dropping the final calendar day.

Frozen requirement:
- first-page maximum timestamp must be on `2024-12-31` UTC;
- any timestamp after `2024-12-31T23:59:59Z` => `PROVENANCE_FAILURE`;
- first-page maximum timestamp before `2024-12-31T00:00:00Z` => `SOURCE_ENUMERATION_INCOMPLETE`.

Only if this upper-boundary gate passes may the collector continue backward to cross below `2023-01-01T00:00:00Z`.

All V0.2 rules, positive controls, canonical Binance Support authority, protected-period firewall and forbidden market-outcome accesses remain unchanged.
