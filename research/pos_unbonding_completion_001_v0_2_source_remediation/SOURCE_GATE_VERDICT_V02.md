# V0.2 source gate verdict

**Outcome: `SOURCE_HISTORICAL_COVERAGE_BLOCKED`.** No pre-outcome analysis freeze or Development run.

V0.2 is source-capability only, frozen for the 2023-2024 interval. V0.1 remains unchanged at `92f106cc4abb732443e8bbde353ecc0b763d84e4`; this branch derives from main `f263c6c6f3a57f26666a7aee28e782f2cbd08418`. No prices, returns, market payloads, volume values, 2025/2026 history, event counts, materiality or dose were accessed or computed.

- **Cosmos Hub:** Citizen Web3 and CryptoCrew returned the same fixed block and `block_results` digests at height 20,000,000 (2024-04-14). `tx_search`: HTTP 500 on Citizen Web3; HTTP 429 on CryptoCrew.
- **Osmosis:** Osmosis Zone and Validatus returned the same fixed block and `block_results` digests at height 15,000,000 (2024-04-17). `tx_search`: HTTP 500 at both.
- **Kava:** Kava Labs fixed block and `block_results` passed at height 9,500,000 (2024-04-20); `tx_search`: HTTP 500. Kava’s official docs identify free public historic archives and document Chainstack, but its RPC hostname failed DNS resolution during testing.
- **Celestia:** Polkachu block at height 2,500,000 (2024-10-06) passed; `block_results`: HTTP 500. StakeMe block request: HTTP 500. No independent consensus-event source verified.
- **dYdX candidate:** Polkachu block and `block_results` passed at height 15,000,000 (2024-05-07); `tx_search`: HTTP 500. Historic application version, exact `x/staking` comparability, independent source and market liquidity capability remain unverified.

The attempted `tx_search` calls failed for every tested chain. Complete lifecycle reconstruction and independent reconciliation across undelegation, cancellation, slashing, holds, validator state and actual EndBlock completion are unproven. The unchanged gates of >=5 comparable chains, >=40 independent material clusters, and >=12 consecutive months of liquid-market source capability per selected instrument remain unverified. Counts remain unknown. See `fixed_height_rpc_probes_v02.json` for request heights, timestamps, response digests, schemas and errors.
