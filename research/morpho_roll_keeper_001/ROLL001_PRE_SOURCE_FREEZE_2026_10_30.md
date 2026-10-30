# ROLL-KEEPER-001 V0.1 — MORPHO MIDNIGHT BORROWER-FUNDED ROLL INCENTIVE
PRE-SOURCE freeze 2026-10-30. Entirely isolated from prior Base Aave liquidator source-block, Polymarket PMR-002 competition, Event Futures, CONVEX and Options V2.1 failed taker/maker route.

## Why a distinct economic mechanism exists
Morpho's official BlueFallbackRolling contract lets a borrower opt in to migrate permitted Midnight debt/collateral to Morpho Blue during a time window. Anyone permitted as caller of a configured roll may receive an explicitly authorized incentive payable in the LOAN token, financed by extra debt the BORROWER assumes, within a single atomic transaction, no flashloan required. This IS NOT a free profit, arbitrage or depositor return: gas, mempool competition, configured window, liquidity, eligibility, failed tx and after-execution timing can eliminate it.
Official https://docs.morpho.org/developers/midnight/concepts/rolling-loans/
Verified interface source https://github.com/morpho-org/midnight/blob/main/src/periphery/blue-fallback-rolling/interfaces/IBlueFallbackRolling.sol
Official deployment registry https://docs.morpho.org/developers/contracts/addresses/
Official Base RPC docs https://docs.base.org/base-chain/api-reference/ethereum-json-rpc-api/eth_getTransactionCount

## Frozen chain and onchain public source
Chain ID exactly 8453 (Base). Official Base BlueFallbackRolling address 0x7bfA8207B818cc0e23a7aBdCBe56572fAbCa831F. Do not extrapolate other deployments; no alternate RPC or contract if unavailable. One public read-only RPC endpoint https://mainnet.base.org, unauthenticated JSON-RPC HTTP POST carrying only safe query method: eth_chainId, eth_blockNumber, eth_getCode, eth_getLogs and up to 3 eth_getTransactionReceipt on objectively ordered Roll logs. NEVER eth_sendRawTransaction, eth_sendTransaction, eth_call to mutate, account/keys, wallet or positions. Total request budget <= 9 (=3 header calls +4 log windows +up to 2 receipts) or <=10 if 3 receipts.
Block anchor = ONE latest eth_blockNumber sampled at start. Fixed interval [max(0, anchor-8191), anchor] — 8192 Base blocks, approx 4.5h at 2s blocks but do not claim time horizon without block timestamps. Query exactly four non-overlapping windows of 2048 blocks each, from oldest to newest; event address only; filter topics[0] in eth_getLogs request can be [SetConfig signature, Roll signature], not a wildcard. Precomputed Ethereum KECCAK-256 topics from Solidity interface (NOT NIST SHA3):
SetConfig(address,address,bytes32,bytes32,uint256,uint256,uint256,uint256,uint256,bool)
0x5a688e1dd9756a8fb6f9121f5bfb867eb485cf594652cab2a837f25c3e43d0d7
Roll(address,address,bytes32,bytes32,bytes32,uint256,uint256,uint256)
0x48b0106d0e5756564fec4b993afdd2145168802e7122df03495d5155fb5aa31e

## Strict validation and receipts
eth_chainId must be exactly 0x2105 (8453), eth_getCode contract !=0x, all 4 eth_getLogs requests must return valid arrays, every log.address exact contract, topics[0] one of fixed signatures, all blockNumbers inside expected fixed range; no silent reruns or skipped windows. Original UTC receipt times, raw response SHA256, and complete public log payloads preserved in artifact (with no wallet secrets). Event log count SetConfig/ROLL, number of positive onchain incentiveAssets decoded from Roll log's 5 ABI nonindexed words [caller, configId, debtAssets, collateralAssets, incentiveAssets]. The Roll event signature and byte schema must be validated independently in unit tests; event incentive in native loan-token base UNITS only. DO NOT guess token decimals, asset USD value, fills, tx value, or user profit. For 3 earliest-by-block/hash positive Roll events, GET original ETH transaction receipts; require success status=1 and compute native gasWei from gasUsed*effectiveGasPrice. Gas in ETH cannot be compared directly to unnormalized loan token incentive.
If no rolls in this fixed interval, ZERO_OBSERVED_ROLLS_IN_WINDOW, NOT claim protocol no events ever. If positive roll events present, ROLL_INCENTIVE_EVENT_OBSERVED_WITHOUT_NET_PROFIT, still no earning feasibility. If source blocked, SOURCE_BLOCKED_FAIL_CLOSED (no attempts to evade provider limits). Any source pass DOES NOT certify currently OPEN/active authorized SetConfig or remaining debt or destination liquidity, obtainable reward, competition or edge.
Do not select a favorable historic window, pay for RPC, lower gate or request new data after seeing outcome. No ongoing jobs or monitoring.
After any source result, economic investment threshold additionally requires witnessed eligible OPEN configuration, payment in recognized token, current borrowing/funding liquidity, actual low-risk tx simulation with realistic fee/L1 data gas, competition/MEV rates, standalone Swiss legal eligibility and operator capital budget. Trading/live / order sending / external wallet mutation PROHIBITED.

## Scientific resource policy
At most this ONE read-only public archive gate. A source-only failure cannot be rescued with a new RPC provider within V0.1. An event observed is payer evidence, NOT simulated realized net revenue. No merges to main, no MEXC or Binance account, no protected holdout or NVIDIA.
