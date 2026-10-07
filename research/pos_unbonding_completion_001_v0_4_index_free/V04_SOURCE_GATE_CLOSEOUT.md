# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.4 INDEX-FREE SOURCE CLOSEOUT

Date: 2026-10-07
Branch: `pos-unbonding-completion-001-v0.4-index-free-census-2026-10-07`
Parent V0.3 closeout: `6cca7f9c26d10592950b51beec9f78bde12082cf`
V0.4 freeze: `71ac365e709b0e0d7074caed7e842f513207aa85`
Main baseline preserved: `f263c6c6f3a57f26666a7aee28e782f2cbd08418`
Market outcomes opened: NO

## Final verdict

**SOURCE_HISTORICAL_COVERAGE_BLOCKED**

This is not NO_EDGE. The economic hypothesis remains untested.

## What V0.4 proved

1. The index-free raw-block route is operationally real: canonical block/block_results data exposes actual `complete_unbonding` events and raw TxRaw reconstruction remains valid.
2. The historical staking queue prefix route at `0x41` cannot be treated as historical when queried through the tested subspace endpoint; V0.4.1 correctly invalidated that route after detecting future-dated queue state at an old response height.
3. A dual-independent block_search route is genuinely viable on some chains:
   - Cosmos Hub: CitizenWeb3 and CryptoCrew returned the identical ordered set of 91 `complete_unbonding` block heights in the frozen 1,024-block light window around H=20,000,000.
   - dYdX: Kingnodes and Polkachu returned the identical ordered set of 167 `complete_unbonding` block heights in the frozen 500,000-height capability window around H=15,000,000.
4. The route is not universal:
   - Osmosis: Validatus indexed completion blocks, but the other tested independent providers returned empty/non-historical indexes.
   - Celestia: KJNodes indexed completion blocks, but Numia and tested alternatives did not provide a matching second block index; Polkachu archive explicitly reported block indexing disabled.
5. The dYdX and Cosmos Hub results prove that historical complete_unbonding indexes can exist and can reconcile across independent operators. V0.3's earlier assumption that this source class was generally unavailable is therefore superseded by the narrower V0.4 finding above.

## Fifth-chain qualification

The fifth-chain order was prospectively frozen before relevant event counts.

Original V0.4 order:
- KAVA
- INJ
- SEI

No candidate proved the required two independent public/free historical paths.

V0.4.3 then prospectively extended the order, explicitly before V0.4.2 completion counts were inspected:
- AKT
- SCRT
- AXL

All three also failed two-source historical qualification in the frozen interval.

Additional Kava source-B remediation tested the independent Valopers explorer. Its chain-specific API exists, but `/blocks/9500000` explicitly returns `Block data not found for block number: 9500000`; its own frontend configuration indicates its indexed Kava history starts later than the required 2023-2024 interval. It therefore does not restore Kava Source B.

## Gate status

- G1 >=5 comparable, version-pinned production chains: FAIL / BLOCKED at fifth-chain source qualification.
- G2 >=2 independent historical paths per selected chain: FAIL for the required five-chain set.
- G3 complete census route: PARTIAL. Proven viable for some chains; not a complete five-chain 2023-2024 census.
- G4 lifecycle reconciliation: primitive proven; full census-scale reconciliation not executed.
- G5 >=40 MATERIAL chain-days TOTAL across >=5 chains: UNKNOWN and not evaluated from an incomplete five-chain census.
- G6 market source capability: not advanced to outcome values.
- G7 scientific firewall: PASS for V0.4 work.

Materiality remains frozen at 10 bps of historical bonded stake. It was not lowered and no sample gate was changed.

## Disposition

V0.4 is closed because its prospectively frozen fifth-chain universe exhausted all six candidates without establishing the required fifth two-source historical chain.

Do not add a seventh candidate inside V0.4 after completion-count evidence has been observed.

A new version may reopen only with a newly frozen source-only candidate rule created before that new candidate's event counts are inspected. Existing V0.4 source findings, including the ATOM and dYdX dual-index successes and the OSMO/TIA index failures, remain immutable evidence.

No PRE-OUTCOME analysis is authorized by V0.4.
No market prices, returns, PnL or economic outcomes were opened.
