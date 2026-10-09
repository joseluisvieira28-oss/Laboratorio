# MEXC-CONVEX-V01 — CAUSAL SIGNAL/QUOTE GATEWAY PRE-OBSERVATION FREEZE
Date: 2026-10-09
Status: PRE-OUTCOME RESEARCH CONTRACT — SOURCE_AND_SIGNAL_GATEWAY_ONLY
Operator: explicit "Próximo ataque autorizado". ZERO account, private API, orders, wallets, live capital, Render or main mutation.

## Background and contamination ledger
- Parent research was BTC-CONVEX-TREND-CAPTURE-001 on BINANCE USD-M. Untouched ETH/SOL/BNB replication positive after historical costs, independent XRP/DOGE/ADA/LINK/AVAX expansion negative; V0.2 2026 new snapshot 3 losses/3 closed, 1 BTC open as of Oct9. Historical Parent strategy can be copied ONLY as an exploratory MEXC *hypothesis*. NONE of the Binance retrospective or shadow performance can be labeled MEXC edge.
- MEXC public source-only sample Oct9 already seen: four symbol quote/depth feeds accessible; 10 USDT size infeasible on ETH and SOL; all four accessible at 25, 50, 100 USDT in ONE sample. This informs feasibility, not profitability or an independent test. Historical quotes/spreads already observed. No retroactive forward credit.
- MEXC source path fixed, no substitutions: contract.mexc.com /api/v1/contract/ping, /api/v1/contract/kline/<symbol> interval Min60, /api/v1/contract/detail?symbol=..., /api/v1/contract/depth/<symbol>?limit=20. NO Binance endpoints or data blending.
- Universe: BTC_USDT, ETH_USDT, SOL_USDT, BNB_USDT perpetual USDT-settled, long-only; no selection or parameter changes after prospective outcomes.

## Fixed inherited ENTRY signal (candidate transfer; never an ex-post training outcome)
On fully CLOSED 1H MEXC contract Min60 bars, use Pine Parent V5 causal entry rule: SMA(close,20); population stddev close20; z=(close-SMA20)/SD20; Wilder RSI14 computed on complete closes; volume > SMA(volume,20); score = (RSI14<30)+(z<-2)+(close< SMA20-2*SD20)+(volume>SMAvol20); signal iff score>=3 AND close>SMA(close,200). Exact 400 continuous 1H warmup bars or BLOCK, no forward fill; no 1H interval substitution. Preserve z/Bollinger redundancy, do not tune thresholds based on known 2026 Parent outcomes. This gateway does NOT simulate trailing/exit or calculate equity.

## Single-run causal contract
For any launch, first admissible signal CLOSED 1H boundary must be strictly AFTER the workflow deployment commit timestamp. Signal evaluation is allowed ONLY if done within [0,600] seconds after the final closed 1H boundary. Github Actions scheduling delay may cause NO_SCORABLE_BOUNDARY; do NOT retrospectively reconstruct a forward event from stale candles.
Capture host UTC and MEXC server clock midpoint offset <=1000 ms. GET only, max source request 2000 ms and book snapshot age in [0,2000] ms. Verify complete ordered 400-bar candle prefix, exact bar-close boundary vs wall-clock; require server and client clock integrity. Any observed 1H signal is computed from bars that were closed when the runtime decided. Log raw SHA256 of kline/quote responses, last closed timestamps, signal details, source timing and rule version.
For the hypothetical 25/50/100 USDT long reference scenario: after the signal calculation capture real fresh public asks/bids and price-depth using MEXC contractSize, minVol, volUnit, maxVol, fees from public detail metadata. Hypothetical BUY = ask sweep, SELL = bid sweep. Require receipt ordering: candle close <= signal computed at <= book HTTP request at <= book HTTP receipt, exchange book.timestamp <= receipt and quote age <=2000ms. The frozen 95% Binance equity allocation is NOT used to claim feasible small-account risk. No leverage or position authority. Explicit NO_FILL if no current on-time quote.
Non-triggering signals are also recorded; any signal not observed in the strict 10-minute window gets no forward credit. Probe may run outside window as SOURCE_DIAGNOSTIC_ONLY but NOT SIGNAL observations.
Trade simulation/fees outcome/funding, funding mark, trailing or stop exits are entirely OUT OF SCOPE; no simulated trade is opened and no PnL will be calculated. New shadow/position experiment requires separate freeze and durable single-writer ledger before first entry. A Github Actions artifact is a single-run immutable receipt only, not a durable trade-position database.

## Hard gates
SOURCE_GATEWAY_PASS: four symbols have 400 contiguous mature MEXC 1H candles; kline data current, contract metadata valid, depth fresh and book contract-unit size tests (25,50,100) pass for all; timestamps and provider clock validate. This status is SOURCE ONLY, not signal/edge or execution evidence.
TIMELY_SIGNAL_OBSERVATION: additionally, for a symbol, <=600 s after hourly close strictly post activation commit, source/quote causal sequence pass, frozen Parent candidate signal legitimately evaluated. NO_SIGNAL is a valid observation. If not inside window, NO_SCORABLE_BOUNDARY; source gate may still PASS.
NEVER report future PnL or account credit; no 10 USDT minimum retroactive rescue. Quote no means of proof of order fill, funding, fee tier, live account access or regulatory venue access.
Re-runs: each has unique Github workflow artifact and SHA; no missing forward evaluations invented. Do not promote due solely to repeated GET success.

## Authority
Actions workflow uses public GET only, contents:read, no secrets, no order keys; branch-only trigger. CI synthetic failure tests first. No main merge, no real trading, no exchange mutation, no protected holdout re-opening. No source substitution or leverage rescue.
