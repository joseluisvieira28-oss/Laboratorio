# LICP-001 — LONG CALIBRATION BLOCK PROTOCOL V0.1

Date: 2026-09-26
Status: OUTCOME-BLIND COLLECTION INFRASTRUCTURE

Purpose:
Accumulate durable forward calibration evidence in long bounded blocks without opening any post-trigger price outcome.

Each block:
- runs for at most 20,700 seconds (~5h45);
- uses the frozen public liquidation collector;
- preserves raw liquidation JSONL, reconnect gap log, health receipt and SHA256;
- builds feature-only calibration summaries;
- uploads the block as a GitHub Actions artifact;
- explicitly scans raw events for forbidden outcome fields.

Forbidden in these blocks:
- MEXC SOL post-trigger return;
- entry/exit BBO;
- PnL;
- MFE/MAE;
- direction accuracy;
- any future-price label.

These blocks do NOT individually satisfy the 7-day freeze requirement.
The trigger freezer remains fail-closed until an aggregate receipt proves:
- >=7 UTC days span;
- >=250 Bybit events;
- >=50 Bybit BTC events;
- >=95% scheduled uptime;
- zero unexplained monotonic clock regressions;
- append-only raw evidence hashes and reconnect gaps.

No live trading authority.
