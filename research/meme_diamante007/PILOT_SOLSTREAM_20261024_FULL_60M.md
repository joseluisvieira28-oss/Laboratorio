# MEME-007 — 24 October 2026 historical 60-minute swap-flow audit

**2026-11-19; read-only scientific research. Original MEME006 prospective thresholds unchanged. No executions, no payments, no actual fills.**

## As-of identity and coverage
- Three previously frozen **H_REVERSAL_PRICE_ONLY** conditions: `2026-10-24 00:37:00 UTC`: BONK (mint DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263, pool 5zpyutJu9ee6jFymDGoK7F6S5Kczqtc9FomP3ueKuyA9); WIF (mint EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm, pool EP2ib6dYdEeqD8MfE2ezHCxX3kP3K2eLKkirfPm5eyMx); USELESS (mint Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk, pool Q2sPHPdUWFMg7M7wwrQKLrn619cAucfRsmhVJffodSp).
- Exact historical eligibility window `[2026-10-23 23:37:00, 2026-10-24 00:37:00)` UTC, END EXCLUSIVE; always use each source record's `blockTime`, not ZIP filenames or 00:37–01:00 post-event swaps.
- Hash of immutable 36 frozen price windows: `bde40bdcf898bca8354a005594b8f3cf0cd5d81577ac90f5517034af1f948b2f`.
- Historic price backtest report hash: `477b3a69edc4e2dd8a08c1d40a5a9d0e7584a0a43143791224c692b1ba4121a4`.

## Real SolanaStreaming archives supplied by operator
| Archive | ZIP SHA-256 | source swaps JSON | newpairs JSON | malformed JSON |
|---|---|---:|---:|---:|
| `20261023-230000.zip` | `7e4874e6976bbe6512fea8844f1e41fe7ed9da7079474a2ca32afec2a2bf65c1` | 1,048,008 | 2,037 | 0 |
| `20261024-000000.zip` | `0c1bbc960d354ab78791a0dfe716291199f9a40205dd79edb735824e3f30ecf9` | 993,436 | 1,789 | 0 |

Source swaps logs SHA256 (uncompressed): `a1397010bd0535d5e049443dafda54cea465b6fa4a8253450dc03c6c4a02a23f` for 23h and `eb32723e62f15ef59917b72a4e16cc82c12f6517362f6255bbb34113c7863363` for 00h. Both ZIP logs read fully with ZIP CRC verified. No source logs were committed.

## Observed exact-pool historical swap counts (no look-ahead)
| Pool/venue | 23:37–00:00 buys/sells | 00:00–00:37 buys/sells | 60m buys | 60m sells | Unique signatures | Frozen swap-flow gate |
|---|---:|---:|---:|---:|---:|---|
| BONK / **Orca** | 60 / 305 | 129 / 195 | **189** | **500** | 689 | **FAIL** |
| WIF / Raydium | 41 / 3 | 15 / 4 | **56** | 7 | 63 | **PASS** |
| USELESS / Raydium | 85 / 1 | 130 / 48 | **215** | 49 | 264 | **PASS** |

Every pool matched `swap.ammAccount==frozen_pool`, `baseTokenMint==frozen_mint`, `quoteTokenMint==WSOL`. **0 repeated swap signatures, 0 contradictory sides, 0 multi-wallet signatures, 0 absent wallet IDs, 0 invalid source-reported USD notional** within all three selected pool windows. **1,016 unique in-window source swaps** across targets; over two million other archive swaps not misclassified as source signals.

### Wallet concentration / sensitivity
| Pool | Wallets distinct | Buyer wallets | Largest buyer-wallet share of buys | Remove entire largest buyer wallet (buys/sells) |
|---|---:|---:|---:|---:|
| BONK | 247 | 93 | 15.87% | 159 / 491 (FAIL) |
| WIF | 14 | 11 | 51.79% | 27 / 7 (PASS) |
| USELESS | 42 | 33 | 35.35% | 139 / 47 (PASS) |

Wallet concentration changes apparent significance but **does not change frozen count-based rule**. Distinct wallet addresses are not necessarily distinct people.

## Price-only outcomes (no fills)
| Pool | Count filter | 4h gross candle | 4h after ILLUSTRATIVE −2.5 percentage points | 24h gross candle | 24h after −2.5pp |
|---|---|---:|---:|---:|---:|
| BONK | FAIL | −1.056% | **−3.556%** | +0.931% | **−1.569%** |
| WIF | PASS | +0.928% | **−1.572%** | −1.649% | **−4.149%** |
| USELESS | PASS | +2.688% | **+0.188%** | +8.576% | **+6.076%** |

Stress subtraction is not real transaction cost and does not establish marketable bid, fill, liquidity or on-chain PnL; original historic DexScreener h1/h6 *rolling* returns are approximated by closed-hour candles. Observing Orca swaps in BONK says nothing about Raydium quote routes. No trade was placed.

## Cumulative gate after two pilot archive dates
- 2026-10-02 22:37: WIF count PASS (161 buys, 30 sells), USELESS FAIL (8,961 buys, 10,480 sells).
- 2026-10-24 00:37: BONK FAIL, WIF PASS, USELESS PASS.
- **5 / 36 frozen price-only signal windows** have complete archived 60m flow reconstructions: **3 PASS / 2 FAIL**, **31 windows remain**.
- For the **three count-only PASS** in these highly selected examples, the 4h average after 2.5pp hypothetical stress is **−0.728%** and 24h is **+1.184%**; no significant economic conclusion (n=3, clustered coins/dates, missing execution/quality gates).

## Scientific verdict
**GO narrowly for 3 more completed 60m historical buyer-count reconstructions. INCONCLUSIVE for full original MEME006 historical gate; NO-GO trading.** Still missing historic age, liquidity, >=50k 24h volume, >=200 24h swaps, contemporaneous DEX/Gecko price reconciliation, Raydium 0.05 SOL bidirectional executable quotes, real fill and independent prospective economic proof.

Operator-facing reproducible deliverables: `MEME007_20261024_0037_FULL_60M.json` SHA256 `61577ced49eb0b990987b56d027d39d937e0fb7e3f0e50c9d7d2592cf3b5b096`; `MEME007_20261024_0037_AUDIT_REPORT.md` SHA256 `cc64a657d0b16ca592a554b712912b11d50736a2aa417d5d2a7289327131a2b5`; `meme007_oct24_full_hour_audit.py` and local reproduction bundle retained in operator conversation.

Next efficient optional zero-spend source test: two H_MOMENTUM_PRICE_ONLY signals at `2026-10-25 00:37 UTC` (BONK, USELESS); the exact preceding hourly files are `20261024-230000.zip` and `20261025-000000.zip`. Do not incur payments or activate trading.