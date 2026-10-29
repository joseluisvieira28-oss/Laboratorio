# Joint source gate closeout — 29 October 2026
**SOURCE_INCOMPLETE / NO_OUTCOME_PROTOCOL / JOINT_MECHANISM_NOT_TESTED / NO_EDGE_ESTABLISHED**

## Executed result
All six free public Bybit/Tardis files for the already-open 2026-04-01 Discovery day were fully downloaded, gzip parsed and hashed:183,596,149 compressed bytes,7,945,015 rows.
All six computed MD5 values match provider x-md5; independent SHA256 receipts are retained. Trades and book sources each cover1440/1440 local UTC minutes. No negative event-to-collector lags or local-timestamp regressions.

|Source|BTC rows|ETH rows|BTC p99 lag|ETH p99 lag|Frozen mechanical gate|
|---|---:|---:|---:|---:|---|
|Aggressor trades|2,089,768|2,393,167|126.748ms|151.688ms|PASS|
|Top5 book snapshots|1,866,426|1,593,323|39.858ms|39.662ms|FAIL timestamp boundary|
|Forced liquidations|1,318|1,013|538.018ms|536.148ms|Record schema/timing PASS; continuity unproven|

## Exact blockers, without overstating source defects
1. Freeze e276595f47d905fab20a09b3dbb5a1722b9e370d required every exchange timestamp inside April1 UTC. The first six book records per asset arrive just after midnight but carry exchange timestamps just before it (BTC up to114ms before, ETH up to218ms before).
   Detailed diagnostics found ZERO nonfinite/nonpositive levels, ZERO crossed/locked books, ZERO sorting or identity defects. This looks consistent with day-boundary capture/arrival semantics, not demonstrated book corruption. Nevertheless it fails the literal frozen rule. No lines dropped, boundary exception, tolerance or gate relaxation was applied after seeing it.
2. Normalized liquidation CSVs do not establish capture continuity through zero-event intervals. There is no heartbeat/disconnect/sequence ledger in these files.193 BTC and166 ETH minutes have liquidation records; the remaining minutes are UNKNOWN, not certified healthy zeros. Longest inter-event gaps are about80.13min and71.41min; they may be quiet intervals and cannot be labelled outages from event absence alone.
3. Reconstructed top5 depth measures displayed liquidity, not separately identified cancellations, and no causal cancellation mechanism is established.

Thus the candidate archive is demonstrably available and temporally alignable at record level; the **joint gate as frozen did not pass**. This is a scoped gate failure, not proof that all public sources are impossible or that this joint mechanism has no predictive effect.

## Transport and reproducibility
Preliminary HEAD requests returned404 despite GET206 success: retained both receipts, did not declare unavailable on HEAD alone.
Full GET and the initial block-transfer attempts were interrupted after slow/stalled progress. Resume completed all files; there is NO remaining transport blocker in the final verdict. Partial bytes were not treated as complete sources.
Implementation evolved only for transport/resume, not quality thresholds, dates, symbols, economic outcomes or selection.
Run from an empty working folder with pandas/numpy:
- python joint_source_gate.py
- python joint_validate.py
- python joint_book_diagnostics.py BTCUSDT
- python joint_book_diagnostics.py ETHUSDT
The final validator supports cached complete files. Python compilation passed for the executed source scripts; real-file hash/schema/timing checks and independent BTC/ETH defect classification were run. No synthetic tests are substituted for source validation.

## Economic verdict and next scientific requirement
The requested directional exploratory study was conditional on source PASS. Therefore **no outcome protocol was activated and no directional outcome join/study was executed**.
Economics for the new joint mechanism are NOT_TESTED, not a negative empirical edge verdict.
Prior LICP NO_EDGE and ATI Discovery limitations remain binding, see JOINT_MECHANISM_AUDIT_2026-10-29.md. No fee change, direction reversal, selected winner or alternative horizon was used to rescue either.
Before a new joint study, establish a public-source continuity/incident record and explicitly predeclare day-boundary snapshot handling in a separate source-only freeze. This would be source remediation, not permission to relabel this failed gate PASS. Preserve this result. Then and only then freeze incremental joint conditioning and component comparisons before outcomes.
Real Event Futures economic claims would additionally need actual direction/time-dependent payouts and exact entry/settlement semantics; hypothetical q sensitivity is not PnL.

## Evidence and controls
See joint_v01/joint_source_validation.json for all six complete SHA256/MD5/bytes/rows/timing receipts; joint_book_defects_BTCUSDT.json and joint_book_defects_ETHUSDT.json identify exact offending rows.
No September2026 source/holdout requested,0 new outcomes joined,0 orders/accounts/private exchange requests/wallets/payments/deployments. No scheduled workflow or Actions run triggered by this task. Only this new research branch written; no main write or merge.
Provider files remain local; public GitHub contains hashes and diagnostics, not redistributed raw archives.
