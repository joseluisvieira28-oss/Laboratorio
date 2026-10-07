# FUNDING-SQUEEZE-001
## V0.3 SCIENTIFIC CLOSEOUT
Date: 2026-10-07
Status: CLOSED — NO_EDGE_LOWCOST_V03
Promotion: PROHIBITED

### Authority chain
V0.3 pre-outcome freeze:
- research/funding_squeeze/FUNDING_SQUEEZE_V03_BINANCE_LOWCOST_2025_CONFIRMATORY_FREEZE_2026-10-07.md
- freeze commit: 40d5ceb94725aacf0d9b73dd00bb04af18b84190

Implementation addendum:
- research/funding_squeeze/FUNDING_SQUEEZE_V031_BINANCE_DATA_VISION_IMPLEMENTATION_ADDENDUM_2026-10-07.md
- addendum commit: 21654c78a5f86fa29b974f4f8f41ca0d98d58a9e

Frozen runner commit:
- 2664a259f8871188c965bd4ff640028d66e589dc

Workflow commit / canonical head:
- b1cc6747c6a12149bb643a5785c959f1331f6e71

Canonical GitHub Actions run:
- 37680768862
- job: 112995903475
- conclusion: success

Canonical artifact:
- name: funding-squeeze-v03-binance-2025-receipt
- artifact ID: 11507939322
- digest: sha256:04e8397fe541d29fa6643ff8e03791087dde0cf4b3d9ac1eef30a966a96fbcc9

### Source integrity
PASS.

Official Binance Data Vision monthly archives with official SHA-256 sidecars:
- fundingRate BTCUSDT: 24/24 frozen months, 2024-01 through 2025-12;
- USD-M BTCUSDT 1h klines: 12/12 months in 2025;
- Spot BTCUSDT 1h klines: 12/12 months in 2025.

2025 hourly price coverage:
- perpetual: 8760 / 8760 = 100%;
- spot: 8760 / 8760 = 100%.

Funding rows available across frozen history:
- 2193.

Confirmatory trade coverage:
- eligible non-overlapping signals: 21;
- analyzable: 21;
- missing trades: 0;
- trade coverage: 100%.

2026 outcome access:
- ZERO.

### Frozen confirmatory specification
- BTCUSDT Binance
- long spot / short USD-M perpetual
- positive settled funding >= past-only trailing q90 over prior 540 settlements
- minimum history 270
- entry at t + 1h 1h-open
- fixed hold 168h
- one active position at a time
- primary all-in round-trip hurdle: 20 bps
- stress hurdle: 25 bps

No post-outcome rule change occurred.

### 2025 result
N = 21

Gross mean:
+12.3821 bps/trade

Funding component:
+12.3334 bps/trade

Spot/perpetual basis-price component:
+0.0487 bps/trade

Primary net @20 bps:
-7.6179 bps/trade

Stress net @25 bps:
-12.6179 bps/trade

Median net @20 bps:
-7.9377 bps/trade

Win rate @20 bps:
9.52%

Profit factor @20 bps:
0.0152

95% circular block-bootstrap CI for mean net @20 bps:
[-9.9312, -4.9358] bps

Chronological half 1 mean net @20:
-7.3263 bps

Chronological half 2 mean net @20:
-7.8829 bps

Mean funding settlements collected per trade:
21.0

### Frozen gate results
PASS:
- source integrity;
- N >= 20;
- zero 2026 access;
- zero post-outcome rule changes.

FAIL:
- mean net20 > 0;
- PF net20 >= 1.10;
- bootstrap lower bound > 0;
- chronological half 1 positive;
- chronological half 2 positive;
- mean net25 > 0.

### Scientific verdict
NO_EDGE_LOWCOST_V03

The 2021-2024 Development sample created a plausible low-cost carry candidate, but the untouched 2025 confirmatory sample did not reproduce sufficient gross carry to cover the pre-frozen 20 bps execution hurdle.

The failure is not caused by basis divergence:
- basis-price contribution was approximately flat (+0.0487 bps/trade).
The failure is primarily economic:
- future funding harvested after the signal averaged only +12.3334 bps over the seven-day hold, below the 20 bps primary hurdle.

The 2025 confidence interval is entirely below zero after the frozen primary cost, and both chronological halves are negative. This is not a near-pass under the frozen confirmatory standard.

### Relation to prior work
- FUNDING-SQUEEZE V0.1 Binance Development at 30 bps: NO_VIABLE_CONFIRMATORY_SPEC.
- V0.2 MEXC low-cost external replication: SOURCE_BLOCKED because public historical Spot coverage was only 69.9%, despite 100% futures-hour coverage.
- V0.3 Binance low-cost untouched 2025: NO_EDGE_LOWCOST_V03.

Therefore FUNDING-SQUEEZE-001 is CLOSED for promotion under these tested specifications.

### No rescue
Do not:
- lower the 20 bps hurdle after seeing 2025;
- select a different quantile or hold using the opened 2025 outcomes;
- add filters from the 2025 trade outcomes;
- relabel gross carry as tradable edge;
- use MEXC missing-history interpolation to manufacture replication;
- promote this family to radar/micro-live/live.

Any future funding-carry research must be a scientifically distinct, prospectively frozen mechanism or use genuinely untouched data with a materially different economic source of edge.

### Governance
- main unchanged;
- no live trading;
- no orders;
- no account/private endpoints;
- no wallets;
- no exchange mutation;
- no spending;
- no 2026 outcomes;
- no post-outcome tuning.
