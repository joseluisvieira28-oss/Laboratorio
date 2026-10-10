# HYPE-BUYBACK-FLOW-001 — SPOT CONTEXT INDEX FIX PRE-PROBE V0.1.4
2026-10-10 UTC. SOURCE-ONLY pre-probe technical amendment, no outcomes.

Run 38042801061, commit 6aff40371e664646b5b74210889bb7f5c92bab4d: 451 official AF HYPE BUY fills / ~1.064938M USDC trailing24h, 7 five complete 24h slices yield 5,250 fills / ~10.96555M USDC, day-6 and day-7 API response capped at 2000 each. Historical 14/21/28/35/60/90d sentinels returned zero; source is **retention-censored**, cannot infer zero buys.
HYPE spot @107 L2 public BBO snapshot: 84.229 bid / 84.23 ask, 0.11872325 bps snapshot spread; top five levels bid notional ~10,915.75 USDC, ask ~15,260.32 USDC. SINGLE snapshot, no historical execution economics.
BUG IN SCRIPT: `market_binding` uses position of pair in the `universe` array (105), rather than market object `index` and context record `coin`. `spotMetaAndAssetCtxs` can report `ctxs` indexed by explicit market index; API schema includes `universe[].index` and contexts[].coin. The old `dayNtlVlm=0` at offset105 cannot be accepted as authoritative volume of @107. NO RATIO COMPUTED; deliberately quarantine it.

Predeclared correction:
1. Query only current PUBLIC `spotMetaAndAssetCtxs` once. Identify HYPE/USDC token pair and exact `@107` name as before.
2. Read `pair.index`, `ctx[i].coin` for indices 105, explicit pair index and exact coin match; report source raw SHA256 and distinct values. Only accept exact context match if unique and explicit `coin=="@107"`; otherwise context market-volume SOURCE_BLOCKED. Do NOT choose whichever mapping produces highest volume or appealing numbers.
3. No buyback+volume causal ratio without matched rolling windows, volume definition and double-count controls.
4. No HYPE price returns, future outcomes, strategy rules, trading, orders, paid data, protected-period access, account secrets, wallets or main merge.

Sources:
https://github.com/hyperliquid-dex/hyperliquid-python-sdk/blob/master/hyperliquid/info.py
https://github.com/ccxt/ccxt/blob/master/ts/src/hyperliquid.ts
