# DEFI-LIQUIDATION-SHOCK-001 — PRE-SOURCE AUTHORITY V0.1

Status: RESEARCH-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Scientific question

Can successful, objectively identifiable on-chain DeFi liquidations create a causal forced-flow event population that is known before any tested future price window and is large enough to justify a later prospectively frozen Discovery?

This authority covers source/data reconnaissance only. It does not authorize returns, PnL, execution-performance metrics, 2025/2026 outcome access, live trading, exchange mutation, alerts/webhooks, deployment, or merge to main.

## Anti-duplication result

A prior lab, LIQUIDATION-PRESSURE-001, studied a different observable: market-wide BTC derivatives liquidation pressure on centralized exchanges. It closed SOURCE_ACCESS_BLOCKED because a reproducible historical market-wide CEX liquidation archive was not proven. No outcome was opened.

DEFI-LIQUIDATION-SHOCK-001 is a separate information family: protocol-level on-chain liquidation transactions and their directly observable forced collateral/debt flows.

## Protected period

Market outcomes in 2025 and 2026 remain protected and must not be opened. Historical source reconnaissance should prefer 2021–2024 or 2022–2024. A protocol with a shorter historical life may be documented, but the period may not be moved because of outcomes.

## Source-selection rule

No protocol is selected by future returns. A protocol may be promoted to a Source Gate only from pre-outcome evidence on:
1. raw historical availability;
2. liquidation instruction/event identifiability;
3. timestamp/slot/transaction ordering quality;
4. successful-vs-failed status;
5. collateral/debt asset and amount reconstruction;
6. pre-event notional/oracle reconstruction without look-ahead;
7. sample size before outcomes;
8. plausible later executable market mapping.

Candidate families include Kamino Lend, marginfi/Project 0, Save/Solend, Drift, and any other lending/perps program actually found in the raw corpus. Presence in this list is not selection.

## Event requirements

A valid source event should contain or causally reconstruct, without future data:
- block time / slot;
- transaction signature and deterministic instruction position;
- protocol/program ID and instruction identity;
- transaction success;
- liquidated obligation/account;
- liquidator when identifiable;
- collateral mint/asset and amount seized/withdrawn;
- debt mint/asset and amount repaid/assumed;
- oracle/reference inputs if used for event-time notional;
- enough ordering information to cluster repeated instructions/cascades prospectively.

Missing fields must remain missing or explicitly derived; no invented fields or post-event price substitution.

## Integrity controls

Before outcomes:
- deduplicate signatures and repeated liquidation instructions;
- separate failed transactions from successful liquidations;
- freeze any cascade/shock clustering rule;
- guard oracle/timestamp leakage;
- forbid future/current token metadata as historical evidence unless versioned;
- forbid post-event price for event notional;
- forbid post-outcome size/asset/protocol selection;
- preserve raw bytes and hashes when available;
- pin historical program/IDL versions rather than decoding old transactions with current layouts.

## Sample gate

No numerical sample threshold is frozen in V0.1. The handoff explicitly requires auditing the raw event population first and setting the sample gate only after source reconnaissance, before outcomes. If the raw corpus cannot be inspected, the lab must fail closed at SOURCE_DATA_BLOCKED rather than invent a threshold.

## Source-route note

Helius archival Solana routes can, in principle, provide full historical transaction/block evidence. Parsed/current protocol APIs may be used for reconciliation only unless their historical retention and event-time semantics are proven. Raw/full on-chain evidence is preferred as scientific authority.

## Promotion rule

Only a demonstrated raw event population with adequate causal fields may advance to:
1. SOURCE_DATA_PASS receipt;
2. FINAL PRE-DISCOVERY AUTHORITY with frozen event, universe, clustering, sample gate, horizons, direction logic, costs, execution assumptions, metrics and statistical gates;
3. one Discovery run.

No outcome access is authorized by this document.
