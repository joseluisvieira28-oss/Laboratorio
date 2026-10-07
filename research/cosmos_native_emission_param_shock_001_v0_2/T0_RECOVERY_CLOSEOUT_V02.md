# T0 source recovery V0.2 — verified closeout, 2026-10-07

Parent: bf51d602eed91d30fe3285189db3f4bf5b8eea7d.
Scope: ONLY SCRT, KAVA, OSMO, AKT 265, AKT 283, CTK 38.
Prices, returns, volumes and market outcomes accessed: NO.
main baseline verified: f263c6c6f3a57f26666a7aee28e782f2cbd08418.
No change to V0.1, event membership, direction, horizon, cost or gates.

## Result

T0_RECOVERED_THIS_ROUND: 3/6.
T0_STILL_UNRESOLVED: SCRT, AKT 265, AKT 283.
V0.2 round verdict under its frozen all-six rule:
SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED.
This is a source boundary failure, not NO_EDGE_DISCOVERY. The economic hypothesis remains untested. No Development and no restoration of the 12/12 gate.
The inherited V0.1 audit counted 6/12 certified; these three recoveries resolve three additional boundary failures, but do not constitute a new full 12-event certification.

## Recovered canonical boundaries

All timestamps and hourly mappings below are UTC. Hourly mappings are arithmetic only; no candles were fetched.

| Event | First reduced-issuance block | Canonical block time | First hourly open >= T0 |
|---|---:|---|---|
| KAVA | 7,972,058 | 2024-01-01T00:00:02.977958813Z | 2024-01-01T01:00:00Z |
| OSMO | 10,192,361 | 2023-06-21T17:16:12.668535802Z | 2023-06-21T18:00:00Z |
| CTK 38 | 17,832,434 | 2024-03-28T07:30:29.276620679Z | 2024-03-28T08:00:00Z |

### KAVA

Official archive RPC headers and block_results establish:
- H-1 = 7,972,057 at 2023-12-31T23:59:56.48099377Z: mint inflation 0.595, mint amount 122584289 ukava.
- H = 7,972,058: inflation_stop with inflation_disable_time 2024-01-01T00:00:02Z; mint inflation 0, annual provisions 0, amount 0.
- H links to H-1 by last_block_id.
Version-pinned v0.25.0 app/upgrades.go sets mainnet disable time to 2024-01-01T00:00:00 UTC; x/community/keeper/disable_inflation.go checks block time, zeros mint min/max and disables kavadist; app/app.go orders community before mint and kavadist.
Sources:
https://github.com/Kava-Labs/kava/blob/v0.25.0/app/upgrades.go
https://github.com/Kava-Labs/kava/blob/v0.25.0/x/community/keeper/disable_inflation.go
https://github.com/Kava-Labs/kava/blob/v0.25.0/app/app.go
https://rpc.data.kava.io/block_results?height=7972058

Correction to prior chat: 9,561,866 is listed as FINAL height of Kava 15 by the archive table, not its start height. The emission boundary is January 1 UTC, not an invented December 31 midnight.
https://docs.kava.io/docs/faq/historic-data/

### CTK 38

Official rpc.shentu.org returns historical execution events in finalize_block_events, with mode attributes identifying original BeginBlock/EndBlock phases.
- 17,832,432: mint inflation 14%.
- 17,832,433 at 07:30:23.301712524Z: BeginBlock mint still 14%; EndBlock active_proposal proposal_id=38, proposal_result=proposal_passed.
- 17,832,434: BeginBlock mint 10%, amount 2104012 vs previous 2945617 uctk.
Therefore proposal execution H is not the first reduced mint; T0 is H+1.
https://rpc.shentu.org/block_results?height=17832433
https://rpc.shentu.org/block_results?height=17832434

### OSMO

Archive RPC historical application state at H-1 and H shows:
- H-1 = 10,192,360: daily epoch 732, epoch provisions 547945205479.452054246575342465 uosmo.
- H = 10,192,361: daily epoch 733; provisions 182648401826.484017899543378995 uosmo.
- H execution events: epoch_end 732, mint epoch_number 732 / amount 182648401826, epoch_start 733.
- Epoch scheduled start was 2023-06-21T17:16:09.898160996Z; actual block header is 17:16:12.668535802Z.
This resolves T0 without choosing arbitrary 17:00 or using publication time.
https://rpc.archive.osmosis.zone/block_results?height=10192361
https://github.com/osmosis-labs/osmosis/blob/v16.0.0/x/mint/keeper/hooks.go

Important eligibility limitation: the observed combined double-thirdening is a 2/3 gross epoch-provision reduction. Do not silently encode it as the standalone discretionary 50% dose. A full dose/eligibility audit must retain the normal scheduled thirdening as a co-occurring component; no change to the frozen protocol is authorized here.

## Unresolved boundaries, with new primary anchors

| Event | Canonical proposal | Voting end UTC | Remaining missing evidence |
|---|---|---|---|
| SCRT | 287, PASSED | 2023-12-07T02:54:58.930543213Z | first reduced mint block/time |
| AKT 265 | 265, PASSED | 2024-08-08T16:13:48.243802688Z | execution and first reduced mint block/time |
| AKT 283 | 283, PASSED | 2025-03-14T13:25:56.642245036Z | execution and first reduced mint block/time |

Correction: March 6 in AKT 283's title is not activation. Its on-chain submission is March 7 and voting ends March 14.
AKT proposals were confirmed through multiple public REST operators. Publicnode /block at 18,000,000 reports lowest available 26,980,292; rpc.akashnet.net reports 28,478,618. Other registry RPC/REST history probes failed. These are observed endpoint limitations, not a proof that recovery is impossible elsewhere.
SCRT 287 was fetched via LavenderFive REST. The Mario archive RPC and LCD documented by Secret Network timed out; other tested history endpoints failed. No vote-end timestamp was promoted to T0.
https://docs.scrt.network/secret-network-documentation/development/resources-api-contract-addresses/connecting-to-the-network/mainnet-secret-4
https://rest.lavenderfive.com/secretnetwork/cosmos/gov/v1beta1/proposals/287
https://akash-api.polkachu.com/cosmos/gov/v1beta1/proposals/265
https://akash-api.polkachu.com/cosmos/gov/v1beta1/proposals/283

## Reproducibility and limitations

RECOVERY_EVIDENCE_V02.json contains relevant verbatim block headers, selected mint/governance/epoch events, complete proposal objects, historical ABCI responses, source URLs, retrieval timestamps and SHA256 receipts. Full raw replies are preserved locally under work/t0_evidence, including the large Osmosis epoch block_results. Repository extracts are intentionally selected events, not claimed complete raw replies. Receipts hash the full replies, not the extracts.
Public operator/official archive responses are canonical chain data, but this round did not perform independent light-client verification of application proofs.
No new events, substitutions, exchange endpoints, account reads, trading or main mutations.
