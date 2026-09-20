# GEOMETRIC-TRENDLINE-001 — DISCOVERY 2021-2024 CLOSEOUT V0.1

Status: TERMINAL / DISCOVERY_FAIL_NO_PROMOTION
Date: 2026-09-20
Branch: geometric-trendline-v0.1
MVE: GTL-THIRDTOUCH-REJECTION-1H-001
Canonical Discovery run: 35500670280
Canonical job: 106051757539
Trigger commit: 47f34dd791e300fa0a97e8323daf23abeef2b2cd

## Frozen hypothesis
Causal two-anchor projected trendline geometry on BTCUSDT Spot 1H:
- pivot radius 3+3;
- consecutive pivot anchors;
- anchor separation 12h..168h;
- line life 336h;
- fixed interaction band 10 bps;
- first future interaction;
- support direction +1 / resistance direction -1;
- primary response +6h;
- UTC-week clustered bootstrap;
- no post-outcome tuning.

## Source
Official Binance Data Vision Spot BTCUSDT monthly 1m archives only.
Window: 2021-01 through 2024-12.
48/48 months checksum-verified.
2,102,767 minute rows.
35,043 valid 1H bars.
7 incomplete 1H hours preserved as continuity breaks.
8 contiguous segments.
2025 accessed: false.
2026 accessed: false.

## Sample
Accepted raw events: 818.
Primary +6h outcome-eligible events: 816.
Support: 416.
Resistance: 400.
Months represented: 48/48.
Sample viability: PASS.

## Primary result
Global mean directional response: -2.2722468272 bps.
UTC-week clustered bootstrap 95% CI: [-13.3402758284, +8.8974763530] bps.
Positive calendar years: 2/4.

By year:
- 2021: N=200, mean -15.5530423140 bps.
- 2022: N=204, mean +13.3106757175 bps.
- 2023: N=198, mean -9.5143090679 bps.
- 2024: N=214, mean +1.9855626209 bps.

By frozen side:
- Support: N=416, mean +5.9885392977 bps.
- Resistance: N=400, mean -10.8634643972 bps.

PASS gates:
- sample viability: PASS;
- global mean >0: FAIL;
- bootstrap lower95 >0: FAIL;
- support mean >0: PASS;
- resistance mean >0: FAIL;
- >=3/4 positive years: FAIL.

Terminal classification:
DISCOVERY_FAIL_NO_PROMOTION.

## Secondary diagnostics — NOT promotion gates
- +1h mean: -1.9917472001 bps.
- +3h mean: -5.2187209581 bps.
- +12h mean: +2.0393692921 bps.
- +24h mean: +5.5869845758 bps.

These secondary horizons were frozen as diagnostics only and cannot rescue the failed +6h primary MVE.

## Interpretation
The exact "third-touch rejection" geometric-trendline mechanism failed its prospectively frozen Discovery gate despite ample sample.

The positive support-side mean is post-outcome diagnostic evidence only. Selecting support-only now would be an unauthorized subgroup rescue of this MVE. It may not be promoted or relabelled as a survivor.

This result does not prove every conceivable geometric-trendline mechanism has no edge. It closes only GTL-THIRDTOUCH-REJECTION-1H-001. Any materially distinct future trendline hypothesis requires a new prospective ID, explicit anti-duplication record, fresh freeze, and evidence not presented as confirmatory on this same 2021-2024 outcome-opened corpus.

## Evidence
Pre-outcome lock run: 35500623887.
Pre-outcome artifact ID: 10602795483.
Pre-outcome artifact ZIP SHA256: 80cfab2f6c876e23368dc925eb73d8a1a602d46ba537a1d442e6b7b49bb067ad.

Discovery artifact ID: 10602101963.
Discovery artifact ZIP SHA256: 74eecbc99d22256117da59ed833d5771e89973ac380fe40140b687ba01239f20.
Receipt SHA256: 2d8b2b3a71bff966575d441d6cf43cd17fda554a7db0c1c0944a0d815970f386.
Events CSV SHA256: e98d53917ea280da4921e889d0055ac00cee6b1662be826e66409425e6badf6b.
Source manifest SHA256: a30c4133a78d769e53d2d32c7de4c3ffa0ee24e5655126b39765830d25190106.

## Firewalls
No PnL.
No fees/slippage model.
No leverage.
No live trading.
No exchange mutation.
No orders.
No wallets.
No main merge.
No 2025.
No 2026.
No rescue / no retuning.
