# BASE-KEEPER-001 — independent mechanism / preregistered source and economic feasibility gate
Date: 2026-10-13. Research-only. No main merge, order, wallet, account, paid API, Render or Windows change.
Distinct from prior DEFI-LIQUIDATION-SHOCK-001 (trading on price reaction), AAVE-RISK-PARAMETER-SHOCK-001 (parameter changes), DLS-POST-LIQUIDATOR-HEDGE (post-liquidation price effects). This candidate is a **primary liquidator keeper collecting contractual collateral discount**.

### Why anyone would pay
Aave permits liquidation of borrower positions under health factor 1. An independent liquidator repays debt and receives seized collateral plus an asset-specific liquidation bonus (minus protocol share). The mechanism pays participants in the liquidation itself, regardless of a price-direction forecast. Aave's Feb-2026 public report documents real liquidation volume and value transfer, but also Oracle Extractable Value competition and recapture via Chainlink SVR; gross bonuses are NOT searcher profit.

### Three economic mechanisms screened / decision
1. Prediction-market complete-set underpricing (YES+NO/<1) — reject as **duplicate / already researched**: frozen POLY-COMBINATORIAL-ARB-001 V0.8 and V0.9 contingent execution. No rebranding.
2. Centralized-exchange price-direction event trading — reject for this restart: already many overlapping fees-fragile/negative research families, no clear external economic payer.
3. **Base Aave V3 direct liquidation keeper** — SELECT source gate, no order. Incentive paid by indebted borrower as a liquidation penalty; data onchain, no API key needed for an initial source feasibility census. Small capital alone does not make actual liquidation competitive: likely competing dedicated MEV searchers, private orderflow, infrastructure.

### Pre-source gate v0.1 (before looking at current logs)
Network Base 8453; Aave V3 Pool contract 0xA238Dd80C259a72e81d7e4664a9801593F98d1c5 (verify source), event signature LiquidationCall(address,address,address,uint256,uint256,address,bool), indexed collateralAsset/debtAsset/user.
Use public https://mainnet.base.org only, JSON-RPC eth_chainId, eth_blockNumber, eth_getLogs, eth_getTransactionReceipt. One frozen window: finalized-ish tip-12 blocks back through preceding **24,000 blocks** (~13h at 2s/block), exactly 1,500 block chunks. Runtime transport budget <= 60s/35 calls to avoid abusing provider; no retries after actual event observations. If endpoint rejects historical logs, label SOURCE_BLOCKED and stop; no switching to conveniently favorable source, no data fabrication. Receipt sample up to last 20 distinct liquidations.
Data integrity: chain ID 8453, exact emitting Pool address and canonical topic, 3 indexed addresses, 128 byte data payload, unique tx+logIndex; zero malformed accepted. Count event frequency, unique liquidator count, concentration of largest and top 3, distinct blocks, gas total cost in ETH derived from receipt gasUsed*effectiveGasPrice plus any explicit l1Fee. RPC gas fields can omit L1 fee; in that case costs incomplete. No unsupported assumption of USD prices, collateral/debt value, real bonus, flash-loan premium, DEX swaps or private auction bids.
**Primary source verdict**:
- SOURCE_PASS if complete 24k-block coverage and >=1 independently valid event and at least 1 tx receipt;
- SOURCE_EMPTY if complete coverage but no events;
- SOURCE_BLOCKED if RPC/errors or incomplete coverage.
**Investability verdict always UNPROVEN** at this stage.
Precommitted stop/kill:
- If SOURCE_BLOCKED, no paid API/runner/strategies; stop at source.
- If SOURCE_PASS with 1 liquidator controlling >90% of events, classify HIGH_CONCENTRATION_BARRIER; no bot without a separate competitive-edge demonstration.
- If 0 events, no daily profit opportunity evidenced.
- Regardless of outcome, do not build a bot until **real executable net economics** (debt repaid USD, discount after protocol fee, swap quotes, flash-loan fee, gas and bids) and credible opportunity acquisition win rate are evidenced from a new preregistered untouched window.

Sources:
- Official Aave V3 overview: https://www.aave.com/docs/aave-v3/overview
- Aave liquidation stats Feb 2026: https://aave.com/blog/historical-liquidations
- Base public RPC docs: https://basehub.org/api-reference/rpc-overview/
- Aave V3 official event ABI: https://github.com/aave/aave-v3-core/blob/master/contracts/interfaces/IPool.sol
- Aave governance deployment Base Pool: https://governance.aave.com/t/arfc-adopt-the-seal-safe-harbor-agreement/23059

### Invariants
No scanner claiming gross bonus = net. No historical performance reconstruction, directional trading, broad asset backtest, paid data, fake orders, protected holdout access, live authority. This is ONE source-first one-shot decision, not a multi-week 50-gate program. Distinct retained from eight retired v0.14.4 Radar motors; active radar stays 0.
