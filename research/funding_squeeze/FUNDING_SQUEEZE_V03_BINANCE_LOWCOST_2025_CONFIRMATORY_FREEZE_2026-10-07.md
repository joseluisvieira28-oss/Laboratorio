# FUNDING-SQUEEZE-001
## V0.3 BINANCE LOW-COST 2025 CONFIRMATORY FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE 2025 CASH-AND-CARRY OUTCOMES

### Purpose
Test the single low-cost candidate motivated by V0.1 Development without altering the failed 30 bps Binance verdict.

### Development-selected specification
Venue: Binance.
Symbol: BTCUSDT.
Position: long 1 BTC spot / short 1 BTC USD-M perpetual.

Signal at settled funding timestamp t:
- realized funding > 0;
- realized funding >= past-only trailing 90th percentile of the prior 540 funding settlements;
- minimum history 270;
- current funding excluded from its own threshold.

Entry:
- both legs at 1h OPEN at t + 1 hour.

Exit:
- FIXED 168 hours after entry.

Overlap:
- one active BTC position at a time.

Funding PnL:
- include every settlement strictly after t and <= exit while position is live.

### Confirmatory calendar
2025-01-01 00:00 UTC through 2025-12-31 23:59:59 UTC only.
History before 2025 may be used solely to initialize the causal trailing threshold.
Any trade requiring a 2026 price or funding observation is excluded.
2026 is hard-closed.

### Public/free source
Binance Data Vision official monthly archives:
- USD-M fundingRate BTCUSDT;
- USD-M BTCUSDT 1h klines;
- Spot BTCUSDT 1h klines.

All used ZIP archives require official CHECKSUM verification.

### PnL
Normalize to initial spot notional:
[(spot_exit-spot_entry) + (perp_entry-perp_exit) + sum(funding_rate_i * perp_price_at_settlement_i)] / spot_entry

### Frozen execution hurdles
Primary: 20 bps all-in round trip.
Stress: 25 bps all-in round trip.

Rationale: low-cost maker-oriented retail execution with fee discounts. This is an execution hurdle, not a guarantee of maker fills. Fill/legging risk remains outside this market-data test.

### Confirmatory verdict gates
If N < 20 independent non-overlapping trades:
INSUFFICIENT_SAMPLE_2025

Otherwise SURVIVES_2025_CONFIRMATORY_LOWCOST requires ALL:
1. source integrity PASS;
2. N >= 20;
3. mean net20 > 0;
4. PF net20 >= 1.10;
5. circular block-bootstrap 95% lower bound of mean net20 > 0;
6. first chronological half mean net20 > 0;
7. second chronological half mean net20 > 0;
8. mean net25 > 0;
9. zero 2026 access;
10. no post-outcome rule changes.

If N >=20 and any scientific gate fails:
NO_EDGE_LOWCOST_V03

Bootstrap:
- 10,000;
- circular block length 5;
- seed 20261007.

Even a survivor is RESEARCH_SURVIVOR_ONLY until maker fill probability, legging risk and actual account fee schedule are validated prospectively/shadow.

### Governance
No main merge, live trading, orders, wallets, account reads, private endpoints, exchange mutation or spending.
