# CRYPTO REPO ARCHIVE MANIFEST V1 — 2026-09-16

Purpose: preserve closed / scientifically dead Wave A branch histories without rewriting scientific verdicts.

Governance:
- archive-only evidence preservation
- no live trading
- no exchange mutation
- no holdout opening
- no strategy rescue
- no merge to main
- blocked / insufficient / active lines excluded
- branch refs may only be pruned after archive reachability is verified

Archive ref target: `archive/crypto-closed-labs-2026-09-16`
Canonical base tree: main @ `5142553275e63724cfad8a9b138a4636be2f093a`
Wave A size: 33 branch refs / 31 unique HEAD commits

## Wave A frozen HEADs

| Branch | Frozen HEAD | Audit classification |
|---|---|---|
| btc-fee-pressure-v0.1 | bc7678d1b0bda5f61874fbb4781c0d4b3962284f | closed family / discovery fail |
| btc-fee-pressure-v0.2-source-remediation | 9db6e1294c74b20d57e22a5cd36af7a41a5a124b | closed family / discovery fail |
| btc-fee-pressure-v0.3-source-remediation | 76f3f3b57c01b4aa0e2c2fa7f19ecacff204d4c6 | closed family / discovery fail |
| btc-fee-pressure-v0.3-source-remediation-chunked | 14990150f1262619296288750b9850d137f8e6f1 | closed family / discovery fail |
| btc-fee-pressure-v0.4-boundary-normalization | b561de1ed62213eb755d57265a70656c956d3e70 | closed family / discovery fail |
| btc-fee-pressure-v0.5-discovery | 92f36a0655e283b1497153bdc1077bcef439efa4 | DISCOVERY_FAIL_NO_PROMOTION |
| btc-settlement-demand-v0.1 | dd2d968d67771611e8b28a3a31f87536657da488 | closed family / discovery fail |
| btc-settlement-demand-v0.2 | 1705a07575acd5e8285ed5e0196168b4357c130a | closed family / discovery fail |
| btc-settlement-demand-v0.3-discovery | 8698c5912baa76ee60f4566e96743f359dc89dc7 | closed family / discovery fail |
| btc-settlement-demand-v0.3-discovery-bindfix | 4b81125371f559c4ced8abb5fa0f063974399c52 | DISCOVERY_FAIL_NO_PROMOTION |
| mve-adx4h-01-oos-v01 | 421f642f642ce528cc3230cf35d15b80671223d6 | historical candidate superseded by failed prospective confirmation |
| mve-adx4h-01-tier1-2025-v01 | 92006662fdd844cede59b861bfdaf58c35c1e11e | TIER4_REJECTED / STONE |
| mve-adx4h-01-tier1-freeze-v01 | fe7bacfe0f8302b8913a5b4e9b97f40dff012dda | closed supporting branch |
| onchain-capflow-discovery-action-v01a | 63850e377ea1d77b57401a40c6184b7beecf3117 | MVE0_FAIL family |
| onchain-capflow-v0.1-discovery-freeze | d9af62d20cbe13ff097cd60877f6db46e96acde8 | MVE0_FAIL family |
| onchain-capflow-v0.1 | d9af62d20cbe13ff097cd60877f6db46e96acde8 | MVE0_FAIL family |
| institutional-flow-v0.1 | 4b40c006d928a5c61d89937234237a2bef07d4c0 | DISCOVERY_FAIL_NO_PROMOTION |
| macro-transmission-001-v01 | ba063e7a38d6eb0918ec4ea930767806a5d907e0 | DISCOVERY_FAIL_NO_PROMOTION |
| macro-transmission-v0.1 | c3cbdf6a8fd4240cd97224123c3da417d84f3af0 | DISCOVERY_FAIL_NO_PROMOTION |
| miner-stress-v0.1 | 5bc05e428fee0b99443e87b7252407cc69fb758a | DISCOVERY_FAIL_NO_PROMOTION |
| tf-gap-extreme-mr-30m-v0.1 | 1e8f90d0a3d5a125023ec7489ddec96cbf9e8310 | closed / discarded TF gap test |
| tf-gap-vwap-15m-v0.1 | 9ce614fa8eb57ec1e2277307d3b84b694e93b953 | closed / discarded TF gap test |
| tf-gap-vwap-30m-v0.1 | ed4801f41c39312c3a58ad4268f68efe3b74e676 | closed / discarded TF gap test |
| mve-cpi-family-01-action-once-v01 | 0fc32085aa1d92c83de4eb1fb15a683f405469da | closed CPI family evidence |
| funding-slot-diag-tmp-do-not-use | 59b57f32058424b1ca8b90ae74912d7e262f958f | duplicate/transit ref; canonical final retained separately |
| funding-slot-diag-v03-work | 59b57f32058424b1ca8b90ae74912d7e262f958f | duplicate/transit ref; canonical final retained separately |
| funding-slot-diag-v03 | 2cb425ffe99dcc11fca58288ce30ff32d3bd09a9 | superseded diagnostic ref |
| cigl-adx-01-action-v01 | 61205c7fa207c5705d275e89a92cb1e235c6d223 | Classic Indicators closed / no primary survivor |
| cigl-bb-01-action-v01 | 72e3db4c5a1c1164895a2ade88f5c68ebebfd029 | Classic Indicators closed / no primary survivor |
| cigl-vwap-01-action-v01 | e543ddc8face30350676a27e73e0e044c8e4d30f | Classic Indicators closed / no primary survivor |
| classic-indicators-gap-lab-v0.1 | b1dd1906fb1e61a372faff573997f5a92c1203ca | Classic Indicators family closed |
| options-spotperp-002-tier1-2025-v01 | 935b56dc48dd1dd8700c03e5ca7626aecb741b1f | TIER4_REJECTED |
| usd-net-liquidity-v0.1 | 4667fd652bef737953498e46b3ebae829afed09a | DISCOVERY_FAIL_NO_PROMOTION exact MVE |

## Explicit exclusions / protected lines

Not part of this archive wave: OPTIONS-SPOTPERP-001 recovery branches, ETF-CME-INSTFLOW-001, Donchian active/prospective watcher branches, PBR source-blocked lines, EMA insufficient-sample line, Coinbase-Binance Lead/Lag DATA_FAILURE, Cross-Asset Vol Stress, Crypto Edge Radar, DeFi/source-recovery lines, MSEL parent/recovery, 2025/2026 protected holdouts, and any branch marked ACTIVE/BLOCKED/PENDING/SURVIVES_DISCOVERY/CANDIDATE/INSUFFICIENT_SAMPLE/DATA_FAILURE/TECHNICAL_FAILURE/PROVENANCE_FAILURE/SOURCE_ACCESS_BLOCKED/REPLICATION_INCONCLUSIVE.

## Preservation rule

The archive commit is intentionally multi-parent: each unique Wave A HEAD is attached as a parent so its commit history remains reachable from the archive ref even if an operational branch ref is later pruned. Duplicate branch refs that share a HEAD are recorded separately in this manifest.
