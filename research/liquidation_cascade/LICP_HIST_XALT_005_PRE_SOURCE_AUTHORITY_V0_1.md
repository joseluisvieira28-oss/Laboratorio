# LICP-HIST-XALT-005 — 2026 CONFIRMATORY PRE-SOURCE AUTHORITY V0.1

Date: 2026-10-01
Status: FROZEN_PRE_SOURCE / OUTCOME_BLIND / RESEARCH ONLY
Branch: licp-xalt-005-2026-confirmatory-v0.1

## Parent evidence
LICP-HIST-XALT-003 is terminally closed as HOLDOUT_SURVIVES on 2025-11 through 2025-12:
BTC liquidation ignition -> SOLUSDT SHORT, entry proxy t0+6m, 60m horizon.

Canonical parent holdout:
- N = 35
- mean gross = +25.071392 bps
- median gross = +16.882386 bps
- positive rate = 60%
- transfer hurdle = 16 bps
- mean after 16 bps hurdle = +9.071392 bps

This child receives no authority to retune the rule.

## Confirmatory objective
Test the exact same coarse historical cross-asset continuation rule on a genuinely later calendar block:
2026-01-01T00:00:00Z through 2026-09-30T23:59:59.999999Z.

No 2026 SOL price outcome may be opened before source feasibility passes and a separate final holdout protocol is frozen.

## Event source
Exact same pinned external event table used by XALT-003:
https://raw.githubusercontent.com/edwinyeeshunwan/forced-or-frantic/fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04/data/event_table_liq.parquet

Allowed source fields during this gate:
- t0
- symbol

Use only symbol == BTC.

Forbidden during source gate:
- event magnitude
- OI
- liquidation notional
- side refinements
- any external outcome/classification column
- SOL price data
- MEXC price data
- PnL

## Market-route source-only check
Official Binance Vision USD-M Futures monthly 1m archive existence only:
SOLUSDT for 2026-01 through 2026-09.
HEAD/metadata only. Do not download ZIP body during source gate.

## Source advancement gates
SOURCE_2026_PASS requires ALL:
- pinned event table is fetchable and SHA256 preserved;
- table contains >=80 BTC events in the confirmatory interval;
- >=6 distinct UTC calendar months contain >=5 BTC events each;
- 9/9 SOLUSDT monthly archive objects exist with positive Content-Length;
- no 2025 outcome is reopened;
- no SOL price row is read.

If failed:
SOURCE_2026_BLOCKED or INSUFFICIENT_2026_EVENT_SAMPLE.

## Frozen rule lineage
If source passes, later holdout MUST preserve:
- target SOLUSDT
- SHORT direction
- entry proxy t0+6m
- exit proxy t0+66m
- gross directional formula from XALT-003
- no threshold
- no magnitude filter
- no target change
- no alternate delay
- no reversal rescue

## Authority
Research only.
No live trading.
No orders.
No exchange mutation.
No main merge.
Trading authority: NONE.
