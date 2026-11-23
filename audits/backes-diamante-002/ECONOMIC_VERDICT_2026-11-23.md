# BACKES-DIAMANTE-002 — Economic evidence audit (2026-11-23)
**Decision: NO-GO LIVE / NO PROVEN EDGE. GO to independent prospective verification only.**

This is an independent BTC/ETH allocation hypothesis inspired by public discussion of ETHBTC higher lows; it is **not Augusto Backes' private or verified trading strategy**. The code and its parameters were created in November 2026, hence all historical periods are **retrospective**. No real trades, deposits or fees were incurred.

## Primary verifiable execution
- Repository: joseluisvieira28-oss/Laboratorio, PR #379, research/backes-diamante-002.
- GitHub Actions job (successful): https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45172325899
- Source artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45172325899/artifacts/14816888088
- Artifact SHA256 (verified against downloaded ZIP): 735fff332994ce546f56258a01787d7f250203efa701586fa24eefd553f1ecaf
- Cutoff: 2018-01-01 to 2026-11-22 UTC, 464 Monday–Sunday weeks, Binance Spot BTCUSDT + ETHUSDT + ETHBTC.
- 384 files (128 per pair), 384 unique filenames, 384 hexadecimal SHA-256 entries, 0 download errors, 654415 compressed source bytes in origin ZIPs. Per-file bytes are not included in the artifact, but downloadable from their original URLs in source_manifest.json.
- 4/4 deterministic unit tests PASS, then source acquisition and portfolio calculation PASS. These PASS checks are not economic proof.
- Report: artifact contains RESULT.md, results.json (28 parameter/period/scenario records), source_manifest.json.
- Source data: Binance Public Data at https://github.com/binance/binance-public-data.
- Execution: 100% spot BTC vs ETH rotation; ETHBTC low swing with 3-week confirmation each side, higher consecutive confirmed lows AND 4-week relative ETHBTC upward trend. Decision on closed weekly candle, hypothetical execution next Monday open. Direct ETHBTC 1-leg cost 10bps each trade in primary display; no borrowing/short/derivatives.
- Comparison: BTC hold; ETH hold; BTC/ETH 50:50 rebalanced weekly. Starting NAV=1 independently per window and initial entry friction. Terminal marked-to-market without final liquidation fee. No account-specific fees were verified.

## 10 bps per trading leg: historical net returns (USDT), NOT realized
| Window | BTC hold | ETH hold | 50/50 | Rotation | ROT max drawdown | ROT switches |
|---|---:|---:|---:|---:|---:|---:|
| 2018–2022 | +21.03% | +63.59% | +73.41% | +62.52% | -82.50% | 40 |
| 2023–2024 | +491.35% | +202.61% | +336.50% | +316.66% | -28.84% | 12 |
| 2025–2026-11-22 | -37.77% | -52.62% | -43.73% | -4.01% | -51.97% | 2 |
| 2018–2026-11-22 | +346.28% | +135.00% | +326.33% | +551.33% | -82.50% | 54 |

**Important:** The full-period return looks large but is retrospective, regime-dependent, and exposed to -82.50% historical maximum drawdown. It does not demonstrate an economic edge.

## Strong 2025–2026 relative result is NOT statistical validation
At 10bps/leg, rotation **lost 4.0107%** vs BTC's -37.7719%. However only **two** BTC/ETH switches occurred in 98 weeks, and ROT max drawdown (-51.97%) was not materially lower than BTC's (-51.75%).

Block bootstrap of **weekly active arithmetic excess** (8-week blocks, 2,000 samples, predetermined seed), 2025–2026:
| Benchmark | Mean excess ROT / week | 95% bootstrap interval |
|---|---:|---:|
| BTC | +0.504% | **-0.086% to +1.560%** |
| ETH | +0.520% | **-0.601% to +1.403%** |
| 50/50 | +0.512% | **-0.159% to +1.033%** |

All three intervals include **zero**. The bootstrap does NOT account for ex post hypothesis selection; it is descriptive, not a prospective significance claim.

## Stress
- 2025–2026 rotation at 35bps per direct ETHBTC exchange: **-4.7295%**.
- 2025–2026 rotation at 35bps per **two-leg switch** (BTC-USDT then USDT-ETH): **-5.3975%**.
- 2018–2022 rotation at 35bps direct: +46.66% vs 50/50 +71.56%; 2023–2024 rotation +303.31% vs BTC +489.87% and MIX +334.94%; the rotation **fails comparative robustness** in two earlier regimes.
- These scenarios are hypothetical; no exchange-level actual fills, dated spreads or liquidity slippage were reconstructed.

## Red-team limitations
1. The 2018–2026 dataset is real, but the strategy was **constructed after viewing public content from 2026**; backtesting cannot establish unexploited edge or validate the influencer's predictions.
2. A 7-week swing pivot known only after 3 following weeks avoids lookahead within the strategy implementation. Economic outcomes remain retrospective and sensitive to definition and market regimes.
3. Binance price series only: no independent exchange replication, stablecoin conversion risk, account custody, exchange outage/slippage tails, or actual tax consequences.
4. ETHBTC direct switching is optimistic for any broker requiring 2 USDT legs; both scenarios model costs but assume Monday-open fills and continuous market liquidity.
5. When the author says "possible rising low" in a video, this has not been validated as an actual timestamped trade recommendation. We cannot attribute model PnL to Augusto Backes.
6. Some year windows are grouped by **week start** (Monday UTC), meaning final evaluation week of 2024 can end in January 2025; report periods should not be misrepresented as strict calendar-year closing marks.
7. Per-archive SHA256 is recorded, but the artifact does not ship raw source ZIPs; reconstruct independently via original Binance URLs and compare hashes.
8. A favorable full-period result cannot override failure against benchmarks in earlier market regimes or the large drawdown.

## Verdict and next gate
**NO-GO for allocating capital or claiming validated advantage.** The rule is reproducibly testable with real market data, and its recent loss-avoidance is worth an **independent prospective shadow observation**, but that is only hypothesis triage. Any follow-up must freeze protocol in advance, use actual fee/spread measurements, independently validate daily source snapshots and keep it fully read-only. Do not modify the hypothesis to fit these observed results and then call the same test out-of-sample.
