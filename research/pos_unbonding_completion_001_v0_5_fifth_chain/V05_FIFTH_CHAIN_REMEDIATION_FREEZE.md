# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.5 FIFTH-CHAIN REMEDIATION FREEZE

Date: 2026-10-07
Parent V0.4 closeout: `89fd41525e81ca7afb25251d66b0c71e6ef1af6c`
Parent verdict: `SOURCE_HISTORICAL_COVERAGE_BLOCKED`
Outcomes opened: NO
Main baseline: `f263c6c6f3a57f26666a7aee28e782f2cbd08418`

V0.5 is source-only. It preserves unchanged:
- actual native x/staking completion as the causal boundary;
- cancel/partial/slash/hold reconciliation;
- materiality = 10 bps of historical bonded stake;
- sample bar = >=40 MATERIAL chain-days TOTAL across >=5 chains;
- zero market prices/returns/PnL/outcome-informed selection;
- no trading/orders/wallet/account/private exchange access;
- no main merge/change.

Immutable V0.4 findings remain evidence:
- ATOM dual historical complete_unbonding block index PASS;
- DYDX dual historical complete_unbonding block index PASS;
- OSMO has one proven historical completion index but no second matching index;
- TIA has one proven historical completion index but no second matching index;
- KAVA, INJ, SEI, AKT, SCRT and AXL failed the V0.4 fifth-chain qualification routes tested.

## New prospectively frozen fifth-chain candidate order

Before inspecting any event counts for these chains:

1. Terra 2 / LUNA (phoenix-1)
2. Coreum / CORE (coreum-mainnet-1)
3. Archway / ARCH (archway-1)

Use the first candidate in this order that proves:
1. production native Cosmos x/staking semantics comparable for its eligible 2023-2024 era;
2. version/fork pinned;
3. two independently operated public/free historical sources reaching the frozen interval;
4. canonical fixed-height block hash/time/app-hash reconciliation;
5. at least one complete census-capable route consistent with V0.4 standards.

Do not inspect complete_unbonding counts for a later candidate until the earlier candidate fails source qualification.

If all three fail, V0.5 closes source-blocked unless a future version freezes a genuinely new source capability/candidate rule before inspecting that candidate's event counts.

No economic verdict can be issued from V0.5 source work.
