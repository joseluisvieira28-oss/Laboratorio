# DEFI-LIQUIDATION-SHOCK-001 — PROTECTED 2025 SOURCE PARTITIONING ADDENDUM V0.2

Date: 2026-09-29
Status: FROZEN / TECHNICAL EXECUTION ONLY / SCIENCE UNCHANGED

## Reason
The V0.1 monolithic collectors provide no partition checkpoint for a full-year source scan. V0.2 changes only execution granularity.

## Equivalence
- Same collector: collect_protected_2025_source_v0_1.py.
- Same programs, discriminators, ABI/account-role rules, success conditions, unit resolution and firewall.
- Same inclusive/exclusive full window: 2025-01-01T00:00:00Z <= timestamp < 2026-01-01T00:00:00Z.
- Exactly 12 calendar-month partitions per protocol, 48 receipts total.
- Each partition is independently fail-closed.
- Finalizer requires exactly one PASS receipt for every protocol/month.
- Rows are concatenated, canonical identities are checked globally for duplicates, then sorted globally before clustering.
- 60-second cascades are clustered across month boundaries after concatenation, so partitioning cannot split a scientific cascade.
- Any T0 >= 2026-01-01T00:00:00Z remains excluded.

No threshold, asset, protocol, class, mapping, cluster rule, strategy rule or economic rule changes.

## Canonical precedence
If V0.2 reaches PROTECTED_2025_SOURCE_AUTHORITY_PASS, V0.2 is the canonical 2025 source authority.
The still-running V0.1 monolithic workflow is non-canonical and may be retained only as redundant technical evidence.

## Firewall
prices_2025_opened=false
returns_2025_opened=false
pnl_2025_opened=false
funding_2025_opened=false
market_direction_2025_opened=false
prices_2026_opened=false
returns_2026_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
