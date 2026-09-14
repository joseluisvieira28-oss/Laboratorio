# TOKEN-UNLOCK-EVENT-001 — PIT REMEDIATION NOTE V0.1

STATUS: SOURCE REMEDIATION / OUTCOME-BLIND
DISCOVERY: CLOSED
2025: LOCKED
2026: LOCKED

## New source route identified

Public repository: `6th-Man-Ventures/token-vesting`.

This repository is materially different from a current reconstructed unlock calendar because Git history supplies immutable publication timestamps for structured vesting-schedule data.

Repository facts observed without opening any 2025/2026 event rows:

- repository created 2023-04-27;
- `data/vesting_data.py` has a commit history beginning 2023-04-27;
- observed commits touching the file include:
  - `98c3d475f22d192589dc4c0afe6a55f313678866` — 2023-04-27T16:37:34Z;
  - `441bbc25bc2ddd064314cb2482b126e53e0f7c7c` — 2023-05-02T17:20:43Z;
  - `df63a117b22dbe8e654cda47e893ee73bd03e949` — 2023-05-03T16:13:34Z;
  - `7d2bf881ca3c6ffe7c30ab34889bb92c08b1904a` — 2023-05-19T18:00:05Z.
- repository tree shows `data/vesting_data.py` plus daily unlock workbooks and analysis code;
- targeted code-search snippets confirm the structured schedule includes fields such as start/end and contains at least one schedule ending in 2024.

## Scientific significance

A Git commit timestamp predating a future release can serve as a defensible `known_at_utc` source primitive. This is stronger PIT evidence than querying a mutable current aggregator today and assuming its reconstructed history equals the schedule known at the time.

Therefore the source problem is no longer merely 'find a provider'. A concrete immutable seed route exists for at least part of the 2023-2024 event space.

## Why the Source Gate does NOT pass yet

The current gate requires >=40 PIT-qualified events, >=15 tokens, >=2 calendar years, and event-level proof of exact amount + timestamp known >=30 days in advance.

Those counts have NOT been established. The complete vesting source file was deliberately not opened because the current lab forbids opening 2025/2026 event rows, and the repository may contain schedules extending beyond 2024. Targeted searches alone are insufficient to enumerate a compliant 2021-2024 manifest.

Accordingly:

- `SOURCE_PIT_PROVENANCE_INCOMPLETE` remains the correct classification;
- `pit_events_proven` remains 0 under the full event-receipt standard;
- no outcome, return, PnL, PF or future price was opened;
- the earlier Source Gate receipt remains valid and is not overwritten.

## Next authorized source action

Build a date-bounded extraction method that reads only schedule entries whose relevant release dates are <= 2024-12-31 from an immutable pre-event Git snapshot, or locate an already date-bounded historical export. For each candidate event, attach project-primary/on-chain evidence where available and enforce the >=30-day known-at rule.

Only after the manifest reaches the frozen gate thresholds may execution semantics be frozen and Discovery outcome authorization be considered.
