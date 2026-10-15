# CROSS-ASSET-VOL-STRESS-001 — SOURCE GATE V0.1

Research-only / outcome-blind.

Lab: `CROSS-ASSET-VOL-STRESS-001`
MVE: `CAVS-VXSETTLE-W1-001`

Official source only: Cboe annual Futures Final Settlement Prices pages for 2018, 2019, 2020, 2021, 2022, 2023, 2024.

Allowed product: `VX - Cboe Volatility Index (VX) Futures`, monthly and weekly final settlement records only.
Excluded: VXM, variance, options on futures, VIX spot, all other products.

PASS requires:
- every source date inside its requested year;
- finite positive final settlement values;
- no conflicting same-date values;
- >=45 unique canonical VX settlement dates in each year;
- >=320 unique canonical VX settlement dates total;
- no URL/request for 2025 or 2026;
- no BTC market data, returns, PnL or outcome calculation.

Raw annual HTML must be preserved byte-for-byte with SHA-256 receipts. Parsed canonical observations and a manifest SHA-256 must be emitted before any Discovery market access.