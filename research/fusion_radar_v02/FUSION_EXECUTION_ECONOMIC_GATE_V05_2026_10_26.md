# Crypto Lab / Fusion AVAX20 BTC20 — EXECUTION ECONOMICS GATE V0.5
Date: 2026-10-26 | Branch: research/fusion-radar-three-panels-v02-2026-10-25 | PR #271 (draft)
Decision: **NO_GO_EXECUTION / FROZEN_RESEARCH_CLUE / NO_PROVEN_STANDALONE_NET_EDGE.**
Not a definitive claim of failure under every possible fee tier or venue.

## Operator evidence and exact accounting
Source artifact: \`AVAX_BTC_DAILY_2022_2023.csv\` SHA256 \`38b042c4d439f8ddf2f6bc5665b24608345a765dddbc00b2f0d4f767729ad8d3\`.
Earlier operator source replay V0.4 locally matched all 74 Binance ZIP+CHECKSUM pairs and every one of 730 calendar observations. Companion checksum validity is local, not remote signature/point-in-time executable bid/ask proof.
The test is NOT a reimplementation of original CED1D; it is 01:00-open to 02:00-open delayed hourly proxy for an AVAX20-direction with optional BTC20-context. Originally published historical results used 14 and 20 bps **total** hypothetical roundtrip cost.

Derived from the exact 568 accepted gross returns:

| Fixed hypothetical TOTAL roundtrip friction | Combined accepted mean net bps/trade | Combined accepted sum bps on daily unit-notional | 2023 accepted mean net bps/trade |
| ---: | ---: | ---: | ---: |
| 4 bps | +11.8510 | +6,731.3846 | +4.4664 |
| 8 bps | +7.8510 | +4,459.3846 | +0.4664 |
| 10 bps | +5.8510 | +3,323.3846 | -1.5336 |
| 12 bps | +3.8510 | +2,187.3846 | -3.5336 |
| 14 bps (old BASE) | +1.8510 | +1,051.3846 | -5.5336 |
| 16 bps | -0.1490 | -84.6154 | -7.5336 |
| 20 bps (old STRESS) | -4.1490 | -2,356.6154 | -11.5336 |

Overall breakeven = mean accepted GROSS return \`15.851029285\` bps (2022 +22.49473043; 2023 **+8.46639493**). Constant 8-bp fee-only assumption leaves 7.851bps overall, but only **0.4664bps per trade in 2023** for all other frictions before net turns negative. Roundtrip fee 8 bps is illustrative only and not a proven user's rate. No fee-double-counting: tables above are *total* frictions, not 14 plus commission.
2022 earns historical positive +2,539.9244bp at BASE14, whereas 2023 loses -1,488.5398bp; accepted 3 biggest winners total about +1718.8bp, exceeding combined BASE14 net +1051.38bp. 2023 market-regime fragility and unrealistically thin execution margin remain primary economic blockers.

**Statistical note:** these values are conditional average of *exposed* 2022-23 outcomes, not expected forward returns. The cost grid is a descriptive feasibility envelope, not selecting a new cost parameter to rescue the strategy. Nor does a positive 8-bp fee-only hypothetical verify makers, deterministic fills, spread or impact.

## Verified published market conditions / precision
- MEXC announcement on AVAXUSDT futures, effective 2026-10-26 10:00 UTC for **selected countries/regions and users only**: maker 0.01% (1 bp per side) and taker 0.04% (4 bps per side). Two taker executions thus imply 8 bps **fees only** if that tier actually applies. MEXC instructs users to consult their own fee page. Source: https://www.mexc.com/announcements/article/adjustments-to-trading-fees-on-btc-wld-and-14-other-futures-in-selected-countries-and-regions-17827791539309
- Other lower MEXC fees exist in specifically advertised regions; no proof they apply to a Switzerland account. Source: https://www.mexc.com/fee
- MEXC publishes a **public no-auth** futures depth endpoint GET \`/api/v1/contract/depth/{symbol}\` and ticker. Source: https://www.mexc.io/api-docs/futures/market-endpoints/get-contract-order-book-depth
- Exact authenticated MEXC user fee, public AVAX order book **current** snapshot, size-dependent VWAP, 01:00/02:00 fill latency distributions and 2022/23 MEXC bid/ask history **were not acquired**. Direct GET attempt in this environment returned inaccessible; container DNS also blocked. Do not invent market spreads, fills or fee tier. A single current spread is insufficient to establish historical average.
- Original prices use **Binance AVAXUSDT USD-M futures**, whereas intended hypothetical venue is **MEXC AVAX_USDT futures**. Cross-venue 2022/23 prices, liquidity and contract market structure have not been reconciled.
- Funding typically crystallizes at contract-specific scheduled timestamps and may not be charged in a 01:00-02:00 UTC hold unless a settlement falls within the interval; this was NOT checked historically for the intended contract. General reference: https://blog.mexc.com/wiki/what-is-funding-rate-in-crypto-how-funding-fees-work/
- OHLC H1 OPEN is not an executable fill at a desired price. Neither maker-fill probability nor taker effective spread/impact, slippage, partial fills, exchange outages, rejection or long-short capacity are established.

## Deliverables and gate behavior
- \`economic_gate_v05.py\`: independently recomputes fixed cost envelope on hash-locked CSV; 2022 and 2023 disaggregated; no networking or mutation.
- \`test_economic_gate_v05.py\`: 14 local assertions (hash, dates, masks, old BASE/STRESS totals, yearly threshold, cost applied ONCE, corruption, NaN/negative rejection) passed in this assistant environment. GitHub CI has NOT run and source CSV is not checked into the repo.
- Run from the user's V0.3 directory with exactly the existing CSV:
\`\`\`powershell
py economic_gate_v05.py --csv results/AVAX_BTC_DAILY_2022_2023.csv --output results/FUSION_ECONOMIC_GATE_V05.json
\`\`\`
- A single **read-only public market data** snapshot may be captured manually on the operator's Windows machine (no authenticated account, orders, keys, or websocket automation):
\`\`\`powershell
Invoke-RestMethod -Method Get -Uri "https://contract.mexc.com/api/v1/contract/depth/AVAX_USDT?limit=20" |
  ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 "results/MEXC_AVAX_PUBLIC_DEPTH_ONE_SNAPSHOT.json"
\`\`\`
This merely records a point-in-time top-of-book/depth and cannot repair missing historical execution evidence. Any account-specific fee must be checked by operator, never inferred from regional announcement, and no passwords/API keys/screenshots of sensitive account info should be uploaded.

## Legitimate next step without contamination
Freeze this AVAX/BTC combination as a historical *contextual information* lead, separate from full multi-family Super Indicator. Any future scientific test must use a genuinely untouched outcome interval with a prior public freeze, baseline/multiplicity/power, fees by venue, quote-time fills, execution latency and full risk. **No opening 2024/25/26 protected periods, no post-outcome retuning 20D/lookback/short-only, no live orders, no main merge.**
