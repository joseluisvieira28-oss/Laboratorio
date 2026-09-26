# IPG-001 BINANCE HISTORICAL ARCHIVE FIXTURE FREEZE V0.1

Frozen: 2026-09-24
Stage: HISTORICAL SOURCE INTEGRITY ONLY

Authority:
Binance official binance-public-data / data.binance.vision archive.

Deterministic fixture date:
2024-01-01 UTC

Datasets:
- Spot BTCUSDT daily aggTrades
- USD-M Futures BTCUSDT daily aggTrades

For each:
1. download the official ZIP;
2. download the sibling .CHECKSUM;
3. require SHA-256 equality;
4. inspect CSV structure without retaining price/quantity values in the receipt;
5. require aggregate-trade IDs nondecreasing;
6. require timestamps nondecreasing;
7. require first/last timestamps inside 2024-01-01 UTC.

No return, spread, direction, price-response, correlation or predictive
calculation is allowed.

PASS only proves official historical Spot and USD-M event archives are
obtainable and internally timestamp/order coherent for the fixed fixture day.
