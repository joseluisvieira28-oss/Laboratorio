# CMM-001 — TECHNICAL CLOSEOUT REPAIR V0.1A

Date: 2026-09-25
Status: FROZEN TECHNICAL REPAIR AFTER OUTCOME ACCESS
Parent scientific authority: CMM001_PRE_DISCOVERY_EXECUTION_AUTHORITY_V01
Parent evidence commit: 7ce2438cdcc9e45ff237daf68ec823e643cbfb42
Parent run: 36107876501

## What happened
The frozen CMM-001 Discovery V0.1 completed the full-corpus source gate successfully and then opened the authorized 2021-2024 CMM outcomes.

The scientific computation reached the terminal result construction, but JSON serialization failed because a diagnostic-only CFTC stratum had Profit Factor = positive infinity (no negative observations) while the serializer was configured with allow_nan=False.

The event ledger, daily state ledger, complete source report and a partial result file were preserved in parent commit 7ce2438.

## Repair authority
This V0.1A repair is TECHNICAL ONLY.

It MAY:
- read the exact preserved CMM001_EVENT_LEDGER_V01.csv;
- read the exact preserved CMM001_DISCOVERY_SOURCE_REPORT_V01.json;
- recompute the already-frozen summary statistics from those immutable event rows;
- reproduce the frozen 10,000-resample bootstrap with seed 20260925;
- encode infinite diagnostic PF safely as the string "INF";
- emit a valid terminal JSON and Markdown closeout.

It MUST NOT:
- access any network or market-data endpoint;
- re-download any source;
- reconstruct or change a signal;
- add, remove or reorder an event;
- change the trigger, threshold, direction, horizon, cost, blocks, feature definitions or promotion gates;
- inspect or access any 2025 or 2026 market outcome;
- use diagnostic funding/CFTC strata to select or rescue the candidate.

## Reproduction anchors
Before the serialization exception, the original run had already computed and preserved these scientific anchors:

A_DISCOVERY:
- N = 15
- mean NET10 = -15.974320184676847 bps
- PF NET10 = 0.9381782766756509

B_REPLICATION_2023:
- N = 16
- mean NET10 = -12.489306569098197 bps
- PF NET10 = 0.8850931891227862

C_REPLICATION_2024:
- N = 4
- mean NET10 = -177.31335986960195 bps
- PF NET10 = 0.09769585257550582

Bootstrap:
- seed = 20260925
- reps = 10000
- P(mean <= 0) = 0.663
- p05 = -166.61399403900987 bps
- p50 = -36.041367109127606 bps
- p95 = +111.00334437994752 bps

V0.1A MUST fail closed if recomputation from the preserved ledger does not reproduce these anchors within numerical tolerance.

## Classification precedence
The frozen parent authority remains controlling:
1. If pooled N < 30 OR any A/B/C block has N < 8 => INSUFFICIENT_SAMPLE, outside Tier 4.
2. Only if sample adequacy passes may Tier 2 / Tier 3 / Tier 4 gates be adjudicated.

No negative result may be upgraded, and no insufficient sample may be relabelled Tier 4 by this repair.

## Safety
No live trading.
No micro-live.
No orders.
No exchange mutation.
No wallet.
No Render.
No merge to main.
No post-outcome rescue.

END OF TECHNICAL REPAIR AUTHORITY
