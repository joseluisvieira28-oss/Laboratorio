# DLS — MARGINFI FEB-MAR SOURCE TRANSPORT OPTIMIZATION ADDENDUM V0.2

Date: 2026-09-29
Branch: dls-marginfi-transient-reversion-v01
Status: FROZEN OPERATIONAL REMEDIATION / SOURCE-ONLY

Parent scientific authority:
MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_TEMPORAL_SOURCE_EXTENSION_FREEZE_V0.1.md

## Reason

Canonical run 36587238422 uses 12 five-day shards and streams both Marginfi and all Jupiter V6
instructions across each full shard window. The scientific rule is valid but the transport path is
expensive because Jupiter traffic is dense.

No shard result, route-member outcome, direction outcome, price, return or PnL from that run has been
opened as of this addendum.

V0.2 changes transport only.

## Population and semantics unchanged

Unchanged:
- source window [2024-02-01, 2024-04-01);
- Marginfi program and discriminator;
- successful committed liquidation population rule;
- fixed account roles asset_bank=1, liab_bank=2;
- bank->mint authority;
- Jupiter post-liquidation route-class definition;
- route-root rule;
- SwapEvent decoder;
- ordered simple-chain rule;
- endpoint direction semantics;
- PASS thresholds;
- no prices/returns/PnL.

## Optimized acquisition

Pass 1:
stream only successful committed Marginfi lending_account_liquidate instructions over each shard.
Preserve exact signature, slot, timestamp, transactionIndex, instructionAddress and accounts.

Pass 2:
for each unique source transaction identity from Pass 1, request its exact Solana slot and retrieve only
committed successful Jupiter V6 instructions plus parent transaction identity.

A Pass-2 response is accepted only if the exact source signature is recovered in the exact slot and
the transaction is successful.

This is source-equivalent to the original full-window Jupiter stream but avoids unrelated Jupiter traffic.

## V0.2 transport shards

Exactly 8 non-overlapping shards:

fm2-01 [2024-02-01, 2024-02-09)
fm2-02 [2024-02-09, 2024-02-17)
fm2-03 [2024-02-17, 2024-02-25)
fm2-04 [2024-02-25, 2024-03-04)
fm2-05 [2024-03-04, 2024-03-12)
fm2-06 [2024-03-12, 2024-03-20)
fm2-07 [2024-03-20, 2024-03-28)
fm2-08 [2024-03-28, 2024-04-01)

## Global adjudication

Exactly the parent V0.1 global source PASS/PARTIAL/BLOCKED thresholds apply.

If both original V0.1 transport and optimized V0.2 transport eventually complete:
- exact source population identity sets and route-member identity sets MUST reconcile;
- any disagreement is SOURCE_BLOCKED pending reconciliation;
- no favorable result may be selected preferentially.

If V0.2 completes first and passes its own full-window identity and semantic gates, it may authorize the
already-prefrozen market Development. The later completion of V0.1 remains an audit cross-check and any
future discrepancy fails closed.

## Firewall

prices=false
returns=false
pnl=false
market_outcomes_feb_mar_2024=false
jan_2024_reused_for_reversion_validation=false
apr_jun_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
