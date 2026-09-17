# BINANCE-MARGIN-BORROW-ACCESS-001 — SOURCE TRANSPORT REMEDIATION V0.2

Date: 2026-09-17  
Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND / TRANSPORT REMEDIATION ONLY**

## Why V0.2 is required

The V0.1 CMS census failed technically because its guard treated several current/future-to-window catalog pages as repeated pagination before it reached the frozen 2023–2024 interval.

More importantly, the live CMS catalog is newest-first. Continuing from page 1 in September 2026 necessarily traverses 2025/2026 announcement metadata before reaching the frozen scientific window. That is incompatible with the pre-source authority's protected-period firewall. V0.2 therefore does **not** continue that route.

The failed V0.1 receipt remains audit evidence. It is not an economic result and is not a source pass.

## Frozen V0.2 transport

Use the official public Binance English announcements Telegram channel only as an **index/transport**:

`https://t.me/s/binance_announcements`

The canonical scientific authority remains the official English Binance Support article. Telegram cannot by itself qualify an event.

### Protected-period-safe upper cursor

The initial request is frozen to:

`https://t.me/s/binance_announcements?before=6900`

This cursor was selected during source-transport diagnosis before any market outcome was opened and is anchored inside the end-2024 announcement region. The collector may move only backward to lower message IDs.

Every parsed message must have a timestamp <= `2024-12-31T23:59:59Z`. If any 2025/2026 message is returned, the run fails closed and no scientific source pass may be emitted.

The collector paginates backward deterministically until it observes timestamps below `2023-01-01T00:00:00Z`. It may not stop after a convenient event count.

## Relevant-record enumeration

The full channel pages are traversed structurally, but only Binance Support announcement links whose message timestamp lies in the frozen 2023–2024 interval may be retained as scientific records.

A retained relevant candidate is a support announcement whose official-channel title contains structural access terms such as `margin`, `borrowable`, or `cross margin`. This is an outcome-blind source filter only.

For every retained candidate and the two pre-frozen positive controls, the collector must resolve the official Binance Support/CMS article detail and require:

- stable 32-hex article code identity;
- non-empty official article text;
- point-in-time release timestamp recoverable from the official article payload when present;
- explicit `Cross Margin` and `borrowable asset` semantics for a qualifying event.

The event universe is defined by deterministic traversal of the official Binance-controlled channel, not by search-engine ranking. Search results were used only to diagnose transport and freeze the safe historical cursor.

## Positive controls unchanged

- 2023: `a74f935eaa2247889d58e33ec23313bb`
- 2024: `6674719e209641bda688729852d35fb5`

They remain source completeness/provenance controls only.

## Scientific rules unchanged

Unchanged:
- event window `2023-01-01` through `2024-12-31`;
- mechanism = newly enabled Cross Margin borrowing/short-access for an already spot-traded asset;
- prior Spot listing proof required before Discovery;
- same-announcement confounds adjudicated before outcomes;
- historical borrow-cost/availability provenance required before executable claims;
- no prices, returns, basis, PnL, win rate, PF, drawdown, authenticated exchange API, account data, orders, wallets or live trading;
- no 2025/2026 scientific data.

## V0.2 terminal classifications

Only the pre-frozen classifications remain admissible:
- `SOURCE_CENSUS_PASS`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `SOURCE_ENUMERATION_INCOMPLETE`
- `PROVENANCE_FAILURE`
- `INSUFFICIENT_EVENT_SAMPLE`

`NO_EDGE` remains forbidden at this stage.
