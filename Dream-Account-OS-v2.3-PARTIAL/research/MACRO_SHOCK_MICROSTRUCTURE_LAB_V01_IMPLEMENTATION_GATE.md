# Macro Shock Microstructure Lab V0.1 — Implementation Gate

Status: **PRE-HOLDOUT ONLY**

Allowed next work:
- implement the frozen contract exactly;
- add deterministic unit tests and synthetic fixtures;
- verify event-calendar reconstruction from official sources;
- verify Binance provenance/checksum handling;
- verify matched-control construction;
- verify flow-sign and continuation calculations;
- verify bootstrap/classification logic;
- run CI and fail-closed safety guards.

Forbidden at this gate:
- access to any 2026 market outcomes;
- access to MEXC Sep–Dec 2025;
- changing event families, symbols, windows, thresholds or classification rules after observing outcomes;
- adding secondary hypotheses;
- live trading or exchange mutation;
- merge to main;
- Render deployment.

Scientific rule: **correct infrastructure, never help the hypothesis survive.**

Stop after implementation + synthetic/unit-test verification. A separate explicit holdout unlock is required before any 2026 outcome evaluation.
