# MEME-007 — REAL HISTORICAL 60-MINUTE FLOW COMPLETE (2/36 windows)

**2026-11-19 audit. Economic NO-GO, 2 of 36 frozen price-only windows independently checked for swap-count flow.** Operator supplied real SolanaStreaming hourly archive ZIPs 20261002-210000.zip and 20261002-220000.zip.

## As-of scope
- Frozen 2026-10-02 **22:37 UTC** H_REVERSAL_PRICE_ONLY price triggers: WIF/dogwifcoin and USELESS/useless-3.
- Exactly 60-min [**21:37:00**, **22:37:00**) UTC, end exclusive, **never** counting 22:37 onward.
- WIF exact mint `EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm`, pool `EP2ib6dYdEeqD8MfE2ezHCxX3kP3K2eLKkirfPm5eyMx`.
- USELESS exact mint `Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk`, pool `Q2sPHPdUWFMg7M7wwrQKLrn619cAucfRsmhVJffodSp`.
- Raw match: `swap.ammAccount` to frozen pool, `baseTokenMint` to frozen mint, `quoteTokenMint` to WSOL, swapType buy/sell, blockTime in window. Unique signature per swap in matched data; no mixed direction or duplicated signatures.

## Actual observed original MEME006 60m buyer-count subgate

| Exact pool | Buys first 23m | Sells first 23m | Buys last 37m | Sells last 37m | 60m buys | 60m sells | Unique swaps | Subgate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| WIF | 49 | 11 | 112 | 19 | **161** | 30 | 191 | **PASS** (buys>=sells and >=20 swaps) |
| USELESS | 56 | 12 | 8,905 | 10,468 | 8,961 | **10,480** | 19,441 | **FAIL** (sells exceed buys by 1,519) |

**Both observed 60-min windows were completed**, total 19,632 unique signatures. 22h reread reproduces *exactly* prior pilot's 112/19 WIF and 8,905/10,468 USELESS. Each pool's sourceExchange is Raydium. These are blockchain archive-derived swap records, not client orders or executable PnL.

### Adversarial flow/volume
- WIF: 20 unique recorded wallet addresses across sides, 11 buying, 13 selling (some overlap). The top buying wallet did **131/161 = 81.37%** buys, plus three sells. Excluding that **entire wallet** as a sensitivity leaves **30 buy swaps vs. 27 sell swaps** across 57 trades, so still PASS but with much smaller imbalance +3. This is NOT an original policy filter and not proof of manipulation.
- WIF source USD buy volume **$34,347.07**, sell **$5,279.18**. USELESS source USD buy volume **$826,928.74**, sell **$817,786.86**: larger buy **value** despite more sell **transactions**. The frozen policy is count-based. Do not retrofit a value-based rule.
- USELESS distinct addresses: 3,042 overall, 2,727 buy and 2,436 sell.
- These are `walletAccount` address counts, not proofs of economically independent people.

## Auditable file hashes and coverage
- 21h ZIP SHA-256: `06d0817f6ae6a588608151005036ebbdaa42f009acb265b70a738585d7da7b96`.
- 21h swaps log SHA-256: `2bbb6a2abd99c240bbc4b15240e818af4936a28fc79df2cdd5b3225ae0cb0319`, **1,181,480 valid JSON records**, no parse errors.
- 22h ZIP SHA-256: `7d6cda072dddeb49e7955404e77179c0c0a6aceb2e502c5b5f73d95050d3c65e`.
- 22h swaps log SHA-256: `5870d3a9000a180b5b4b4299cdc8ec87655253e461e207e7025286289d86b0bc`, **1,325,407 valid JSON records**, no parse errors.
- Total 2,506,887 source swap records scanned. Only 19,632 in exact target pools in 60min. All hourly source records had minor seconds around clock boundaries: time filter used each record's `blockTime`, **not ZIP filename**.
- Frozen 36 price windows SHA256 `bde40bdcf898bca8354a005594b8f3cf0cd5d81577ac90f5517034af1f948b2f`.
- Structured 60m audited JSON SHA256 `297d993a99e5cc7d2494445bc82f5d63dbd0c462f973442f087ee05011d30ee4` (retained in operator chat; raw archives not committed).
- Exact pool checks 0 duplicate signatures, 0 conflicting direction, 0 missing wallet and 0 missing USD value within matched pool swaps.

## Outcomes are price-only, not realized trades
- WIF 4h **+1.701115%** gross historic close-price, 24h **+4.125388%**; after *hypothetical fixed 2.5 percentage-point* cost **−0.798885%** / **+1.625388%**.
- USELESS 4h +0.355075%, 24h +6.774071% gross; after same stress −2.144925% / +4.274071%. **USELESS failed the flow filter** and cannot be counted as an eligible signal.
- Price patterns were obtained from **closed hourly candles**, not actual DexScreener rolling h1/h6 at 22:37. Historic 24h metrics, pool age, liquidity >$150k, cross-source source-price reconciliation, Raydium marketable quotes and fills NOT reproduced.

## Economic gate
**Scientific GO for this narrow 60m-flow reconstruction (2/36 only); full MEME006 historically INCONCLUSIVE. Economic and real-capital NO-GO.** WIF count-only pass is a **single selected historical event**, not evidence of a statistically significant tradable advantage. 34 frozen candidate windows lack historical flow audits. No adjustments to frozen MEME006 main prospective runner, no private keys, wallet funds, trades or payments.

Report in operator chat: `MEME007_20261002_2137_2237_VERDICT.md`, structured result `MEME007_20261002_2137_2237_full_hour.json`. Do not publish raw SolanaStreaming archives or individual wallet addresses.
