# CCLM-002 DISCOVERY PREDICTOR VIABILITY GATE V0.1

Frozen: 2026-09-25
Price outcomes: CLOSED

## Preconditions

Required before execution:
- FULL_HISTORICAL_SETTLED_FLOW_SOURCE_PASS;
- canonical batch parser technical amendment V0.1A.

The target-market source may be validated independently, but no AVAX/BTC price
value is opened by this gate.

## Source interval

Only the already frozen Discovery period:
2023-05-01T00:00:00Z through 2023-12-31T23:59:59Z.

Reconstruct the same canonical completed CCTP V1 native-USDC settlements.

Settlement event time:
destination-chain block timestamp containing canonical MessageReceived /
MintAndWithdraw completion.

Signed flow:
- Ethereum -> Avalanche: + amount_atomic
- Avalanche -> Ethereum: - amount_atomic

Aggregate to every UTC hour. A zero-flow hour is a true zero because every
Discovery month already belongs to the passing complete historical source corpus.

## Frozen predictor, unchanged

For each hour h:
- trailing window: previous max 720 hourly observations;
- require >=672 valid prior hours;
- trailing median;
- MAD = median(abs(x - median));
- if MAD == 0: no trigger;
- robust_z = (NET_h - median) / (1.4826 * MAD);
- raw trigger iff abs(robust_z) >= 3.0.

De-cluster:
after accepting one trigger, ignore further trigger hours for the next 6 hours.

## Gate

DISCOVERY_PREDICTOR_SAMPLE_PASS:
>=30 independent de-clustered triggers.

INSUFFICIENT_SAMPLE:
<30 independent de-clustered triggers.

If INSUFFICIENT_SAMPLE:
- do not open any AVAX/BTC price outcome;
- do not change threshold, lookback, MAD rule or de-clustering;
- do not rescue with amount quantiles or one-sided flow.

This gate earns zero promotion credit.
