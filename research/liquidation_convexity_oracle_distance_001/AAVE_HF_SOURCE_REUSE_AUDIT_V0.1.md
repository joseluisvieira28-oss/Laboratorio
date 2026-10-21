# AAVE-HF-CROWDING SOURCE REUSE AUDIT V0.1

Date: 2026-09-24
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Compared branch: aave-health-factor-crowding-v0.1

## Verdict

PARTIAL_REUSE_ONLY.

The existing AAVE-HF-CROWDING-001 collector is intentionally insufficient for LCOD-001.

### What can be reused conceptually

- v4 reserve enumeration via get_markets;
- borrower enumeration via get_reserve_holders;
- outcome-blind population/source discipline;
- idempotent UTC-day snapshot pattern.

### What cannot be reused as canonical LCOD state

The existing population receipt explicitly records:
- debt_values_retained = false
- collateral_values_retained = false
- price_values_retained = false

The existing calibration collector:
- calls get_user_summary;
- extracts only health-factor values;
- does not retain wallet addresses;
- does not retain individual health-factor values;
- does not retain component collateral/debt legs.

Therefore it cannot deterministically reprice each borrower under the LCOD frozen oracle-shock grid.

## Required LCOD delta

A new source-only component collector must obtain, at one bounded snapshot boundary:

1. borrower identity for in-run joining only; output may hash/pseudonymize after component assembly;
2. get_user_positions for supplies and borrows;
3. get_position_items where v4 position components require item-level principal/interest;
4. reserve details / market metadata sufficient to bind the correct reserve and liquidation semantics;
5. the exact price/valuation fields used by the Aave read surface, with snapshot provenance;
6. collateral-enabled state and any v4 position semantics needed to reproduce health;
7. an independent reconciliation against get_user_summary health factor before the snapshot is accepted.

Current Aave MCP documentation confirms:
- get_user_positions: v3/v4 supplies and borrows, with per-position health on v4;
- get_position_items: v4 individual supplies/borrows;
- get_user_summary: aggregate position and health factor;
- get_markets/get_reserve_details: reserve context.

Authority:
https://aave.com/docs/mcp/tools

## Fail-closed reconciliation gate

A component snapshot is accepted only if reconstructed HF agrees with the official get_user_summary / position health semantics within a tolerance frozen before first real snapshot.

The tolerance itself MUST be chosen from numeric representation/rounding evidence, not from market outcomes.

If reconciliation cannot be achieved without undocumented fields, LCOD-001 remains SOURCE_BLOCKED.

## Scientific separation

No threshold or q90 state from AAVE-HF-CROWDING-001 is imported.
No closed result from AAVE-LIQUIDATION-OVERHANG-001 is re-opened.
LCOD-001 remains a separate deterministic shock-surface mechanism.
