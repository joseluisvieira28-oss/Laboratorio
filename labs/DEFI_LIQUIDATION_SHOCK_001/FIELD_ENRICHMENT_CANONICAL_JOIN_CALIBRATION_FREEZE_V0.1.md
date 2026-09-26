# DEFI-LIQUIDATION-SHOCK-001 — FIELD ENRICHMENT CANONICAL JOIN CALIBRATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

Authority:
- `FIELD_ENRICHMENT_CANONICAL_JOIN_FREEZE_V0.1.md`
- `FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS`
- `FIELD_DECODER_AUTHORITY_8_OF_8_CLASS_PASS`

## Purpose

Prove that requesting instruction account references for enrichment does not alter the realized-event population
returned by the same frozen SQD source route.

## Frozen representative slices

### Collector family A — Kamino/Save11 census implementation
Protocol representative: Kamino
Window:
`[2023-11-17T14:48:24Z, 2023-11-18T00:00:00Z)`
Program:
`KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`
Prefix:
`b1479abce2854a37`

### Collector family B — Marginfi/Save0c census implementation
Protocol representative: marginfi
Window:
`[2023-02-13T00:00:00Z, 2023-02-14T00:00:00Z)`
Program:
`MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`
Prefix:
`d6a997d5fba756db`

### Collector family C — Drift census implementation
Window:
`[2022-11-07T00:00:00Z, 2022-11-08T00:00:00Z)`
Program:
`dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`
Classes:
- liquidate_perp / 4b2377f7bf128b02
- liquidate_spot / 6b00802923e5fb12
- liquidate_borrow_for_perp_pnl / a911205acf94d11b
- liquidate_perp_pnl_for_deposit / ed4bc6ebe9ba4b23

## A/B query rule

For each slice run two independent, fully completed stream traversals with identical:
- program filter;
- slot envelope;
- exact UTC local membership;
- local discriminator decode;
- execution-state classification;
- canonical key.

A = baseline fields used for census identity.
B = same fields plus `instruction.accounts=true`.

No price/balance/token amount fields are requested.

Canonical realized key:
`class_or_protocol + signature + instructionAddress`

## PASS rule

For each collector family:
- baseline successful key count > 0;
- enriched successful key count > 0;
- missing keys = 0;
- extra keys = 0;
- classification conflicts = 0;
- enriched account list non-empty for every successful key;
- source anomaly count = 0 in both traversals.

Global PASS:

`FIELD_ENRICHMENT_CANONICAL_JOIN_3_OF_3_FAMILY_PASS`

Any mismatch:

`FIELD_ENRICHMENT_CANONICAL_JOIN_CALIBRATION_FAIL_CLOSED`

PASS permits population-wide source enrichment using the same immutable canonical event population.
It does not authorize prices, notional, returns or PnL.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
balances=false
token_amounts=false
token_decimals=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
