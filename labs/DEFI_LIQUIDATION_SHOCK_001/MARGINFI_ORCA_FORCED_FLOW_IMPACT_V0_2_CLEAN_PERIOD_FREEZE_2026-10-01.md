# DLS — MARGINFI ORCA FORCED-FLOW IMPACT V0.2 — CLEAN-PERIOD PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-route-migration-v01
Status: FROZEN BEFORE OCT-DEC 2024 MARKET OUTCOMES

Family ID:
DLS-MARGINFI-ORCA-FORCED-FLOW-IMPACT-002

## Reason for V0.2

V0.1 Jul-Sep was quarantined without inspecting its market metrics because an obsolete executor opened
the period with an implementation inconsistent with the written SHORT rule.

Quarantine authority:
MARGINFI_ORCA_IMPACT_V0_1_JULSEP_OUTCOME_QUARANTINE_2026-10-01.md

V0.2 does not use any Jul-Sep outcome, metric, return, PnL, fold result or bootstrap result.

## Scientific hypothesis

Unchanged from the original written V0.1 freeze:

Source-proven forced SOL selling executed through Orca Whirlpools leaves immediate one-minute
continuation after the source cascade terminates.

side = SHORT SOLUSDT
hold = 1 minute

## Source semantics

Unchanged:
- Marginfi lending_account_liquidate;
- native/wrapped SOL collateral;
- post-liquidation Orca Whirlpools route;
- classification DIRECTION_PROVEN;
- route semantic COLLATERAL_TO_LIABILITY_ORCA_PROVEN;
- asset label SIGNED_SELL_PRESSURE_PROVEN;
- exact route input amount > 0.

No Jupiter events.
No liability filter.
No Orca instruction-type filter.
No hop filter.
No amount threshold.

## Source window

Clean Development candidate:
[2024-10-01T00:00:00Z, 2025-01-01T00:00:00Z)

Canonical Marginfi field-enrichment partitions:

October:
artifact ID 10924878593
digest sha256:a6635c5a7ca8b2d1d49670acb5482dda82db56459af068739c6acc535c82b6d7
classification FIELD_ENRICHMENT_PARTITION_PASS
enriched rows 1,432
missing 0
extra 0
duplicates 0
semantic conflicts 0

November:
artifact ID 10925847270
digest sha256:43f749aeca0999f8e35262c73ca5ac8bbf7c0920f04db205d24e969de6a61fd7
classification FIELD_ENRICHMENT_PARTITION_PASS
enriched rows 10,141
missing 0
extra 0
duplicates 0
semantic conflicts 0

December:
artifact ID 10927608033
digest sha256:0228f85921f9a30d6310b0fa3e5798f2695b9750c4add737e82a7611959892a4
classification FIELD_ENRICHMENT_PARTITION_PASS
enriched rows 4,880
missing 0
extra 0
duplicates 0
semantic conflicts 0

No alternative population scan may redefine these partitions.

## Source PASS

Before market outcomes, exact historical transactions must be adjudicated under the already calibrated
Orca instruction decoder.

MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS requires:
- exact union of canonical SOL identities;
- missing identities 0;
- extra identities 0;
- duplicates 0;
- global source errors 0;
- Orca route count > 0;
- source-complete among Orca routes >= 95%;
- deterministic direction among source-complete >= 90%;
- contradictions 0.

## Cascade construction

Unchanged:
sort by timestamp, signature, canonical instructionAddress.

Subsequent eligible event joins current cascade iff timestamp <= 5 minutes after immediately previous
eligible event.

Decision time:
A = first full UTC minute strictly after cascade last_event_time.

## Mandatory pre-outcome sample gate

READY only if:
- eligible source events >= 500;
- source cascades >= 100;
- distinct UTC cascade-end days >= 20;
- F1 Oct-Nov source cascades >= 60;
- F2 December source cascades >= 20.

Otherwise:
MARGINFI_ORCA_IMPACT_V02_PREOUTCOME_INSUFFICIENT_SAMPLE

No market outcome may open after insufficient sample.

## Correct SHORT execution math

Gross SHORT return:
1 - exit_open / entry_open

Nominal execution:
entry sell = entry_open * (1 - slippage)
exit buy-to-cover = exit_open * (1 + slippage)

ratio = exit_exec / entry_exec
net = (1 - ratio) - fee * (1 + ratio)

This is frozen before Oct-Dec outcomes.

## Market execution

Only after source PASS + pre-outcome READY:

symbol SOLUSDT
side SHORT
entry OPEN of minute A
exit OPEN of A + 1 minute

One position at a time.
Collision candidates ignored.
Funding boundary excluded if [entry,exit] contains 00:00, 08:00 or 16:00 UTC.

## Market-data authority

Binance public USDT-M SOLUSDT perpetual 1m daily archives.
Published SHA256 checksum required.
Unique monotonic timestamps.
All entry/exit minutes required.

## Costs

Nominal:
MEXC Futures API taker fee 8 bps/side
slippage 2 bps/side
approximately 20 bps round trip

Stress descriptive:
same fee
5 bps slippage/side
approximately 26 bps round trip

## Development folds

Development:
[2024-10-01, 2025-01-01)

F1:
[2024-10-01, 2024-12-01)

F2:
[2024-12-01, 2025-01-01)

## Frozen gate

SURVIVES iff ALL:
1. n >= 100
2. distinct UTC entry days >= 20
3. nominal mean > 0
4. nominal median > 0
5. nominal PF > 1.10
6. F1 n >= 60
7. F2 n >= 20
8. F1 nominal mean > 0
9. F2 nominal mean > 0
10. UTC-day block-bootstrap 95% lower bound > 0

Bootstrap:
20,000 replicates
seed 26100102

Otherwise:
MARGINFI_ORCA_IMPACT_V02_DEVELOPMENT_NO_EDGE

## Future boundary

2025 and 2026 remain protected.
No OOS period is authorized by this freeze.
If V0.2 survives, a separate untouched-period authority is required before any further outcome.

## Forbidden rescue

After Oct-Dec outcomes open:
- no LONG mirror;
- no hold change;
- no amount/event-count threshold;
- no instruction-type/hop/liability selection;
- no time filter;
- no cost change;
- no fold deletion;
- no Jul-Sep result inspection for rescue;
- no 2025/2026 opening.

## Firewall

inspect_quarantined_julsep_outcomes=false
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
