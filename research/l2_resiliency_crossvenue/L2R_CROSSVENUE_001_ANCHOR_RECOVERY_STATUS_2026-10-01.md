# L2R-CROSSVENUE-001 — PARENT ANCHOR RECOVERY STATUS — 2026-10-01

Status: **ARTIFACT_PRESENT / RAW BYTES UNAVAILABLE TO CURRENT RUNTIME**

## Exact artifact located

Personal Library contains:
- path: `/Crypto/L2_RESILIENCY_001_SWEEP_EVENT_ANCHORS_V0_1.zip`
- size: `200205120` bytes
- created: `2026-09-19T19:38:57Z`
- Library file id: `libfile_8b4253384564819192d7299d4dd24c0b`

The adjacent authoritative preflight receipt records:
- inner CSV: `L2_RESILIENCY_001_SWEEP_EVENT_ANCHORS_V0_1.csv`
- inner CSV SHA256: `be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3`
- rows: `9181478`
- classification: `SWEEP_EVENT_PREFLIGHT_PASS`

## Runtime recovery attempts

The current runtime cannot materialize the historical Library ZIP bytes:
- direct materialization by backing file id: unavailable;
- direct materialization by stable `libfile_` id: unavailable;
- exact native-Library recovery copy: created successfully, but inherited the same non-exportable backing state;
- Files-layer upload into a dedicated Google Drive recovery folder: failed twice;
- direct Google Drive upload rejected the native Library id because it is not a connector file reference.

No regeneration and no requester-pays reacquisition was triggered.

## Scientific meaning

This is a **transport/materialization blocker**, not missing scientific evidence and not NO_EDGE.

The exact anchor artifact is known to exist and its inner CSV identity is frozen. Cross-venue Discovery remains closed until the bytes are presented to the runtime and the inner CSV independently verifies to:

`be2c2d795a55ac3522fc6f3cdeb2d2c2ccf38bef8640a505934cbc76d9337eb3`

## Other prerequisite completed in parallel

Binance 2024 timestamp/cadence preflight: PASS.

Frozen external lookup:
- first aggTrade at-or-after target;
- no interpolation;
- no backward fill;
- max lateness: **2,000 ms**;
- derived prospectively from timestamp-only global p99.9 = 1,947 ms.

2025 remains protected holdout.
2026 remains forbidden.
No outcome opening, live trading, orders, exchange mutation or main merge.
