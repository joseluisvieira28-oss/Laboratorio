# CROSS-ASSET-VOL-STRESS-001 — TIMING ADDENDUM V0.1

**PRE-OUTCOME / IMMUTABLE AFTER DISCOVERY**

Lab: `CROSS-ASSET-VOL-STRESS-001`  
MVE: `CAVS-VXSETTLE-W1-001`

## Causal timing correction
After `SOURCE_DATA_PASS` and before any BTC price/outcome access, the source audit identified an official Cboe timing exception for the U.S. National Day of Mourning on 2018-12-05. Cboe documented that the VIX weekly contract retained expiration date 2018-12-05 while the final settlement value was determined on 2018-12-06.

Official notice:
`https://cdn.cboe.com/resources/schedule_update/2018/Cboe-to-Observe-National-Day-of-Mourning-on-Wednesday-December-5-2018.pdf`

Therefore `expire_date + 1 calendar day 00:00 UTC` is not universally causal.

## Amended frozen execution rule
- signal date authority remains the provider `expire_date`;
- entry = `expire_date + 2 calendar days`, BTCUSDT daily open at 00:00 UTC;
- exit = entry + exactly 7 calendar days, BTCUSDT daily open;
- D+2 applies uniformly to **every** 2018–2024 settlement;
- any required bar outside 2018–2024 or missing is dropped fail-closed;
- one-position overlap policy remains unchanged.

## Everything else unchanged
- delta VX > 0 => SHORT BTC;
- delta VX < 0 => LONG BTC;
- delta VX = 0 => no trade;
- NET10 primary / NET20 stress;
- no thresholds, level filters, monthly-vs-weekly selection, VIX term-structure filter, BTC filter or regime filter;
- bootstrap 5,000 / seed 230911 / block length 4 resolved trades;
- promotion gates remain N>=300, NET10 mean>0, PF>1, bootstrap 95% lower>0, >=5/7 non-negative years, >=3/4 non-negative years in 2021–2024, provenance/firewalls pass.

At this freeze: BTC market values = unopened; returns/PnL = uncomputed; 2025=false; 2026=false; live trading=false; exchange mutation=false.
