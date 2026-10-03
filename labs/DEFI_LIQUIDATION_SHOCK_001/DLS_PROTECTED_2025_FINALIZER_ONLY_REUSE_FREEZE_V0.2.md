# DLS PROTECTED-2025 — FINALIZER-ONLY REUSE FREEZE V0.2

Date: 2026-10-03
Status: FROZEN SOURCE-ONLY TECHNICAL FINALIZATION / OUTCOMES CLOSED

## Purpose
Close the already-frozen Protected-2025 source authority using only immutable PASS partition artifacts that already exist.

No new source collection is authorized by this finalizer-only stage.
No market price, return, PnL, funding or directional outcome may be opened.

## Canonical scientific code
Materializer:
- path: labs/DEFI_LIQUIDATION_SHOCK_001/source/materialize_hybrid_protected_2025_source_v0_1.py
- Git blob: fb7607385833db7c98dc14f46d2d7381acb7b6f1

Finalizer:
- path: labs/DEFI_LIQUIDATION_SHOCK_001/source/finalize_protected_2025_source_v0_2.py
- Git blob: d4345422aaf4f2f4042fe311c333352d9a208652

Neither scientific implementation may change.

## Immutable source runs authorized for reuse
Only these workflow runs may supply partition receipts:

1. 36740555628
   - canonical Protected-2025 V0.2 SQD partitions
2. 36733498831
   - canonical Protected-2025 V0.2 SQD partitions
3. 36986263576
   - A3B Helius gTFA, Marginfi 12/12 PASS set
4. 36996055142
   - targeted canonical SQD recovery; completed PASS artifacts include Kamino 05/06, Save0c 02/03, Save11 01/05
5. 36992630389
   - A3B hybrid gap-fill; completed PASS artifacts include Kamino 06/07 and Save group 01/02/03/05

The 2026-10-02 resume audit independently verified 31 earlier PASS partitions and identified only missing partition identities. Subsequent immutable artifacts now cover those gaps.

## Deterministic selection
The frozen materializer must:
- discover only PROTECTED_2025_PROTOCOL_SOURCE_PASS receipts;
- require exact protocol/class/month window;
- require error_count=0 and duplicate_count=0;
- compute canonical scientific payload SHA;
- allow duplicate transport receipts only when their canonical scientific payload SHA is identical;
- BLOCK on any scientific conflict;
- select exactly one receipt for each of 48 protocol/month identities;
- require 48/48.

The unchanged finalizer then:
- unions exact rows;
- checks cross-partition duplicate canonical identity;
- applies the frozen 60-second clustering once;
- targets SOL collateral only under the already-frozen semantics;
- excludes T0 crossing 2026;
- emits PROTECTED_2025_SOURCE_AUTHORITY_PASS only if all checks pass.

## Downstream authority
Only PROTECTED_2025_SOURCE_AUTHORITY_PASS may authorize the already-frozen 2025 economic holdout.

A GitHub Actions green check without PASS classification is not authority.

## Firewall
prices_2025_opened=false
returns_2025_opened=false
pnl_2025_opened=false
funding_2025_opened=false
market_direction_2025_opened=false
prices_2026_opened=false
returns_2026_opened=false
post_outcome_tuning=false
purchases=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
trading_authority=NONE
