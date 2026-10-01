# DLS — MARGINFI Q1-2025 STABLECOIN-LIABILITY REGIME PERSISTENCE GATE V0.1

Date: 2026-10-01
Branch: dls-marginfi-2025-q1-regime-source-v01
Status: FROZEN BEFORE Q1-2025 SOURCE RESULTS ARE OPENED

Parent source freeze:
MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_FREEZE_V0.1.md

Purpose:
Adjudicate whether the December-2024 stablecoin-liability source regime persists into Q1 2025.

Stablecoins in this V0.1 gate are exactly:
- USDC mint EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
- USDT mint Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB

No other mint may be added after Q1 source results are observed.

Month sufficient-sample gate:
- SOL-collateral Marginfi liquidation count >= 30.

Month stablecoin-dominant gate:
- sufficient sample; and
- (USDC liability count + USDT liability count) / SOL-collateral count >= 0.80.

Global persistence PASS:
MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_PERSISTS

only if ALL:
1. parent Q1 source classification = MARGINFI_2025_Q1_LIABILITY_REGIME_SOURCE_PASS
2. Q1 aggregate SOL-collateral event count >= 100
3. Q1 aggregate USDC+USDT liability share >= 0.80
4. at least 2 of the 3 calendar months are sufficient-sample
5. at least 2 of the 3 calendar months are stablecoin-dominant

If parent source PASS but persistence gates miss:
MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_NOT_PROVEN

If parent source is incomplete/blocked:
MARGINFI_2025_Q1_STABLECOIN_LIABILITY_REGIME_SOURCE_BLOCKED

This is a SOURCE-ONLY classification.
It does not authorize market outcomes, trading, or a claim of profitable edge.

Consequence of PERSISTS:
A separate source-route census may test whether the persistent stablecoin-liability SOL liquidations
continue to execute through Orca Whirlpools in 2025. That source-route test must precede any 2025
market-outcome opening.

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
