# ETH-STAKING-FLOW-001 — V3 STAGE-A CBT RESPONSE-ENVELOPE REMEDIATION V0.1.9

Date frozen: 2026-09-27
Status: FROZEN BEFORE V0.1.9 NETWORK EXECUTION / SOURCE-ONLY / OUTCOME-BLIND

Observed V0.1.5 fact:
- LAB_PROXY returned HTTP 200 for dim_validator_status queries.
- The V0.1.5 parser classified the response unusable because it expected a JSON object containing dim_validator_status/items.
- No market outcomes were opened.

Official cbt-api documentation confirms:
- endpoint shape GET /api/v1/{table};
- underscore filter suffixes such as _gte/_lte/_eq;
- page_size/page_token pagination.

## Purpose

Determine the actual JSON response envelope exposed by the public LAB_PROXY for dim_validator_status and, only if structurally compatible with the official dim_validator_status schema, permit a transport/parser correction without changing source semantics or scientific rules.

## Frozen endpoint

https://lab.ethpandaops.io/api/v1/mainnet/dim_validator_status

Frozen probe:
- validator_index_gte=0
- epoch_lte=401063
- page_size=3
- order_by=validator_index,epoch

## Allowed response-shape outputs

- HTTP status
- content type
- raw byte length and SHA256
- JSON root type: object/list/other
- object top-level keys only
- array length
- first-row field names only
- presence/type of next-page token
- no validator-level numeric field values need be emitted

## Acceptable transport envelopes

A later reconstruction may accept either:
1. documented object wrapper containing repeated dim_validator_status rows plus optional next_page_token; or
2. a bare JSON list whose rows expose the exact official dim_validator_status field names.

Any other structure remains technical failure.

A bare list without a defensible complete-pagination mechanism is NOT sufficient for full Stage-A reconstruction.

## Firewalls

No signal evaluation.
No ETH/BTC price data.
No returns/PnL.
No source after 2026-08-31.
No live trading/orders/wallets/exchange mutation.
No main merge.
No post-outcome tuning.
