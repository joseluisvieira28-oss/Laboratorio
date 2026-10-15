# CBBTC-ETH-MINT-BURN-FLOW-001 — GOVERNANCE DECISION TREE V0.1

Frozen: 2026-09-26

## Gate 1 — Source

Required:
SOURCE_PASS on the exact Ethereum cbBTC zero-address mint/burn definition and the two fixed source windows.

If SOURCE_BLOCKED after transport-only remediation:
CLOSE exact lab.
Do not add Base/Arbitrum/Solana, change windows, or substitute ordinary transfers.

## Gate 2 — Full outcome-blind flow census

Required:
PREDICTOR_FLOW_CENSUS_PASS.

Must include:
- complete 2024-09-12 through 2025-12-31 zero-address ledger;
- exact daily series;
- exact start/end totalSupply reconciliation;
- zero duplicate/decode/source errors;
- 2026 unopened.

If blocked:
CLOSE exact lab.
Do not drop days, impute supply, change source or shorten period.

## Gate 3 — Flow-state calibration

Required:
FLOW_STATE_CALIBRATION_PASS.

Frozen:
- prior-supply-normalized signed daily net flow;
- calibration 2024-10-01 through 2025-06-30;
- nearest-rank q10/q90.

If q10 >= q90 or calibration is invalid:
CLOSE exact lab.
No alternate quantile/z-score/raw-flow rescue.

## Gate 4 — Outcome-blind Discovery predictor sample

Required:
FLOW_PREDICTOR_SAMPLE_PASS.

Frozen:
- H2 2025;
- transition-only de-clustering;
- >=20 events total;
- >=6 negative;
- >=6 positive.

If insufficient:
CLOSE exact lab.
Do not widen tails or change de-clustering.

## Gate 5 — 2025 BTC mechanism Discovery

Only Gate 4 PASS may open 2025 BTCUSDT Spot daily price files.

Frozen:
- POSITIVE_EXTREME expects positive next-24h BTC return;
- NEGATIVE_EXTREME expects negative next-24h BTC return;
- entry only at next UTC day;
- 24h primary;
- 72h diagnostic cannot rescue;
- events requiring any 2026 price are censored.

If outcome-eligible sample <20 / <6 per tail:
DISCOVERY_OUTCOME_INSUFFICIENT_SAMPLE — CLOSE.

If FLOW_DISCOVERY_FAIL:
CLOSE exact lab.
No sign/horizon/venue/subperiod rescue.

If FLOW_DISCOVERY_PASS:
2026 remains CLOSED pending separate OOS authority.

## Gate 6 — 2026

Protected.
No historical access merely because 2026 data are technically available.

Only a new explicit OOS authority after Discovery PASS may open 2026.

## Trading / PnL

No stage above authorizes:
- execution-cost fitting;
- PnL;
- position sizing;
- orders;
- exchange mutation;
- wallet mutation;
- main merge.

Promotion credit remains zero until later governance gates explicitly permit otherwise.
