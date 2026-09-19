# PERP-CROWDING-UNWIND-001 — SOURCE TRANSPORT AMENDMENT V0.1A

Date: 2026-09-19
Parent run: `35471166220`

The first source gate established that Binance daily metrics and futures 1h klines were available on all five frozen representative dates, with aggregate open-interest fields and parseable timestamps.

The funding path in V0.1 used a daily archive location that returned no files. This amendment changes only the packaging route for the same Binance funding-rate source from daily ZIPs to the monthly funding-rate ZIP archive. The probe must additionally verify that each frozen representative date exists inside its corresponding monthly archive.

No venue, asset, period, signal, threshold, direction, cost, outcome, or economic rule changes. No returns or PnL are opened.
