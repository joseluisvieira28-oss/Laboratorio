# FUNDING-SQUEEZE-001
## V0.1 DEVELOPMENT GRID FREEZE
Date: 2026-10-07
Status: DEVELOPMENT RULES FROZEN — 2025/2026 OUTCOMES CLOSED

### Purpose
Develop one economically defensible Binance BTC spot/perpetual cash-and-carry specification using only the already-opened 2021-2024 research era. The sole purpose is to decide whether one specification deserves a genuinely untouched 2025 confirmatory test.

This is a NEW family/version. It does not relabel or rescue FUNDING-CASH-CARRY-001 V0.1.

### Economic mechanism
Extreme positive realized perpetual funding means longs paid shorts at settlement. If elevated positive carry persists, a delta-neutral long-spot / short-perpetual position can collect future funding while largely hedging BTC direction. Net economics also include spot/perp basis movement and round-trip execution cost.

### Development data
Venue: Binance.
Symbol: BTCUSDT.
Calendar: 2021-01-01 through 2024-12-31 only.
Public Binance Data Vision:
- USD-M monthly fundingRate;
- USD-M BTCUSDT 1h klines;
- Spot BTCUSDT 1h klines.

2025 and 2026 are hard-closed during Development.

### Signal
At a settled funding timestamp t:
- funding rate > 0;
- funding rate >= past-only trailing quantile of the prior 540 settlements;
- minimum trailing history 270 settlements;
- rolling series shifted by one settlement so current/future data cannot set its own threshold.

Frozen quantile grid:
- 0.85
- 0.90
- 0.95

Entry:
- long 1 BTC spot + short 1 BTC USD-M perpetual;
- both at the 1h OPEN at t + 1 hour;
- one active BTC position at a time.

### Exit grid
Frozen max-hold hours:
- 24
- 48
- 72
- 120
- 168

Frozen exit modes:
1. FIXED: exit at entry + max-hold hours.
2. STOP_NONPOSITIVE: after entry, remain positioned until the first subsequently SETTLED funding observation <= 0, then exit at the next 1h open; otherwise exit at the max-hold boundary.

STOP_NONPOSITIVE is causal: the rate is used only after it has settled. If it is negative, that settlement is included in funding PnL because the position was still open.

No predicted funding is used.

### PnL
Gross normalized to initial spot notional:
[(spot_exit - spot_entry) + (perp_entry - perp_exit) + sum(funding_rate_i * perp_price_at_settlement_i)] / spot_entry

Funding settlements included:
strictly after signal t and <= final exit decision settlement/time while the position is live.

Primary execution hurdle:
- 30 bps all-in round trip.

Diagnostics only:
- gross;
- 10 bps all-in round trip;
- funding component;
- basis-price component.

A low-cost diagnostic may NOT promote a candidate that fails 30 bps.

### Development eligibility
For each grid cell:
- N >= 60 non-overlapping trades;
- mean net30 > 0;
- profit factor net30 >= 1.10;
- circular block-bootstrap 95% lower bound of mean net30 > 0;
- at least 3 positive calendar-year mean net30 values.

Bootstrap:
- 10,000 resamples;
- circular block length 5 trades;
- seed 20261007.

### Candidate selection
If multiple grid cells pass ALL Development gates:
1. choose the cell with highest bootstrap 95% lower bound;
2. tie-break: higher mean net30;
3. then shorter max hold;
4. then stricter quantile.

If no cell passes every gate:
VERDICT = NO_VIABLE_CONFIRMATORY_SPEC
and 2025 remains unopened.

If one cell is selected:
VERDICT = DEVELOPMENT_CANDIDATE_SELECTED
and a separate immutable 2025 PRE-OUTCOME CONFIRMATORY FREEZE must be committed before any 2025 funding/spot/perp value is opened.

### Governance
- research only;
- no main merge;
- no live trading/orders/wallets/account reads/private endpoints;
- no exchange mutation/spending;
- 2025/2026 closed;
- no post-Development change to this grid.
