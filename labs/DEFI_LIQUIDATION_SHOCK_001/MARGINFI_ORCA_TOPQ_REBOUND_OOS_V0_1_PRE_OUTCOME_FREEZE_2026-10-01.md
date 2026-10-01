# DLS — MARGINFI ORCA TOP-QUARTILE REBOUND OOS V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-01
Branch: dls-marginfi-orca-rebound-oos-v01
Status: FROZEN BEFORE OCT-DEC 2024 MARKET OUTCOMES

Family:
DLS-MARGINFI-ORCA-TOPQ-REBOUND-OOS-001

## Scientific lineage

Discovery authority:
DLS-MARGINFI-ORCA-FLOW-RESPONSE-001

Canonical discovery run:
36814416648

Canonical discovery artifact:
dls-marginfi-orca-flow-response-v01
artifact ID 11140333264
digest sha256:df7e37d1b2ea23052589802cda1d0b0dc37921bae3a1c23fe6dd3bd2fd614162

Discovery classification:
MARGINFI_ORCA_FLOW_RESPONSE_DISCOVERY_PASS

Discovery result:
- analyzable cascades = 191
- distinct UTC days = 35
- overall Spearman rho = +0.2806386056764949
- rho day-block bootstrap 95% CI = [+0.10959738083216897, +0.36433335124610083]
- F1 Jul-Aug rho = +0.26730195548223445
- F2 Sep rho = +0.2055003819709702
- top quartile mean 1m response = +0.0022275670785056193
- bottom quartile mean 1m response = +0.00029603927259659395
- top-minus-bottom = +0.0019315278059090254
- delta bootstrap 95% CI = [+0.0009593048662427454, +0.0028075244133034024]

Jul-Sep is discovery only and may not be reused as executable validation.

## Frozen source semantics

Use the exact source semantics proven by:
MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS

Eligible event:
- Marginfi lending_account_liquidate
- asset mint = So11111111111111111111111111111111111111112
- post-liquidation Orca Whirlpools route
- classification = DIRECTION_PROVEN
- route_semantic = COLLATERAL_TO_LIABILITY_ORCA_PROVEN
- asset_label = SIGNED_SELL_PRESSURE_PROVEN
- exact_route_input_amount > 0

Event sold SOL:
exact_route_input_amount / 1,000,000,000

No Jupiter requirement.
No liability-mint filter.
No hop-count filter.

## Frozen source cascade

Sort eligible events by:
timestamp, signature, canonical instructionAddress.

A subsequent event belongs to the same cascade iff its source timestamp is <= 5 minutes after the
immediately previous eligible event timestamp.

Decision time:
A = first full UTC minute strictly after last_event_time.

cascade_sold_sol =
sum of source-proven exact input SOL amount across cascade members.

## Frozen turnover feature

Market feature authority:
Binance public USDT-M SOLUSDT perpetual 1-minute base-asset volume.

Use exactly the five complete minutes:
[A-5m, A)

pre5m_base_volume_sol =
sum of base-asset volume over those five minutes.

flow_turnover_intensity =
cascade_sold_sol / pre5m_base_volume_sol

No post-A volume enters the feature.

## Frozen numeric signal threshold

The discovery freeze pre-specified a top-vs-bottom quartile contrast before Jul-Sep outcomes.

After the frozen funding firewall, discovery analyzable N = 191.

Frozen top group size:
floor(191 / 4) = 47

Using the already-existing pre-outcome feature artifact only, the minimum feature value among those
47 highest-X observations is:

ORCA_FLOW_TURNOVER_TOPQ_THRESHOLD =
1.252336612578286e-05

This numeric threshold is feature-derived from the pre-outcome Jul-Sep artifact and is not selected
from returns.

Signal in OOS iff:
flow_turnover_intensity >= 1.252336612578286e-05

No alternative percentile or threshold may be tested in this family.

## Frozen executable rule

For each selected Oct-Dec cascade:

side = LONG SOLUSDT

entry =
OPEN of minute A

exit =
OPEN of minute A + 1 minute

Only one trade per cascade.

If a later selected cascade would enter before an existing trade exits, ignore the later candidate.

No pyramiding.
No scaling.

## Funding firewall

Exclude a candidate if [entry, exit] contains:
00:00 UTC, 08:00 UTC or 16:00 UTC.

## Frozen execution costs

