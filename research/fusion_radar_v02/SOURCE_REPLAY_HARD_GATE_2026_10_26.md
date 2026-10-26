# FUSION AVAX20 x BTC20 — SOURCE GATE + ADVERSARIAL SCIENCE CLOSEOUT
Date: 2026-10-26 | PR #271 | research-only | No main merge or exchange activity

## Source inputs genuinely reviewed this turn
Uploaded operator files:
- `AVAX_BTC_DAILY_2022_2023.csv`: SHA256 `38b042c4d439f8ddf2f6bc5665b24608345a765dddbc00b2f0d4f767729ad8d3`
- `AVAX_BTC_DEV_2022_2023.json`: SHA256 `11b78a5c72aaaf45c06442275cb51a09bb15a0670f1936344eedaa4a04ef3f61`
- Original prior V0.3 Python code reviewed from the delivered ZIP. 730 daily observations, 74 manifest archive entries, 74 unique URLs; source archive bytes **NOT UPLOADED** in this session.

The original script fetches monthly ZIP+CHECKSUM and checks their SHA256, exact expected archive member, required time-aligned close clocks and period boundary, then computes closed-daily AVAX20/BTC20 sign and AVAX futures H1 OPEN(01:00)-OPEN(02:00) proxy. The approach is causally delayed by construction but **historical monthly ZIP publication and revisions do not establish a 2022-23 point-in-time executable record**.

A standalone, independent Python stdlib source/ledger verifier is now in `research/fusion_radar_v02/audit_fusion_source_v04.py`. It does **not download** or access the account, 2024-2026, Render or Telegram. It reads EXACTLY the 74 2021-12 to 2023-12 cached archives already on the operator Windows machine, verifies ZIP bytes against local .CHECKSUM, reconstructs all 730 daily signals and 01:00-02:00 price gross from raw CSV rows, checks every uploaded operator CSV value, and reconciles BASE14/STRESS20 aggregate ledger totals and full source manifest. Fail-closed on missing/incorrect prices or identifiers. No new economic selection rule.

**Crucial limitation:** the script was committed to GitHub and fetched back successfully but has NOT run against the operator's 74 genuine raw ZIPs in this assistant environment (network DNS blocked, raw files not attached). Six related synthetic local fixture regressions passed for the longer independent verifier (including deliberate hash/gross/side/source-corruption cases). Do not count this as official source PASS, independent replay PASS, profitable edge, or remote CI PASS.

## Historical economic verdict preserved
Original BASE14 baseline -2270.57bp, Fusion +1051.38bp over 730 daily opportunities. STRESS20 Fusion -2356.62bp, meaning no standalone robust profitability.
2022 BASE14 Fusion +2539.92bp (299 trades); 2023 BASE14 Fusion -1488.54bp (269 trades).
568 Fusion accepted trades; 162 excluded. Accepted +1.851bps/trade BASE, -4.149bps/trade STRESS, break-even observed gross ~15.851bps of total RT fee/friction.
Long accepted -1176.62bp, short +2228.00bp BASE; after removing 3 largest accepted winners, accepted total -667.42bp. Not a valid rationale for post-hoc SHORT-only selection.
Matched 30k random year+direction selections: upper-tail ~1.63%, but 2023 upper-tail ~31.66%, conditional on exposures and exposed history. 50k circular year-wise BTC context shifts: tail ~8.64% for alternate shifts; no evidence that the exact timing is uniquely valuable. Block bootstrap L30 95% intervals: Fusion BASE daily mean [-6.40,+9.99]bp and incremental advantage vs baseline [+1.60,+7.67]bp, conditional/exploratory; not multiplicity-corrected or independent OOS.
**2024, 2025, 2026 remain protected and unopened.** Shifting BTC using future data is an adversarial diagnostic only, not a legal alternative strategy.

## Operator runbook (Windows, no network)
Place `audit_fusion_source_v04.py` next to the existing `historical_avax_btc.py` in the historical V0.3 folder. Keep downloaded archives in `historical_archives/` and put both operator report files in `results/`:
```powershell
py audit_fusion_source_v04.py --archive-dir historical_archives --csv results/AVAX_BTC_DAILY_2022_2023.csv --json results/AVAX_BTC_DEV_2022_2023.json --receipt results/FUSION_SOURCE_AUDIT_V04.json
```
Require exit code 0 and `LOCAL_ARCHIVES_AND_CSV_REPLAY_MATCH` with 74 verified local ZIPs and 730 price-reconstructed days. If anything fails, **stop**; do not patch data or cherry-pick dates. User can upload the receipt without uploading 74 raw ZIPs.

## Decision
RESEARCH_MECHANISM_CLUE / SOURCE_REPLAY_PENDING_OPERATOR_BYTES / NO_NET_EXECUTABLE_EDGE / NO_STANDALONE_LIVE_GO / NO NEW MODEL VARIANTS.
No legitimate independent historical test can be claimed without a genuinely untouched dataset and a freeze made before seeing its outcomes. Avoid claiming a 2024/25/26 block is still virgin without explicit scientific custody review. The historical 2022-23 period is now exhaustively exposed for this hypothesis, so its positive comparisons remain descriptive.
