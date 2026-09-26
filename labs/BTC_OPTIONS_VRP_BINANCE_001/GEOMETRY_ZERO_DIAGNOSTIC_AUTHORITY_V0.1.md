# BTC-OPTIONS-VRP-BINANCE-001 — GEOMETRY ZERO-ROW DIAGNOSTIC AUTHORITY V0.1

Date: 2026-09-19
Parent census: `BOVRP-BINANCE-PREDISCOVERY-GEOMETRY-001`
Parent run: `35461347235`
Parent result: `PREDISCOVERY_GEOMETRY_INSUFFICIENT`

## Why a technical diagnostic is allowed

The parent census loaded 147 source days and found non-zero 08:00 rows on the files, but zero complete structural rows and therefore zero 24h episodes in every frozen DTE bin. Because the earlier source gate already proved that the files expose bid/ask prices and quantities, option identity, strike, right, expiry and Greeks, this all-zero geometry is suspicious for a field-value/semantic incompatibility.

This diagnostic may identify only the first structural rejection reason per row. It may not emit option prices, returns, IV outcomes, VRP, PnL, future realized variance, or any performance statistic.

## Fixed diagnostic rows

Use only the three original source-gate sample dates:
- 2023-05-18
- 2023-07-01
- 2023-10-23

At 08:00 UTC, count rows rejected because of:
1. symbol missing;
2. expiry parse failure;
3. unknown option type;
4. strike parse failure;
5. delta parse/missing;
6. incomplete BBO price/quantity fields;
7. structurally complete.

Also report distinct source `type` labels and counts, but no option prices.

## No scientific rule change

This diagnostic does not alter:
- decision hour;
- 24h geometry;
- DTE bins;
- 80-episode gate;
- 4-month gate;
- source envelope;
- economic hypothesis.

Any later correction requires a separate frozen technical amendment based solely on this structural receipt.
