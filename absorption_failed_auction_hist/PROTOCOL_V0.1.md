# ABSORPTION-FAILED-AUCTION-HIST-001 — Historical Mechanism Test V0.1

Status: FROZEN PRE-OUTCOME / RESEARCH ONLY
Branch: absorption-failed-auction-hist-v0.1
Frozen before any historical R5/R15/R30/R60/R240 outcome is computed.

## Question
Does the same absorption-vs-efficient-acceptance mechanism used by ABSORPTION-FAILED-AUCTION-001 survive on a fully reconstructible Binance-native historical footprint?

This is a separate scientific identity. It does not backfill or alter the prospective child.

## Source authority
Only official public Binance Spot BTCUSDT data:
- Binance Vision monthly aggTrades archives + official .CHECKSUM.
- Binance Vision monthly 1m kline archives + official .CHECKSUM.
No TradingView historical export is required.

Aggressor side:
- isBuyerMaker=false => aggressive BUY
- isBuyerMaker=true => aggressive SELL
Quantity is BTC base quantity.

## Deterministic historical footprint
Timeframe: UTC 5m.
Price row: fixed 1.00 USDT.
For every aggTrade, row_lower=floor(price / 1.00)*1.00.

Per row:
- total=buy+sell
- POC = row with maximum total volume; ties choose the lower price row.
- POC mid = row_lower + 0.50 USDT.
- Value Area starts at POC and expands one adjacent row at a time toward the side with greater adjacent total volume; ties expand downward first; stop once cumulative volume >=70% of bar total.
- buy imbalance at row i iff buy_i > 3 * sell_(i-1).
- sell imbalance at row i iff sell_i > 3 * buy_(i+1).

Canonical 5m flow:
agg_delta_pct=(aggressive_buy_qty-aggressive_sell_qty)/base_volume.

LTF path efficiency uses the five official Binance 1m klines inside each 5m bar exactly like MM-V1:
path = |close_1-open_1| + |close_2-close_1| + ... + |close_5-close_4|;
net = |close_5-open_1|;
efficiency = net/path when path>0.

bar_return_bps=(close_5/open_1-1)*10000.
poc_migration_bps=(poc_mid_t-poc_mid_t-1)/close_t*10000.

A 5m bar is structurally valid only with aggTrades, exactly five aligned 1m bars, finite required fields, VAL<=POC<=VAH, and no impossible imbalance counts.

## Frozen classifier
Copied without threshold rescue from ABSORPTION-FAILED-AUCTION-001 V0.1.1:
- rolling baseline: 2,016 prior valid 5m bars;
- extreme aggression: q95 prior abs(agg_delta_pct);
- participation: >= q75 prior agg_base_volume;
- low path efficiency: <= q25;
- high path efficiency: >= q75;
- low displacement: <= q25 prior abs(bar_return_bps);
- FAILED_AUCTION: extreme + low path efficiency + d*POC_migration<=0 + weak displacement;
- EFFICIENT_ACCEPTANCE: extreme + high path efficiency + d*POC_migration>0 + d*bar_return_bps>0;
- cooldown: 60 minutes / 12 bars;
- unclassified extremes and cooldown-suppressed candidates cannot enter the primary groups.

## Frozen outcomes
Outcome clock starts at event-bar close.
For H in {5,15,30,60,240} minutes:
R_H = d * (close_T+H / close_T0 - 1) * 10000.
Primary horizon: R60.
No PnL, stop, target, leverage, sizing, fees or slippage is part of this mechanism test.

## Frozen split
Discovery:
- warmup/source context: December 2023;
- evaluable events: 2024-01-01 through 2024-12-31 UTC.

OOS:
- opened only if Discovery returns MECHANISM_SURVIVES;
- warmup/source context: December 2024;
- evaluable events: 2025-01-01 through 2025-12-31 UTC.
No rule, threshold, source semantic, feature definition or adjudication criterion may change between Discovery and OOS.

## Minimum evidence and primary gate
For each phase independently:
- >=100 FAILED_AUCTION;
- >=100 EFFICIENT_ACCEPTANCE;
- >=30 distinct UTC event dates;
- >=99% structurally valid 5m source coverage;
- >=99% R60 coverage in each group;
- zero unresolved source conflicts.

MECHANISM_SURVIVES requires all:
1. median FAILED_AUCTION R60 < 0;
2. median EFFICIENT_ACCEPTANCE R60 > 0;
3. median contrast EA-FA > 0;
4. deterministic 10,000-resample event bootstrap 95% CI lower bound >0;
5. FAILED_AUCTION reversal rate >50% and Wilson lower95 >50%;
6. EFFICIENT_ACCEPTANCE continuation rate >50% and Wilson lower95 >50%.

Seed: 20260924.

Discovery failing the gate => stop before OOS.
Discovery passing but OOS failing => OOS_FAILED.
Both passing => OOS_REPLICATED_MECHANISM.

## Anti-rescue
After Discovery outcomes are opened:
- no row-size change;
- no alternate VA algorithm;
- no alternate imbalance definition;
- no threshold/quantile/cooldown/horizon change;
- no session, volatility, side or date filtering;
- no lag shift;
- no source swap;
- no event subgroup rescue;
- no OOS opening after a failed Discovery.

Any changed design requires a new lab ID and new pre-outcome freeze.

## Authority
Historical mechanism research only.
No edge promotion by itself.
No live trading.
No order routing.
No exchange mutation.
No merge to main.
