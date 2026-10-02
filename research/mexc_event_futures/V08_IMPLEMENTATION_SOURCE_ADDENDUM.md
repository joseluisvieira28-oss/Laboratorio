# V0.8 IMPLEMENTATION / SOURCE COVERAGE ADDENDUM

Date: 2026-10-02
Status: FROZEN BEFORE V0.8 OUTCOME EXECUTION

Additional fail-closed implementation details:

- Parent Discovery artifact digest expected from GitHub metadata:
  `sha256:a810a6eaa7a1f476ab265a9f2bb614eb9f4bf251c58d43037bb2ca414ce6e5cd`.
- Parent 2025 OOS artifact digest expected from GitHub metadata:
  `sha256:dbbcb7ca0bd1a4fdc759b5ec0211743cfb9b441b304d23692094b148bdcfbf82`.
- Discovery ledger expected rows: 1210.
- 2025 OOS ledger expected rows: 363.
- Parent zero-position rows, if any, are excluded before price resolution.
- MEXC Min5 requests use seconds and five-calendar-day chunks.
- A Min5 close with source timestamp `s` maps to observable time `s+300s`.
- Exact entry and outcome timestamps must exist in the mapped series; no interpolation or nearest-price substitution.
- Discovery source coverage for a horizon must resolve at least 95% of nonzero parent signals AND at least 500 non-tie outcomes. Otherwise that horizon is `SOURCE_BLOCKED`, not `NO_EDGE`.
- 2025 OOS source coverage for a selected horizon must resolve at least 95% of nonzero parent signals AND at least 250 non-tie outcomes. Otherwise OOS classification is `OOS_SOURCE_BLOCKED`.
- MEXC source requests are limited to timestamps required to cover the immutable parent signal ledgers through calendar 2025.
- No 2026 source request is permitted.
- No interpolation, source fallback, price-field substitution, or clock shift may be introduced after outcomes are seen.
