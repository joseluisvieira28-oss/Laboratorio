# DLS — MARGINFI SOL APR-JUN SOURCE DAILY TRANSPORT FALLBACK V0.1

Date: 2026-09-30
Branch: dls-marginfi-flow-turnover-impact-v01
Status: OPERATIONAL FALLBACK / SOURCE-ONLY

Parent scientific authority:
MARGINFI_SOL_FLOW_TURNOVER_IMPACT_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md

Purpose:
provide a fail-closed transport fallback if the canonical monthly exact-slot Apr-Jun source census is
interrupted by rate limits or runner wall-clock limits.

No market outcome is used to define this fallback.

## Unchanged source science

Unchanged:
- canonical monthly field-enrichment populations;
- SOL asset-bank selection;
- Marginfi liquidation identity;
- bank registry;
- exact successful historical transaction recovery;
- Jupiter post-liquidation route-member definition;
- SwapEvent decoder;
- route-root rule;
- ordered simple-chain rule;
- direction semantics;
- source PASS thresholds.

## Fallback partition

A failed/incomplete month may be partitioned into UTC calendar-day shards using only the timestamp
already present in its canonical field-enrichment rows.

Each shard:
- includes every SOL-population row whose canonical source timestamp is within that UTC day;
- issues exact-slot requests only for those identities;
- may not drop any unresolved slot;
- must preserve the exact same output semantics as the monthly collector.

Global reassembly for a month must exactly equal the canonical frozen SOL population identity set for
that month.

If both monthly and daily transports complete, exact population and route-member identity reconciliation
is mandatory. Any discrepancy fails closed.

## Firewall

prices=false
returns=false
pnl=false
apr_jun_market_outcomes_opened=false
jul_sep_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
