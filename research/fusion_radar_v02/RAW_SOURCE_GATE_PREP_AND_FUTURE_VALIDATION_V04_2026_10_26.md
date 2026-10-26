# FUSION V0.4 — RAW SOURCE GATE + INDEPENDENT VALIDATION TRIAGE
Date: 2026-10-26. Research-only, PR #271.

## Source boundary and receipts
Operator supplied AVAX_BTC_DEV_2022_2023.json (SHA256 11b78a5c72aaaf45c06442275cb51a09bb15a0670f1936344eedaa4a04ef3f61) and AVAX_BTC_DAILY_2022_2023.csv (SHA256 38b042c4d439f8ddf2f6bc5665b24608345a765dddbc00b2f0d4f767729ad8d3). Existing CSV auditor reconciled 730 rows across the entire 2022-2023 daily UTC calendar; 568 accepted, 162 opposite/rejected; BASE14 fusion +1051.384634 bps; STRESS20 fusion -2356.615366 bps. Both sources are operator-generated, not independent exchange raw-archive custody. The uploaded JSON includes 74 distinct Binance Vision archive URL and SHA256 entries (50 daily + 24 hourly; aggregate claimed 19,042 candles). Its field source_archive_immutable_bytes=false does not make those ZIP bytes available here.

**Current raw-source verdict: NOT_VERIFIED_FROM_OPERATOR_ARCHIVES.** On the present runtime the 74 ZIP/CHECKSUM pairs are not mounted; public data.binance.vision DNS lookup fails, so no live retrieval can be claimed. A checksum entry in JSON cannot replace checking each ZIP's bytes. Do not treat source verification as complete.

The original V0.3 script included fixed 2022-2023 archive URLs, a GET-only fetch procedure, local ZIP/companion checksum parsing, UTC daily signal from D-1 vs D-21 closes and AVAX USD-M open 01:00 to open 02:00 UTC price proxy. Static trace of code confirms no explicit post-2023 source path, but cannot prove the archival market price or point-in-time receipt.

## Technical deliverable
- The branch contains `research/fusion_radar_v02/audit_fusion_source_v04.py`, independent read-only recomputation gate for all local ZIPs, SHA256 companion files, JSON manifest, exact 730 reconstructed daily signals and hourly prices versus CSV, and totals. Its successful execution must be documented with operator-generated receipt; no passing raw archive execution has yet been observed in this session.
- A second offline standalone auditor was prepared as a ZIP in the conversation: `fusion_source_truth_gate_v04.py` (more stringent calendar completeness and month/time checks) with `test_fusion_source_truth_gate_v04.py`, 8/8 synthetic offline tests PASS including tampering, missing hours, malformed close timestamps, modified gross CSV, and all 74 synthetic archives through full 730-row recomputation. V0.3's original 51/51 synthetic tests also PASS locally. **These tests validate software, NOT market outcome.**
- Both auditors require existing operator folder `historical_archives/` and the exact JSON/CSV. No raw dataset is silently downloaded, altered, used as historical hindsight correction or regarded as a previously unavailable holdout.

## Scientific blockers / severity
1. **DATA_PROVENANCE_PENDING:** genuine operator ZIP/CHECKSUM bytes, hashes and kline semantics not yet independently attested.
2. **POINT_IN_TIME_PUBLICATION_UNPROVEN:** Binance states historical archives can be revised after posting. Modern monthly ZIP hashes do NOT establish that each 2022/23 bar value/version was available at 01:00 UTC on its respective simulated trade day.
3. **NOT ORIGINAL PARENT STRATEGY:** delayed 01:00-02:00 UTC H1 trade proxy based on 20D close trend is not original CED1D-0031 AVAX20 identity, entry/exit, mark-price/funding, or actual broker fill. No realized impact, spreads, costs, margin, stop, capacity, outage reconciliation.
4. **ECONOMICS WEAK:** BASE14 PF 1.045 and +1051bps with largest-three accepted winners removal changing to -667bps; 2023 BASE14 net -1488.54bps; STRESS20 net negative. Positive incremental daily performance vs baseline is not standalone profit and random/time-shift placebos have limited independence.
5. **DATA CONTAMINATION:** Prior positive result was already viewed. No further optimization of directions, BTC lag/lookback, held hours, fee route or asset subsets; no 2024/25/26 holdout opening.

## Independent validation: preregistration planning only
- Candidate confirmatory object (NOT AUTHORIZED, not source/power passed): frozen existing member identities only; exact AVAX USD-M/BTC Spot 20D, 01:00→02:00 UTC proxy, BASE14/STRESS20 and baseline plus unrelated control.
- Genuine untouched temporal observation would be 2027 UTC or later, provided 2027 is genuinely not known when freeze finalized. The 2024-26 blocks remain protected and are NOT a new OOS test simply because labeled as such.
- Must pass source gate, point-in-time emission/receipt clock audit, independent replication of cached raw ZIPs for historical custody, pre-outcome power gate with non-outcome-based design alternative and temporal cluster variance, multiplicity accounting (all tried models incl. losers), capacity/slippage/funding and execution feasibility separately before any scientific promotion.
- Primary standalone economic bar must NOT be lowered because STRESS20 was negative in 2022-23. Relative filter superiority without positive executable standalone net edge can only justify research, not live GO.

## Verdict
**SOURCE_VERIFICATION_PENDING / RELATIVE_HISTORICAL_SIGNAL_DESCRIPTIVELY_POSITIVE / EXECUTABLE_STANDALONE_EDGE_UNPROVEN / NO_NEW_OOS_OPENED / NO_PROMOTION.**

No trading, credentials, private exchange API, main merge, Render, Windows task modification, 2024-2026 data or spend.
