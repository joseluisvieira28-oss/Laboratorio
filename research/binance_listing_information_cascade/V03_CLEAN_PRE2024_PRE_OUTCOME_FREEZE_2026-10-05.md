# BINANCE-LISTING-INFORMATION-CASCADE-001 — CLEAN PRE-2024 DISCOVERY FREEZE V0.3
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2022-2023 OUTCOME INSPECTION
Branch: binance-listing-cascade-v0.3-clean-pre2024-source-2026-10-05

## Why this clean line exists
The 2024 V0.2 line is not admissible as confirmatory evidence because its source-only union admitted BOME even though the observed Bitget history began less than 24h before T0, violating the original >=24h pre-T0 requirement. That V0.2 line subsequently produced outcomes elsewhere in repository history. This V0.3 branch was forked from source-only commit 5d4dde6b0742c5c030f17e097f049063ac81621b, before V0.2 outcome execution. No V0.2 outcome values are inputs to this protocol.

## Research question
When Binance publicly announces a new spot listing for a token already continuously traded for >=24h on another liquid centralized venue, does the announcement create a reproducible positive information shock on that pre-existing venue?

## Clean discovery period
2022-01-01 through 2023-12-31.
Official announcement authority: Binance public CMS catalog + matching official announcement code.
2024 is quarantined from confirmatory use in this line.
2025-2026 remain unopened by this line.

## Full-census/source-gate procedure
The outcome-blind Binance CMS census found 48 listing/open-trading announcements in 2022-2023. Stablecoins FDUSD and AEUR are mechanically excluded. Launchpad/TGE events without >=24h external trading fail source coverage mechanically.

A strict public 1m source probe required ALL:
1. at least one bar timestamp <= T0-24h;
2. at least one bar in [T0-10m,T0);
3. at least one bar in [T0,T0+5m];
4. exact asset identity; ticker collisions are excluded unless underlying identity is proven independently.

LUNA/Terra 2.0 is excluded because the official announcement explicitly distinguishes new LUNA from old LUNA/LUNC, so pre-T0 ticker history cannot be assumed to represent the announced asset.

## Frozen eligible universe (12)
IMX, API3, WOO, ASTR, LDO, STG, FLOKI, PEPE, PENDLE, ORDI, BLUR, BONK.

Official CMS T0 milliseconds:
- IMX 1641794176091 — article 7a1f332b6a204dfda65840ae33047a0f
- API3 1642746484252 — article 43b644d339394646bf65bf5c1e70d031
- WOO 1644286833903 — article 8bd474c77c55450fbe828ec536963162
- ASTR 1646033043037 — article e9542fb981594bb2831eedbd18056f6
- LDO 1652079437647 — article b76eb4e952a94959afb5964c32ddbb7a
- STG 1660889501192 — article 04619e62e3784dc09b17fea81ad4d0fd
- FLOKI 1683285604106 — article f68a3bc6eb014ed9bacf1d6c71dc1134
- PEPE 1683285604106 — article f68a3bc6eb014ed9bacf1d6c71dc1134
- PENDLE 1688365335567 — article 56c9c5899f3747b2b9a0452450f5eb24
- ORDI 1699339453500 — article 4bd64404aa384fe5a00e0f9b131035db
- BLUR 1700806187186 — article 85306854c60347a6a4131493ec8d26a6
- BONK 1702612713180 — article 1592b7a6ec9a408daf4b778f50ab1ca6

## Frozen venue hierarchy
KuCoin spot first, Bitget spot second. This hierarchy was selected from source availability before outcomes.
Expected binding from source-only probe:
KuCoin: IMX, API3, WOO, ASTR, STG, FLOKI, ORDI, BLUR, BONK.
Bitget fallback: LDO, PEPE, PENDLE.
No venue shopping after outcomes.

## Layer A — information-shock endpoint (primary scientific gate)
P0 = close of the final complete 1m bar whose open time is strictly before floor(T0 to minute).
Event returns R1/R5/R15/R60 use the close of the latest available event bar with open time <= floor(T0)+N minutes, divided by P0 minus 1.
MFE/MAE are measured over those event windows.

5m volume shock = sum volume of the first five full 1m bars with open_time >= ceil(T0 to minute), divided by median non-overlapping 5m volume over T0-24h through T0-1h.

Primary frozen survival gate — ALL required:
- n >= 12;
- median R15 > +0.75%;
- R15 positive hit-rate >= 65%;
- median R5 > +0.50%;
- median 5m volume shock >= 2.0x;
- leave-one-out median R15 remains > 0 after dropping any one observation;
- no single observation contributes >35% of summed positive R15.

If n<12 due source/runtime coverage: SOURCE_BLOCKED.
If n>=12 and any gate fails: NO_EDGE_DISCOVERY.
If all pass: SURVIVES_INFORMATION_DISCOVERY.

## Layer B — delayed executable drift (secondary, non-gating in V0.3)
To prevent confusing instantaneous repricing with executable edge:
entry_time = first full minute boundary at least 60 seconds after T0.
entry_price = open of the 1m bar at entry_time.
Report gross returns after 5m, 15m and 60m from that entry, hit-rates, median MFE/MAE, and venue-matched BTC-relative returns.
These metrics do NOT change the Layer A verdict. No fee/slippage claim is allowed in V0.3.

If Layer A survives, a new pre-outcome execution/cost freeze is mandatory before any further holdout or tradability claim.

## Anti-hindsight
No eligible asset, T0, source hierarchy, metric, threshold, direction, or gate may change after V0.3 outcomes are opened.
Technical fixes may preserve this freeze but may not alter scientific meaning.

## Governance
Research-only. No main merge. No live trading. No orders. No private endpoints. No wallets. No account reads. No post-outcome tuning.
