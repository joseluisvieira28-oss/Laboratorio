# DEFI-LIQUIDATION-SHOCK-001 — DRIFT LIQUIDATE-PERP-WITH-FILL CENSUS FREEZE V0.1

Date: 2026-09-29
Status: FROZEN SOURCE-ONLY / NO MARKET OUTCOMES

## Purpose

Census the distinct Drift instruction liquidate_perp_with_fill separately from direct liquidate_perp.

Anchor instruction discriminator:
- liquidate_perp = 4b2377f7bf128b02
- liquidate_perp_with_fill = 5f6f7c6956a9bb22

## Window

2022-11-04T15:17:54Z <= source timestamp < 2025-01-01T00:00:00Z.

## Realized instruction rule

Include only instructions where:
- programId = Drift v2 program;
- instruction data starts with 5f6f7c6956a9bb22;
- parent transaction err is null;
- instruction isCommitted is true;
- instruction error is null;
- exact transaction signature and instructionAddress exist.

Deduplicate by:
signature + canonical instructionAddress.

Decode only source fields:
- market_index from bytes 8:10 little-endian;
- transaction/signature identity;
- slot/timestamp;
- instruction address.

No prices or returns.

## Next gate

If successful realized count = 0:
DRIFT_WITH_FILL_CENSUS_ZERO.

If count > 0 with no identity/source conflict:
DRIFT_WITH_FILL_CENSUS_PASS.

Only PASS permits a deterministic source sample for fill-mechanism classification.

## Firewall

prices=false
returns=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
