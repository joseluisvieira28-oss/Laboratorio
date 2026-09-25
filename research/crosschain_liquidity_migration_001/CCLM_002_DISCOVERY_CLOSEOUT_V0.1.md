# CCLM-CCTP-SETTLED-FLOW-002 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-25
Parent: CROSSCHAIN-LIQUIDITY-MIGRATION-001

## Frozen verdict

NO_EDGE_DISCOVERY

OOS: CLOSED
Protected holdout: CLOSED
Promotion credit: ZERO

## Source chain that passed before outcomes

- CCTP V1 Ethereum <-> Avalanche native-USDC completed settlements.
- Full frozen historical source corpus 2023-05 through 2024-12:
  7,397 canonical settled flows.
- 20 / 20 months present.
- 0 semantic mismatches after the contract-order batch parser correction.
- Binance AVAXUSDT / BTCUSDT 1h target-source integrity gate: PASS.
- Outcome-blind Discovery predictor viability:
  89 independent triggers, above frozen minimum 30.

## Frozen primary Discovery

Period:
2023-05-01 through 2023-12-31 UTC.

Predictor:
- signed completed CCTP flow to Avalanche;
- 720h trailing median/MAD;
- >=672 prior hours;
- |robust z| >= 3;
- 6h de-clustering.

Primary target:
signed AVAX/BTC relative log return over 4h.

Null:
10,000 independent monthly circular shifts of RAW hourly flow;
predictor and de-clustering recomputed from scratch for every permutation;
NumPy PCG64 seed 20260924;
positive rotation np.roll(+k).

## Result

Independent primary samples: 89.

Observed mean signed 4h relative log return:
0.001658689493784451.

Valid nulls:
10,000 / 10,000.

Null statistics >= observed:
6,205.

One-sided empirical p:
0.6205379462053795.

Frozen survival threshold:
p <= 0.05 and observed effect > 0.

Result:
FAIL.

The observed primary effect is not unusual under the frozen null. The null mean,
0.002301766038355704, is itself above the observed statistic.

## Secondary descriptive horizons

1h:
mean signed relative log return = -0.0008157779946732809.

12h:
mean = 0.009810215676895384.

24h:
mean = 0.01810184117179924.

These horizons were explicitly secondary/descriptive. They did not receive the
frozen primary null test and cannot rescue the failed 4h hypothesis.

No post-outcome change to:
- threshold;
- lookback;
- de-clustering;
- flow sign;
- horizon;
- target;
- date split;
- null;
is permitted.

## Final scientific interpretation

Completed native-USDC migration through CCTP is reconstructable historically and
the source pipeline is scientifically useful.

But the frozen hypothesis that extreme signed completed CCTP flow predicts the
predeclared 4h AVAX/BTC relative response did not survive Discovery.

Therefore:
CCLM-CCTP-SETTLED-FLOW-002 = NO_EDGE_DISCOVERY.

Do not open 2024-H1 OOS.
Do not open protected 2024-H2 holdout.
Do not promote.
Do not rescue using the positive 12h/24h descriptive numbers.

No live trading, PnL, bridge mutation, exchange mutation or main merge occurred.
