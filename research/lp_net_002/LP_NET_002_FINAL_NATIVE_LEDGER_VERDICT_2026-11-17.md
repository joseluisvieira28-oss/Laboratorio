# LP-NET-002 — FINAL source-level closeout: reconstructed DAI/USDC NFT cashflows
2026-11-17 · **ECONOMIC_NO_LIVE_GO** · research-only, 0 CHF spent, zero orders, no wallets, no keys, no merges or production actions.

## Independent evidence and reproducibility
- Source: public published dataset ThanosDrossos/IL_Measurement pinned at commit e75c0c566116b63a68107b9f8907071c53ca8ef2; DAI_USDC_500 full CSV git blob ab68f0cf6690b57cd26e018a854b2c020947c934. Source is historical and does NOT demonstrate forward 2026 selection.
- Frozen targets selected before opening Ethereum receipts: NFT 102244, 107633 and 106475. All on Ethereum mainnet; Uniswap v3 manager 0xc36442b4a4522e871399cd717abdd847ab11fe88; pool DAI/USDC tier 500 at 0x6c6bc977e13df9b0de53b251522280bb72383700.
- GitHub CI run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44136191948, artifact 14352716099. It includes JSON receipts from both Routescan indexed records + original tx receipts and independent Blockscout v2 transaction + indexed manager log indexes, manager lifecycle indexed logs, pool Mint reconciliation, and deterministic Decimal ledger. **11 offline regression tests PASS.**
- Important genuine correction: initial source-gate implementation had wrong v3 Pool.Mint topic. Three raw pool logs from actual receipts showed topic 0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde. This was corrected, then the entry pool Mint, NFT initial transfer and manager IncreaseLiquidity validated for all 3. Do not present the earlier 0/3 identity failure as final.
- Final source counts: 3/3 position opening transactions independently cross-checked Routescan/Blockscout, exactly one canonical expected DAI/USDC pool Mint event each matching manager liquidity and DAI/USDC amounts; 3/3 successful withdrawal/collect tx independently cross-checked, exact manager logs 6/6 in Routescan original receipts and 3/3 index-pairs in Blockscout; source-indexed manager lifecycle contained 1 Increase, 1 Decrease, 1 Collect, and 1 zero-address NFT mint Transfer per tokenId, with full pagination. There may still be relevant operations NOT captured by these event filters, and coverage is from one indexer, not an independently complete full node.

## Exact native token cash flow (without ETH gas or external price assumptions)
| NFT | Mint block | Withdrawal block | Deposited DAI | Deposited USDC | Collected DAI | Collected USDC | Delta DAI | Delta USDC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 102244 | 12942153 | 12964997 | 83.923612264326 | 200.000000 | 134.941624396698 | 149.019162 | +51.018012132373 | −50.980838 |
| 107633 | 12987234 | 15092225 | 207.778545460467 | 240.000000 | 273.797637932707 | 178.376912 | +66.019092472240 | −61.623088 |
| 106475 | 12978437 | 17948957 | 98840.344613710436 | 111681.518504 | 107076.687000423094 | 108291.900781 | +8236.342386712659 | −3389.617723 |
- Liquidity Increase and Decrease raw amounts are exactly equal for each NFT; the available manager event history indicates full removal. Collect-minus-decrease yields fee excess 0.047431969984516912 DAI + 0.021948 USDC; 2.227206255322449230 DAI + 2.185467 USDC; 2430.568782964132206703 DAI + 2418.686739 USDC, respectively.
- With an **artificial DAI=USDC=1 USD at both deposit and withdrawal**, incremental inventory value versus keeping initial token balances is +$0.03717413237; +$4.39600447224; +$4846.72466371266. These match the published CSV, but are **NOT actual realized USD PnL**. Actual token prices can depart from 1 USD on different dates. HODL has the original initial DAI and USDC amounts, not a static dollar amount.

## Two-source transaction gas: actual ETH spent by whole transactions
| NFT | Mint tx gas ETH | Withdrawal tx gas ETH | Two whole tx gas ETH | Incremental return at artificial 1 USD peg, pre-gas |
|---|---:|---:|---:|---:|
| 102244 | 0.011000948 | 0.00596889 | **0.016969838** | +$0.037174 |
| 107633 | 0.013163970317363076 | 0.009178795008558976 | **0.022342765325922052** | +$4.396004 |
| 106475 | 0.018140715 | 0.002927298294138186 | **0.021068013294138186** | +$4846.724664 |
Whole transaction gas is real and independently corroborated, but which actions an LP position should bear is still an allocation decision. Historical ETH/USD must be marked at the precise transaction timestamp to value gas; entry and exit prices differ. At equal hypothetical ETH/USD price in both transactions, the rate that would completely erase illustrative gross is only ~$2.19/ETH for NFT102244, ~$196.75/ETH for NFT107633, and ~$230,000/ETH for NFT106475. Actual historical ETH spot was far above those first two thresholds (and far below the large third threshold). This is an *economic falsification sensitivity*, not realized tax/accounting PnL.

## Economic verdict
1. **TECHNICAL SOURCE VERIFICATION PASS:** opening and closing contract event location+amounts, pool identity from canonical matching pool Mint, independent indexer gas and tx identity, deterministic native-token ledger 3/3; 11/11 offline tests.
2. **FULL ECONOMIC USD PNL INCONCLUSIVE:** source does not fully establish independent DAI/USD, USDC/USD and ETH/USD marks at each transaction block, tx gas attribution (possible batching), opportunity cost, counterfactual with same inventory, or 2026 pool fee rules.
3. **SMALL CAPITAL CONSTRAINT:** under full actual entry+exit tx gas and realistic historical ETH prices, the positive at-peg excess of the two small NFTs would be eliminated. They are not a credible Ethereum-mainnet fee diamond at those position sizes.
4. **LARGE CAPITAL CONSTRAINT:** NFT106475 needs roughly 210,522 USD source initial inventory and ~742 days for only ~2.302% at-peg incremental gross versus HODL (roughly ~1.127% annualized) before gas, token risks and missed alternatives. A historical fee collector is not a generalizable pre-entry edge.
5. **NO LIVE GO / NO NEW BOT:** no independently pre-registered chronological selection signal, holdout and forward economics. No capital use authorized by this result.
6. **Next single research gate:** precise per-transaction historical token/ETH USD marks + gas attribution; then compare net LP vs same-inventory HODL and riskless cash on truly point-in-time OOS/prospective positions with all 2026 protocol fees. If independent mark sources blocked, label SOURCE_BLOCKED rather than inventing fills.

Canonical executable evidence snapshot: GitHub Actions run 44136191948, artifact 14352716099 (seven JSON files, including reconciled_native_ledger.json); expected output status SOURCE_NATIVE_LEDGER_RECONCILED, positions 3, economic_verdict NO_LIVE_GO.