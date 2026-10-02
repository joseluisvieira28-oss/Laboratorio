# OPTIONS MULTI-ASSET — SOURCE GATE CHECKLIST V0.1

Status: PREPARATION ONLY  
Assets: ETH / SOL / XRP  
BTC is excluded from this new-source checklist because its existing V2.1 source identity is preserved.

For each new hook, the Source/Data Gate must close independently before any outcome evaluation.

## Required source proofs

- Exact options instrument naming and parsing demonstrated.
- Underlying/index field identified and timestamp-safe.
- IV field definition and units demonstrated.
- Trade timestamps proven UTC-consistent.
- Expiry and strike parsing proven.
- DTE derivation proven without future information.
- Moneyness calculation proven from information available at the trade timestamp.
- Duplicate trade-ID handling defined.
- Pagination completeness / truncation behavior tested.
- Historical date coverage measured before outcome calculations.
- Raw-source hashes or equivalent reproducible manifests recorded.
- No protected OOS/holdout rows accessed during Development.
- Fail-closed behavior for missing, zero, non-finite or schema-drifted IV/index values.
- Differences in option settlement / inverse / linear conventions documented per asset.

## Per-hook artifacts required before Development

### ETH
- OPTIONS_ETH_001_SOURCE_FREEZE_V0.1
- OPTIONS_ETH_001_SOURCE_GATE_RECEIPT_V0.1
- OPTIONS_ETH_001_PRE_OUTCOME_SCIENCE_FREEZE_V0.1

### SOL
- OPTIONS_SOL_001_SOURCE_FREEZE_V0.1
- OPTIONS_SOL_001_SOURCE_GATE_RECEIPT_V0.1
- OPTIONS_SOL_001_PRE_OUTCOME_SCIENCE_FREEZE_V0.1

### XRP
- OPTIONS_XRP_001_SOURCE_FREEZE_V0.1
- OPTIONS_XRP_001_SOURCE_GATE_RECEIPT_V0.1
- OPTIONS_XRP_001_PRE_OUTCOME_SCIENCE_FREEZE_V0.1

## Execution-feasibility separation

Source/Data Gate PASS does not imply MEXC execution feasibility.

Execution feasibility is a separate prospective check against the asset-specific perpetual contract at signal time. A hook may remain scientifically active while real-money execution is CAPITAL_FEASIBILITY_BLOCKED.

## Forbidden shortcuts

- Reusing BTC results as ETH/SOL/XRP evidence.
- Copying BTC thresholds after viewing new-asset outcomes.
- Raising the micro-live cap to overcome a venue minimum without a new authority.
- Converting a blocked asset signal into another asset.
- Treating a missing/invalid options source as NO_EDGE.
