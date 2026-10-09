# BTC CONVEX — NATIVE MEXC 1H FULL 2021–2025 PRICE-ONLY TRANSFER FREEZE V0.1
Published 2026-10-09 before 61-month native-MEXC hourly ingestion. Original 2021–25 first-basket historical outcomes and 13-asset generalization already known, so this is RETROSPECTIVE cross-venue price-transfer diagnostic, NOT independent untouched holdout/OOS. No original research authority altered.

## Frozen sample and data
- ALL 3 ETH_USDT / SOL_USDT / BNB_USDT (MEXC USDT linear perpetual) exactly, no dropping losers, no alternate markets.
- Warmup 2020-12-01T00:00Z → 2020-12-31T23:00Z, economic 2021-01-01T00:00Z → 2025-12-31T23:00Z.
- REST public `GET https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=Min60&start={MONTH_START_UNIX_SECONDS}&end={MONTH_END_UNIX_SECONDS}`, monthly partitions (61 months per symbol, 183 responses), raw SHA256 each response, validate time-series exactly 1h, no holes, no duplicates or extra/out-of-month rows, 43,824 evaluation bars/symbol; malformed/missing/403/429 => fail closed. No private endpoints or auth.
- Original pinned code `labs/btc-convex-trend-capture-001/cross_asset_cost_validation_v0_1.py` from commit `8832eb8e8fe95e7914d3fe8628b0398d9695ad4a`, Git blob `49e2bafd2e487352db24f2a812e936372a2cb1ff`. Extract definitions before `out={` without executing original Binance data download/original experiment. Use exact `simulate(symbol,bars,{},'PARENT',slip)` once for BASE slip .0002 and STRESS slip .0005 for each MEXC venue symbol.
- Original causal signal, RSI, regime, z/Bollinger, volume, 4% hard stop, trailing logic, next-open entry and bar-model fill rules preserved; no timing or threshold changes.

## Scientific-economic boundaries
- PRICE-ONLY net after `10bps commission per side` and `2 or 5bps slippage per side` **but ZERO funding input because actual MEXC 2021–2025 historical funding coverage is not established**. The fee assumption is carried over solely for apples-to-apples simulator comparison, NOT a verified 2021–2025 MEXC API cost schedule.
- This is explicitly `MEXC_RETROSPECTIVE_PRICE_TRANSFER_EXCLUDING_FUNDING` and must NOT use `REALIZED_EXECUTABLE_NET_RETURN` or `AFTER_ALL_COSTS` labels, even if 3/3 positive.
- Stopping on 1h low / same-bar known stop remains bar model, NOT executable historical MEXC bid/ask, execution slip or guaranteed queue fill. No 2026 economics/holdout opening or no 2026 recent source as signal.
- Apply previous low-risk **0.25% and 0.50%** per position, shared initial 10,000 USDT and 1% aggregate planned risk, max 3 concurrent, using existing audited `events_for` + `replay` on newly generated native MEXC trade ledgers without funding; report results as price-only incomplete cost. No new risk/fee optimization after observations.
- Preserve original Binance first ETH/SOL/BNB local historical PASS as BINANCE historical only and full 13 instrument FAIL. A positive MEXC price-only replay does not promote execution or restore generalization; a negative transfer rejects this venue's price-only shape at exact rule.

## Predeclared outputs and gates
1. `NATIVE_MEXC_HISTORICAL_1H_SOURCE_PASS` only if 3/3 symbols all 43,824 bar economically complete, 2020 Dec warmup complete and source URLs/SHAs recorded.
2. Original frozen rule metrics per 3 assets per BASE/STRESS: trades, win %, price-only net return excluding funding, fees, slippage, 1h bar MTM DD, positive years, profitability summary, cross-asset spread. **No fee-free hiding:** negative costs included as specified.
3. Exact common low-risk portfolio BASE/STRESS at .25% and .50%, complete source 2021–25 all trades and planned risk cap/skipped counts, explicitly no original-MEXC carry.
4. `MEXC_VERIFIED_FULL_NET_AFTER_COSTS` ALWAYS `NOT_ESTABLISHED` without historic actual MEXC funding+BBO+depth. No live trading authority, API mutation, accounts, secrets, wallets, money or main merge.
5. Archived Binance 13-asset expansion failure remains authoritative for its exact original test, not changed by this diagnostic.

Full 2021–25 native market prices are new *source data*, but the strategy/hypothesis, candidate basket, market period and outcomes category are not a new unseen independent sample. Do not tune after seeing returns.
