# LP-NET-002 — Verified independent receipt cross-check and economic diagnostic
Date: 2026-11-17. **RESEARCH_ONLY; ECONOMIC_NO_LIVE_GO; 0 CHF spent, 0 orders.** PR #360 stacked above #358.

## Source and evidence authority
- Original source CSV: https://github.com/ThanosDrossos/IL_Measurement/blob/e75c0c566116b63a68107b9f8907071c53ca8ef2/data/full/DAI_USDC_500_normalized_data.csv ; Git blob SHA1 ab68f0cf6690b57cd26e018a854b2c020947c934.
- Routescan indexed Ethereum historical manager logs + transaction receipts: GitHub run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44132632481 , artifact 14351495379 (all 6 manager log indexes, topics, data and block hashes match corresponding successful tx receipts); replicated in run 44133892181, artifact 14350383530 (6/6).
- Independent Blockscout v2 tx and transaction-log index cross-check: same GitHub run 44133892181, artifact 14350383530. Both sources agree 3/3 tx hashes, blocks, gas used and gas prices, and 3/3 manager log-index pairs. Two **indexers**, not independent archive full-nodes or NFT full-lifecycle reconstruction.
- Ethereum mainnet Uniswap NonfungiblePositionManager 0xc36442b4a4522e871399cd717abdd847ab11fe88. Declared pool: Uniswap v3 DAI/USDC tier500 (0.05%), 0x6c6bc977e13df9b0de53b251522280bb72383700. Historical positions(tokenId) archive eth_call via no-key Routescan returned NOTOK for all 3 (run 44133080405); identity at this historical block is **NOT YET CONTRACT-VERIFIED**.

## Three empirically matched withdrawal transactions
| NFT | Block | Transaction hash | Manager event indexes | Decrease DAI/USDC | Collect DAI/USDC | Collect minus decrease DAI/USDC |
|---|---:|---|---|---|---|---|
| 102244 | 12964997 | 0x3b058c2b32cbad853282fc6a4c4e19e4ab8407ae617c96c55b12a2a631c55d92 | 276, 280 | 134.894192427 / 148.997214 | 134.941624397 / 149.019162 | 0.047431970 / 0.021948 |
| 107633 | 15092225 | 0x710bcc27d0cf34657dc68816752c9b0804dc3e08075105abebe39e446cebb723 | 201, 205 | 271.570431677 / 176.191445 | 273.797637933 / 178.376912 | 2.227206256 / 2.185467 |
| 106475 | 17948957 | 0x5c2b52327b1933bfd72cd24bfabb7089cb43960c364d3e9536041386eb9fab7c | 272, 276 | 104646.118217459 / 105873.214042 | 107076.687000423 / 108291.900781 | 2430.568782964 / 2418.686739 |
The within-transaction Collect-minus-Decrease amounts match the original publisher's attributed fees after rounding. This is **not full lifetime fee accounting**; Collect can combine principal and accrued fees, prior collects and owed tokens remain unknown.

## Actual whole-transaction gas independently corroborated
| NFT | gasUsed | effectiveGasPrice wei | gas in ETH | Published gross above HODL before gas in USD | ETH/USD at which entire exit-tx gas alone erases that gross |
|---|---:|---:|---:|---:|---:|
| 102244 | 221070 | 27000000000 | 0.005968890 | +0.037174 | 6.23 |
| 107633 | 221068 | 41520233632 | 0.009178795008558976 | +4.396004 | 478.93 |
| 106475 | 221094 | 13240062119 | 0.002927298294138186 | +4846.724664 | 1655698.93 |
**IMPORTANT:** full transaction gas is not necessarily position-attributable gas. Initial mint/increase gas, intermediate costs and independent full position cost accounting NOT verified.

## Approximate daily-price sensitivity only, not a measured investable LP PnL
Daily historical ETH/USD snapshots (NOT transaction-time marks): Aug 5 2021 2827.33 USD (https://coinmarketcap.com/historical/20210805/); Jul 7 2022 1237.59 USD (https://coinmarketcap.com/historical/20220707/); Aug 19 2023 1669.47 USD (https://coinmarketcap.com/historical/20230819/).
| NFT | Initial USD (publisher) | Held days (publisher) | Gross USD above HODL (publisher) | Whole exit tx gas USD approx | Gross minus whole exit tx gas (only scenario) |
|---|---:|---:|---:|---:|---:|
| 102244 | 283.923612 | 3.610 | +0.037174 | 16.8760 | −16.8388 |
| 107633 | 447.778545 | 332.071 | +4.396004 | 11.3596 | −6.9636 |
| 106475 | 210521.863118 | 741.945 | +4846.724664 | 4.8870 | +4841.8376 |
Large NFT source fee+IL gross (not true net) is +2.302% over ~2.03 years or ~1.127% annualized **before** entry costs, opportunity costs, swaps, risk and 2026 protocol fee rule changes. The two small position examples fail after full exit gas under the historical daily ETH/USD scenario; not proof for a lower-fee L2 or alternate setup.

## Economic and scientific closeout
- Event receipts and transaction gas: **SOURCE_VERIFIED_TWO_INDEXERS**, 3/3 txs, six event locations; Routescan ABI fields+receipt proof and Blockscout independent tx metadata/index locations.
- NFT historical pool identity: **SOURCE_BLOCKED** on archive state eth_call; original publication labels DAI/USDC tier 500 but the onchain position state remains unproved.
- Full NFT opening-to-close ledger: **NOT COMPLETED**. No historical mint/increase, prior collects, owner transfers, gas by position, token USD as-of and HODL reconciliation. Single exit gas is NOT full cost.
- Economic GO: **NO**. No positive OOS decision rule, no 2026 forward PnL or executable profit. Do not open trades.
- Next exact gate: full manager log history + complete cashflow matching by NFT, pool mint/burn identity and gas, real historical exchange rates, then frozen prospective selection on independent dates.