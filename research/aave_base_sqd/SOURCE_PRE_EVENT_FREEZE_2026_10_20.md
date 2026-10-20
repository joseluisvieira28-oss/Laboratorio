# AAVE-BASE-DIRECT-LIQUIDATION-BONUS — SQD SOURCE RESCUE FREEZE V0.1
2026-10-20 UTC. **COMMITTED BEFORE ANY SQD CONTRACT EVENT RESPONSE**.
Research-only, no economic outcome and no order. Distinct source transport from the frozen FAILED Aave Base keeper V0.1/V0.2 RPC eth_getLogs tests in PR #205; scientific hypothesis remains direct liquidator bonus, NOT the already-negative LICP cross-venue price continuation.

## Named payer, lawful mechanism and hard limits
Borrower eligible for liquidation with HF < 1 bears reserve-specific collateral liquidation bonus: liquidator repays actual debt, receives collateral including protocol-defined incentive. Not necessarily net profitable, not automatically obtainable by ordinary users: MEV/front-running, private bundles, transaction revert gas, flashloan premiums, pre-trade pool liquidity and nonce/latency can cost more than gross discount. Aave Base V3 pool address: 0xA238Dd80C259a72e81d7e4664a9801593F98d1c5 from official Aave Address Book. Topic0 exact Aave LiquidationCall(address,address,address,uint256,uint256,address,bool): 0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286. Event abi indexes collateral, debt, borrower; payload uint256 debtToCover, collateralLiquidated, liquidator, receiveAToken.

## Pre-source window / source gate (NO selection after seeing events)
**Dataset** SQD public Base `https://portal.sqd.dev/datasets/base-mainnet/stream` (no RPC, no auth).
**Frozen base range** block 33,000,000 to 33,099,999 inclusive, divided into four consecutive nonoverlapping 25,000-block partitions, 33000000–33024999, 33025000–33049999, 33050000–33074999, 33075000–33099999. This fixed archival range should predate 2026 but MUST be checked via returned block timestamps. If outside 2025, fail closed and do not silently choose alternative. NO protected 2026 outcome data.
**Public POST** only, documented SQD stream request: type=evm, fromBlock/toBlock exact, fields block.number/timestamp and log.address/topics/data/transactionHash/logIndex. logs filter only official Aave Base V3 Pool and LiquidationCall topic0. No other DeFi venues or wallets.
**Source gate success** all four responses 200/parseable NDJSON/allowed schema, boundary marker exactly toBlock for each partition, no out-of-range events, no duplicate block+logIndex, valid event topic/address and 4 topics + 128-byte ABI data, first and last boundary headers in 2025 UTC, all bytes archived per SHA256, count samples and distinct liquidator addresses. Blocks that contain no event do not count as zero source quality; SQD streams sparse blocks and a terminal block header sentinel, so require exact final boundary header. Any failure = SOURCE_BLOCKED, NOT ZERO EVENTS/NO EDGE.
**Output** only source-count census, unique liquidator pseudonymous SHA256 digests, timestamps, hashes and integrity metrics; DO NOT convert debt or collateral into USD, infer bonus%, compute "profits", rank winners, or infer actual accessibility. Names/raw wallet IDs are not printed or committed. Raw public response bytes preserved only within GH Actions artifacts, which may be accessible publicly in this public repo.

## Next gates NOT authorized to open during source scan
G2 only after source PASS, NEW explicit pre-outcome economic freeze: same-block per-reserve liquidation incentive and protocol fee, gas actually consumed (including failed attempts if measurable), loan notional, contract decimals/chainlink price, DEX executable unwind, flashloan fee, actual capital and competitors' realized net. First identify whether any net surplus could exist for different notional sizes; do not assume 5% generic bonus, no extrapolating fee=0. Must distinguish historically claimed by dominant keeper from economically accessible opportunity to a new entrant. If account/mempool data unavailable, ECONOMIC_ACCESS_UNPROVEN; no bot coding.

Sources (public):
- Aave V3 Base official addresses: https://github.com/aave-dao/aave-address-book/blob/main/src/AaveV3Base.sol
- Aave event ABI: https://github.com/aave/aave-v3-core/blob/master/contracts/interfaces/IPool.sol
- Aave bonus mechanics: https://www.aave.com/docs/aave-v3/smart-contracts/pool-configurator
- SQD Base / stream: https://sqd.dev/chains/base/ ; https://sqd.dev/solutions/analytics/
- Prior transport failure: https://github.com/joseluisvieira28-oss/Laboratorio/pull/205

## Controls
Exactly four fixed public requests; no retries, no market price read, no 2026 protected holdout, no login/account reads, no wallet, no flashloan transaction, no exchange API mutation, no capital spend, no Render, no main merge, no source-driven tuning. A green CI is not an economic PASS. Report definitive source status without relabeling SOURCE_BLOCKED as NO_EDGE. No automatic future retries.
