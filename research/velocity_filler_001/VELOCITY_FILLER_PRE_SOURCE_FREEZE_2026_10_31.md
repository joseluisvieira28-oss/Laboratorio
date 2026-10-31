# VELOCITY-FILLER-001 V0.1 — EXACT ACTUAL FILLER REWARD SOURCE-AND-ECONOMIC GATE
PRE-SOURCE SCIENCE FREEZE — 2026-10-31, before this study's market/API observations.

## New real payer and different economic mechanism
Velocity Protocol documents permissionless Solana futures order matching, with filler/keeper rewards funded by a share of taker trading fees, bounded by an age-based cap. Documented formula for a fill: reward = MIN(10% of taker fee, reward increasing from $0.01 with order age). The actual accounting field is fillerReward in quote precision (1e6). This does NOT imply any unused job, readily capturable reward, liquidity investment, market-making rebate, or user profit. Distinct from BTC/ETH direction, Event Futures payout, Options V2.1, Morpho borrower roll, Polymarket maker rewards, Aave liquidations and NFP macro surprise.
Official https://docs.velocity.exchange/protocol/how-it-works/keepers/keeper-incentives
Official https://docs.velocity.exchange/developers/data-api
Official https://docs.velocity.exchange/developers/data-api/glossary
Official data host https://data.velocity.exchange

## Frozen exact public source request budget
One GitHub Actions fresh runner; no accounts or wallet. Four unauthenticated public HTTP GETs exactly, in sequence, maximum 2MB per request, <=12s timeout, no retries, alternative hosts, user-specific APIs, pagination or private API:
1. https://data.velocity.exchange/stats/markets
2. https://data.velocity.exchange/market/SOL-PERP/trades?limit=100
3. https://data.velocity.exchange/market/BTC-PERP/trades?limit=100
4. https://data.velocity.exchange/market/ETH-PERP/trades?limit=100
Read original unmodified HTTP200 JSON, UTC receipt time, raw bytes SHA256, HTTP status, byte count, save entire JSON responses in one artifact. No auth, no signatures, POST/tx builders, any wallet activity, query historical protected data, replay or payment.

## Exact data guardrails
- /stats/markets must be valid JSON, and if a list of market objects it is checked for SOL/BTC/ETH symbols and their advertised status/24h volume. No extrapolation from unrelated markets.
- Each trade feed must be a JSON list or object with documented data:list; accepting an undocumented alternate wrapper schema is forbidden. For each record: integer Unix ts, valid Solana transaction signature text, nonnegative integer or numeric decimal fillerReward and takerFee (if missing at least fillerReward, record SOURCE_FIELD_MISSING and do not compute). Quote precision = 1,000,000; aggregate original raw rewards with arbitrary precision decimal. Negative rewards fail.
- Keep market and sample scope unchanged, no replacement if a market is inactive; if any feed errors mark SOURCE_BLOCKED or INCOMPLETE, no success claim. No trades is valid ZERO_TRADES_IN_BOUNDED_FEED, not a worldwide zero activity claim. If response meta.nextPage exists, explicitly classify sample as truncated; NEVER infer whole-day activity from 100 most recent.
- Source gate PASS if all 3 feeds valid and at least ONE record contains a valid positive explicit fillerReward, or SOURCE_VALID_ZERO_REWARDS if all feeds valid but zero positives. A PASS is solely HISTORICAL ALLOCATION FIELD, NOT verified transfer to an operator or economic profit.
- Economic stop/veto: public records must show >=10 independently sourced positive rewards within 7 calendar days across the 3 market feeds AND >=3 distinct txSig and sum at least 10 USD of observed quote-denominated rewards to warrant further analysis. This is a predeclared *research prioritization* hurdle, not expected user income / trading GO. If any condition fails -> STOP_THIS_FAMILY_NO_MEANINGFUL_OBSERVED_REWARDS_IN_SAMPLE. If it passes -> FURTHER_TX_FEE_AND_COMPETITION_GATES_REQUIRED, still zero edge.
- Research budget max ONE source run. No automatic repeat on failure, no jobs with accounts, no new markets after seeing results. Time limits and source freshness stop apply as frozen.

## Economic caveats
Rewards belong to HISTORICAL other operators and may be reported not directly paid to their wallet; the same tx may include multiple fill records (not statistically independent). Need explicit quote token/market precision, actual receipt transfer, fee payer Solana tx fees+compute priority fee, probability of winning race, failed transaction burn, infrastructure, operator uptime and Swiss eligibility. Without these, no expected net income or bot GO. Total taker fee pool is shared among multiple fillers and other participants.
No markets selected by profitability or after-the-fact best sample; no look-ahead outcomes.
No other crypto research family reactivated, no main merge, no Binance/MEXC account, paid API, wallet, keys, real transactions, Telegram, trading capital, protected 2026 historical holdouts or NVIDIA duplicate work.
