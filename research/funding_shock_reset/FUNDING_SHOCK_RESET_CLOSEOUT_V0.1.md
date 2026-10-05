# FUNDING-SHOCK-RESET-001 — SCIENTIFIC CLOSEOUT V0.1

Date: 2026-10-05
Branch: `funding-shock-reset-v0.1-prereg-2026-10-05`
Status: **CLOSED — NO_EDGE_V0.1**
Promotion: **PROHIBITED**

## Authority chain

Pre-outcome freeze commit:
`e8c4a302a1c2ce1f8d5e80f89bcefb079827d22c`

Frozen runner commit:
`ddff4396fcf79c98629231044e9732d9b984239a`

Workflow commit:
`2fe81747f0eee09959a74bc10e8503f1bae9e92e`

Serialization-only technical fix:
`cf30382ffa3bdfd370eb1a6e675215a6eb1122d0`

The technical fix changed only conversion of NumPy boolean gate values to native Python booleans for JSON serialization. It did not alter signals, thresholds, horizons, costs, source selection, universe, outcomes, or gates.

Authoritative successful GitHub Actions run:
`37337686278`

Authoritative artifact:
`funding-shock-reset-v01-receipts`
Artifact ID: `11356514606`
Artifact SHA-256 digest:
`b0cec49eefef21f1a8a5b9217795855748f49664c1d7452e5c837ec7e4b514bd`

## Source integrity

**PASS**

Official Binance Data Vision monthly USD-M archives were retrieved for:
- BTCUSDT 5m klines, 2021-01 through 2025-12;
- BTCUSDT funding rates, 2021-01 through 2025-12;
- ETHUSDT 5m klines, 2021-01 through 2025-12;
- ETHUSDT funding rates, 2021-01 through 2025-12.

Every downloaded archive was verified against its official `.CHECKSUM` sidecar before use.

Coverage:
- BTCUSDT klines: 525,888 rows
- BTCUSDT funding observations: 5,478
- ETHUSDT klines: 525,888 rows
- ETHUSDT funding observations: 5,478
- 2026 outcomes opened: **0**

## Frozen signal

No post-outcome changes were made.

- `abs(funding_rate) >= 0.05%`
- `abs(pre_60m_return) >= 0.50%`
- positive funding + positive momentum => SHORT after settlement
- negative funding + negative momentum => LONG after settlement
- entry: open of T0 + 5m bar
- primary exit: 4h
- primary round-trip friction stress: 8 bps
- primary evidence unit: equal-weight portfolio by distinct funding timestamp

## Result

Distinct primary event timestamps: **38**
Symbol-level signals:
- BTCUSDT: **19**
- ETHUSDT: **29**

Signal concentration by year:
- 2021: 37 symbol-level signals
- 2022: 1
- 2023: 1
- 2024: 9
- 2025: 0

### Primary 4h result

Gross mean:
**+27.45 bps/event**

Net mean after frozen 8 bps round-trip friction:
**+19.45 bps/event**

Win rate:
**60.5%**

Gross compounded event sequence:
**+9.53%**

Net@8bps compounded event sequence:
**+6.25%**

Break-even round-trip friction:
**27.45 bps**

### Cost stress

- 4 bps RT: +23.45 bps/event
- 8 bps RT: +19.45 bps/event
- 12 bps RT: +15.45 bps/event

### Asset replication

- BTCUSDT: N=19, mean 4h **+30.71 bps**, win 63.2%
- ETHUSDT: N=29, mean 4h **+15.44 bps**, win 51.7%

Both asset means are positive.

### Frozen robustness gates

- source_integrity: **PASS**
- min_n_40: **FAIL** — only 38 distinct event timestamps
- mean_gross_positive: **PASS**
- mean_net8_positive: **PASS**
- bootstrap_lower_positive: **FAIL**
- all_thirds_positive: **FAIL**
- btc_eth_same_sign_if_n10: **PASS**
- no_2026: **PASS**

95% UTC-day block-bootstrap CI for net@8bps mean:
**[-65.51, +98.09] bps**

Chronological thirds, net @ 8 bps:
1. N=13, mean **+19.93 bps**, compound +1.63%
2. N=13, mean **+38.88 bps**, compound +4.89%
3. N=12, mean **-2.11 bps**, compound -0.32%

The apparent aggregate profitability is therefore not statistically or temporally robust under the preregistered gate.

## Scientific verdict

**NO_EDGE_V0.1**

This family produced a high-quality false-positive candidate: attractive average returns, positive BTC and ETH replication, and apparent capacity to tolerate realistic friction, but insufficient independent observations, a confidence interval crossing zero, severe event concentration in 2021, zero qualifying signals in 2025, and failure of the final chronological third.

The result MUST NOT be promoted, traded, tuned, threshold-relaxed, or relabelled as an edge.

The correct interpretation is:

> Mechanism remains economically interesting, but V0.1 did not establish a reproducible trading edge.

Any future funding-shock research must be a separately preregistered version with a legitimate untouched dataset or prospective forward observation. The opened 2021–2025 outcomes may not be reused as an untouched validation set.

## Governance

- no merge to main;
- no live trading;
- no orders;
- no account/private endpoints;
- no wallets;
- no exchange mutation;
- no post-outcome tuning;
- 2026 remains unopened by this experiment.
