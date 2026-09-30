# DLS — MARGINFI -> ORCA WHIRLPOOLS FULL JUL-SEP SIGNED-FLOW CENSUS V0.1 — FREEZE

Date: 2026-09-30
Branch: dls-marginfi-route-migration-v01
Status: FROZEN SOURCE-ONLY BEFORE FULL ORCA CENSUS

Family:
DLS-MARGINFI-ORCA-SIGNED-FLOW-001

Parent calibration authority:
MARGINFI_ORCA_SIGNED_FLOW_CALIBRATION_PASS

Calibration run:
36770954139

Calibration artifact:
dls-marginfi-orca-signed-flow-calibration-v01
artifact ID 11124145615
digest sha256:be6d0fe8c6c91dd7d7183af91b4f408e2829f763c4c790cced9b9fa8f67d627a

Calibration result:
- 64 / 64 source-complete
- 64 / 64 direction proven
- 64 / 64 exact route input amount proven
- 0 ambiguity
- 0 contradictions

## Canonical Jul-Sep SOL population

Source authority:
MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PASS

Canonical run:
36769242124

Canonical artifact:
dls-marginfi-sol-julsep-signed-flow-source-v01-fallback
artifact ID 11123027458
digest sha256:ce0627614a9fdc3b5acb7d8dac3d8c189b88024a31e038b069d3c8aa375dc38d

Canonical population file:
MARGINFI_SOL_JULSEP_SOURCE_POPULATION_V0.1.ndjson

Exact population:
8,857 source-authoritative Marginfi SOL-collateral liquidation identities.

The full Orca census may NOT redefine, drop or add population identities.

## Orca authority

Program:
whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc

Pinned upstream authority:
orca-so/whirlpools
commit f4b99e79e7140f3917e4ce81a2e8ad06ccdf8ce4

Use exactly the instruction discriminators, account layouts, direction rules and legacy pool-mint
resolution frozen in:
MARGINFI_ORCA_SIGNED_FLOW_CALIBRATION_FREEZE_V0.1.md

No decoder semantic may change after the full population is opened.

## Frozen population sharding

Every canonical population identity is assigned to exactly one of 16 shards.

Identity string:
signature + "|" + canonical-json(instructionAddress)

Shard:
int(SHA256(identity), 16) mod 16

Shard IDs:
orca-00 through orca-15.

Sharding is transport only.

## Exact transaction adjudication

For every assigned canonical population row:

1. query its exact finalized slot;
2. recover the exact successful parent transaction by signature and transactionIndex;
3. bind the canonical Marginfi liquidation by exact program ID + instructionAddress;
4. retain successful committed Orca instructions strictly after the canonical liquidation;
5. decode all supported Orca swap instructions under the frozen calibration semantics.

If there is no post-liquidation Orca instruction:
classification = NOT_ORCA_ROUTE

If Orca is present but no supported/complete swap route can be proven:
classification = SOURCE_EVIDENCE_INCOMPLETE

If source-complete route endpoints are:
SOL -> Marginfi liability mint:
classification = DIRECTION_PROVEN
route_semantic = COLLATERAL_TO_LIABILITY_ORCA_PROVEN
asset_label = SIGNED_SELL_PRESSURE_PROVEN
liability_label = SIGNED_BUY_PRESSURE_PROVEN

If reverse:
LIABILITY_TO_COLLATERAL_ORCA_PROVEN

If complete endpoints are neither:
DIRECTION_AMBIGUOUS

Contradictions are fail-closed.

## Exact input amount

For a proven route:

exact_route_input_amount is source-proven iff the first decoded Orca swap has
amount_specified_is_input=true.

Otherwise direction may remain proven but exact amount is UNPROVEN.

No estimated amount is permitted.

## Shard PASS

MARGINFI_ORCA_FULL_SOURCE_SHARD_PASS iff:
- every assigned population identity has exactly one adjudication row;
- parent transaction identity conflicts = 0;
- unresolved exact-slot transport failures = 0;
- population duplicates = 0.

Scientific incompleteness is preserved row-by-row and does not by itself transport-block a shard.

## Global PASS

MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS only if ALL:

1. all 16 shard receipts PASS;
2. merged population count = 8,857;
3. merged adjudication count = 8,857;
4. missing identities = 0;
5. extra identities = 0;
6. duplicate identities = 0;
7. Orca route-presence count > 0;
8. source-complete rate among Orca-presence rows >= 95%;
9. direction-proven among source-complete Orca routes >= 90%;
10. contradictions = 0.

PARTIAL:
valid full population but source-semantic thresholds miss.

BLOCKED:
transport, identity, population, merge or decoder-authority conflict.

## Reporting

Report:
- month population counts;
- Orca route presence by month;
- source-complete by month;
- direction proven by month;
- exact input amount coverage;
- instruction type distribution;
- route semantic distribution;
- incomplete reasons;
- liability mint distribution.

## Consequence

PASS authorizes design of a separately frozen Orca market-impact family.

PASS does NOT authorize market outcomes by itself.

Jul-Sep 2024 market outcomes remain CLOSED during this census.

## Firewall

prices=false
ohlc=false
returns=false
pnl=false
jul_sep_market_outcomes_opened=false
oct_dec_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_decode_tuning=false
