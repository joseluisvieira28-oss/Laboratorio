# MEXC EVENT FUTURES LAB — V0.11.6 CLOSEOUT

Date: 2026-10-03
Status: SOURCE GATE PASSED FOR CURRENT PRODUCT/PAYOUT SNAPSHOT
Verdict: `EXACT_PAYOUT_FIELDS_FOUND`

## Run authority

Authoritative hardened run:

- Workflow: `MEXC Event Futures Browser Exact Capture V0.11.6`
- Run: `37070907487`
- Head: `b6442f65364e2ab642e57565c8ca7ea87c805981`
- Artifact: `mexc-event-futures-browser-exact-v0116-evidence`
- Artifact id: `11254487787`
- Artifact digest: `sha256:f11288ddaaa8f7e7c78b4ac2bfd151d4d3bbecedb75443b361543c1ae7635a91`

Safety checks passed:

- NO_AUTH = PASS
- NO_ORDERS = PASS
- NO_MUTATION = PASS
- NO_PRIVATE = PASS
- GET_ONLY_TRANSMITTED = PASS
- service workers blocked
- fresh Chromium context; no imported login/profile/cookies

## Critical source result

A normal unauthenticated Event Futures page load returned HTTP 200 JSON from:

`https://www.mexc.com/api/platform/futures/api/v1/event_contract/detail`

This was observed passively from the page; V0.11.6 did not actively call the bundle-marked `needLogin:true` detail function.

The response contained exact current Event Futures product configuration, including:

- `symbol`
- `contractId`
- `state`
- `cycleConfigMap`
- `upPayRate`
- `downPayRate`
- `investMinAmount`
- `investMaxAmount`
- `indexPriceScale`
- `payRateScale`
- settlement coin and quote/base metadata

Therefore the blocker that prevented exact payout observation from a bare GitHub-runner GET is resolved by the fresh public browser session.

## Current authoritative snapshot

### BTC_USDT

- state: ONLINE
- contractId: 10
- min/max amount: 1 / 250 USDT
- 10 minute: upPayRate 0.70 / downPayRate 0.70
- 30 minute: 0.85 / 0.85
- 1 hour: 0.85 / 0.85
- 1 day: 0.85 / 0.85

### ETH_USDT

- state: ONLINE
- contractId: 11
- min/max amount: 1 / 150 USDT
- 10 minute: 0.40 / 0.40
- 30 minute: 0.85 / 0.85
- 1 hour: 0.85 / 0.85
- 1 day: 0.85 / 0.85

### NVIDIA_USDT

- state: PAUSE
- contractId: 1357
- min/max amount: 5 / 150 USDT
- 10 minute: 0.80 / 0.80
- 30 minute: 0.85 / 0.85
- 1 hour: 0.85 / 0.85
- 4 hour: 0.85 / 0.85

### MUSTOCK_USDT

- state: PAUSE
- contractId: 1594
- min/max amount: 5 / 150 USDT
- 10 minute: 0.80 / 0.80
- 30 minute: 0.85 / 0.85
- 1 hour: 0.85 / 0.85
- 4 hour: 0.85 / 0.85

### SPCXSTOCK_USDT

- state: PAUSE
- contractId: 1929
- min/max amount: 5 / 150 USDT
- 10 minute: 0.80 / 0.80
- 30 minute: 0.85 / 0.85
- 1 hour: 0.85 / 0.85
- 4 hour: 0.85 / 0.85

The same detail response also exposed additional currently OFFLINE products (SOL_USDT, XRP_USDT, SUI_USDT, DOGE_USDT). They are preserved in the artifact but are not promoted into the active prospective scope.

## Public schedule routes

The same browser context returned HTTP 200 JSON for both bundle-proven public routes across all five scoped symbols:

- `/event_contract/trade_date_time?symbol=...`
- `/event_contract/last_trade_date_time?symbol=...`

For the stock-linked symbols, the schedule response exposed `openDate` / `stopDate` windows and `lastDateTime` / `contractId`.

BTC_USDT and ETH_USDT returned empty trade-date arrays and zeroed last-trade-date records in this snapshot; that is preserved as an observed source fact, not interpreted as a product-state verdict.

## Important correction to prior assumption

Payout is not defensibly represented by one fixed 80% constant.

The exact live product response showed simultaneous current values of 0.40, 0.70, 0.80, 0.85 and 0.87 across product/cycle configurations.

Any Event Futures edge test from this point forward MUST use the payout actually observed for the relevant asset, side and horizon at the decision timestamp. Historical proxy analyses that assumed 0.80 remain proxy analyses only and cannot be re-labelled as exact-product EV tests.

## What V0.11.6 does NOT prove

- It does not provide historical payout history.
- It does not prove how often or why payout changes.
- It does not prove the exact settlement/index observation stream yet.
- It does not prove any trading edge.
- It does not authorize live trading.
- It does not authorize order placement or private endpoints.

## Next legitimate gate

V0.12 must be a strictly prospective exact-product collector.

No payout history may be reconstructed retroactively. The forward boundary starts only after the V0.12 freeze is committed. Each snapshot must preserve the exact observed pay-rate fields and product state before later outcome resolution.
