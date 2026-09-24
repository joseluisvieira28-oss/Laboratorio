# AAVE-HF-CROWDING-001 — FORWARD CROWDING CALIBRATION FREEZE V0.1

Date frozen: 2026-09-24
Stage: OUTCOME-BLIND FORWARD CALIBRATION
Market/liquidation outcomes: CLOSED

## Daily population

At one snapshot per UTC calendar day:
1. enumerate all Aave v4 reserves from the official Aave MCP;
2. for every reserve query borrow-side `get_reserve_holders` with fixed `limit=5`;
3. deduplicate borrower wallets across reserves;
4. query `get_user_summary(version="v4")` for every deduplicated wallet;
5. define wallet health factor as the **minimum finite positive value** found under any response key whose normalized key contains `healthfactor`.

No reserve, wallet, chain or asset may be selected after values are seen.

## Frozen predictor

Primary daily crowding statistic:
- fraction of valid sampled borrower wallets with health factor **< 1.10**.

Diagnostics only:
- fraction with HF < 1.05;
- fraction with HF < 1.25;
- median borrower HF;
- valid-HF coverage.

No debt-size weighting. Every deduplicated sampled wallet has equal weight.

## Calibration gate

Collect exactly one valid snapshot per UTC day.
Do not open liquidation outcomes, BTC/ETH prices, returns, volatility or PnL during calibration.

Calibration becomes ready only after:
- >=30 distinct UTC daily snapshots;
- every counted snapshot has >=20 valid borrower HFs;
- median valid-HF coverage across snapshots >=80%.

Then freeze the nearest-rank **q90** of the primary HF<1.10 crowding statistic as the future stress threshold.

No q80/q95 rescue after outcomes.

Until then:
`HF_CROWDING_CALIBRATION_COLLECTING`

Ready state:
`HF_CROWDING_Q90_READY_TO_FREEZE`

## Safety

Read-only official Aave MCP only.
Never call prepare/action/submit/sign/cancel tools.
No wallets owned by the user are queried by intent; the cohort is protocol-defined public borrower population.
No live trading, orders, exchange mutation or main merge.
