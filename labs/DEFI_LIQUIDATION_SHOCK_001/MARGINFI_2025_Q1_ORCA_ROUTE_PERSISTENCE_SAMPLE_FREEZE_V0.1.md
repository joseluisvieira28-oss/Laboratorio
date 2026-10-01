# DLS — MARGINFI Q1-2025 ORCA ROUTE PERSISTENCE SAMPLE V0.1 — CONDITIONAL FREEZE

Date: 2026-10-01
Branch: dls-marginfi-2025-q1-regime-source-v01
Status: FROZEN SOURCE-ONLY / CONDITIONAL / NO 2025 MARKET OUTCOMES

Prerequisite:
MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_PERSISTS

If that prerequisite does not PASS, this sample MUST NOT run.

## Purpose

Test whether the Q1-2025 SOL-collateral Marginfi liquidation regime continues to route through Orca
Whirlpools after the December-2024 route/liability transition.

No price, return, PnL, funding or market-direction outcome may be read.

## Population authority

Use the exact rows from:
MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_PASS

For each month 202501, 202502, 202503:
- restrict to asset_mint = So11111111111111111111111111111111111111112;
- rank each canonical identity by ascending SHA256 of:
  signature || "|" || JSON-canonical instructionAddress;
- select the first 64 events.

If a month has fewer than 64 SOL events, select the full month and flag SAMPLE_UNDERSIZED.

No amount, liability mint, transaction composition or later data participates in ranking.

## Exact transaction census

For every selected identity:
- query exact finalized slot;
- recover exact successful parent transaction by signature + transactionIndex;
- bind exact canonical Marginfi instructionAddress;
- enumerate committed successful instructions after the canonical liquidation.

Orca Whirlpools official program:
whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc

Orca presence:
at least one committed successful Orca Whirlpools instruction strictly after the canonical Marginfi
liquidation in the same transaction.

## Direction semantics

For Orca-presence events, reuse exactly the already validated source decoder and semantics from:
MARGINFI_ORCA_SIGNED_FLOW_CALIBRATION_PASS

Accepted instruction types:
- swap
- swap_v2
- two_hop_swap_v2

Use source-proven token-flow endpoints only.
No market price or return.

## Sample source PASS

MARGINFI_2025_Q1_ORCA_ROUTE_SAMPLE_PASS only if:
- every selected transaction is recovered exactly;
- canonical Marginfi binding complete;
- identity conflicts = 0;
- source structural errors = 0.

## Route persistence verdict

MARGINFI_2025_Q1_ORCA_ROUTE_PERSISTS only if ALL:
1. sample source PASS;
2. all three months have sample size = 64;
3. combined Orca-presence share >= 0.50;
4. at least 2 of 3 monthly Orca-presence shares >= 0.50;
5. source-complete direction evidence among Orca-presence events >= 0.95;
6. contradictions = 0.

If sample source PASS but these persistence gates miss:
MARGINFI_2025_Q1_ORCA_ROUTE_NOT_PROVEN

This is source-only and does not authorize 2025 market outcomes or live trading.

Firewall:
prices_2025_opened=false
returns_2025_opened=false
pnl_2025_opened=false
funding_2025_opened=false
market_direction_2025_opened=false
prices_2026_opened=false
returns_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
