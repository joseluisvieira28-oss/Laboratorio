# DEX-LIQUIDITY-PROVISION-001 — DISCOVERY ARTIFACT-LAYOUT AMENDMENT V0.1

Date: 2026-09-21
Status: TECHNICAL-ONLY / SCIENCE UNCHANGED

Canonical Discovery source run `35564286069` completed all eight economic-source shards successfully. The evaluation step failed before statistical adjudication because the evaluator expected uploaded files to retain the local directory name `dex_lp_discovery_shard_N`. GitHub Actions stored each uploaded directory's contents at the artifact root, so the evaluator found zero matching payloads.

This is an artifact-path binding error only.

Authorized correction:
- identify each shard by the immutable fields inside `shard_receipt.json` (`phase`, `shard_id`, `shard_count`);
- bind `minute_prices.jsonl.gz` and `lp_buckets.jsonl.gz` from that receipt's parent directory;
- reuse the exact eight immutable Discovery shard artifacts from run `35564286069`;
- apply the unchanged frozen evaluator and unchanged FINAL PRE-DISCOVERY protocol;
- open 2024 replication only if the unchanged Discovery verdict is `DISCOVERY_SURVIVES`.

Unchanged:
- pool, pair, fee tier and chain;
- 6H feature/outcome windows;
- LP withdrawal-score definition;
- future RV definition;
- sample floors;
- Spearman/quintile statistics;
- bootstrap seed/resamples;
- all decision thresholds;
- 2025/2026 firewall;
- no PnL/live/orders/wallets/exchange mutation/main merge.

No Discovery statistic or outcome was successfully computed before this correction.
