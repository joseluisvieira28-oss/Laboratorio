# DUAL-LST-RV-001 — GOVERNANCE DECISION TREE V0.1

Frozen: 2026-09-27

## Gate 1 — Authoritative source V0.1B

Required:
DUAL_LST_RV_001_SOURCE_GATE_RECEIPT_V0.1B.json
classification == SOURCE_PASS.

Only V0.1B is authoritative.
Original V0.1 results are diagnostic-only.

PASS requires:
- rETH anchor valid 4/4;
- wstETH anchor valid 4/4;
- stETH totalSupply == getTotalPooledEther >0 at 4/4;
- at least one direct rETH/wstETH pool valid and liquid 4/4;
- blockHash-pinned EIP-1898 historical state;
- zero unresolved selected-path source errors.

If BLOCKED:
close exact direct-market lab.
No synthetic rETH/ETH divided by wstETH/ETH rescue.

## Gate 2 — Predictor census

Required:
PREDICTOR_CENSUS_PASS.

Frozen:
- deterministic direct-pool selection rule;
- exact 556 blocks;
- exact common-numeraire NAV;
- direct market price only;
- 556/556 valid.

If BLOCKED after transport-only retry:
close exact lab.
No cadence/pool/imputation rescue.

## Gate 3 — q10/q90 calibration

Required:
PREDICTOR_STATE_CALIBRATION_PASS.

No alternative quantile, z-score or volatility normalization rescue.

## Gate 4 — Discovery predictor sample

Required:
DUAL_LST_PREDICTOR_SAMPLE_PASS.

Frozen:
- 139 Discovery blocks;
- predecessor 23,992,800;
- transition-only de-clustering;
- >=20 events total;
- >=6 cheap;
- >=6 rich.

If insufficient:
close exact lab as DUAL_LST_PREDICTOR_INSUFFICIENT_SAMPLE.
Do not widen thresholds, change cadence or drop one tail.

## Gate 5 — Mechanism Discovery

Only Gate 4 PASS may open future d values at:
- +7,200 blocks primary;
- +21,600 blocks diagnostic.

PASS requires all pre-frozen conditions:
- pooled mean signed closure >0;
- 10,000-bootstrap 95% lower bound >0;
- cheap-tail mean >0;
- rich-tail mean >0.

If FAIL:
close exact mechanism.
No direction/horizon/pool/threshold rescue.

If insufficient after outcome availability:
close exact Discovery path.

## Gate 6 — OOS

Region:
25,000,000 <= entry block < 26,000,000.

OOS remains CLOSED until a separate authority is frozen after Discovery PASS.

No OOS tuning.

## Gate 7 — Protected holdout

entry block >=26,000,000.

Remains CLOSED until separate prior-gate authority.

## Executable economics

Even mechanism/OOS/holdout PASS does not authorize PnL or live trading.

Execution costs, financing, position sizing and route must be frozen separately before any PnL test.

## Permanent firewall

No gate authorizes:
- live orders;
- exchange/wallet mutation;
- main merge.

Promotion credit remains 0 unless later governance explicitly changes it.
