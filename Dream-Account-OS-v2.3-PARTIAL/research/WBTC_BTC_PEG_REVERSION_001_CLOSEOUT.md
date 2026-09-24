# WBTC-BTC-PEG-REVERSION-001 — DISCOVERY CLOSEOUT

Date: 2026-09-24
Branch: `wbtc-btc-peg-reversion-v0.1`
Source gate run: `35987768556` — PASS
Discovery run: `35987933949` — SUCCESS
Scientific classification: **DISCOVERY_INSUFFICIENT_SAMPLE**
Maturity: **M3 DISCOVERY — CLOSED EXACT V0.1**

## Frozen mechanism

Discount-only WBTC/BTC peg reversion:
- signal on completed 1h WBTCBTC close <=0.995 after prior bar >0.995;
- liquidity filter fixed pre-outcome;
- enter next-hour open;
- hold 24 completed hours;
- base hurdle 20 bps;
- stress hurdle 30 bps;
- no overlapping positions.

Discovery: 2022-2023.
2024: protected OOS.

## Source

Binance Data Vision WBTCBTC 1h monthly archive source gate passed across 2022, 2023 and 2024 control months before prices were opened.

## Discovery result

Frozen sample gate required:
- >=30 completed non-overlap episodes;
- >=8 in 2022;
- >=8 in 2023.

Observed:
- total completed episodes: **6**
- 2022: **6**
- 2023: **0**
- exclusions: 0

Therefore the exact Discovery is mechanically underpowered and classified:
**DISCOVERY_INSUFFICIENT_SAMPLE**.

Diagnostics only:
- mean entry discount: 52.17 bps
- mean gross 24h return: +13.74 bps
- mean base-net: **-6.26 bps**
- median base-net: -4.42 bps
- base PF: **0.2318**
- bootstrap95 mean base-net: [-14.64 bps, +2.44 bps]
- positive / negative: 3 / 3
- sign p = 0.65625
- mean stress-net: **-16.26 bps**
- stress PF: 0
- largest positive episode share: 80.60%
- fraction touching 0.999 within 24h: 0%

These diagnostics do not establish NO_EDGE because the frozen sample gate failed, but they provide no scientific basis to consume the protected 2024 OOS.

## Decision

- close exact V0.1 as DISCOVERY_INSUFFICIENT_SAMPLE;
- do not open 2024;
- do not lower 50-bps threshold;
- do not change to cross-rate WBTCUSDT/BTCUSDT;
- do not loosen volume/trade filters;
- do not use premium-side inversion;
- do not change horizon/costs;
- do not open 2025/2026;
- no promotion.

Source bundle SHA256:
`3863cf3ebe4f3286f1bc2ce95b685f98a5045f39441e7c50517e3369aeb05694`
