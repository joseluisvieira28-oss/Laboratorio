# BINANCE-LISTING-INFORMATION-CASCADE-001 — V0.7 DELAYED-ENTRY 2023 RETROSPECTIVE OOS PRE-OUTCOME FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2023 MARKET OUTCOME ACCESS IN THIS FAMILY

## Purpose
Independently test the delayed-entry continuation hypothesis on calendar-year 2023, which has not been opened in this research family.
This is a retrospective out-of-sample replication, not a prospective live claim.

## Event census
Official Binance CMS catalog.
All 2023 articles whose title begins exactly "Binance Will List ".
T0 = official CMS releaseDate.
Multiple assets in one announcement remain separate observations.
Exclude stablecoins, fiat-like wrapped assets, staked/wrapped derivatives, and assets without >=24h pre-T0 public spot trading.

## Frozen venue hierarchy
1. Bitget spot
2. KuCoin spot
3. MEXC spot
4. Gate spot
5. OKX spot
No venue shopping after outcomes.

## Frozen delayed-entry rule
M = floor(T0 to containing UTC minute).
LONG entry = OPEN of candle M+1m.
H5 = close of M+5m / entry - 1.
H15 = close of M+15m / entry - 1.
H60 = close of M+60m / entry - 1.
MFE/MAE measured from the same delayed entry.
5m volume shock = M..M+4m volume / median 5m wall-clock baseline T-24h..T-1h.

## Frozen survival gate
ALL required:
- n>=12;
- median H15 > +0.75%;
- H15 positive hit rate >=65%;
- median H5 > +0.50%;
- median 5m volume shock >=2x;
- leave-one-out median H15 >0;
- no observation >35% of summed positive H15.

n<12 => SOURCE_BLOCKED_DELAYED_ENTRY_2023.
Otherwise any failed performance gate => NO_EDGE_DELAYED_ENTRY_2023.
All pass => SURVIVES_DELAYED_ENTRY_2023_OOS.

## Governance
No 2023 outcomes may be inspected before source census, source gate and exact observation->venue activation freeze.
No fees/slippage/execution claim unless survival occurs and a separate cost freeze is created.
2026 remains unopened under the source-blocked V0.4-V0.6 program.
No live trading, private endpoints, accounts, orders, wallets, mutation or main merge.
