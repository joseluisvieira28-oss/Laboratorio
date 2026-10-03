# LIQUIDATION-FLOW-FWD-001 — CALIBRATION HEALTH ADDENDUM V0.13.1

Date: 2026-10-03
Status: PRE-CALIBRATION / SOURCE-ONLY
Effective only after `LIQUIDATION_FLOW_ETH_SOURCE_COMPLETION_FREEZE_V013_V01.md` reaches SOURCE_GATE_PASS.

This addendum does not alter the frozen signal hypothesis, 95th-percentile threshold rule,
0.80 imbalance requirement, 10-minute horizon, min N=100 or FOLLOW_FORCED_FLOW direction.
It only makes "healthy 60-second calibration bin" operationally exact before any calibration begins.

## Bin clock

- UTC minute bins [start, start+60000).
- Collection begins at the first full UTC minute strictly after the source-gate PASS receipt.
- A valid liquidation belongs to the bin containing source event timestamp T, not local receive time.
- Finalization waits 5000 ms after the minute end so a still-fresh late delivery can be assigned by T.
- No interpolation, imputation or reassignment across bins.

## Healthy-bin requirements per symbol

A bin is healthy only if all are true:

1. dedicated public websocket connection for that symbol was open before bin start;
2. that symbol's subscription acknowledgement succeeded before bin start;
3. the same connection epoch remained continuously open through bin end + 5000 ms;
4. no transport exception, malformed JSON or invalid liquidation item occurred for that symbol during the bin/finalization grace;
5. public heartbeat pong evidence exists in both halves of the minute:
   - at least one pong received in [start, start+30000);
   - at least one pong received in [start+30000, start+60000).

Ping cadence is 15 seconds. Pongs are preserved raw with receive timestamps and hashes.

An empty but healthy bin is a defensible zero-event bin. An empty bin without all health evidence is MISSING, not zero.

## Bin quantities

For each healthy bin:

- `forced_sell_proxy` = sum(v*p) for Bybit side Buy, because Buy means a long position was liquidated;
- `forced_buy_proxy` = sum(v*p) for Bybit side Sell, because Sell means a short position was liquidated;
- `total_notional_proxy` = forced_sell_proxy + forced_buy_proxy;
- `signed_buy_minus_sell_proxy` = forced_buy_proxy - forced_sell_proxy;
- `absolute_imbalance_ratio` = abs(signed_buy_minus_sell_proxy) / total_notional_proxy when total > 0.

The bankruptcy-price product v*p remains a proxy, not executed USD notional.

## Threshold finalization

No numeric threshold may be computed or published until a merged calibration ledger has,
for EACH symbol:

- at least 1440 healthy bins;
- at least 100 healthy bins with total_notional_proxy > 0.

At that point only the pre-frozen nearest-rank 95th percentile of nonzero healthy-bin
total_notional_proxy is permitted, rank ceil(0.95*n). No alternate quantile is tested.

Source-gate observations, including the three prior BTC events and the ETH event that may
complete the gate, are excluded from calibration.

No MEXC payout/index/outcome subscription is permitted during calibration.
