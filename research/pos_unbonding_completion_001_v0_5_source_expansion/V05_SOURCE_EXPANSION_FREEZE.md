# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.5 SOURCE EXPANSION FREEZE

Date: 2026-10-07
Parent V0.4 closeout: 89fd41525e81ca7afb25251d66b0c71e6ef1af6c
Parent verdict: SOURCE_HISTORICAL_COVERAGE_BLOCKED
Market outcomes opened: NO

V0.5 preserves every V0.4 result and reopens only fifth-chain source qualification under a newly frozen source-only rule.

## Candidate rule frozen before candidate unbonding counts

Select Cosmos-SDK production chains that:
- were live during a material portion of 2023-2024;
- use native x/staking undelegation semantics or a version-pinned equivalent;
- have public/free archive infrastructure explicitly discoverable from official/chain-registry metadata;
- have a native token with >=12 consecutive months pre-2026 market-source capability metadata.

Deterministic order frozen now:
1. Terra 2 / LUNA (phoenix-1)
2. Archway / ARCH (archway-1)
3. Coreum / CORE (coreum-mainnet-1)

Stop at the first candidate proving two independently operated public/free historical paths plus fixed-height reconciliation and a viable complete census route. Do not inspect a later candidate's unbonding counts after an earlier candidate passes.

No candidate unbonding/completion event counts were inspected to choose this order.

## Inherited science

Completion interval: 2023-01-01 through 2024-12-31 UTC.
Materiality: M_d >= 0.001 (10 bps historical bonded native stake).
Hard bar: >=40 material chain-days TOTAL across >=5 qualifying chains.
Lifecycle: successful MsgUndelegate -> cancellation/slash/hold reconciliation -> actual complete_unbonding.
Expected maturity is not T_completion.

V0.4 dual-index evidence for ATOM and DYDX remains valid immutable source evidence. OSMO/TIA second-index failures remain evidence, not grounds to change gates.

## Firewall

No prices, returns, PnL, economic outcomes or outcome-informed search.
No live trading/orders/wallet/account/private exchange endpoints/spending.
No main changes.
No lowering materiality/sample gates.
No candidate substitution based on event counts.

Allowed source verdicts only: SOURCE_GATE_PASS, SOURCE_HISTORICAL_COVERAGE_BLOCKED, SOURCE_CENSUS_INCOMPLETE, INSUFFICIENT_INDEPENDENT_SAMPLE, MECHANISM_NOT_COMPARABLE, SOURCE_PROVENANCE_INCOMPLETE, TECHNICAL_FAILURE.
NO_EDGE is impossible in V0.5 source work.
