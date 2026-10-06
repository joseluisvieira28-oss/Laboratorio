# AAVE-GOV-LT-FORCED-DELEVERAGING-001 — Source provenance progress
2026-10-06; SOURCE-ONLY / OUTCOME-BLIND; NOT A SOURCE_GATE_PASS OR ECONOMIC VERDICT.

Freeze: 54743a9200eac68c0348c280379d6bfc5c3b8ace.
Prior exact execution-time 2023–2024 lab remains terminal; its five-episode closeout is not reopened.

## Independently verified source witnesses
| Core proposal | Ethereum payload | First Core queue block | Effective block | Natural window (s) | Known base-LT reductions |
|---|---|---|---|---|---|
|55|84|19514630|19526281|142296|7|
|71|98|19620893|19628049|86436|4|
|87|112|19761838|19769002|86436|2|
|100|122|19840919|19848075|86436|2|

Four independent known 2024 proposals; 15 per-reserve reductions, NOT 15 independent shocks.
All 15 new threshold values recovered by archival collateralsUpdates() at the first Core queue block exactly match the independently acquired 2023–2024 configuration census.
Old threshold is read from pool getConfiguration(asset) at signal block minus one.
Payload 122 also changes sDAI LT from 7700 to 7800 (increase); retain source context, do not count it as a decrease.
KEEP_CURRENT sentinels remain raw, not misdecoded as enormous real LTVs.
One target on proposal 87 exposes no collateralsUpdates() ABI; retain its revert and bytecode, do not pretend full multi-action source verification is complete.

## Why first queue matters
Proposal 55 entered Core queue on 2024-03-25T23:04:47Z, before the execution-network payload queue. The full approved signal-to-effect interval is 142296 seconds (~39.53h), not the 86460s payload-timelock interval.
Other witnesses also entered Core queue one block (12s) before their payload queue. No window is chosen from borrower responses.

## Public source capability
8 alternate public archival checks: 5 PASS across 4 chains (Ethereum twice, Polygon, Optimism, Base).
Ethereum dRPC and Alchemy return the same 37-reserve ABI hash at block 21525890 (2024-12-31T23:59:59Z).
Historical parameter reads succeed on Alchemy. dRPC historical governance-log queries returned HTTP 400; a single-address filter / alternate public provider recovered 4/5 V3 queue/execution links. The remaining known 2023 event is Governance V2, not absence of a governance event.

## Outstanding source gate
Complete 2022–2025 configuration census; exact upgrade/eMode semantics; Governance V2 lineage; all related cross-chain payload clustering; >=12 independent fully defensible shocks; reconstructible pre-signal borrower universe / balances / flags / indices / oracles; behavioral-log availability without inspecting outcomes.
The four source witnesses alone do not establish historical sample sufficiency or borrower exposure.

## Runs and artifact digests
- initial capability: 37441092166 / artifact 11400389250 / sha256 11376b3b6a287e4b6edb1d8226b0dcf04ff2d24d3eac0dfba071a733895135d4
- corrected configuration census: 37441365906 (still supervised; no economic authorization)
- alternate archives: 37441517075 / 11401561807 / sha256 ad87b982871f79027ed1c963296efc100f5de827e50297b409a792006830a800
- initial lineage: 37441936274 / 11401691987 / sha256 bd2d34416c087de6d0470351a0fbc69ddb3809455518c80d08670e9fe85c0df1
- recovered lineage: 37442082107 / 11401886626 / sha256 df2b7f75635ba5f2274eaa688b0ae68ddb6230bcd3284afc184490ec005e07e3
- Core approved parameters: 37442695966 / 11402041112 / sha256 74ab1937ac4756a5065238de9c8037d28b5943b8f2208a18ddd2eca011931a70

151 initial, 12 archive-fallback, 106 recovered-lineage and 117 approved-parameter raw response hashes verified locally. Initial artifact's downloadable bytes SHA256 equals adjoined Actions upload digest only after independent checking (package-level checks recorded in the final evidence manifest).

## Safety
Economic outcomes opened = 0. Development runs = 0. 2026 outcomes closed.
No live trading/orders, operator wallets/accounts, private chain endpoints, exchange mutation or main modification.
Subjective 30/50/20 forecast is retained, not a statistical probability.
