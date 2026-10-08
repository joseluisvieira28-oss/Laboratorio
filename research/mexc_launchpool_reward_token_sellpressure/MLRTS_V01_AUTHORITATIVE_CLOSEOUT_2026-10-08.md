# MEXC-LAUNCHPOOL-REWARD-TOKEN-SELLPRESSURE-001 — V0.1 AUTHORITATIVE CLOSEOUT
Date: 2026-10-08
Status: CLOSED — MARKET_DATA_INSUFFICIENT / SOURCE_BLOCKED_FOR_DISCOVERY

## Frozen scientific identity
- Event: official MEXC Launchpool initial listing of the reward token
- Market: PROJECT/USDT relative to BTC/USDT
- T0: official MEXC spot-listing time
- Entry: first exact 15m candle open at/after T0
- Exit: exact +24h
- Expected sign: negative
- Frozen Discovery minimum: N >= 10

Pre-outcome freeze commit:
dd6093a09b12cd444be477aeeb10a2e9a7f9b864

Frozen source-corpus commit:
2a0b61a6e822424e1d741c701a5b57f171938710

## Source gate
PASS:
- 11 eligible initial-listing Launchpool events
- 11 unique reward symbols
- calendar years 2025 and 2026
- exact official listing T0 for all 11

## First frozen Discovery run
Workflow:
MLRTS V0.1 Frozen Discovery
Run:
37745840540

Result:
- planned events: 11
- analyzable: 4
- required: >=10
- classification: MARKET_DATA_INSUFFICIENT

Resolved market outcomes are preserved and are NOT sufficient for scientific adjudication.

Observed diagnostics from the incomplete N=4 block:
- negative observations: 1/4
- mean relative 24h log return: +0.9197549228533155
- median relative 24h log return: +0.9999139526149391
- negative fraction: 0.25
- one-sided negative sign-test p: 0.9375
These values are descriptive only because the frozen N gate failed.

## Missing historical symbols
The current official MEXC history route could not resolve:
- IP
- TERM
- K
- EPT
- ICEBERG
- BOMB
- TRN

## Technical remediation audit
A remediation freeze was committed before recovery attempts:
9b0d449a60091a81661063667bf85eb1fd5b661c

Four independent public/official recovery routes were exhausted:

### V0.1.1 Historical binding probe
Run 37771655551
- current symbol metadata: no recoverable bindings for the seven missing symbols
- market-data-download pages: no embedded historical IDs recovered

### V0.1.2 Public bundle symbol-ID probe
Run 37771697765
- 59 public MEXC JS bundles scanned
- token-hit count for IP, TERM, K, EPT, ICEBERG, BOMB, TRN: 0 each

### V0.1.3 Official history-index recovery
Run 37771768231
- tokens with working official history: 4 total
- no expansion beyond the already resolvable set sufficient to reach N >=10

### V0.1.4 Public kline recovery
Run 37771904398
- direct public historical kline probes returned no usable rows for all seven missing symbols

## Authoritative classification

SOURCE_GATE_PASS
+
FROZEN_DISCOVERY_N_4_OF_11
+
FOUR_OFFICIAL_PUBLIC_RECOVERY_ROUTES_EXHAUSTED
=
MARKET_DATA_INSUFFICIENT__SOURCE_BLOCKED_FOR_DISCOVERY

This is NOT NO_EDGE.

The four resolved outcomes lean strongly opposite the frozen sell-pressure hypothesis, but the precommitted sample minimum was not met. They cannot legitimately be promoted into a LONG hypothesis or used to declare a terminal edge verdict.

## Forbidden rescue
- no sign inversion using the N=4 outcomes;
- no promotion of frozen 1h/6h diagnostics;
- no alternate T0/horizon;
- no event deletion;
- no replacement venue for the same frozen family;
- no post-outcome token-category or reward-size filter.

## Reopen conditions
This exact family may reopen only if:
1. authoritative/public MEXC historical 15m data for enough of the frozen seven missing symbols becomes available to reach N >=10; or
2. a prospective corpus independently reaches the frozen sample requirement under a new pre-outcome forward protocol.

## Governance
Research only.
No live trading.
No orders.
No account access.
No exchange mutation.
No wallet.
No spending.
No main merge.
