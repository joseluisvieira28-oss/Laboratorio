# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.2

SOURCE CAPABILITY REMEDIATION FREEZE — 2026-10-06
Parent: V0.1 `SOURCE_HISTORICAL_COVERAGE_BLOCKED` (immutable; no rejudgment).
Branch base main: `f263c6c6f3a57f26666a7aee28e782f2cbd08418`.
Status: SOURCE-CAPABILITY ONLY / outcome lock remains active.

## Scope
This version may verify historical endpoint documentation, public/free access, endpoint methods, fixed-height historical archive responses, independently operated source provenance, protocol source versions, and source-only market archive metadata for the unchanged 2023-01-01 through 2024-12-31 study interval. It must not request current/latest chain state, prices, market payloads, volume values, returns, PnL, 2025 data, or 2026 chain/market event values. Historical consensus block/event results at explicit heights inside the frozen interval are permitted solely to validate source capability and staking-event schema; do not compute event counts, materiality, dose or economic outcomes in this remediation version.

No paid endpoints, accounts, tokens, keys, authenticated/private endpoints, wallet queries, exchange mutation or orders. Endpoint descriptions alone are not a capability pass. Every live test must use a specific fixed height validated to lie in 2023-2024 and persist request parameters, provider identity, response status/schema, height/time, digest and errors. Do not issue `/status`, unbounded search, latest block, or endpoints that silently return current data.

## Scientific and governance invariants
V0.1 remains exactly `SOURCE_HISTORICAL_COVERAGE_BLOCKED`; its commit and files are not changed. No hypothesis, T_signal, T_completion, population, dose, direction or minimum gate is tuned in V0.2. Primary eligibility requires actual, chain-version-pinned Cosmos SDK native `x/staking` semantics. Exclude DOT/KSM, NEAR, DA-only Celestia data, liquid-staking receipt tokens and incompatible epoch/manual-withdrawal regimes from this family.

Target lifecycle is `MsgUndelegate` initiation and entry details → cancellation/partial cancellation → slashing → validator state and ICS/module holds → actual EndBlock `complete_unbonding` → final released amount and canonical block timestamp. SDK documentation says staking EndBlocker emits `complete_unbonding` with amount, validator and delegator. Actual block/state evidence is required; nominal durations are not a substitute. Source A and Source B must have independent operators or independently reconstructed methods and must reconcile completeness, pagination, cohort principal, event block and final amount. A second website fronting the same underlying source is not independence.

The frozen bar remains >=5 comparable chains and >=40 independently defensible material event clusters / source units as required by the parent freeze. Do not lower either count. Materiality must be source-only against on-chain supply/staking state; V0.2 does not calculate materiality or event counts. Search all eligible candidates under the deterministic universe, not only the named leads. For each market-mapped instrument, prove >=12 consecutive months of pre-2026 liquid-market source capability and provenance without opening market values. Archive existence alone is not liquidity.

## Leads to verify
1. Cosmos Hub / ATOM: Citizen Web3 archive RPC candidate `rpc.cosmoshub-4-archive.citizenweb3.com`; CometBFT `block_results`, `tx_search`, block and block-results methods.
2. Osmosis / OSMO: `rpc.archive.osmosis.zone`; independent Validatus archive RPC candidate `rpc.archive.osmosis.validatus.com`.
3. Kava / KAVA: official Kava historic-data documentation lists free Kava Labs archive RPC/API across version periods, including the frozen 2023-2024 interval; test versions/heights around upgrades and source A/B.
4. Celestia / TIA: only explicitly identified archival CONSENSUS RPC/API nodes qualify; do not count DA archive endpoints as consensus/staking history. Confirm `block_results` or equivalent finalize-block event history.
5. Additional comparable chain(s): search the full frozen registry universe by source capability. Injective, Akash, dYdX, or other chain names are candidates only; verify no-key/free archive capability, history retention, actual `x/staking` implementation and market metadata independently.

## Gate outcome
V0.2 may report only one of: `SOURCE_GATE_PASS`, `SOURCE_HISTORICAL_COVERAGE_BLOCKED`, `INSUFFICIENT_INDEPENDENT_SAMPLE`, `MECHANISM_NOT_COMPARABLE`. `SOURCE_GATE_PASS` requires all parent source gates, complete historical lifecycle/source reconciliation and unchanged >=5 / >=40 thresholds. If not passed, stop with the evidenced blocker and preserve unknown counts. Do not create a PRE-OUTCOME ANALYSIS FREEZE or inspect any outcome. If passed, the next artifact is a new separate PRE-OUTCOME ANALYSIS FREEZE before one Development run.

## Lineage
V0.1 source/mechanism freeze, addendum, source receipt and evidence remain untouched on `pos-unbonding-completion-001-source-v0.1-2026-10-06`. This branch derives from main and contains only the V0.2 remediation authority/evidence. No merge or main update.
