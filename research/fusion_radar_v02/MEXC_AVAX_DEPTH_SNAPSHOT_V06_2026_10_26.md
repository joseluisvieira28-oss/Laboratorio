# Fusion Radar AVAX20 × BTC20 — MEXC AVAX_USDT public order-book snapshot V0.6
Date: 2026-10-26. Research-only. Branch: `research/fusion-radar-three-panels-v02-2026-10-25`; PR #271. NO LIVE GO, no orders, no account reads, no main merge.

## Actual supplied evidence
- User-uploaded `MEXC_AVAX_DEPTH.json`, byte SHA-256 `3e8aad0d5411d581786db6c0014355672fae20492aea736ba6c1126b491cab9b` (UTF-8 JSON, 7841 bytes).
- The payload says `success=true`, `code=0`, `version=8471919502`, `timestamp=1793011973450` = **2026-10-26T10:52:53.450Z**; 20 ordered positive-price positive-volume levels each side; no crossed book.
- Best bid **8.954 USDT**, best ask **8.955 USDT**; midpoint **8.9545**; spread (10,000 × (8.955 - 8.954) / 8.9545) = **1.11675694 bps**.
- Order sizes in MEXC book are **contracts**, not AVAX. The official MEXC AVAX_USDT trading rules give **1 contract = 0.1 AVAX**; do not misread raw `5568` as 5568 AVAX.
- Top bid `5568` contracts = 556.8 AVAX ~ **4,985.59 USDT** at 8.954; top ask `22339` contracts = 2,233.9 AVAX ~ **20,004.57 USDT** at 8.955.
- Total 20-level displayed bid notional ~**1,477,988.00 USDT** and ask notional ~**1,425,828.82 USDT**. These are **nonfirm snapshot book values**, not executable, refreshed 2022/23 depth, or reliable trading capacity.
- Local file checks validated ladder monotonicity, third field (order count) positive, bid below ask. **No independent cryptographic attestation of remote origin**: exchange payload came from operator machine.

## Static fully aggressive hypothetical roundtrip depth walk
For each notional Q, use integer ceil(Q/(0.1 × 8.9545)) contracts; compute asks-side buy VWAP and bids-side sell VWAP from *same* book and compare to midpoint: `10,000 × (VWAP_ask - VWAP_bid)/8.9545`. **This is not a claim of realized one-hour roundtrip cost**, not historical MEXC market depth, and does not model cancellations, time priority, market impact, liquidity replenishment or latency.

| Q nominal USDT | Static spread/depth walk bps | Conditional 8-bps taker/taker fee + walk bps |
|---:|---:|---:|
| 100 | 1.11676 | 9.11676 |
| 1,000 | 1.11676 | 9.11676 |
| 5,000 | 1.11996 | 9.11996 |
| 10,000 | 1.67674 | 9.67674 |
| 25,000 | 2.44423 | 10.44423 |
| 50,000 | 3.45563 | 11.45563 |
| 100,000 | 5.17655 | 13.17655 |
| 250,000 | 8.54490 | 16.54490 |

## Compare to original already-exposed proxy returns
Historic accepted Fusion gross mean 2022/23 **15.85102929 bp/trade**, but year 2023 only **8.46639493 bp/trade**. Under a conditional fee tier of taker 0.04% per side (total **8bps**), the first ~1.117bps observed best-book spread would leave **-0.650362bps per trade** versus *2023* historical breakeven, **before** any time-sensitive slippage, latency, adverse selection, funding (if applicable), or cross-venue basis. Overall sample remains +6.73427bps/trade under this static fee+spread model but heavily regime- and tail-dependent. This juxtaposition does **not** establish 2023 MEXC costs with a 2026 snapshot and the 2022/23 returns were measured on Binance futures price proxies, not executable MEXC quotes.

The MEXC Oct 26 2026 fee notice sets AVAXUSDT taker 0.04% for **selected countries/regions/users**; account-specific Switzerland fee tier has **NOT** been authenticated or checked, and alternate 0.02% East Asia fees are not Switzerland evidence. Fee schedule source:
https://www.mexc.com/announcements/article/adjustments-to-trading-fees-on-btc-wld-and-14-other-futures-in-selected-countries-and-regions-17827791539309
MEXC AVAX contract rules (1 Cont = 0.1 AVAX): https://www.mexc.com/futures/AVAX_USDT/
Book API depth field definition: https://www.mexc.io/api-docs/futures/market-endpoints/get-contract-order-book-depth

## Gate disposition
- `READ_ONLY_SNAPSHOT_PARSED_PASS`
- `STATIC_BOOK_DEPTH_COMPUTED_PASS`
- `REAL_HISTORICAL_EXECUTION_COST_UNPROVEN`
- `ACCOUNT_FEE_TIER_UNVERIFIED`
- `STANDALONE_NET_EDGE_NOT_CERTIFIED`
- **`NO_GO_FOR_LIVE_OR_PAPER_TO_LIVE_PROMOTION`**.

To pursue an execution study prospectively without orders: register source/observation timestamps, randomly or pre-scheduled observe during the exact decision clock and entry/exit clock (01:00 and 02:00 UTC), hold matched book levels over a precommitted observation window, read symbol contractSize from public contract metadata, and obtain fee tier from operator-supplied non-sensitive account fee display. Neither one snapshot nor retrospective timing selection can validate actual one-hour fills. Maintain 2024–2026 protected outcomes closed; no post-outcome 20D threshold, long/short or cost retuning.
