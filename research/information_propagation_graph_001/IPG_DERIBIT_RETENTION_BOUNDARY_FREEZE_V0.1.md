# IPG-001 DERIBIT RETENTION-BOUNDARY REMEDIATION FREEZE V0.1

Frozen: 2026-09-24
Stage: SOURCE CAPABILITY ONLY
Market/predictive outcomes: CLOSED

## Trigger

The first fixed 2024-06-01 probe returned:
- 74 currently exposed expired BTC options;
- zero options expiring in June 2024;
- BTC perpetual funding history present (23 hourly rows);
- mark-price history and DVOL calls syntactically valid but zero rows for that 2024 day.

This remediation does not change any IPG hypothesis or outcome threshold.

## Deterministic source-only rule

1. Fetch current expired BTC option inventory.
2. Persist only count and min/max expiration timestamps plus a histogram by expiration month.
3. Select the lexicographically first option among instruments at the EARLIEST
   expiration timestamp currently exposed by the API.
4. Define fixture window as the UTC calendar day immediately preceding that
   selected option expiration.
5. Probe that exact option's public trade history and mark-price history.
6. Probe BTC-PERP mark/funding and BTC DVOL over the same fixture day.
7. Persist counts/timestamp ranges/schema/hashes only. No price, IV, amount,
   direction, return or PnL value may be persisted.

## Interpretation

RETENTION_BOUNDARY_SURFACE_PASS:
at least one option historical surface returns >0 rows inside the objectively
observed retention boundary, plus at least one perp/DVOL surface.

RETENTION_BOUNDARY_PARTIAL:
only a subset works.

RETENTION_BOUNDARY_BLOCKED:
no upstream historical surface works even at the retention boundary.

This may establish API retention capability, but cannot backfill the frozen
2024 Binance fixture or count as predictive evidence.
