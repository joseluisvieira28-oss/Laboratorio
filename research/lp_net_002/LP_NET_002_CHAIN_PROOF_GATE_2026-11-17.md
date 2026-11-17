# LP-NET-002 — historical DAI/USDC v3 0.05% NFT onchain forensic proof gate
**Date:** 2026-11-17. **Parent:** LP-NET-001 PR #358 (source quality), preceding dual audit PR #357. **No trading, wallets, positions, secrets, paid data, private APIs, funds, live deployment or main merge.**

## Hypothesis and source boundary
Original published Uniswap v3 position data: https://github.com/ThanosDrossos/IL_Measurement/blob/e75c0c566116b63a68107b9f8907071c53ca8ef2/data/full/DAI_USDC_500_normalized_data.csv
Git blob SHA-1: `ab68f0cf6690b57cd26e018a854b2c020947c934`. Semicolon CSV, comma decimal, each row a **burn event**, NOT a fully audited NFT-level realised PnL. Documented original fee attribution uses paired collects and carried-forward collections; must not equate Collect amount with *fees only*. Historical source has 414 burn rows, 370 distinct position IDs, 12 duplicated event identifiers, 2 rows with negative attributed fee and historical dates before May 2022. Duplicate negative-fee example: NFT `424275`, block `16682398`, `event_feesUSD=-0.011789` occurs in **two identical keyed rows**. This is source evidence, not confirmed onchain negative fees.

## Frozen source targets — selected BEFORE opening event receipts
Ethereum mainnet v3: `NonfungiblePositionManager=0xc36442b4a4522e871399cd717abdd847ab11fe88`; factory `0x1f98431c8ad98523631ae4a59f267346ea31f984`; DAI `0x6b175474e89094c44da98b954eedeac495271d0f`; USDC `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`; declared fee tier 500 (0.05%), pool `0x6c6bc977e13df9b0de53b251522280bb72383700`.
- NFT **102244**, block **12964997**, timestamp **1628166792**; published amount withdrawn 134.894192 DAI + 148.997214 USDC, fee attributed 0.069380 USD; initialValue 283.923612 USD; **source gross apparent return vs HODL=+0.037174 USD, BEFORE gas**.
- NFT **107633**, block **15092225**, timestamp **1657153859**; published amount withdrawn 271.570432 DAI + 176.191445 USDC, fee attributed 4.412673 USD; initialValue 447.778545 USD; **source gross apparent return vs HODL=+4.396004 USD, BEFORE gas**.
- NFT **106475**, block **17948957**, timestamp **1692449783**; published amount withdrawn 104646.118217 DAI + 105873.214042 USDC, fee attributed 4849.255522 USD; initialValue 210521.863118 USD; **source gross apparent return vs HODL=+4846.724664 USD, BEFORE gas**.
These are **source assertions ONLY**. They are deliberately NOT represented as onchain-verified fee PnL or tradable edge. The big capital and very long holding periods make raw USD figures misleading.

## Implementation & trust controls
`onchain_source_probe.py` (standard library) queries bounded single known block for each NFT via `eth_chainId`, `eth_getLogs` restricted to the Uniswap NFT manager's `IncreaseLiquidity`, `DecreaseLiquidity`, and `Collect` event topics and indexed token ID; `eth_getTransactionReceipt` for corresponding transactions, and `eth_getBlockByNumber`. Verifies receipt status, block+log index agreement and CSV timestamp agreement. Binds NFT pair + tier + factory-derived pool via **pre-withdrawal** historical `eth_call positions(tokenId)` and `getPool(DAI,USDC,500)` if a public RPC supports archive calls. Failing those archive checks leaves pool identity explicitly unverified; never promoted silently.
Records actual full-tx gas used and effective price in **ETH** if available. Because transactions can aggregate other work, this is *transaction gas*, NOT proven attributable position gas. Ethereum ETH/USD price must be grounded to the historical block before converting gas to dollars.
The `Collect` event includes owed principal **and** fees. The probe does NOT try to extract fee PnL from one block and never sets a realised fee, full position PnL, or annual return. Full lifecycle from original NFT mint, increases, decreases, all collects, possible transfers, final burn, owner and token transfer receipt accounting is mandatory before an economic number.
**Source restrictions:** public no-key HTTPS RPC only; no private wallet or keys, no `eth_send*`; fixed 3 NFTs and one bounded block per NFT, bounded 12-second RPC timeout, bounded Action job 6 min.

## Observed access in current research environment
Ran the standalone local companion probe (identical fixed target set and ABI event topics) in 2026-11-17 environment with public `https://ethereum.publicnode.com`. All three NFT probes returned `URLError: Temporary failure in name resolution`, `SOURCE_BLOCKED`, `pnl_usd=null`. Not a blockchain negative result; network unavailability is not economic NO_EDGE. Seven deterministic offline ABI/event/gas tests passed locally. CI on this draft PR is configured to retry sources on GitHub's runner and preserve JSON receipt; if no verified RPC events it MUST remain `SOURCE_BLOCKED` and economic gate `NO_LIVE_GO`.

## Adjudication rules
- **GO source only** if both block event/receipt and NFT+factory identity verify, with two independent public RPC confirmations for any economically material discrepancy.
- **No economic GO** from single-block logs alone. Even a genuine `Collect` cannot separate fee vs returned principal without full history.
- **Next gate** full tokenId lifecycle + independent true flow accounting + per-position gas attribution + historical token & ETH prices at identical timestamps + HODL counterfactual + chronological untouched OOS. No retroactive data cleaning based on profit.
- **Current verdict: SOURCE_BLOCKED here / ECONOMIC NO-GO**.
