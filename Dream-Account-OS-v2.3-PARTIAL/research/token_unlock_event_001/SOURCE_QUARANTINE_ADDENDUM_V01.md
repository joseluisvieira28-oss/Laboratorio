# TOKEN-UNLOCK-EVENT-001 — SOURCE QUARANTINE ADDENDUM V0.1

STATUS: FROZEN_PRE_OUTCOME
DISCOVERY: CLOSED
OUTCOMES OBSERVED: NONE
2025/2026 MARKET/OUTCOME DATA: FORBIDDEN

## Reason for this addendum

The immutable 6th Man Ventures `token-vesting` source snapshot dated 2023-05-19 contains vesting schedules whose stated end dates can extend beyond 2024. A partial manual source read exposed a schedule end-date string in 2025. No 2025/2026 price, return, PnL, volume, market cap or other outcome data was accessed.

That manual read is quarantined and any post-2024 schedule row exposed by it is forbidden from scientific use.

## Frozen quarantine rule

An automated source-only extractor may read the immutable 2023-05-19 vesting metadata snapshot solely to reconstruct schedule events, but it MUST:

1. emit no event whose derived scheduled date is later than 2024-12-31;
2. emit no source schedule row whose start date is later than 2024-12-31;
3. never request market, price, return, volume, market-cap, supply-outcome or PnL data for 2025/2026;
4. store only the filtered <=2024 candidate manifest plus aggregate counts;
5. mark all rows as CANDIDATE_ONLY until event-level PIT and timing provenance are separately proven;
6. use immutable source commit `7d2bf881ca3c6ffe7c30ab34889bb92c08b1904a` only;
7. use `known_at_utc = 2023-05-19T18:00:05Z` for this source snapshot;
8. require candidate event date >= 2023-06-19, giving at least 30 full calendar days after the immutable commit;
9. exclude daily schedules from MVE1 candidate generation because they represent continuous/near-continuous release rather than discrete event shocks;
10. preserve the original SOURCE_PIT_PROVENANCE_INCOMPLETE classification until the frozen hard gates are actually proven.

## Scientific non-change statement

This addendum does NOT change:
- LAB_ID or MVE_ID;
- economic direction;
- ADV30 normalization;
- event-count/token-count/year-count gates;
- 2025/2026 outcome locks;
- prohibition on returns/PnL during Source Gate;
- no-rescue/no-inversion governance.

It only defines how a mixed-horizon 2023 source document can be filtered without allowing future-period rows into the scientific dataset.
