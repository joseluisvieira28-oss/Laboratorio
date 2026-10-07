# V0.4 INDEX-FREE CENSUS — immutable source-remediation freeze

Family: POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001
Base closeout: 6cca7f9c26d10592950b51beec9f78bde12082cf
Date: 2026-10-07 UTC. No new counts or outcomes inspected before this commit.

All rules in INHERITED_FREEZE_V03.md and the V0.2 scientific/governance invariants are binding without modification. V0.1/V0.2/V0.3 remain immutable. Main verified remotely at f263c6c6f3a57f26666a7aee28e782f2cbd08418; never merge/update main.

Completion interval [2023-01-01T00:00:00Z,2025-01-01T00:00:00Z). 2025/2026 outcomes CLOSED. Zero market prices/returns/volumes/PnL, tuning/subsets/rescue, trading/orders/wallets/account reads/private or authenticated endpoints/spending. No latest/status chain reads. Only explicit historical heights and protocol/source metadata.

M_d=R_d/B_d; material iff >=0.001 (10 bps). B_d is historical bonded_tokens immediately before UTC day, preserving inherited genesis-day exception. >=40 MATERIAL chain-days TOTAL across >=5 chains. Retain all days including sub-threshold/zero days. Apply no materiality/count gate until full independent census completeness PASS. Unknowns remain unknown.

Same initiation cohort vs actual completion. Expected maturity only locates search; never T0. Successful tx requires explicit same-height txs_results code 0; missing result fails closed. Cancellation/partial cancellation, slash, validator/module/ICS holds and remaining principal must be resolved or fail closed. Do not silently exclude unresolved cohorts/days from denominator or counts. Lifecycle events may aggregate entries: ambiguous mapping blocks ledger certification.

Primary chains/order: ATOM, OSMO, KAVA, TIA, DYDX. Preserve deterministic registry universe and exclusions from parent freezes. KAVA Source B mandatory before final pass. If it fails, prospectively qualify INJ then SEI then other registry-eligible native staking candidates using mechanism + two independent historical paths before their census or outcome use; source-only eligibility, never counts/outcomes. Version-pinned production SDK/app mapping must cover upgrades, not merely latest source.

Index-free protocol: binary-search explicit block timestamps for start and exclusive end; genesis and missing/pruned segments explicitly recorded. Raw TxRaw -> TxBody -> Any scan in deterministic contiguous shards; successful MsgUndelegate/MsgCancelUnbondingDelegation, minimal receipts/hash/tx index/creation height, emitted metadata, append-only checkpoints, idempotent resume. Every block_results lifecycle must be covered as well: checking only expected maturity cannot prove absence of delayed held releases. No tx_search/index dependency. Census includes required pre-2023 initiation history: start at genesis unless historical opening queue/state plus independent proofs certify all outstanding cohorts. No arbitrary maximum hold/lookback assumption. Missing ranges are blockers, never zero events.

Independent route: production-version-pinned staking queue/state reconstruction through public historical ABCI proofs, exports/snapshots/restoration/dumps. Confirm prefix/key format (0x41 only where source-pinned) and proof verification/root binding; isolated ABCI key absence is neither range completeness nor evidence of empty queue. Full two-path coverage, principal/cancellation/slash/hold/completion reconciliation required.

Operational tests: bounded free/public requests, deterministic shards, bounded concurrency/retries, receipts including failures/throughput/provider response. Smoke scans cannot infer event frequency or full-run impossibility. Runner availability/cost restrictions are recorded independently from provider capability. Do not launch paid workloads or assume Actions allowance is free. Technical bug fixes/reruns allowed without science changes.

G1-G7 and allowed verdicts unchanged. SOURCE_HISTORICAL_COVERAGE_BLOCKED / SOURCE_PROVENANCE_INCOMPLETE require evidenced failures, not workload estimates or incomplete effort. Never NO_EDGE. Operational partial progress has no final scientific verdict.

Only after census completeness and G1-G5 PASS: G6 source capability/provenance metadata >=12 consecutive months pre-2026 per instrument WITHOUT values. If all source gates PASS, create separate PRE-OUTCOME freeze preserving paired T_signal/T_completion, exact windows, controls, costs, clustering, concentration/LOO gates and one-shot rule; STOP before price payloads/outcomes. No automatic economic execution.
