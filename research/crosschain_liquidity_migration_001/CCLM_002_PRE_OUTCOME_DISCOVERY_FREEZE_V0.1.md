# CCLM-002 PRE-OUTCOME DISCOVERY FREEZE V0.1

Frozen: 2026-09-24
Parent: CROSSCHAIN-LIQUIDITY-MIGRATION-001
Child: CCLM-CCTP-SETTLED-FLOW-002
Outcome access at freeze: CLOSED

Execution condition:
DO NOT open price outcomes unless
CCLM_CCTP_SETTLED_FLOW_002_FULL_HISTORICAL_RECEIPT.json classifies
FULL_HISTORICAL_SETTLED_FLOW_SOURCE_PASS.

## Economic object

Canonical events are completed CCTP V1 native-USDC settlements only.

Signed flow convention:
- Ethereum -> Avalanche settlement: + amount_atomic / 1e6 USD nominal
- Avalanche -> Ethereum settlement: - amount_atomic / 1e6 USD nominal

Aggregate into fixed UTC hourly buckets.

Hours with zero canonical settlements are true zero only after the monthly
source reconstruction for that month passes.

## Predictor

For hour h:
NET_CCTP_USDC_AVAX_h = signed completed USDC flow in hour h.

Trigger score uses only strictly prior values:
robust_z_h = (NET_h - trailing_median) / (1.4826 * trailing_MAD)

Trailing window:
- 30 calendar days = 720 hourly observations;
- require at least 672 valid prior hours (28 days);
- if MAD = 0, no trigger.

Frozen trigger:
abs(robust_z_h) >= 3.0

No alternative thresholds are tested in V0.1.

Trigger sign:
- positive z => net completed USDC migration into Avalanche;
- negative z => net completed USDC migration out of Avalanche.

## Target

Primary target:
signed AVAX relative-to-BTC forward log return.

Use Binance official historical spot archives:
- AVAXUSDT
- BTCUSDT

Hourly close construction must be independently integrity-checked before
joining to flow events.

relative_return_H =
log(AVAXUSDT[t+H] / AVAXUSDT[t]) -
log(BTCUSDT[t+H] / BTCUSDT[t])

Signed continuation statistic:
sign(trigger) * relative_return_H

Primary horizon:
4 hours.

Secondary descriptive horizons, multiplicity-labelled and NOT independent
promotion routes:
1h, 12h, 24h.

The primary scientific decision is 4h only.

## Temporal alignment

Flow in UTC hour h is finalized at h+1:00.
Entry/measurement timestamp t is the first complete hourly market close at or
after the end of hour h.

No price from inside trigger hour h may enter the forward target.

## Frozen periods

DISCOVERY:
2023-05-01T00:00:00Z through 2023-12-31T23:59:59Z

OOS:
2024-01-01T00:00:00Z through 2024-06-30T23:59:59Z

PROTECTED HOLDOUT:
2024-07-01T00:00:00Z through 2024-12-31T23:59:59Z

The protected holdout MUST remain unopened unless Discovery and OOS both satisfy
the survival rule below.

No 2025 or 2026 market data is authorized.

## Discovery minimum / null

Minimum:
>=30 independent trigger hours after a 6-hour de-clustering rule.

De-clustering:
after accepting one trigger, ignore further triggers for the next 6 hours.

Primary null:
within each calendar month, circularly shift the entire hourly flow series by a
uniform offset drawn from [48h, month_length-48h], preserving autocorrelation
and the market-return series.

Use exactly 10,000 deterministic permutations with seed 20260924.

Primary statistic:
mean signed 4h relative return across accepted triggers.

One-sided empirical p-value:
(1 + null_stats >= observed count) / (10001).

## Survival rule

DISCOVERY_SURVIVES only if:
- >=30 independent triggers;
- observed mean signed 4h relative return > 0;
- one-sided permutation p <= 0.05.

If Discovery fails:
NO_EDGE_DISCOVERY. Do not open OOS.

OOS_SURVIVES only if, using the exact frozen predictor and trigger:
- >=15 independent OOS triggers;
- mean signed 4h relative return > 0;
- one-sided permutation p <= 0.05.

If OOS fails:
NO_EDGE_OOS. Do not open holdout.

Only after both survive may the protected 2024-H2 holdout be opened under a
separate explicit holdout receipt using these same rules.

## Anti-rescue rules

Forbidden after any outcome is seen:
- changing 3.0 threshold;
- changing 30-day lookback;
- changing 6h de-clustering;
- replacing 4h primary horizon;
- switching AVAX/BTC to AVAX/USD or another coin;
- conditioning on flow size quantiles, day-of-week, volatility, funding or trend;
- changing date partitions;
- selecting only one flow direction;
- excluding adverse events except for pre-frozen source-integrity reasons.

## Allowed verdicts

SOURCE_BLOCKED
INSUFFICIENT_SAMPLE
NO_EDGE_DISCOVERY
DISCOVERY_SURVIVES
NO_EDGE_OOS
OOS_SURVIVES_PENDING_HOLDOUT

No trading, PnL, live execution or promotion is authorized by this freeze.
