# TV EVIDENCE VAULT — RENDER LOG RECOVERY / 2026-10-09 HANDOFF

Source service: Render workspace `Laboratorio`, service `tv-footprint-calibration-ingest-v01` (`srv-daqgvt0u01pc7384vsa0`); TradingView MM-V1 / BINANCE:BTCUSDT / UTC 5m; research only, no exchange operation.

## What was fixed
The Render webhook receiver is **LIVE** (authentic TVFP_RECEIPT app logs and HTTP 202 webhook deliveries on 2026-10-09). GitHub daily vault archiving had stopped after 2026-09-30. Original Render messages were recovered using read-only service logs, WITHOUT seeing or copying webhook tokens.

Existing original `tradingview_evidence_vault/vault.py` validated actual payload SHA256, key identity, dedup/conflict, hash chain and continuity, then generated committed daily archives from raw staging. No 5m observation was synthesized from Binance prices.

## Immutable restored daily snapshots
`tradingview_evidence_vault/archive/YYYY-MM-DD/` now holds:
- 2026-10-02: **175 authentic observations**, 09:25-23:55 UTC, partial earlier coverage not retrievable.
- 2026-10-03 through 2026-10-08: **six complete consecutive UTC days**, 288 valid bars/day, zero gaps.
- 2026-10-09: NOT finalized as UTC day. An immutable `recovery/2026-10-09_ASOF_1100UTC_RAW_TVFP_RECEIPTS.jsonl` snapshot covers 133 verified 5m receipts through 11:00 UTC. It is NOT a substitute for final day-end archive.

The 175+1728+133 = **2036 consecutive receipt spans** have been validated from Oct02 09:25 through Oct09 11:00 UTC. This is source-only; it allows at most 20 first candidate event bars after an exact 2016 valid-predecessor baseline, and does not mean 20 true events.
Proof: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37921551326
Receipt artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37921551326/artifacts/11612057944

## Critical source gap
Previously preserved 2026-10-01 CSV and old September evidence are distinct earlier segments, separated from Oct02 09:25 by missing immutable Render receipts. The frozen `ABSORPTION-FAILED-AUCTION-001` requires 2016 IMMEDIATELY PRECEDING VALID FORWARD BARS; never silently bridge the gap by resampling, filling, replaying fabricated footprints or using old 2016 bars.

## Continuing daily archival
The existing `.github/workflows/tv-evidence-vault-staged-archive.yml` is **not** a cron-based Render exporter; it runs only when a `tradingview_evidence_vault/staging/YYYY-MM-DD.raw.jsonl` file is committed on this branch. A successful GitHub Actions run on static old data does not mean ongoing source capture.

Until a least-privilege recurring exporter is configured, an operator must:
1. Fetch yesterday's complete UTC day `TVFP_RECEIPT` Render logs through authorized workspace access **before log retention expires**.
2. Preserve original receipt JSON and received_at; never print/send the secret webhook URL.
3. Dedup only exact same-key payloads. Conflicting receipts must fail closed, not pick latest.
4. Verify expected full-day count 288 with first close 00:00 and last close 23:55 UTC when applicable. Publish partial only with an explicit partial coverage warning.
5. Commit `staging/YYYY-MM-DD.raw.jsonl` on this Vault branch. Existing CI archives daily and hashes permanently. Validate generated manifest.
6. Never overwrite an immutable daily snapshot; corrections need separate explicit revision and audit.
7. If a prospective source gap occurs, preserve it and restart the **frozen** 2016-bars causal lookback only after uninterrupted valid data resume.

## Pending source join
BTCUSDT Binance spot aggTrades 2026-10-02..08 public daily ZIPs SHA-256 verified in an independent source-only workflow: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37922287209 — **7,091,269 trades**, **1903 verified matched Vault bars**, no future economic outcomes. The 2026-10-09 partial bar stream additionally requires bounded official public API verification; its classifier status must be taken from the immutable current run, not assumed.

No main merge, live orders, trading authority, private exchange endpoints, wallets or outcomes were opened by this recovery.
