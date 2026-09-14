# BTC-FEE-PRESSURE-001 — DISCOVERY V0.5 CLOSEOUT

Status: TERMINAL — DISCOVERY_FAIL_NO_PROMOTION  
Date: 2026-09-14 UTC  
MVE: BFP-TOTALFEES-7D-001  
Run: 34887365707  
Selection job: 104121209969  
Discovery job: 104121271313  
Branch: btc-fee-pressure-v0.5-discovery  
Trigger HEAD: 1db0fb09c11e324731b091c5c6d18282bb5fce07

## Verdict

**DISCOVERY_FAIL_NO_PROMOTION.**

This is a scientific/economic Discovery failure under the frozen MVE, not a technical failure, not a source failure and not a protected-period failure. The exact MVE `BFP-TOTALFEES-7D-001` is closed. No rescue, inversion, threshold change, lookback change, timing change, hold change, source switch or subperiod selection is authorized under this MVE ID.

## Frozen source and selection integrity

- V0.4 source gate: SOURCE_DATA_PASS.
- V0.4 source run: 34886378068.
- V0.4 source manifest SHA256: `4af2e98ac18aaf28686f7f80580ece5a7a34461f20e1955ad562e0a7328c9093`.
- Source coverage: 1461/1461 UTC days, 2021-01-01 through 2024-12-31, zero missing days/heights and zero malformed rows.
- Outcome-blind candidate signals: 299.
- Accepted non-overlapping trades: 73.
- Suppressed overlaps: 226.
- Selected-trades SHA256: `f4082155d3c5976e142bfced79881ef1ed7a8893875370fcdc31780648cfd2f7`.
- Selection manifest SHA256: `2b88b455c40c58bc2f745f16c8a2cc8714971269dc80cfabb44f19d425e64939`.
- Pre-outcome selection artifact: 10365520917.
- Pre-outcome selection artifact ZIP SHA256: `7e095182ee771fd6c1ab309955da9d6866c6ee29512c0ff406165f91449648a0`.
- Drive pre-outcome selection archive: `13ALxDLpWLsEjz_yar2LuwQ9QXicpsBaf`.

## Discovery economics

- N: 73 trades.
- Mean gross: **-56.80234076551992 bps/trade**.
- Median gross: **-18.202975447232372 bps/trade**.
- Mean NET10: **-66.80234076551992 bps/trade**.
- Mean NET20: **-76.80234076551992 bps/trade**.
- NET10 profit factor: **0.7736454086934457**.
- NET10 win rate: **0.4794520547945205**.
- Non-negative calendar years: **1 / 4**.
- Bootstrap p(mean NET10 <= 0): **0.7928**.
- Bootstrap 95% CI NET10: **[-230.45938830552777, 90.33894284808053] bps**.
- Maximum positive-year gross contribution share: **1.0**.
- Cumulative NET10 diagnostic: **-4876.570875882956 bps**.
- Max drawdown NET10 diagnostic: **-9085.252838482233 bps**.

## Calendar-year results

| Entry year | N | Mean NET10 (bps/trade) | Gross sum (bps) |
|---|---:|---:|---:|
| 2021 | 8 | -412.0504026571152 | -3216.403221256922 |
| 2022 | 23 | -217.7305415227545 | -4777.802455023353 |
| 2023 | 30 | +137.93063729506537 | +4437.919118851961 |
| 2024 | 12 | -59.19035987122003 | -590.2843184546404 |

Only 2023 was non-negative under NET10.

## Frozen promotion gates

PASS:
- N >= 50.
- source binding.
- outcome-blind selection hash.
- official Binance Data Vision checksum validation.
- frozen timing/non-overlap rule.
- protected-period firewall.

FAIL:
- mean NET10 > 0.
- NET10 profit factor > 1.00.
- at least 3 / 4 non-negative years.
- bootstrap p(mean NET10 <= 0) <= 0.20.
- maximum positive-year gross contribution share <= 70%.

Because multiple frozen economic/statistical gates fail, promotion is prohibited.

## Market evidence and hashes

- Market source: official Binance Public Data Vision SPOT daily BTCUSDT 1d archives.
- Required market days: 108; receipts: 108.
- All required market checksum validations passed.
- Market receipts JSON SHA256: `1a4801405757ccdd05e39f7d586a65bc8ad3def747757f50cdea897e5d7dc7ed`.
- Trades JSON SHA256: `56af9fded27aef8f4ce541135f9ce9c9cd6324ed8fd16470a2e9288438744e1c`.
- Discovery summary JSON SHA256: `51d1236602820460d0d64ac1268cda81bee271f1b90d5206a64276c5755fb4e4`.
- Final Discovery artifact: 10365237174.
- Final Discovery artifact ZIP SHA256: `409443ea1fcc90eb2510069da225e7b9c9727c96d6876e6a0414ab0ad8db0369`.
- Final Discovery TAR SHA256: `8ff7e8ed057d560e2eb0f287761e4e497da63e2974351c96713dbbed430dda1a`.
- Drive final Discovery archive: `1KFXs05WyWgoMKfX1YI9IaMVWdu7NN1BT`.

## Firewalls

- 2025 accessed: false.
- 2026 accessed: false.
- live trading: false.
- exchange mutation: false.
- merge to main: not performed.
- deployment: not performed.

## Governance consequence

The exact MVE `BFP-TOTALFEES-7D-001` is **CLOSED — DISCOVERY_FAIL_NO_PROMOTION**. V0.4 source success remains historically valid, but it does not rescue the failed economic hypothesis. No post-outcome modification is permitted. Any future blockspace/fee-pressure experiment must be materially different, receive a new MVE ID and be frozen prospectively before outcome inspection.
