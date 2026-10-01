# MARGINFI ORCA DECEMBER 2024 SOURCE REGIME AUDIT — PASS CLOSEOUT

Date: 2026-10-01
Branch: dls-marginfi-orca-dec-regime-v01

Canonical audit run:
36816036519

Canonical artifact:
dls-marginfi-orca-dec-regime-audit-v01
artifact ID 11141292778
digest sha256:7cf366470d7a51d50ac33a8cdeacfaa7b29fe41262485e0a1187ec384e7e6d36

Classification:
MARGINFI_ORCA_DEC_REGIME_SOURCE_AUDIT_PASS

The audit is source/feature-only.
No 2025 market price, return or PnL was opened.

## Structural regime shift

December 2024 differs from October-November by orders of magnitude.

Median cascade sold SOL:
- Oct: 0.007638541 SOL
- Nov: 0.060262811 SOL
- Dec: 53.021716597 SOL

Ratios:
- Dec / Nov = 879.8414x
- Dec / Oct = 6941.3408x

Median individual event sold SOL:
- Oct: 0.004348837 SOL
- Nov: 0.021001327 SOL
- Dec: 0.1181227 SOL

Ratios:
- Dec / Nov = 5.6245x
- Dec / Oct = 27.1619x

Median prior-five-minute SOLUSDT base turnover:
- Oct: 66,142 SOL
- Nov: 178,843 SOL
- Dec: 415,357 SOL

Turnover increased, but far less than forced-flow cascade size:
- Dec / Nov = 2.3225x
- Dec / Oct = 6.2798x

Median flow-turnover intensity:
- Oct: 7.7239893575e-08
- Nov: 3.2826278863e-07
- Dec: 1.0539137511e-04

Ratios:
- Dec / Nov = 321.0579x
- Dec / Oct = 1364.4682x

Therefore the December intensity regime is numerator-dominated: forced SOL selling grew far more than
the preceding market turnover denominator.

## Cascade structure

October:
- 61 source events
- 24 cascades
- median 2 events/cascade
- max 9 events/cascade

November:
- 162 source events
- 37 cascades
- median 2 events/cascade
- max 30 events/cascade

December:
- 2,040 source events
- 16 cascades
- median 50.5 events/cascade
- max 599 events/cascade
- total sold SOL = 2,430.042886589

December forced flow is therefore organized into far larger and denser liquidation cascades.

## Liability composition

October and November are dominated by liquid-staking-token liabilities.

December changes regime sharply:

USDC mint:
EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
- 1,835 / 2,040 events
- 89.95098%

USDT mint:
Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB
- 183 / 2,040 events
- 8.97059%

USDC + USDT:
- 2,018 / 2,040 events
- 98.92157%

Top-3 liability share:
99.41176%

Thus December is not merely a larger version of the earlier regime. The debt composition changes from
primarily LST liabilities to overwhelmingly stablecoin liabilities.

## Concentration

December source flow occurs on only 2 decision days.

- top day share of sold SOL = 68.7749%
- top 2 days share = 100%
- top cascade share = 27.0284%
- top 5 cascades share = 82.4829%

The regime is temporally concentrated rather than a uniform month-wide state.

## Scientific consequence

This source audit establishes a real structural December liquidation regime:
large, dense, stablecoin-liability Marginfi SOL liquidations routed through Orca.

It does NOT establish an executable edge.

The terminal rolling-relative-intensity OOS family remains NO_EDGE because:
- Oct-Nov gross mean was slightly negative;
- the frozen net OOS failed;
- positive OOS gross was concentrated in December.

A future regime-conditioned trading family requires an untouched market period.
The next legitimate step is source-only persistence testing in 2025 before any 2025 market outcome is opened.

## Firewall

prices_2025_opened=false
returns_2025_opened=false
pnl_2025_opened=false
market_direction_2025_opened=false
prices_2026_opened=false
returns_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
