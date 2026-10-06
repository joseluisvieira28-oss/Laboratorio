# Aave Gov LT V0.5 continuation handoff — 2026-10-06

Status: SOURCE_GATE_PENDING / historical hypothesis NOT TESTED. This is progress, not a replacement economic closeout. Original freeze 54743a92 and V0.1 SOURCE_BLOCKED closeout preserved. All economic outcomes and 2026 remain closed.

## Completed remediation evidence
- V02 source run 37450125748, artifact 11407036313, ZIP SHA256 889de600008f199aef66798c638478496a2de7211917240be76a2e9b04ef8999: public Alchemy supports historical logs in <=100-block requests; previous HTTP400 was excessive range. Pre-signal account/config/eMode getters respond. Contiguous acquisition 16490000–16639999 verified (1500 ranges, 12 config logs), not a full census.
- Corrected borrower capability run 37450841297, artifact 11407056709, ZIP SHA256 75b202247bde7a635a8d1c34e6a9783fbe662a9709e9f1f9643e38d38c66e494: historical reserve/aToken/stableDebt/variableDebt getters respond at 19620892. Selected January 2023 borrower has zero balances in the tested reserve at snapshot; this is a capability test, not an affected borrower or complete universe. Oracle/HF exposure not reconstructed.
- Ethereum 2025 run 37450651992, artifact 11405488216, ZIP SHA256 339ab29f2ded6b2c7d396e1dc6e17497b851cec90087fa4f6b2ae307498e29e6: 1987 accepted 100-block ranges, 43 configuration logs total, 13 failed ranges (HTTP429). Only 1660 ranges through 21691890 are a continuous prefix, containing 24 logs. This exact prefix has a committed source cache, not zero-fill beyond it.
- Standard batch capability run 37451041207, artifact 11405598305, ZIP SHA256 de6c1bd606723748db092dc42c173b50411d0b745dd6c7fe4a718612df8e9868: 10 independent 100-block calls accepted in a JSON-RPC batch; subsequent per-call 429 errors demonstrate compute-unit throughput limiting. Original implementation failed an assertion rather than gracefully retrying individual errors; V05 remedies that without changing science.
- SQD alternatives run 37450377105: legacy gateway requires API credentials (not used); finalized endpoint returned HTTP403. Public provider alternatives run 37451372113, artifact 11406682994, ZIP SHA256 d6fd33421d623a0f1aaeee8a35680bc99160db018e52a273b212c975fe78b6da: Llama challenge HTTP403, Flashbots gateway HTTP504, MEVBlocker HTTP403. No challenge bypass or authentication attempted.

## Active continuation
Run 37451732395, head cb77f3ec474e6618169eb5bd0fce016a1cf8e41d, workflow Aave Gov LT Sustainable Public Source V05. One-time public backfill; starts at 21691891, terminal 24136052. Two <=100-block requests per batch, >=0.6 seconds between requests, individual transient RPC/HTTP retries with backoff and Retry-After, bounded nine attempts, three-hour acquisition budget. Checkpoint and raw responses uploaded on exit. No recurring exchange/chain collector and no economic activation.

Hourly continuation checks have been configured for this run; when it completes, audit the artifact and continue only source-authorized tasks. Do not create duplicate acquisitions while active. End the continuation checks when the new cycle reaches a legitimate closeout.

## Remaining source tasks
Complete outcome-independent 2022–2025 configuration coverage including compatible prior cache, missing eMode/upgrade history, governance V2/V3 approved payload and old/new lineage, coordinated cross-chain shock clustering, then complete pre-signal borrower enumeration/balances/flags/eMode/index/oracle reconstruction. Capability successes alone are not SOURCE_GATE_PASS. Four known 2024 shocks / 15 LT reductions remain source witnesses only. Total fully defensible sample still UNKNOWN.

Need >=12 independent fully source-gated shocks. No behavioral outcomes before a separately committed PRE-OUTCOME ANALYSIS FREEZE after source pass. No subsets, lowered gates, 2026, main merge/modification, trading, orders, operator accounts/wallets, paid/authenticated chain endpoints or scientific tuning.
