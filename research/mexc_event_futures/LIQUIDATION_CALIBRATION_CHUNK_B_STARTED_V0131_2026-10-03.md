# LIQUIDATION-FLOW-FWD-001 — Chunk A verified / Chunk B started
Date: 2026-10-03. SOURCE-ONLY. No main change.

## Chunk A closeout
Verdict: CHUNK_PASS__CALIBRATION_INCOMPLETE.
Run 37123311409 attempt 1, artifact 11277529165, SHA 6371a003f0b554935c7d5fc736bd4929a3349be5.
Downloaded ZIP SHA256: cbb18ac560aead300a532f8856f03c31a4bfc5b5e88f430ac9962c0311ddd179.
All 1347 receipt evidence entries verified against bytes and SHA256.
Receipt SHA256: 3118da214715f11ffd3f1d2dce0a08d40024f34bb7e6fa21a6067195dab168b2.
Calibration bins SHA256: e1504c18a7ffd436b080952d61641736aeb816060f29d4c1d022d51e746d2224.
360 unique (symbol,minute_start_ms) rows; no duplicate keys.
UTC interval [2026-10-03T12:35:00Z,2026-10-03T15:35:00Z).
Milliseconds [1791030900000,1791041700000); finalization through 1791041705000.
BTCUSDT and ETHUSDT each: 180 healthy, 3 nonzero healthy.
Frozen merger liquidation_flow_calibration_merge_v0131.py executed locally on Chunk A only:
CALIBRATION_INCOMPLETE; conflicts=[]; raw_rows=unique_rows=360; both P95 null.
This is local source-ledger validation, not activation or a repository data merge.
research_outcomes_opened=0; mexc_subscriptions=0; threshold_computed=false; activation_allowed=false.

## Continuity and bounded Chunk B
Operational verdict: NEXT_BOUNDED_SOURCE_ONLY_CHUNK_STARTED.
Existing workflow rerun via GitHub browser; no YAML/code changes, no alternative workflow.
Run 37123311409 attempt 2, same SHA 6371a003f0b554935c7d5fc736bd4929a3349be5.
Run started 2026-10-03T16:10:56Z; job 111240266718.
Frozen tooling self-test succeeded; 180-minute source-only collection in_progress.
GitHub display retains "Chunk A": logical Chunk B identity is run+attempt, not artifact name.
Attempt 1 archive preserved separately before rerun. Never overwrite/mix A with B by filename.

Pre-dispatch continuity receipt at 2026-10-03T16:10:20.714988Z:
earliest next full minute 1791043860000 > A end + 5000.
Collector rule unchanged: B.first=((collector_now_ms//60000)+1)*60000;
B.end=B.first+180*60000; finalize=B.end+5000.
Exact B timestamps remain unverified until its receipt is available.
Gap [A.end,B.first) must be recorded as MISSING; no backfill, zero filling or imputation.
At closeout verify B.first >= A.end, exact timestamps, raw hashes, safety receipt and unique keys.
Only then merge A+B using frozen merger. No B rows counted yet.
Do not launch another concurrent liquidation chunk.

## Other families checked
OPTIONS V0.2 run 37127908110 attempt 1 remains in_progress, SHA 7b19fbeedc33cdade76314635133351ea91d3ae4.
Read OPTIONS_VOL_SOURCE_CALIBRATION_FREEZE_V02.md: >=1440 observed minutes and >=1200 valid matched-pair minutes EACH symbol; sole nearest-rank P95 abs(skew_pp); no V0.1 rows.
No rerun, merge, threshold or outcomes for Options in this continuation.

MACRO V0.1 canonical PREARM and activation freeze verified on macro research branch:
ARMED_AWAITING_FIRST_ELIGIBLE_RELEASE; UID 7d17bd53-87ad-4c74-a328-528f5e2b1e82;
2026-10-14T12:30:00Z; research_outcomes_opened=0. No runtime activation claim.

## Unchanged gates
Liquidation >=1440 healthy + >=100 nonzero healthy bins EACH symbol before numeric P95.
No MEXC outcomes, trading, orders, login, private/account/wallet endpoints, post-outcome tuning or main mutation.
