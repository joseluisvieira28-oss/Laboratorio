# AAVE-GOV-LT-FORCED-DELEVERAGING-001 — V0.1 SOURCE / MECHANISM FREEZE
Date: 2026-10-06 UTC
Status: PRE-OUTCOME; SOURCE ONLY; 2026 CLOSED

## Authority and prior knowledge
Operator instruction in this session authorizes a 2022–2025 census and public historical borrower reconstruction, not operator wallet access, account reads or authenticated chain endpoints.
Base: aave-risk-parameter-shock-v0.1 at 9888f840d5cd585e0c7c05588a78bcb8cc879029.
Prior related lab is terminal for its exact 2023–2024 execution-time protocol: 72 configuration logs, 16 LT-decrease logs, 5 independent episodes, insufficient sample. Preserve its closeout. This new lab tests anticipatory borrower response during the approved/queued-to-effective interval, not post-execution liquidation pressure. Old source counts are known, old economic outcomes were never opened. Enlarging years is explicitly requested by the current operator and is recorded, not represented as fresh blind discovery.

## Fixed source universe and boundary
Census window: 2022-01-01T00:00:00Z through 2025-12-31T23:59:59Z. Ethereum V3 first. Ethereum deployment absence before activation is structural, not missingness.
Canonical Ethereum PoolConfigurator: 0x64b761d848206f447fe2dd461b0c635ec39ebb27.
Canonical base event: CollateralConfigurationChanged(address,uint256,uint256,uint256).
Do not query latest logs or 2026. Resolve terminal block with timestamp-only binary search or dated historical index, then enforce header timestamp ceiling on every returned row.
Expansion priority fixed now: Polygon, Avalanche, Arbitrum, Optimism, Base; only include a network if canonical deployment lineage, equivalent collateral/eMode semantics, governance queue linkage and historical public log/state access can be demonstrated. No outcome-based network selection.
Configuration events may be inspected to identify eligible shocks; borrower behavior, liquidation outcomes and market outcomes remain forbidden.

## Mechanism
LT reduction enters only when pre-existing collateral contribution to HF can decline under old/new configuration. LTV alone is not HF and cannot be labelled forced deleveraging: include only with an exact demonstrated constraint on existing exposure, otherwise EXCLUDED_LTV_ONLY. Cap/freeze/new-borrow restriction alone excluded. Collateral disablement with LT=0 and equivalent eMode collateral LT reductions require their own exact old/new mapping, cannot be silently omitted or substituted to rescue counts.
First per-asset observed configuration is a baseline, not a change. Require previous canonical config or historical state at signal-1; account for pool upgrades and eMode overrides before classifying actual exposure.

## Signal and effect
T_signal: first on-chain finalized approved/queued state for this immutable payload with all new parameters definitively recoverable. Payload creation, discussion, proposal creation and execution alone do not qualify.
T_effect: exact chain block/tx applying configuration. Require T_signal < T_effect and old/new parameters, reserve identities, proposal/payload linkage and chain/block/tx hashes.
For governance v2 and v3 prove their respective queue semantics separately. Direct risk steward changes without a prior approved/queued anchor are SOURCE_TIMING_INELIGIBLE.
Immutable code is not enough when dynamic calldata/state can change parameters: reproduce effective arguments at the prior signal state.

## Independence and sample gate
Same proposal, related payloads and coordinated cross-chain executions are one economic shock. Also conservatively group otherwise unresolved clusters in fixed 24-hour episodes from earliest effect timestamp; do not split to inflate n.
Need >=12 independent fully defensible shocks. Count raw configuration events and potential shocks separately from accepted governance shocks. Incomplete lineage is not zero and never establishes a full-universe insufficient-sample verdict.
If full audited eligible universe has <12: INSUFFICIENT_SAMPLE. If coverage/lineage/state cannot be proved: SOURCE_BLOCKED. Hypothesis remains NOT TESTED in both cases.

## Source gate requirements
Every accepted shock needs old/new state, exact signal/effect, immutable payload/proposal proof, affected reserves, historical pre-signal borrower enumeration and reconstructible collateral/debt balances, collateral flags, eMode, isolation semantics, token index/accrual and oracle snapshot at signal-1.
Probe behavioral log availability with schemas/ranges/coverage only; do not inspect behavioral values or counts in signal/effect intervals before universe/exposure and separate analysis freeze.
Public archival eth_call is allowed for historical protocol state only. No signer, private key, wallet connection, transaction send, authenticated RPC or paid sources.

## Next stage, strictly conditional
Only after SOURCE_GATE_PASS publish separate PRE-OUTCOME ANALYSIS FREEZE defining one primary defensive-deleveraging formula, matched same-pool contemporaneous controls, natural signal-to-effect window, shock-level inference, LOO, concentration and missingness gates. No Development now. Exactly one Development after that freeze; no subsets, horizons or secondary rescue.
Survivor means SURVIVES_MECHANISM_DISCOVERY, not tradability. Stop before execution/holdout and require a new confirmatory freeze.

## Safety and receipts
No main changes/merge, trading, orders, exchange mutation, wallets, private endpoints, economic outcomes or 2026 outcomes. Record source request bodies, exact ranges, raw response hashes, coverage/continuation, failures, commits and runs.
Subjective pre-data forecast retained: 30% survivor / 50% no edge / 20% source/sample block; this is not a statistical probability.
