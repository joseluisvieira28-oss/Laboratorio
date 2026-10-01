# DLS — MARGINFI ORCA FORCED-FLOW IMPACT V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-route-migration-v01
Status: FROZEN BEFORE JUL-SEP 2024 MARKET OUTCOMES

Family ID:
DLS-MARGINFI-ORCA-FORCED-FLOW-IMPACT-001

## Motivation

Full source census proves that Marginfi SOL liquidation execution migrated from Jupiter toward Orca
Whirlpools in Jul-Sep 2024.

Canonical Orca source authority:
- run 36780139559
- artifact ID 11127536853
- digest sha256:4cbe2bad99237aee32d1e21c5055b17258897df6c312639678e68f15c4ae8dcb
- classification MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS
- SOL population 8,857
- Orca presence 7,744
- direction proven 7,717
- contradictions 0
- exact route input amount proven 7,717 / 7,717

Jul-Sep market OHLC/returns remain unopened.

## Scientific question

Does source-proven forced SOL selling executed through Orca Whirlpools create immediate executable
continuation in SOLUSDT after a source-only liquidation cascade ends?

This is economically/source-distinct from the prior Jupiter-only continuation family because it tests
the newly discovered dominant external execution route and a much larger source-proven flow population.

## Eligible source event

Require:
- canonical Orca full-census row;
- classification = DIRECTION_PROVEN;
- route semantic = COLLATERAL_TO_LIABILITY_ORCA_PROVEN;
- source-proven SOL sell pressure;
- exact route input amount proven and > 0.

No Jupiter events are included.
No liability filter.
No Orca instruction-type filter.
No hop filter.
No amount threshold.

## Frozen cascade construction

Sort eligible Orca source events by:
timestamp, signature, canonical instructionAddress.

A subsequent event joins the current cascade iff its timestamp is <= 5 minutes after the immediately
previous eligible event timestamp.

Otherwise the cascade closes and a new cascade starts.

Decision time:
A = first full UTC minute strictly after cascade last_event_time.

No market data participates in cascade formation.

## Mandatory pre-outcome sample gate

Before any Jul-Sep OHLC/return is read, construct source-only cascades.

READY only if:
- source eligible events >= 500;
- source cascades >= 100;
- distinct UTC cascade-end days >= 20;
- F1 Jul-Aug source cascades >= 60;
- F2 September source cascades >= 20.

If any fails:
MARGINFI_ORCA_IMPACT_PREOUTCOME_INSUFFICIENT_SAMPLE

No market outcome may be opened after an insufficient-sample result.

## Frozen trade hypothesis

Only after pre-outcome READY:

side = SHORT SOLUSDT

entry =
OPEN of minute A

exit =
OPEN of A + 1 minute

Only one position at a time.
If another cascade would enter before the existing position exits, ignore the later candidate.

No source-flow threshold.
No amount threshold.
No event-count threshold.

Reason frozen before outcomes:
the newly discovered Orca route represents direct source-proven forced SOL sale execution. V0.1 asks
the simplest falsifiable question: whether that forced external flow leaves immediate one-minute
continuation after the source cascade terminates.

## Funding firewall

Exclude a trade if [entry, exit] contains:
00:00 UTC, 08:00 UTC or 16:00 UTC.

## Market-data authority

Binance public USDT-M SOLUSDT perpetual 1-minute daily klines.

Require:
- published checksum PASS;
- unique monotonic timestamps;
- all required entry/exit minutes present.

## Frozen costs

Nominal:
- MEXC Futures API taker fee 8 bps/side;
- slippage 2 bps/side;
- ~20 bps round trip.

Stress descriptive:
- fee unchanged;
- slippage 5 bps/side;
- ~26 bps round trip.

Primary classification uses nominal.

## Development

[2024-07-01T00:00:00Z, 2024-10-01T00:00:00Z)

F1:
[2024-07-01T00:00:00Z, 2024-09-01T00:00:00Z)

F2:
[2024-09-01T00:00:00Z, 2024-10-01T00:00:00Z)

## Frozen Development gate

MARGINFI_ORCA_IMPACT_DEVELOPMENT_SURVIVES iff ALL:

1. analyzable trades >= 100;
2. distinct UTC entry days >= 20;
3. nominal net mean > 0;
4. nominal net median > 0;
5. nominal net PF > 1.10;
6. F1 n >= 60;
7. F2 n >= 20;
8. F1 nominal mean > 0;
9. F2 nominal mean > 0;
10. UTC-day block-bootstrap 95% CI lower bound of nominal mean > 0.

Bootstrap:
- 20,000 replicates
- complete UTC entry-day blocks
- seed 26100101

Otherwise:
MARGINFI_ORCA_IMPACT_DEVELOPMENT_NO_EDGE

## Future boundary

Only if Development SURVIVES:
Oct-Dec 2024 becomes OOS candidate after a separate unchanged-semantics source authority.

2025/2026 remain protected.

## Forbidden rescue

After Jul-Sep outcomes open:
- no LONG mirror inside V0.1;
- no hold change;
- no amount/event-count threshold;
- no Orca instruction-type selection;
- no hop selection;
- no time-of-day filter;
- no cost change;
- no deleting September;
- no opening Oct-Dec if Development fails.

Any distinct hypothesis requires a new pre-outcome family.

## Firewall

jul_sep_market_outcomes_opened=false
oct_dec_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
