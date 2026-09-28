# CBBTC-ETH-MINT-BURN-FLOW-001 — PROSPECTIVE FORWARD POST-H1 PRE-OPEN FREEZE V0.1

Frozen: 2026-09-28
Status: PREPARED / NOT ARMED / NO FORWARD DATA OPENED BY THIS FREEZE

## Parent state

Parent Discovery:
- FLOW_DISCOVERY_PASS (2025)

Independent H1-2026 OOS:
- OOS_PREDICTOR_CENSUS_PASS
- OOS_INSUFFICIENT_SAMPLE
- BTC H1-2026 prices were NOT opened
- H1 closeout is immutable and receives zero OOS promotion credit

This forward plan is NOT a rescue of H1.

## Prospective boundary

To avoid retrospective reuse of already elapsed H2-2026 data:

- no cbBTC Transfer-log scan for 2026-07-01 through 2026-09-28;
- no BTC outcome access for 2026-07-01 through 2026-09-28;
- 2026-09-29 is predecessor/state-anchor day only;
- first forward event-eligible UTC day = 2026-09-30.

A single exact circulating-supply anchor immediately before 2026-09-29T00:00:00Z is permitted only to initialize prior_supply for the first observed day. It carries zero event/outcome credit and must be EIP-1898 blockHash-bound.

## Frozen predictor

Unchanged from Discovery/OOS:

f_t = (mint_t - burn_t) / prior_supply_t

Ethereum mainnet cbBTC:
0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf

Mint:
ERC-20 Transfer from zero address.

Burn:
ERC-20 Transfer to zero address.

No exchange-wallet heuristics, clustering, other networks, bridges or ordinary-transfer substitutions.

## Frozen thresholds

Reuse exact pre-outcome calibration. No recalibration.

q10:
- numerator = -18316281339
- denominator = 1601692985627

q90:
- numerator = 35266522085
- denominator = 1057456895899

States:
- NEGATIVE_EXTREME iff f_t <= q10
- POSITIVE_EXTREME iff f_t >= q90
- NEUTRAL otherwise

## Frozen transition logic

Transition-only de-clustering remains unchanged.

Event occurs only when:
- current state is NEGATIVE_EXTREME and prior observed UTC day was not NEGATIVE_EXTREME; or
- current state is POSITIVE_EXTREME and prior observed UTC day was not POSITIVE_EXTREME.

2026-09-29 may establish predecessor state but cannot itself be counted as a forward event.

## Frozen forward outcome

For each event day t:

entry:
00:00 UTC of t+1

exit:
00:00 UTC of t+2

primary horizon:
24h

directional signing:
- POSITIVE_EXTREME: +raw BTC return
- NEGATIVE_EXTREME: -raw BTC return

Price source:
official Binance public historical BTCUSDT Spot 1d UTC archives / source equivalent already frozen by parent, checksum-verified where available.

72h remains diagnostic only and cannot rescue the primary.

## Interpretation firewall

Forward events may be collected as they resolve, but no promotion/adjudication verdict may be issued until the accumulated post-boundary sample contains at least:

- 20 outcome-eligible transition events total;
- 6 NEGATIVE_EXTREME;
- 6 POSITIVE_EXTREME.

Before that threshold the only valid state is:
FORWARD_COLLECTING_INSUFFICIENT_SAMPLE.

No early win-rate, mean-return, bootstrap or promotion interpretation may be used for governance.

## Final forward gate once sample minimum is reached

Use the same contract as Discovery:

- pooled mean signed_return_24h > 0;
- bootstrap 95% lower bound > 0;
- POSITIVE_EXTREME mean signed return > 0;
- NEGATIVE_EXTREME mean signed return > 0;
- 10,000 deterministic event-row bootstrap resamples;
- seed = 20260926.

Possible terminal evaluation states:
- FORWARD_PASS
- FORWARD_FAIL

Until the minimum sample is reached:
- FORWARD_COLLECTING_INSUFFICIENT_SAMPLE

## No-rescue rules

Do not:
- import Jul–Sep 2026 historical event rows;
- count 2026-09-29 as an event;
- widen q10/q90;
- change de-clustering;
- drop a tail;
- alter direction;
- alter the 24h primary;
- switch venue because of results;
- lower the 20 / 6 / 6 gate;
- splice H1 observations into the forward sample.

## Authority boundary

This freeze alone does NOT authorize the forward collector to open data.

A separate explicit FORWARD_OPEN authority is required before:
- reading 2026-09-29+ cbBTC logs;
- resolving forward BTC outcomes;
- scheduling a recurring collector.

No PnL, sizing, live trading, orders, exchange/wallet mutation or main merge are authorized.
