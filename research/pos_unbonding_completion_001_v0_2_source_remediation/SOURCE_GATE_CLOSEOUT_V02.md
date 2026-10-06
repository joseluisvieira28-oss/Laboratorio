# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 â€” V0.2 source capability closeout

**Outcome: `SOURCE_HISTORICAL_COVERAGE_BLOCKED`.** This is a new source-capability version only. It does not alter or re-judge V0.1 (`SOURCE_HISTORICAL_COVERAGE_BLOCKED`).

The V0.2 authority freeze was committed before live historical-source probes. The probe window was fixed to 2023-01-01 through 2024-12-31. No market prices, returns, market payloads, volume values, event counts, materiality, dose, or economic outcomes were accessed or computed. No 2025/2026 history was requested.

## Verified source capability

- **Cosmos Hub / ATOM:** Citizen Web3 returned block and `block_results` for fixed height 20,000,000 (2024-04-14). A separate CryptoCrew archive returned the same block response digest at that height, its initial block-results request was rate-limited (HTTP 429), then a retry succeeded with the same response digest as Citizen Web3. CryptoCrew `tx_search` was rate-limited (HTTP 429); Citizen Web3 `tx_search` returned HTTP 500.
- **Osmosis / OSMO:** Osmosis Zone and Validatus each returned the fixed block and `block_results` at height 15,000,000 (2024-04-17). The block response digests matched across providers. `tx_search` returned HTTP 500 at both providers. Thus distinct archive operators are evidenced for block provenance, but transaction-history reconciliation is not established.
- **Kava / KAVA:** Official Kava documentation identifies free public archive nodes for historic versions, including the 2023â€“2024 versions, and lists Kava Labs and Chainstack archive endpoints. Kava Labs returned block and `block_results` at height 9,500,000 (2024-04-20); `tx_search` returned HTTP 500. The documented Chainstack host failed DNS resolution during this probe. See [historic-data archive matrix](https://docs.kava.io/docs/faq/historic-data/) and [public archive endpoint list](https://docs.kava.io/docs/using-kava-endpoints/endpoints/).
- **Celestia / TIA:** Polkachu returned fixed block 2,500,000 dated 2024-10-06, but its `block_results` request returned HTTP 500. The second candidate, StakeMe, returned HTTP 500 for the fixed-height block request. Neither qualifies as a tested consensus-event source from these probes.
- **Additional candidate â€” dYdX / DYDX:** Polkachu documents its archive RPC as freely available to the public. At fixed height 15,000,000, the endpoint returned a block and `block_results` dated 2024-05-07. dYdX documentation identifies the native token as used for staking on a Cosmos-SDK-based chain. This makes it a plausible fifth chain for a later comparability audit, but V0.2 did not pin its historic application version or establish exact native `x/staking` lifecycle equivalence, an independent second source, or liquid-market capability. Its `tx_search` also returned HTTP 500. See [Polkachu dYdX archive endpoint](https://polkachu.com/partnerships/dydx) and [dYdX chain FAQ](https://docs.dydx.community/dydx-chain-technical-docs/getting-started/faq-and-resources).

The [Cosmos SDK staking specification](https://github.com/cosmos/cosmos-sdk/blob/main/x/staking/README.md) documents `complete_unbonding` EndBlock events with amount, validator and delegator attributes, and `MsgUndelegate` initiation attributes. The V0.2 probes observed fixed-height event response schemas on successful providers; they did not find or count unbonding events, infer lifecycle records, or assert that a random fixed block should contain one.

## Gate decision and stop

The source gate does not pass. Historical block access is demonstrated on several archives, but the attempted transaction-index method failed on all tested chains; full lifecycle enumeration and reconciliation across undelegation, cancellation, slashing, holds, validator state and actual completion remains unproven. The fifth-chain candidate is not yet version-pinned or comparability-qualified. The unchanged >=5 comparable-chain and >=40 independent material-cluster gates remain unverified, and no chain has a completed source-only materiality census. Twelve consecutive months of liquid-market source capability and provenance for each selected instrument also remain unverified; archive-file existence is not treated as liquidity.

Accordingly, do not create a PRE-OUTCOME ANALYSIS FREEZE and do not run Development. Unknown sample and material-cluster counts remain unknown. No rescue universe, threshold change, subset, venue switch, or outcome inspection was performed.

## Reproducibility and lineage

Fixed-height requests, endpoint/provider names, response digests, timestamps, schemas, errors, and scope assertions are in [the probe receipt](fixed_height_rpc_probes_v02.json). V0.1 remains at commit `92f106cc4abb732443e8bbde353ecc0b763d84e4`; V0.2 derives from main `f263c6c6f3a57f26666a7aee28e782f2cbd08418`. This branch is isolated; neither `main` nor V0.1 was changed.

