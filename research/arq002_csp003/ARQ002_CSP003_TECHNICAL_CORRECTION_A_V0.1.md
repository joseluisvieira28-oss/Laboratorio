# ARQ-002-CSP-003 — TECHNICAL CORRECTION A V0.1

Date: 2026-09-23
State: frozen after first 2022 monthly run completed, BEFORE accepting or using its annual scientific adjudication.

## Incident

Frozen authority defines for event minute M:
- event close E = t + 60s;
- OI_now = greatest exact UTC 5m boundary <= E;
- funding = latest official funding observation <= E.

The first monthly implementation loaded:
- next-day 1m klines for outcome continuity;
- but metrics only through the current month's last UTC day;
- funding only through the current month.

Therefore an event at 23:59 UTC on the last day of a non-December month closes at 00:00 of the next month, while the implementation did not have:
- next-day 00:00 metrics available for OI_now;
- next-month 00:00 funding available if an official funding timestamp exists there.

Observed technical symptom:
- August first run reported one source-masked sweep despite the frozen August 2022 source mask having zero missing/invalid slots.

## Frozen correction

For each monthly shard:
1. load previous day metrics;
2. load all current-month metrics;
3. for Jan-Nov only, also load the first UTC day of the next month;
4. load previous-month + current-month funding;
5. for Jan-Nov only, also load next-month funding;
6. source-mask hash comparison remains restricted to the frozen current-month source mask;
7. event scientific rules remain unchanged.

This is implementation alignment to the already-frozen causal clock, not a scientific rule change.

## Superseded run

GitHub Actions run:
- 35912287935

Classification:
- SUPERSEDED_TECHNICAL__DO_NOT_USE_FOR_SCIENTIFIC_ADJUDICATION

Its monthly/aggregate outputs remain preserved as audit evidence but may not promote, reject, tune, or otherwise influence CSP-003.

## Invariants unchanged

No change to:
- Discovery year 2022;
- 2023 replication lock;
- sweep/reclaim 30m rule;
- trapped-aggressor CVD sign;
- OI_CHANGE > 0 confirmation;
- funding sign;
- 5m reversal outcome;
- 10/14/20 bps costs;
- bootstrap;
- 12 Discovery gates;
- source validity masks;
- protected-period firewalls.
