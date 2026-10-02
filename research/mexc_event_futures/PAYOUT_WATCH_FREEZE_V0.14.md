# MEXC EVENT FUTURES LAB — PROSPECTIVE PAYOUT WATCH FREEZE V0.14

Date: 2026-10-02
Status: SOURCE-ONLY / PROSPECTIVE / NO TRADING

## Trigger

Two anonymous browser captures minutes apart showed that Event Futures payout is genuinely dynamic:
- ETH_USDT 10m = 0.70 in V0.12.1;
- ETH_USDT 10m = 0.40 in V0.12.2.

This directly confirms that a historical fixed-payout assumption is unsafe.

## Objective

Create the first exact prospective payout time series from the public Event Futures product route.

## Source

Anonymous browser page:
`https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT`

Exact public product route:
`https://www.mexc.com/api/platform/futures/api/v1/event_contract/detail`

## Frozen observation schedule

- 12 snapshots
- one snapshot every 30 seconds
- total observation window ~5.5 minutes after first sample
- all records returned by the exact product route are preserved
- flattened payout observations are emitted per:
  symbol × state × time-unit × duration × up/down payout

No trading hypothesis is tested.

## Safety boundary

- fresh anonymous browser context;
- no imported cookies;
- no login;
- no account endpoints;
- GET only;
- no order submission;
- no exchange/account mutation;
- no live trading;
- no main merge.

## Outputs

1. raw timestamped product snapshots;
2. flattened payout time series;
3. per-contract observed min/max/change count;
4. explicit state changes if any.

No profitability or edge verdict is allowed in V0.14.
