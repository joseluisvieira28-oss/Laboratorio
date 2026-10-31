# CRYPTO LAB — VELOCITY FILLER FINAL SCIENTIFIC AND ECONOMIC CLOSEOUT, 2026-10-31

**FINAL: DOCUMENTED FEE-FUNDED PAYER, ACTIVE MARKETS, NO VERIFIED ACTUAL FILLER-REWARD RECORDS DUE TO SOURCE BLOCK; MICRO-SIZED REVENUE OPPORTUNITY, NO-GO FOR BUILDING BOT.**

## 1. The economic mechanism
Velocity Protocol Solana order keepers may permissionlessly fill existing perpetual market orders. Their explicit reward is the LESSER of 10% of the taker fee and a time/order-age-derived cap starting from USD0.01. This is financed by the client/taker's commission, not by guessing direction. However not every fill is capturable, nor must an operator earn net income. This is distinct from our prior Event Futures, Options V2.1, Polymarket maker rewards, Morpho rollover, liquidation and news-shock studies.

Documented regular **SOL/BTC/ETH** taker fee baseline: **6bps**. Therefore a fee-bound filler reward for those baseline trades is AT MOST **0.6bps of filled notional**, then further limited by the age cap, and before real paid gas or race failures. These fee rates are admin-settable and do not necessarily apply to every market.
Official https://docs.velocity.exchange/protocol/how-it-works/keepers/keeper-incentives
Official https://docs.velocity.exchange/protocol/trading/trading-fees
Official https://docs.velocity.exchange/developers/data-api
Field fillerReward and transaction identity https://docs.velocity.exchange/developers/data-api/glossary

## 2. Immutable actual source attempts
V0.1 pre-source freeze SHA 8ed264b700318371490639b3d861d5774dcb78c0. Original read-only GitHub Actions https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41227701534 artifact 13052212342 ZIP sha256 b325e1dec08dedcc46a7f7d41409d39023cd9cf3c04cda002bc9e63674ce34c9. Public GET /stats/markets was HTTP200, but study wrongly expected top-level array or data array: STATS_MARKETS_SCHEMA_BAD. No trade reward endpoints called, original SOURCE_BLOCKED_FAIL_CLOSED remains unchanged.

V0.1a separate POST-source independent strictly OFFLINE forensic https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41227815313 read ONLY archived raw GET, checked actual SHA256 05c501e4894232f464154246af91964ed5a3e2cb75a1c1cfc286cac89967c1f1, and found exactly public wrapper with keys success + markets, markets array length 10. No new market API requests or extracted market outcome.

V0.2 separately pre-frozen ONE parser correction SHA 9e6769a35c52be95ec2859062e34f9fbee97d52b; no market, filter, economics or source change. Final source run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41227910778 artifact 13053035791 ZIP sha256 660c0adf8aaa2a605100fd319b5c0a51dd659b7b0614c1ec194bd691074b9299.
- Public /stats/markets now PASSED, exactly 10 markets, SOL-PERP active marketIndex 0, BTC-PERP active index 1, ETH-PERP active index 2.
- The FIRST trade feed GET /market/SOL-PERP/trades?limit=100 returned HTTPError. The study failed closed immediately, BEFORE any public record field fillerReward could be read.
- Consequently 0 payouts VERIFIED BY US (not proof of worldwide ZERO actual rewards), 0 valid reward events usable, 0 user profits, no official trade API receipt. NO third request/provider rescue permitted under freeze.
- No credentials, private user account, wallet, order, paid sources, real transaction, SOL fee spending or main merge.

## 3. Separate, real-scale economic screen (conditional arithmetic)
Public DefiLlama https://defillama.com/protocol/velocity as accessed 2026-10-31 reported 24h notional about **USD 115,957**, 7d **USD 288,302**, 30d **USD 1.34M**. Not real operator profits and time-varying; third-party aggregated notional data may be imperfect.

A GENEROUS ILLUSTRATIVE REGULAR-MAJOR-MARKET hypothetical: apply the 6bps regular taker fee across the full venue-reported volume (regardless of market), then suppose fillers capture the ENTIRE 10% fee sub-pool with no age cap, in every transaction. Result across **ALL filler operators combined**, BEFORE onchain and server costs:
- 24h 115,957 x .0006 x .10 = **6.95742 USD**
- 7d 288,302 x .0006 x .10 = **17.29812 USD**
- 30d 1,340,000 x .0006 x .10 = **80.40 USD**

This is NOT a strict global upper bound or certified revenue amount: fees on non-major markets may differ, taker tiers may be cheaper, age reward cap may reduce distribution, the aggregate provider may report different definitions, volume and fees change over time. But even with favorable assumptions under the documented major-market baseline, the total pool's magnitude is single-digit dollars per day in this public 24h reference — a deeply weak practical prospect for a new independent always-on competing keeper bot.

Never treat observed third-party notional as actual rewards paid to anyone. No wallet payout evidence or execution gas receipts; no demonstrated positive net PnL.

## 4. Final decision
SOURCE RESULT: v0.1 blocked; v0.1a offline source schema proven; v0.2 official stats PASS but trade history HTTP BLOCKED.
ECONOMIC MECHANISM: real documented commission-funded filler reward.
SCALE: illustrative daily fee-filler pool very small versus build/operation/competition.
USER ECONOMIC EDGE: NOT CERTIFIED.
ACTION: **STOP VELOCITY FILLER BOT BUILD / NO LIVE GO**; do not code 24/7 infrastructure, trade or spend fees to chase tiny hypothetical incentives. Keep old results and the original failures intact. Zero main changes and zero actual orders.

Prior OPTIONS-SpotPerp 10x market/market, NFP historical and Event Futures closures unchanged. New opportunity search, if any, must require verified recipient payouts and sufficient aggregate fee budget BEFORE any more implementation. User value likely higher in real business/client-paid automations than an unverified micro-filler bot, but that is a separate commercial hypothesis.

**NO PROFITABLE AUTOMATED CRYPTO CASHFLOW SYSTEM DISCOVERED IN THIS ROUND.**
