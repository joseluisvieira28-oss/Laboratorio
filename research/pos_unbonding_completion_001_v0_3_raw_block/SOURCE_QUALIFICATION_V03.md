# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — SOURCE QUALIFICATION V0.3

Date: 2026-10-07  
Branch: `pos-unbonding-completion-001-source-remediation-v0.3-raw-block-2026-10-07`  
V0.3 freeze commit: `93e0c6abff72d1d645c709382d8f06ccc558a34e`  
Parent V0.2: `SOURCE_HISTORICAL_COVERAGE_BLOCKED`  
Market outcomes opened: **NO**

## What V0.3 proved

V0.3 removed `tx_search` as a logical dependency for validating a known cohort/block. Canonical historical `/block?height=H` plus `/block_results?height=H` are sufficient to:

- obtain raw base64 Cosmos `TxRaw` bytes;
- decode `TxRaw -> TxBody -> Any`;
- identify native staking `MsgUndelegate` and `MsgCancelUnbondingDelegation`;
- validate transaction success only against the same block's `txs_results`;
- inspect later staking lifecycle events in `end_block_events` / `finalize_block_events`;
- avoid the invalid assumption that initiation and later `complete_unbonding` share a transaction index.

The cohort ledger must remain cross-block and reconcile cancellation/partial cancellation, slash effects, validator/module/ICS holds and final released principal. Expected `completion_time` is not by itself `T_completion`.

## Materiality was frozen before counts

At commit `93e0c6ab...`, before any census/count was opened:

`M_d = R_d / B_d`

where:
- `R_d` = final qualifying native principal actually released by canonical completion on UTC chain-day d;
- `B_d` = historical bonded native tokens immediately before that UTC day.

A day is MATERIAL iff `M_d >= 0.001` (10 bps / 0.10% of bonded stake).

The hard sample bar remains **>=40 MATERIAL chain-days TOTAL across >=5 chains**. It is not 40 per chain. No observed count was used to choose the threshold.

## Historical source qualification

| Chain | Historical source A | Historical source B | Fixed-height reconciliation | V0.3 source status |
|---|---|---|---|---|
| Cosmos Hub / ATOM | CitizenWeb3 archive | CryptoCrew archive | inherited V0.2 H=20,000,000 match | TWO-SOURCE FIXED-HEIGHT PASS |
| Osmosis / OSMO | Osmosis archive | Validatus archive | inherited V0.2 H=15,000,000 match | TWO-SOURCE FIXED-HEIGHT PASS |
| Kava / KAVA | Kava Labs archive | none proven | H=9,500,000 canonical only | SECOND SOURCE BLOCKED |
| Celestia / TIA | KJNodes raw archive | Numia public historical RPC | H=2,500,000 exact block hash/time/app-hash match | TWO-SOURCE FIXED-HEIGHT PASS |
| dYdX / DYDX | Kingnodes archive | Polkachu archive | H=15,000,000 exact block hash/time/app-hash match | TWO-SOURCE FIXED-HEIGHT PASS |

### New Celestia reconciliation

At H=2,500,000, KJNodes and Numia independently returned:

- time: `2024-10-06T00:47:34.967040066Z`
- block hash: `02F5FF93FBF197FFB271496D98E2F524CE15C12696C161E42D20955311F6E0F6`
- app hash: `327CCEBAB73158CEA1A4397DED49EEF7FA0D95281D4F098D0355E65AF6F2A432`

### New dYdX reconciliation

At H=15,000,000, Kingnodes and Polkachu independently returned:

- time: `2024-05-07T02:26:27.6649283Z`
- block hash: `232A1EDF008D6368DFFF915D297E2F69F98AC89CBA405343BEF3C3D62D653A90`
- app hash: `C30225F0AC948EA924D3882113A7D2175A0D243BA5D426072A45A4CED4B80F66`

A bounded raw scan of 501 dYdX blocks around H=15,000,000 completed with zero request errors and found no qualifying staking initiation in that arbitrary window. This proves raw scan operability only; it is not an event-frequency claim.

### Kava second-source result

Kava Labs served H=9,500,000 canonically:

- time: `2024-04-20T05:02:33.015922027Z`
- block hash: `A37031A071F215F108C485A46D5E59E0C382E416B4FAD07FD3BB852F2B79D591`
- app hash: `1665B5F05C3BBF2680D986313BF8FF7C3EFB8006434C5655890311EA116B83C6`

PublicNode, Polkachu, Pocket and Jjozzie no longer retain that height (their reported lowest retained heights are far later). Nodies' listed archival endpoints do not expose Tendermint `block` / `block_results` methods at the tested public endpoints. No independent second Kava historical path was proven.

## Historical enumeration result

A full census requires discovery of all qualifying 2023-2024 initiations/completions before raw-block reconciliation.

V0.3 tested three discovery layers:

1. archive `block_search` / `tx_search`;
2. ordinary public Tendermint RPC `tx_search`;
3. Cosmos Tx gRPC-gateway REST `/cosmos/tx/v1beta1/txs`, with both:
   - modern Cosmos SDK v0.50+ `query=` syntax; and
   - legacy repeated `events=` syntax.

The modern REST query was explicitly bounded by historical heights and accepted with HTTP 200 on multiple independent providers for ATOM, OSMO, TIA and DYDX, but returned zero historical rows. Kava's legacy route likewise returned zero. PublicNode endpoints explicitly require strict `tx.height = H`, which is useful only after a height is already known.

The same empty historical result appeared across multiple operators and chains. This is evidence that current public indexes do not provide the bounded historical transaction index needed for complete discovery; it is not evidence that no undelegations occurred.

Raw `/block` access can validate known heights, but exhaustive 2023-2024 discovery would require scanning millions of blocks across each chain. V0.3 did not establish a bounded, independently reconcilable, complete public census path for that workload.

## Gate status

| Gate | Status |
|---|---|
| G1 >=5 comparable production chains, version/lifecycle pinned | PARTIAL / NOT FULLY CERTIFIED |
| G2 two independent historical paths per selected chain | FAIL: 4/5 fixed-height pairs; Kava B missing |
| G3 raw initiation + actual completion reconstruction without tx_search | PRIMITIVE PROVEN; FULL CENSUS NOT PROVEN |
| G4 cancel/slash/hold reconciliation | SPECIFIED, NOT CENSUS-PROVEN |
| G5 >=40 material chain-days TOTAL across >=5 chains | UNKNOWN / NOT MEASURABLE FROM COMPLETE CENSUS |
| G6 >=12 months pre-2026 market source capability | NOT ADVANCED; parent metadata only |
| G7 receipts/firewall | PASS for executed source work |

## Receipts

Relevant GitHub Actions runs:
- `37618176798` — initial raw source probe
- `37618463162` — expanded raw source probe
- `37619119438`, `37619373220`, `37619625536` — historical indexer probes and corrected query encoding
- `37620128159`, `37620299342`, `37620414387` — final source-capability probes including Cosmos v0.50 `query=` correction

Repository receipts:
- `SOURCE_PROBE_RECEIPT_V03.json`
- `INDEXER_AND_SECOND_SOURCE_PROBE_V03.json`
- `FINAL_SOURCE_CAPABILITY_PROBE_V03.json`

No market price, volume, return, PnL, wallet/account/private endpoint, order or exchange mutation was opened or executed.
