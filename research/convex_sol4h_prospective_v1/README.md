# CONVEX SOL4h prospective feasibility V1

Read `ECONOMIC_VERDICT_PT.md` first, then immutable `FREEZE_V1.md`.

State: **INCONCLUSIVE / NO ECONOMIC COLLECTOR / NO LIVE GO**. Source one-shot finished 20 Oct 2026: 0/17 usable JSON. No active daemon, scheduler, prospective signals, trades, funding or PnL. Statistical feasibility gate failed before activation.

Files:
- `identity.json`: exact signal/historical blobs, AGENTS census, protection scope.
- `precision.py`, `evidence/precision.json`: reproducible old-ledger precision/power planning.
- `evidence/AUDIT_REPRODUCTION.json`: exact PR265 recomputation proof and relevant old rows.
- `source_probe.py`, `test_protocol.py`: bounded public GET and hermetic evidence unit tests; not a bot or strategy runner.
- `evidence/OFFICIAL_SOURCES.json`: official sources and evidence limitations.
- `evidence/source_probe_v1/`: raw public response bodies and request/receive receipts; HTTP200 HTML is NOT market evidence.
- `evidence/STATUS.json`: first freeze authority and actual final state.

Local tests: `python -m unittest discover -s research/convex_sol4h_prospective_v1 -p test_protocol.py -v`.

Planning: Python standard library, two original BASE ledgers. Source reconstruction follows artifact IDs in PR265; no new market replay. Do not open sealed 2026 outcomes, run top-level historical vendor program, rerun probe within exhausted budget, dispatch collection or merge into main.
