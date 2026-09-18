# AAVE-LIQUIDATION-OVERHANG-001 — R1 V0.3 RECONSTRUCTION SCIENTIFIC STOP

Date: 2026-09-18
Canonical continuation run: 35378904880
Pinned continuation head: 1ec8c78b492b10108c92472f3bbcb49f99e3b9ec
Canonical audit precondition: V0.2E run 35378692311 — R1_AUDIT_PASS

## Final route classification

RECONSTRUCTION_RECONCILIATION_FAILURE / SCIENTIFIC_STOP

This is NOT NO_EDGE and is NOT a market-outcome verdict.

## Triggering evidence

The first terminal scientific failure in R1 V0.3 occurred in reserve replay shard 5.

Job:
- 105710172163

Artifact:
- AAVE_R1_V03_RESERVE_SHARD_5
- artifact ID 10562210914
- artifact ZIP digest sha256:c0e422f2e3feb54e0d9509067e20ac4d3968ffd4645bbc3430abebb2b90064cd

Receipt:
- classification: RECONSTRUCTION_RECONCILIATION_FAILURE
- canonical logs: 115719
- reserves: 4
- negative states: 0
- reserve-index decreases: 0
- collateral-flag violations: 3
- health factor computed: false
- liquidation overhang computed: false
- future liquidation outcomes computed: false
- market prices opened: false
- returns opened: false
- PnL opened: false
- 2025/2026 accessed: false

Exact violations:
1. reserve 0xae78736cd615f374d3085123a210448e74fc6393 / user 0xb5b29320d2dde5ba5bafa1ebcd270052070483ec
   reason: collateral_flag_true_with_zero_scaled_atoken_at_tx_end
2. reserve 0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee / user 0xa16eec8476d15caf3908a0eef9458a79908f15b5
   reason: collateral_flag_true_with_zero_scaled_atoken_at_tx_end
3. reserve 0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee / user 0xa16eec8476d15caf3908a0eef9458a79908f15b5
   reason: collateral_flag_true_with_zero_scaled_atoken_at_tx_end

## Governance adjudication

The frozen Reconstruction Gate Authority requires collateral enabled/disabled state changes to be time ordered and compatible with reconstructed holdings before RECONSTRUCTION_DATA_PASS.

That mandatory reconciliation condition failed.

Per the user's 18 Sep 2026 continuation authority:
- provenance/reconciliation failure => STOP scientific on this route;
- preserve the verdict;
- do not force a rescue.

Therefore:
- do NOT patch or rerun shard 5 to obtain a pass;
- do NOT reinterpret the failure as a transport timeout;
- do NOT proceed to canonical aggregate as if all shards passed;
- do NOT compute health factor;
- do NOT compute liquidation distance or liquidation overhang;
- do NOT open future liquidation outcomes;
- do NOT create or execute FINAL_PRE_DISCOVERY_PROTOCOL for this route;
- do NOT open market returns or PnL;
- do NOT open 2025/2026;
- do NOT perform live trading, orders, wallets, exchange mutation or main merge.

Any future attempt to answer the economic hypothesis would require a separately justified, prospectively frozen reconstruction route that does not rewrite this V0.3 failure. This closeout does not authorize such a route.

## Scientific meaning

The market hypothesis remains UNTESTED because the source/state reconstruction gate failed before predictor or outcome construction.

Canonical status for this route:
RECONSTRUCTION_RECONCILIATION_FAILURE / SCIENTIFIC_STOP / NOT_NO_EDGE
