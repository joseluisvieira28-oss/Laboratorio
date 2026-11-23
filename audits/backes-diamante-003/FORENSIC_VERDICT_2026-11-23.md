# BACKES-DIAMANTE-003 — Forensic economic closeout (2026-11-23)
**Decision: HISTORICAL ATTRIBUTION COMPLETE / ECONOMIC NO-GO / FORWARD OBSERVATION NOT YET ACTIVE**

## Identifiable primary evidence
- PR: https://github.com/joseluisvieira28-oss/Laboratorio/pull/388
- GitHub Actions run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45186921464
- ZIP artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45186921464/artifacts/14822189772
- ZIP artifact SHA256: babf60dd59e9abf4d34222ecd3651857980b19112a3443f45b5160a052484ede
- Predecessor #379 artifact SHA256: 735fff332994ce546f56258a01787d7f250203efa701586fa24eefd553f1ecaf
- Independently re-downloaded Binance Spot 1d archives, 384 / 384 per-source SHA256 exactly matching the predecessor manifest; 0 mismatches. 464 complete weekly bars.
- Identical frozen signal function (3-week confirmation each side for rising ETHBTC lows, plus positive 4-week ETHBTC momentum; decision on weekly close, modeled switch next Monday open).
- 10bps per trade; real fills zero. No parameters updated.

## Historical reconciliation (BTC benchmark, additive log relative return)
| Window | Weeks held ETH | In-window BTC/ETH switches | Rotation relative log return vs BTC |
|---|---:|---:|---:|
| 2018–2022 | 60 | 40 | +29.477 log-pp |
| 2023–2024 | 9 | 12 | **-35.012 log-pp** |
| 2025–2026 Nov22 | 10 | 2 | +43.343 log-pp |
| Full 2018–2026 | 79 | 54 | +37.808 log-pp |

These results REPRODUCE the earlier total returns and max drawdowns within rounding tolerance.

## The key concentration fact
The 2025–26 allocation held BTC for 27 weeks, ETH for only **10 consecutive weeks, 2025-07-14 to 2025-09-21**, then BTC for 61 weeks:
- BTC 2025-01-06..07-13: +0.000 log-pp vs BTC.
- ETH 2025-07-14..09-21: **+43.443** log-pp vs BTC (includes entry costs).
- BTC 2025-09-22..2026-11-22: -0.100 log-pp vs BTC (exit switching cost).
- Total +43.343 log-pp = ROT -4.0107% vs BTC -37.7719% for this window.

Best weeks: 2025-07-14 +24.871, 2025-08-04 +15.166, 2025-08-18 +10.044 log-pp. Total top-3 +50.081 log-pp, **greater than all 2025–2026 net relative gain**; the remainder offsets some of these gains.
Worst: 2025-07-28 -5.738, 2025-09-01 -4.605, 2025-08-25 -3.739, 2025-09-15 -3.494 log-pp.

**Adversarial counterfactual (post-hoc ONLY, not a tradable modification):** neutralize the 10-week 2025 ETH allocation *and* its subsequent switch-back fee, keeping every other modeled position and BTC returns unchanged. Full-period relative log excess would change from **+37.808 to -5.535 log-pp**, equal to **-5.385%** relative to BTC. Therefore, the apparent full-period lead against BTC **depends on one 10-week event**. This does not imply that BTC would otherwise have been known to be better at the time.

## Interpretation
- Descriptive BTC_UP/DOWN regimes and best/worst weeks use **realized future returns**. These labels cannot be used as input without lookahead.
- 2023–24 rotation underperformed BTC strongly; maximum historical strategy drawdown -82.50%; 2025–26 had only two switches.
- An attractive multi-year percentage return is **not enough** for an edge. This concentrated, high-drawdown sample is **ECONOMIC NO-GO** for real capital.
- This is a **Crypto Lab-designed hypothesis**, not proof regarding Augusto Backes' actual trades, courses or profitability.

## Prospective mode and current blocker
- New weekly_snapshot.py and workflow backes-diamante-003-forward.yml are committed on the isolated #388 research branch, with official Binance public-only endpoints, POST-signal quotes and UTC timestamp checks; earliest eligible capture 2026-11-30.
- The forward mode uses Binance 1w historical candles and *post-Monday-00:00* public bookTicker prices. This is a **delayed observational adaptation, not the same Monday-00:00 theoretical fill** as historical BACKES-002; no false execution equivalence.
- An automated ChatGPT schedule was attempted but rejected: **too_many_active_automations; 5 active / plan limit 5**. No existing automation was changed. **No automatic weekly run is currently enabled** and no prospective signal or future profit has yet been observed.
- Manual dated GitHub request files can trigger the read-only forward workflow if the operator chooses to initiate on eligible Mondays. A new automation slot or explicitly authorized replacement is required for unattended weekly triggering.
- Prospective decision remains INCONCLUSIVE. No funding, trade or subscription.
