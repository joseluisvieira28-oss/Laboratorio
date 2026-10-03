# MACRO-POSTRELEASE-FWD-001 — BLS ICS TZID PARSER CORRECTION V0.13.1A

Date: 2026-10-03
Status: TECHNICAL SOURCE PARSER CORRECTION / ZERO OUTCOMES

Initial source-gate run 37128148825 returned PARTIAL_SOURCE only because the official BLS
ICS uses TZID `US-Eastern`, while the GitHub runner's zoneinfo database did not expose
that legacy alias.

The raw BLS ICS was fetched successfully (HTTP 200) and preserved with SHA256:
`92a350111ace106deaab5584e4084366bd367b594a0d0bad116008d82d63e501`.

CPI and Employment Situation pages were both public/schema-valid, and both BTC/ETH MEXC
public index sources passed.

Correction:
- normalize ICS TZID `US-Eastern` to IANA `America/New_York`;
- no event filter, release rule, direction, horizon, source, or scientific criterion changes;
- rerun the same source gate;
- zero outcomes remain opened.
