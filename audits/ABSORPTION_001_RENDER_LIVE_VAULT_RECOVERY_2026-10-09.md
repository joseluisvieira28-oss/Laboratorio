# ABSORPTION-FAILED-AUCTION-001 — RENDER LIVE / GITHUB VAULT RECOVERY AUDIT
Date: 2026-10-09
Workspace: `Laboratorio` (`tea-daffqvgu01pc73a9sad0`)
Source service: `tv-footprint-calibration-ingest-v01` (`srv-daqgvt0u01pc7384vsa0`)
Mode: RESEARCH_ONLY, TRADING_AUTHORITY=NONE

## Correction of earlier diagnostic
The earlier GitHub freshness audit reported **committed archive/intake stale**; that was valid for the canonical branch but **did not prove TradingView or Render was down**.
Explicitly authorized read-only Render investigation now finds real accepted `TVFP_RECEIPT` logs every 5 minutes on 2026-10-09, including receipts up to 11:00 UTC. The service is not suspended and its deployed revision remains `8e0319e7ff718ba7736f8b391a7c6810a8b71aa7`, original deploy live on 2026-09-24. HTTP POST requests from the `TradingView Webhook` user-agent were accepted with status **202**. The true operational break was **Render log to immutable GitHub Evidence Vault archival/persistence**, not a confirmed live alert outage.

Do not publish webhook request paths or tokens in logs, documentation or PRs.

## Authentic evidence recovered directly from Render app logs
Staged on `tv-evidence-vault-v0.1` with original raw `TVFP_RECEIPT` fields. Original `vault.py` independently validated each payload SHA256, immutable dedup identity and corpus hash chain; no substitute sensor and no reconstructed candles.

| UTC date | Authenticated Render receipts | Publication | Gaps |
|---|---:|---|---|
| 2026-10-02 | 175 | PARTIAL, first 09:25, last 23:55 | 113 earlier UTC-day slots unavailable in Render logs |
| 2026-10-03 | 288 | FULL-DAY archive | 0 |
| 2026-10-04 | 288 | FULL-DAY archive | 0 |
| 2026-10-05 | 288 | FULL-DAY archive | 0 |
| 2026-10-06 | 288 | FULL-DAY archive | 0 |
| 2026-10-07 | 288 | FULL-DAY archive | 0 |
| 2026-10-08 | 288 | FULL-DAY archive | 0 |
| 2026-10-09 | 133 | AS-OF snapshot **00:00–11:00 UTC**, not final daily archive | 0 inside this observed span |

Old canonical archive ended 2026-09-30. Previously committed `2026-10-01` CSV intake remained preserved but did **not** supply a full immutable daily Render receipt archive. Historical gap between old epoch and 2026-10-02 09:25 is preserved. Lost earlier Oct02 (and unarchived Oct01 authentic receipts) are **not** substituted using spot candles or synthetic footprint. Render's shorter log retention explains the source retrieval limit; any precise cause of missed archival before Oct03 cannot be confirmed merely from receiver logs.

## End-to-end verification
Read-only cross-day and SHA-chain workflow:
https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37921551326

The frozen `vault.py` source-only validation demonstrated:
- **2036 exactly consecutive** MM-V1 UTC 5-minute observations from 2026-10-02 09:25 UTC to 2026-10-09 11:00 UTC, from 175 + 6*288 + 133.
- SHA256 payloads, evidence identities, corpus SHA256, SHA256 chains, and 5-minute timestamp continuity passed for all published 2026-10-02..08 daily snapshots and the independent Oct09 partial raw receipts.
- Minimum structural lookback for `ABSORPTION-FAILED-AUCTION-001`: 2016 PRECEDING valid forward 5-minute bars. Thus **20 post-baseline bars exist as source-only candidates** as of 11:00 UTC 2026-10-09, *not* 20 approved events. First possible candidate close is 2026-10-09 09:25 UTC.
- **ZERO new primary scientific events classified or economic outcomes opened** by this recovery.
- The complete current Oct09 UTC day is not yet archived; as-of copy is stored under `tradingview_evidence_vault/recovery/` rather than falsely completing the daily archive.
- GitHub upload artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37921551326/artifacts/11612057944

## Remaining blocker: authentic canonical aggTrades join and forward re-arm
The original frozen event classifier needs, for EACH contiguous sensor bar, actual corresponding Binance **spot aggTrades** (aggressor delta and base volume), causal q95/q75 quantiles, strict 2016 forward-bar history, same event suppression and original scientific thresholds.
The old `absorption_failed_auction/collector.py` naïvely enforces continuity across the ENTIRE old plus new sensor stream and fetches Binance trades from the old terminal boundary even across the sensor blackout; rerunning unchanged on the recovered full Vault will fail due to the honest gap or waste many REST requests. It must not be forced by filling gaps, modifying thresholds or pretending the old baseline covers the new epoch.
Any transport-only recovery must explicitly **segment on true source gaps, reset the 2016-bar rolling causal baseline, verify official Binance spot aggTrades for precisely the new contiguous epoch, preserve all original locked outcomes and event boundary**, then issue a source-only integrity receipt before new prospective event classification. This must be reviewed as an engineering repair, not disguised scientific retuning.

## LICP-001 observation 2026-10-09
Canonical V03 run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37919982538 completed successfully but accrued **0 additional qualifying primary events**, durable ledger 12 accepted receipts, 10 independent BTC_CONFIRMED episodes, only 2 UTC dates. Remains `FORWARD_INSUFFICIENT` at 10/20 and 2/3 dates. No GO, no exchange mutation.

## Operational tasks still outstanding
1. Sustain immutable daily TVFP archival. The current staging-to-archive GitHub Actions workflow only runs when a `staging/YYYY-MM-DD.raw.jsonl` file is pushed; it does **not** itself poll Render. Do not claim automatic future archival is operating.
2. Authorize/engineer a real continuous durable Render-log extraction mechanism with least-privilege credentials and bounded retry/dedup; original Render logs have finite retention. No secrets should enter GitHub commits or assistant text.
3. Finish current 2026-10-09 UTC day archive ONLY after the day completes and validate against earlier partial as-of snapshot, not overwrite any immutable receipts.
4. Conduct a SOURCE-ONLY Binance aggTrades historical/archive availability and cost/volume probe before attempting a long backfill, then technical-only collector epoch segmentation. No outcomes opened.
5. Continue canonical LICP-first-20 forward observations according to existing freeze; do not invent missing episodes or claim 6->10 means an edge.

## Boundaries
NO main merge, orders, trading, accounts/wallets, authenticated exchange endpoints, Render deploy, threshold changes, or post-outcome tuning. This is evidence recovery and scientific-governance work, not financial execution.
