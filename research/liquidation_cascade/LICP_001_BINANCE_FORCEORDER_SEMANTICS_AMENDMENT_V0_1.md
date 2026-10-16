# LICP-001 — BINANCE FORCEORDER SOURCE SEMANTICS AMENDMENT V0.1

Date: 2026-10-05
Status: PRE-OUTCOME SOURCE CONTRACT CORRECTION
Branch: liquidation-cascade-propagation-v0.1

## Reason

The existing LICP-001 freeze text describes Binance USD-M `forceOrder` as publishing the latest liquidation order from the sampling interval.

Binance's official derivatives changelog states that, effective 2026-04-14, the USD-M liquidation-order stream descriptions for `<symbol>@forceOrder` and `!forceOrder@arr` were updated from "latest liquidation order" to "largest liquidation order".

This amendment corrects source semantics before any new propagation outcome is opened.

## Scientific consequence

Binance `forceOrder` remains a lossy confirmation sensor only.

It MUST NOT be interpreted as:
- complete liquidation volume;
- complete liquidation event count;
- proof that no liquidation occurred when no message is observed;
- a complete ordering of all liquidation events;
- a substitute for Bybit `allLiquidation`.

For LICP-001, any `BINANCE_SNAPSHOT` notional quantile describes the distribution of the Binance-published largest liquidation snapshots observed by this collector. It is not an estimate of total forced-liquidation notional.

## Frozen role after amendment

Primary ignition source:
- Bybit `allLiquidation.BTCUSDT`.

Cross-venue confirmation:
- Binance BTCUSDT `forceOrder` snapshot.
- Same normalized forced-pressure direction remains required.
- Binance remains confirmation-only.

No Bybit threshold, outcome horizon, target venue, direction rule, fee model, or post-trigger outcome rule is changed by this amendment.

## Outcome isolation

At the time of this amendment:
- trigger config remains UNFROZEN;
- no new MEXC propagation outcome is authorized by this document;
- no PnL, MFE, MAE, hit-rate, Sharpe, or forward-return result may be used to choose thresholds.

## Authority

This is a source-semantics correction only. It does not rescue, weaken, or tune the hypothesis.

Official source:
- Binance derivatives changelog, 2026-04-10 entry, effective 2026-04-14.
