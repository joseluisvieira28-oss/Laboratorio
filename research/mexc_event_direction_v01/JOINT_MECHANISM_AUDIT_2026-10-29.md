# Audit: joint aggressor flow, liquidations and displayed-liquidity depletion
29 October 2026. Research only. No candidate model activation.

## Audited immutable references
- PR107 head 418e94638aaecd1a6c8289cad116c829bf748bbb.
- PR276 head 83634a62bf11946c837e89d52728b2d3abd7f63f.
- PR277 head 4006749653f6521a15c5b893710ada1d8543ba2e.
- This source-gate freeze: e276595f47d905fab20a09b3dbb5a1722b9e370d, committed before full-file parsing; preliminary HEAD/GET availability was already observed and explicitly disclosed.

## Finding 1: PR107 body is stale; terminal receipt wins
Read LICP_001_FORWARD_ECONOMIC_VERDICT_FREEZE_V0_1.md, LICP_001_FORWARD_ECONOMIC_CLOSEOUT_2026-10-14.md and receipts/LICP_001_FORWARD_ECONOMIC_VERDICT_2026-10-14.json at PR107 head.
The source-header/PR-body 17/20 insufficient state is superseded by terminal NO_EDGE.
Independently recomputed from the 18 valid primary episode rows: mean base -16.37455407056966bps; median -16.473403717856538bps; stress mean -32.37455407056966bps; positive 2/18. First20 fixed, six dates, 90% coverage, BTC60s, 16/32bps fees.
No rerun, reinterpretation, reverse direction, horizon/cost rescue or new LICP observation was performed.
The exact liquidation-cascade continuation hypothesis is retired.

## Finding 2: PR276 established aggressor source, not edge
Read ATI_HIST_SOURCE_FREEZE_V01.md via PR changed-file inventory and source scope/body; read the detailed joint closeout at PR277.
Existing run40864318462 independently confirmed completed/success, head83634a62.
Previously reported source evidence: 3,139,877 Binance aggTrades across BTC/ETH, publisher-validated ZIP SHA256, all1440 active minutes on 2026-04-01.
This audit did not download/revalidate those two ZIPs or assert a fresh source capture from that run.

## Finding 3: PR277 is already-open Discovery
Read ATI_ONE_DAY_PROXY_FREEZE_V01.md and ATI_FIRST_SOURCE_AND_PROXY_CLOSEOUT_2026-10-29.md.
Run40864653127 independently confirmed completed/success at db91c5ac819ecd7e3894ae465d7736b8ae1999d6.
Three completed1m flow bins, sign-only,10m/30m index outcome proxies: BTC10m68/141, BTC30m26/47; ETH10m73/141, ETH30m24/46 ex ties.
At hypothetical q80%,0/4 positive ATI EV; at q85%,1/4, BTC30m, a post-view singleton. No subset promotion, no new OOS, no actual historical payout.
April already-open Discovery only; protected September2026 never requested.

## Distinct mechanism boundary
The only defensible new question would be incremental joint conditioning: does aligned forced flow plus genuinely contemporaneous aggressor pressure plus displayed depth depletion improve prediction beyond each component on matched decisions?
Merely renaming continuous ATI, static imbalance, LVAC or LICP is duplication.
Existing 2023 staticL2 and LVAC failures remain closed. Failed-absorption event-count gates remain unchanged.
A future study would need fixed definitions, component ablations, common decisions, overlap handling, lag and freshness rejection, all prespecified cells and economics before any joint outcomes.
This audit does not freeze an outcome rule or numerical trigger: the upstream joint source gate has not passed.

## Source search and semantic evidence
Candidate: free first-of-month Tardis Bybit trades, liquidations and book_snapshot_5 for BTCUSDT/ETHUSDT on 2026-04-01.
Provider documents collector local_timestamp and exchange timestamp; both are retained. HTTP availability is insufficient.
Bybit official allLiquidation S=Buy means long position liquidated. Tardis mapping at d20b650010b653801e1d1cd640fca4862b44e04b/src/mappers/bybit.ts lines309-321 reverses it into forced execution side. Do not reverse normalized side again.
Liquidation price is bankruptcy price, not an executable fill; v*p is a proxy.
Top5 snapshots are reconstructed and provider removes crossed levels; source transformations must be disclosed. They do not identify cancellations separately from fills/moving levels.
Binance April1 liquidationSnapshot BTC/ETH GET returned404 NoSuchKey; its public forced-order stream is throttled to latest event per symbol per1000ms. It cannot silently substitute for a complete census.
Bybit live feeds have event timestamps but cannot backfill April. OKX orderbook history alone does not supply the missing joint liquidation continuity. No new dates, vendor subscription or private endpoints were used.

Sources:
- https://docs.tardis.dev/downloadable-csv-files
- https://docs.tardis.dev/downloadable-csv-files/data-types
- https://docs.tardis.dev/historical-data-details/bybit
- https://github.com/tardis-dev/tardis-node/blob/d20b650010b653801e1d1cd640fca4862b44e04b/src/mappers/bybit.ts#L309-L321
- https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation
- https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook
- https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Liquidation-Order-Streams
- https://www.okx.com/en-us/historical-data

## Economic decision
For this joint mechanism: NOT_TESTED / NO_EDGE_ESTABLISHED / NO_LIVE_GO until source gate passes, then a separate pre-outcome rule can be frozen. Source validation cannot establish predictability.
At symmetric payout q, break-even p=1/(1+q):55.56% for q80%,54.05% for q85%,71.43% for q40%. These are identities, not measured product payouts. Actual direction-dependent decision-time payouts and exact settlement parity remain unestablished for historical proxies.
LICP has an observed negative economic result; this proposed joint mechanism has no measured economic result. Keep these verdicts separate.

## Operational record
Only new research branch writes, no main write or merge. No order, exchange authentication, account/private endpoint, wallet, payment, subscription, deployment, scheduler or triggered GitHub Actions.
No protected holdout file/content fetched, no September source API requested. Existing references to the protected month in governance documents were read as boundaries.
See joint_v01/joint_source_get_availability.json and final source validation receipt for executed probe/transfer results.
