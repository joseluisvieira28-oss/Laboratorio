# BTC-CONVEX-TREND-CAPTURE-001 — PROSPECTIVE SHADOW FORWARD FREEZE V0.1

**Frozen:** 2026-09-24  
**Boundary authority commit:** db9141383dad77a47dc187175742afcdfff056c1  
**Boundary commit timestamp:** 2026-09-24T04:46:50Z  
**First eligible fully post-freeze 1h bar open:** 2026-09-24T05:00:00Z  
**Mode:** RESEARCH-ONLY SHADOW / NO ORDERS

## Canonical forward universe

Exactly:
- BTCUSDT
- ETHUSDT
- SOLUSDT
- BNBUSDT

Rationale:
- BTC has survived causal reconstruction diagnostics;
- ETH/SOL/BNB passed the first frozen untouched basket;
- no asset discovered later from failed baskets is added post hoc.

TRX is explicitly excluded despite strong observed historical performance because adding it after seeing its outcome would be cherry-picking.

## Rule

Use the recovered Parent V5 causal rule unchanged:

Entry signal on completed 1h bar:
- SMA20
- STDEV20
- zScore < -2
- RSI14 < 30
- close < SMA20 - 2 × STDEV20
- volume > SMA20(volume)
- score >= 3
- close > SMA200
- long-only while flat

Execution:
- signal only on completed bars;
- entry at next 1h bar open;
- initial stop = 4%;
- peak updates only from causally completed bar information;
- trail distance = 12%;
- original non-latched trail selection:
  use trail only while completed-bar close profit >= +5%;
  otherwise revert to initial stop;
- no same-bar historical reentry using final current-bar information.

## Shadow economics

Independent shadow account per symbol:
- initial equity = 10,000 USDT
- allocation = 95% equity
- commission = 10 bps per executed side
- adverse slippage = 2 bps per executed side
- official USD-M perpetual funding

No leverage rescue.
No portfolio pooling.

## Data source

Live/forward public official Binance USD-M endpoints only.

Required:
- 1h klines with complete warmup;
- public funding-history records;
- funding timestamp normalization <=1 second;
- direct official funding markPrice for forward records.

If source is unavailable or ambiguous:
**FORWARD_DATA_BLOCKED**.

No private exchange endpoint is permitted.

## Forward-state reconstruction

Each observation replays deterministically from the frozen forward boundary using:
- warmup bars only for indicator initialization;
- zero economic credit before 2026-09-24T05:00:00Z;
- starting state FLAT;
- starting equity 10,000 USDT.

Therefore no mutable external shadow-state store is required and restart/replay is deterministic.

## Minimum evidence before any forward adjudication

No promotion decision may be made until all are true:

1. at least **90 calendar days** have elapsed from the forward boundary;
2. at least **40 closed trades** exist across the four-symbol family;
3. at least **3 of 4 symbols** have produced at least 5 closed trades;
4. source coverage has no unresolved hourly gaps;
5. there is no causal-execution integrity blocker.

Before those conditions:
**FORWARD_COLLECTING_ONLY**.

## Frozen forward report

Required per symbol:
- completed bars observed after boundary;
- entry signals;
- closed trades;
- wins/losses;
- realized PnL;
- marked equity;
- current open position;
- active stop;
- funding;
- commission;
- slippage;
- max MTM drawdown;
- deterministic evidence timestamp.

Family:
- closed trades total;
- positive realized symbols;
- equal-weight marked return;
- collection-age days;
- readiness conditions.

## Governance

This forward is scientific observation only.

Prohibited:
- real orders;
- private API mutation;
- exchange account changes;
- changing parameters because of forward outcomes;
- retroactive insertion of signals;
- adding/removing symbols because of performance.

Historical filter mining for this family is closed.
