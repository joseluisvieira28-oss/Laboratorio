# DLS — MARGINFI FEB-MAR SOURCE DAILY SHARDING FALLBACK V0.3

Date: 2026-09-29
Branch: dls-marginfi-transient-reversion-v01
Status: FROZEN OPERATIONAL FALLBACK BEFORE V0.2 SOURCE OUTCOMES

Parent scientific authority:
MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_TEMPORAL_SOURCE_EXTENSION_FREEZE_V0.1.md

Parent exact-slot transport authority:
MARGINFI_FEBMAR_SOURCE_TRANSPORT_OPTIMIZATION_ADDENDUM_V0.2.md

Purpose:
reduce per-runner wall-clock exposure only if the five-day exact-slot V0.2 transport is operationally
interrupted before producing complete receipts.

No source result, price, return or PnL is used to define this fallback.

## Daily partition rule

Partition the unchanged source window [2024-02-01T00:00:00Z, 2024-04-01T00:00:00Z)
into exactly 60 UTC calendar-day shards.

Each shard is [00:00:00Z on day D, 00:00:00Z on day D+1).

Use the exact same V0.2 exact-slot collector and source semantics.
Only start/end transport boundaries differ.

## Global reassembly

Require:
- exactly 60 COMPLETE daily receipts;
- first start = 2024-02-01T00:00:00Z;
- final end = 2024-04-01T00:00:00Z;
- every interval is exactly one UTC calendar day;
- every next start equals previous end;
- population duplicate identities = 0;
- member duplicate identities = 0;
- members are a subset of population;
- route_member_count > 0;
- source-complete rate >= 95%;
- deterministic direction among source-complete >= 90%;
- contradictions = 0.

Classifications remain:
MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_PASS
MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_PARTIAL
MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_BLOCKED

If another transport version also completes, exact population/member/direction identity reconciliation
is mandatory; any discrepancy fails closed.

## Firewall

prices=false
returns=false
pnl=false
market_outcomes_feb_mar_2024=false
apr_jun_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
