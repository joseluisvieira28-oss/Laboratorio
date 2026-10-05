# BINANCE-LISTING-INFORMATION-CASCADE-001 — V0.4 DELAYED-ENTRY 2026 HOLDOUT PRE-OUTCOME FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2026 MARKET OUTCOME ACCESS

## Scientific question
Does the Binance public spot-listing information shock exhibit exploitable-looking continuation AFTER the announcement is already public, rather than only an instantaneous mark-up from the pre-announcement price?

This is a NEW hypothesis. It does not alter or rescue the V0.3 verdict NO_EDGE_HOLDOUT.

## Holdout
Calendar 2026 official Binance listing announcements from 2026-01-01T00:00:00Z through 2026-10-04T23:59:59Z.
2026 market outcomes have not been opened in this family before this freeze.

## Event census
Authority: official Binance CMS catalog.
Include every article in the frozen interval whose title begins exactly "Binance Will List ".
T0 = official CMS releaseDate.
Multiple assets per announcement remain separate asset observations.
Exclude stablecoins, fiat-like wrapped assets and staked/wrapped derivatives.
Require >=24h of pre-T0 public spot trading on the selected venue.

## Frozen venue hierarchy
1. Bitget spot
2. KuCoin spot
No venue shopping after outcomes.
Other venues can only be post-result integrity replicas.

## Frozen delayed entry
Let M = floor(T0 to the containing UTC minute).
LONG entry price = OPEN of the candle starting M+1 minute.
This deliberately waits until the next minute boundary after the public announcement.
No P0/pre-announcement price is used in the trade return.

Frozen gross trade returns:
- H5: entry OPEN at M+1m to CLOSE of candle M+5m (5 one-minute candles);
- H15: entry OPEN at M+1m to CLOSE of candle M+15m (15 one-minute candles);
- H60: entry OPEN at M+1m to CLOSE of candle M+60m (60 one-minute candles).
MFE/MAE are measured from the same delayed entry price over each holding interval.
Direction is always LONG.

Context metric:
5m volume shock = volume in M..M+4m / median non-overlapping wall-clock 5m volume buckets T-24h..T-1h.

## Frozen V0.4 holdout gate
SURVIVES_DELAYED_ENTRY_HOLDOUT iff ALL:
- n >= 12;
- median H15 > +0.75%;
- H15 positive hit rate >= 65%;
- median H5 > +0.50%;
- median 5m volume shock >= 2x;
- leave-one-out median H15 remains >0;
- no single observation contributes >35% of summed positive H15.

If n<12 => SOURCE_BLOCKED_DELAYED_ENTRY.
If n>=12 and any performance gate fails => NO_EDGE_DELAYED_ENTRY.

## Governance
No fees/slippage/fill-quality claim yet. If and only if V0.4 survives, a separate pre-cost freeze is required before modelling executable net PnL.
No threshold, direction, event selection, venue order, entry rule or horizon may change after any 2026 market outcome is opened.
No live trading, private endpoints, accounts, wallets, exchange mutation, orders or main merge.