Primary:
- MEXC Futures API taker fee = 8 bps per side
- slippage = 2 bps per side
- approximate round-trip cost = 20 bps

Stress descriptive only:
- same taker fee
- slippage = 5 bps per side
- approximate round-trip cost = 26 bps

Primary classification uses nominal costs only.

No maker fills.
No rebates.
No VIP discount.
No leverage benefit.

## OOS period

[2024-10-01T00:00:00Z, 2025-01-01T00:00:00Z)

Temporal folds:

F1:
October + November 2024

F2:
December 2024

## Canonical population authority

Use only canonical FIELD_ENRICHMENT_PARTITION_PASS artifacts from run 36263998920:

October:
- artifact ID 10924878593
- digest sha256:a6635c5a7ca8b2d1d49670acb5482dda82db56459af068739c6acc535c82b6d7
- population 1,432 / 1,432
- missing=0, extra=0, duplicate=0, semantic conflicts=0

November:
- artifact ID 10925847270
- digest sha256:43f749aeca0999f8e35262c73ca5ac8bbf7c0920f04db205d24e969de6a61fd7
- population 10,141 / 10,141
- missing=0, extra=0, duplicate=0, semantic conflicts=0

December:
- artifact ID 10927608033
- digest sha256:0228f85921f9a30d6310b0fa3e5798f2695b9750c4add737e82a7611959892a4
- population 4,880 / 4,880
- missing=0, extra=0, duplicate=0, semantic conflicts=0

## Mandatory source gate

Before any Oct-Dec market outcome opens:

MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS

requires:
1. canonical SOL population fully reconstructed from the three frozen field-enrichment partitions
2. population duplicate identities = 0
3. every canonical SOL identity adjudicated for post-liquidation Orca route presence
4. source completeness among Orca-presence rows >= 95%
5. deterministic direction among source-complete Orca rows >= 90%
6. contradictions = 0
7. missing canonical identities = 0
8. extra identities = 0
9. exact route input amount proven for every DIRECTION_PROVEN eligible event

PARTIAL:
valid source but scientific source thresholds miss

BLOCKED:
transport, identity, structural, decoder or source-integrity conflict

No market price, OHLC, return or PnL may be opened before source PASS.

## Mandatory pre-outcome sample gate

After source PASS but before Oct-Dec OHLC/returns:

compute:
- source cascades
- prior-five-minute base volume
- flow_turnover_intensity
- threshold selection
- funding exclusions

READY only if ALL:
- selected signal count >= 25
- distinct UTC decision days >= 8
- F1 selected >= 15
- F2 selected >= 8

If any fail:
MARGINFI_ORCA_TOPQ_REBOUND_OOS_INSUFFICIENT_SAMPLE

and OOS closes without reading Oct-Dec OHLC/returns/PnL.

## Frozen OOS gate

MARGINFI_ORCA_TOPQ_REBOUND_OOS_SURVIVES only if ALL:

1. analyzable trade count >= 25
2. distinct UTC entry days >= 8
3. nominal net mean > 0
4. nominal net median > 0
5. nominal net profit factor > 1.10
6. F1 trade count >= 15
7. F2 trade count >= 8
8. F1 nominal net mean > 0
9. F2 nominal net mean > 0
10. UTC-day block-bootstrap 95% CI lower bound of nominal mean > 0

Bootstrap:
- 20,000 replicates
- complete UTC entry-day blocks
- seed = 26100103

Otherwise:
MARGINFI_ORCA_TOPQ_REBOUND_OOS_NO_EDGE

Market/source integrity failure:
MARGINFI_ORCA_TOPQ_REBOUND_OOS_SOURCE_BLOCKED

## Consequence of SURVIVES

SURVIVES would establish an OOS executable edge under the frozen cost model.

It would NOT by itself authorize live trading.
2025/2026 remain protected pending separate governance.

## Forbidden rescue

After Oct-Dec outcomes open, V0.1 may NOT:
- change top-quartile threshold
- inspect alternative quantiles
- change side LONG
- change 1-minute hold
- change 5-minute cascade linkage
- change turnover denominator
- add event-count, amount, liability, hop-count or time-of-day filters
- change costs
- delete December
- change fold definitions
- reuse Jul-Sep as executable validation
- open 2025 as rescue after OOS failure

## Firewall

jul_sep_discovery_only=true
oct_dec_market_outcomes_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
