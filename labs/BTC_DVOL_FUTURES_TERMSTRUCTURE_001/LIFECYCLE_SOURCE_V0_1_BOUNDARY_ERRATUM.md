# BTC-DVOL-FUTURES-TERMSTRUCTURE-001 — Lifecycle Source V0.1 Boundary Erratum

Date: 2026-09-17

## Preserved result

`DVOL-TS-LIFECYCLE-SOURCE-001` remains closed as `LIFECYCLE_SOURCE_DATA_INSUFFICIENT` under its original authority. Canonical run `35087694157` is not rewritten.

The gate passed every frozen source-density and field-coverage requirement except exact metadata integrity, which was 18/19 = 0.9473684210526315 against a frozen 1.0 threshold.

The sole exact-metadata rejection was `BTCDVOL_USDC-26APR23`. Its archived metadata was returned successfully and reported:

- instrument_name = `BTCDVOL_USDC-26APR23`
- kind = `future`
- price_index = `btcdvol_usdc`
- creation_timestamp = 2023-03-23T10:07:30Z
- expiration_timestamp = 2023-04-26T08:00:00Z

It failed only because V0.1 required `creation_timestamp >= 2023-03-27T00:00:00Z`.

## Boundary inconsistency

The V0.1 authority separately stated that lifecycle trade acquisition was bounded to the accepted instrument lifecycle **clipped to** `2023-03-27T00:00:00Z` through the pre-2025 upper bound. Therefore a contract that already existed at the lower boundary could have been observed safely from `max(creation_timestamp, lower_bound)` without requesting any pre-window trades.

V0.1 nevertheless encoded creation-on-or-after-lower-bound as an exact metadata acceptance requirement. That makes the metadata-integrity gate sensitive to whether the first in-scope contract was listed a few days before the observation window, rather than to whether its metadata is exact and its observed lifecycle overlaps the window.

This erratum does not change or pass V0.1. It records the source-boundary design issue discovered after the source-only run. No basis, convergence, returns, PnL, 2025 or 2026 outcomes were opened.

## Authorized new question

A new source gate ID may test the same deterministic Wednesday candidate enumeration and the same source-viability thresholds, but define an accepted exact contract by **overlap with the bounded observation window** rather than by creation after the lower bound.

For such a new gate:

- exact metadata identity, kind and price_index remain mandatory;
- contract creation must be before its expiration and before 2025;
- expiration must overlap the observation window and remain before 2025;
- trade acquisition starts at `max(creation_timestamp, 2023-03-27T00:00:00Z)`;
- trade acquisition ends at `min(expiration_timestamp, 2024-12-31T23:59:59.999Z)`;
- all density/coverage thresholds remain unchanged;
- 2025/2026 and all economic outcomes remain forbidden.

This is a new source-feasibility gate, not a retroactive waiver of the failed V0.1 metadata threshold.
