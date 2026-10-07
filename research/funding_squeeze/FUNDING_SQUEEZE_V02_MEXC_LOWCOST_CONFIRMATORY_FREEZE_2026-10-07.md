# FUNDING-SQUEEZE-001
## V0.2 MEXC LOW-COST EXTERNAL CONFIRMATORY FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE MEXC HISTORICAL BTC FUNDING/PRICE OUTCOMES

### Why this version exists
Binance Development V0.1 found no viable specification at the frozen 30 bps retail spot+perp hurdle, but the pre-frozen diagnostic showed that q90 / 168h / FIXED had enough gross carry to be economically interesting at materially lower all-in costs.

V0.2 is a NEW external-venue confirmatory experiment. It does not lower the cost of V0.1 and does not reopen Binance 2025.

### Venue / instrument
MEXC
- Spot: BTCUSDT
- USDT-M perpetual: BTC_USDT

### Confirmatory calendar
Primary outcome window:
- 2024-01-01 00:00 UTC through 2025-12-31 23:59 UTC.

History needed only for causal threshold initialization may begin before 2024.
All 2026 historical outcome values are forbidden.
Signals whose required exit would reach 2026 are excluded before outcome construction.

### Sources
Public unauthenticated official MEXC market endpoints only:
- realized funding history: GET /api/v1/contract/funding_rate/history
- spot 1h klines: GET /api/v3/klines
- futures 1h klines: GET /api/v1/contract/kline/BTC_USDT

No account/private endpoint.

### Frozen signal copied from the Binance Development candidate
At a settled BTC perpetual funding timestamp t:
- realized funding rate > 0;
- realized funding rate >= past-only trailing 90th percentile of the prior 540 settled funding observations;
- minimum trailing history = 270;
- current observation excluded from its own threshold.

Entry:
- t + 1 hour;
- long spot BTCUSDT / short BTC_USDT perpetual;
- notionally 1 BTC each;
- use the corresponding 1h OPEN;
- one active position at a time.

Exit:
- FIXED 168 hours after entry.
- no dynamic exit and no optimization on MEXC outcomes.

Funding receipts:
- every realized settlement strictly after signal t and <= exit while position is live;
- positive rate is received by the short; negative is paid.

### PnL
Normalize to initial spot notional:
[(spot_exit - spot_entry) + (perp_entry - perp_exit) + sum(funding_rate_i * perp_price_at_settlement_i)] / spot_entry

### Frozen cost model
Primary all-in round trip hurdle:
- 15 bps.

Stress:
- 20 bps.

Rationale is prospective low-cost maker-oriented execution, not a claim of guaranteed fills. Current public MEXC fee information shows a low-fee spot/futures structure but venue/channel/region can differ.

No zero-fee assumption is allowed.

### Confirmatory gates
SURVIVES_LOW_COST_REPLICATION requires ALL:
1. source coverage/integrity PASS;
2. N >= 50 non-overlapping trades;
3. mean net15 > 0;
4. PF net15 >= 1.10;
5. circular block-bootstrap 95% lower bound of mean net15 > 0;
6. 2024 mean net15 > 0;
7. 2025 mean net15 > 0;
8. mean net20 > 0;
9. zero 2026 outcome access;
10. no rule changes after outcome access.

Bootstrap:
- 10,000;
- circular block length 5 trades;
- seed 20261007.

Verdicts:
- SOURCE_BLOCKED
- LOW_COST_REPLICATION_FAIL
- SURVIVES_LOW_COST_REPLICATION

Even SURVIVES is research-only and NOT live-trading authority because maker fill probability, legging risk, depth/slippage and actual user-specific fees are not modeled.

### Governance
- main unchanged;
- no live trading/orders/wallets/account reads/private endpoints;
- no exchange mutation/spending;
- no 2026 outcome data;
- no post-outcome tuning.
