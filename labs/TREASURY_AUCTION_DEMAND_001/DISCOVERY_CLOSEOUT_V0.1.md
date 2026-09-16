# TREASURY-AUCTION-DEMAND-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-16

## Canonical run

- MVE: `TAD-BTC-D1-001`
- GitHub Actions run: `35130514904`
- Job: `104910072414`
- Head SHA: `a885c8dac5a2e168ec228042ad3f281ada19c969`
- Evidence artifact ID: `10461500763`
- Artifact ZIP SHA-256: `14cc0c3cae7320361d24a9035da56b86f3102c24ccfd30d069551415c6c15601`
- Treasury canonical SHA-256: `ab2695123b04c6e320bda23e5496b1dcfadabec8c6784211a10407ac87499892`
- Resolved-trades SHA-256: `2f5240889f19a61c319b5fb674f1078234213b79d1182135952ab65b8d3ea2c1`
- Binance market-manifest SHA-256: `3bbcbc05701e17fe441c6d7ba5dce1712d403531d4dbbbe58a3dfb2e8198ef5d`
- Verified Binance monthly archives: 36

## Classification

`DISCOVERY_FAIL_NO_PROMOTION`

The exact MVE is closed. 2024 OOS remains locked and was not opened.

## Results

- resolved trades: **220**
- LONG: **114**
- SHORT: **106**
- same-date directional conflicts suppressed: **7**
- zero-only dates: **4**
- mean gross: **+4.1434 bps/trade**
- median gross: **-10.9510 bps/trade**
- mean NET10: **-5.8566 bps/trade**
- mean NET20: **-15.8566 bps/trade**
- NET10 profit factor: **0.952923**
- NET10 win rate: **47.73%**
- moving-block bootstrap 95% CI for mean NET10: **[-52.4372, +40.8050] bps/trade**

Calendar years, NET10 mean:
- 2021: n=70, **-54.7815 bps/trade**
- 2022: n=74, **+3.6404 bps/trade**
- 2023: n=76, **+29.9588 bps/trade**

## Frozen gates

PASS:
- N >= 180
- LONG >= 60
- SHORT >= 60
- at least 2/3 years non-negative NET10
- positive-year concentration <= 80%
- exact source binding
- protected-period firewalls

FAIL:
- mean NET10 > 0
- PF NET10 > 1.05
- bootstrap 95% lower bound > 0

## Interpretation

The frozen auction-demand direction produced a small positive gross mean, but the magnitude was below the frozen 10 bps round-trip cost and was not statistically robust. The negative 2021 regime was materially adverse, while 2022 and 2023 were non-negative after costs. Under the prospectively frozen all-gates-required protocol this is not promotable.

No inversion, tenor subset, threshold, timing, hold, cost reduction, bidder-share filter, regime filter or subperiod rescue is authorized for this exact MVE.

## Firewalls

- latest BTC market date opened: `2023-12-31`
- BTC 2024 opened: false
- BTC 2025 opened: false
- BTC 2026 opened: false
- live trading: false
- exchange mutation: false
- orders submitted: false
- OOS 2024 authorized: false
