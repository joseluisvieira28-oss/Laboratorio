# MEME-007 — 25 Oct 2026 00:37 UTC: 2 historical momentum flow windows (FULL 60m)

**19 Nov 2026 audit. Read-only, archived SolanaStreaming provider-decoded swaps. Economically NO-GO. Original MEME006 main prospective workflow unchanged.**

## Frozen event identity
- `H_MOMENTUM_PRICE_ONLY` from immutable 36-window manifest SHA256 `bde40bdcf898bca8354a005594b8f3cf0cd5d81577ac90f5517034af1f948b2f`.
- As-of **2026-10-25 00:37 UTC**: only swaps `2026-10-24 23:37:00 <= blockTime < 2026-10-25 00:37:00 UTC`, exact frozen pools and mints, WSOL quote; no post-signal lookahead.
- BONK pool Orca `5zpyutJu9ee6jFymDGoK7F6S5Kczqtc9FomP3ueKuyA9`; token `DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263`; price-only h1 +2.76235%, h6 +5.22050%.
- USELESS pool Raydium `Q2sPHPdUWFMg7M7wwrQKLrn619cAucfRsmhVJffodSp`; token `Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk`; price-only h1 +3.61028%, h6 +11.57143%.

## Archived source verified
| Hourly ZIP | SHA256 | Source swaps log SHA256 | Parsed swap JSONL | Newpair JSONL | JSON errors |
|---|---|---|---:|---:|---:|
| `20261024-230000.zip` | `eeaefabd562289b046921a95578ac04c3afdc05c36a8283b1c6b625ce2653b74` | `55ff0ab9e58d6193c265fb0378237e6defd12a135a87e4f1829829d3e72909b3` | **1,029,128** | 2,292 | 0 |
| `20261025-000000.zip` | `9b97c029513918f60364c1cf9261cab08d9971bc3e258c61e43dddd4738c7cb8` | `13f127e97ed70c525903eeb0f05a0fe44998c1a72271c1d06dd879a64e78f8a1` | **1,096,848** | 2,064 | 0 |

**2,125,976** total provider-decoded swaps parsed; ZIP CRC validated. **1,711** exact-pool, as-of swaps, all with distinct signatures and no mixed direction or wallet ambiguity; zero same-pool mismatches for expected token/quote, zero missing wallets and zero invalid source-reported USD fields. Provider data not independently transaction-by-transaction RPC-audited. No raw wallet IDs added to repo.

## Historical flow rules (original frozen count-based policy only)
| Pool | 23:37–00:00 buys/sells | 00:00–00:37 buys/sells | Total BUY | Total SELL | Unique swaps | Buyer-count flow |
|---|---:|---:|---:|---:|---:|---|
| BONK / **Orca** | 395 / 587 | 188 / 156 | **583** | **743** | 1,326 | **FAIL**, excess sells −160 |
| USELESS / **Raydium** | 129 / 18 | 153 / 85 | **282** | 103 | 385 | **PASS**, excess buys +179 |

Both satisfy >=20 1h swaps; BONK fails `buys>=sells`, USELESS passes. Prices and volumes remain separate gates; no claimed financial edge.

## Adversarial wallet concentration
- BONK: 370 distinct wallet addresses, 218 buyer addresses, 14.07% of buys by largest buyer wallet; remove its entire activity -> 501 buys vs 712 sells (**FAIL remains**). Source-reported USD buy 25,426.43, sell 24,895.74 (USD nearly balanced despite count-sell dominance).
- USELESS: 72 distinct wallet addresses, 53 buyers; largest buyer wallet accounts for 76/282=26.95% of buys, top three 57.09%; remove largest buyer entirely -> 206 buys vs 103 sells (**PASS remains**). Source USD buy 46,527.56, sell 19,640.88. Wallet counts are addresses, not necessarily economically independent persons.

## Outcomes (from immutable MEME006 HIST001 report; NOT real fills)
| Token | 4h gross price | 4h after purely **illustrative** cost 2.5 percentage points | 24h gross price | 24h after same illustrative cost |
|---|---:|---:|---:|---:|
| BONK **FAIL** | −1.624716% | **−4.124716%** | −4.872992% | **−7.372992%** |
| USELESS **PASS** | +7.385067% | **+4.885067%** | −2.234734% | **−4.734734%** |

Original source: HIST001 price report SHA256 `477b3a69edc4e2dd8a08c1d40a5a9d0e7584a0a43143791224c692b1ba4121a4`. Historical price conditions used completed hourly candles, not exact as-of rolling DEX Screener h1/h6. Costs are assumed; historical Raydium two-way marketable quotes, price-source consensus, pool age/liquidity, 24h volume/swap gates and actual fills absent.

## Cumulative evidence
- 02 Oct 22:37: WIF PASS, USELESS FAIL.
- 24 Oct 00:37: BONK FAIL, WIF PASS, USELESS PASS.
- **25 Oct 00:37: BONK FAIL, USELESS PASS.**
- Total **7/36 frozen price-only signal windows** with completed 60m flow; **4 PASS, 3 FAIL, 29 untested**.
- Four count-filter PASS events: simulated after-2.5pp mean **+0.675601% at 4h**, **−0.295556% at 24h**. n=4, event/currency dependence, selection, incomplete quality gates and no executable PnL: **not a statistically valid economic edge**.

## Reproducibility / safety
- Operator-attached derived report file `MEME007_20261025_0037_MOMENTUM_AUDIT_REPORT.md` SHA256 `47ac3ff8e9811a061896e95b070bea845d6e533ec27ab04fea92b8d0ffd9218b`.
- Structured 60m output `MEME007_20261025_0037_MOMENTUM_FULL_60M.json` SHA256 `94c324d62043fdd6bc9150c4579cfabd7ca340df07bf8b273696568f97e2eae8`.
- Repro package `MEME007_20261025_REPRODUCIBLE_AUDIT.zip` SHA256 `716558dd15a26903af5378b784f420f4837e72ac75d58d5ce76fb6527a3bb8ad` includes parser, summary and derived data without raw swaps.
- **NO-GO for real capital**, **GO only for cautious scientific flow reconstruction**. Keep the prospective MEME006 on `main` untouched, no orders, purchases, subscriptions or payments.