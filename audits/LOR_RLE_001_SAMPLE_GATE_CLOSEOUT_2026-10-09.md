# LOR-RLE-001 — DISCOVERY SAMPLE GATE CLOSEOUT (2026-10-09)

**FINAL SCIENTIFIC CLASSIFICATION: SIGNAL_SAMPLE_INSUFFICIENT / ECONOMIC EDGE NOT ADJUDICATED**
**Process disclosure: OUTCOME-METRICS-EXPOSED-BEFORE-SAMPLE-GATE — SCIENTIFIC FIREWALL INCIDENT**
Authority: research only, ZERO live trading, NO promotion, no retuning, no merge.

## Frozen prior to historical market outcome
- Economic/signal freeze: commit `4dcbbba0a81782a2ccdcabb60c7267852651a0a8`
- 2022–24 BTCUSDT Binance USD-M only; 2021-12 1h indicator warmup; 1h event detection; 1m execution replay.
- Official Binance Vision ZIP+CHECKSUM for each consulted month.
- Quantified RLE is a *lab adaptation* of attributed source (>=8 tight candles, ignition 80% body, range >20 bars, EMA9/SMA21 and SMA200, 2R), NOT a certified exact copy of premium videos.
- Comparator has the same trend, breakout strength, stops, targets and costs but **non-narrow** preceding eight-bar range; independent serialization.
- Absolute net26, net40, 1.15 PF, UTC-week bootstrap and incremental uplift all frozen, not inspected to select or tune anything after Discovery.
- 2025 OOS and 2026 holdout explicitly SEALED.

## Canonical evidence
- Preoutcome source gate: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37917283674
- 26/26 synthetic tests passed.
- 73/73 public ZIP HEAD/checksum metadata passed.
- SHA256 engine: `20396824b2495c3db3f71648328c478ad5cc050e2fa1258d0d4f8eff294d9c5c`
- SHA256 synthetic tests: `55d603458c243671cd82801c982fe7ae6cc0bd5e1b1b7f6c892351eed186ada5`
- SHA256 freeze: `f1418ecf270906563bed9274e1bc64008e83f2ff24ade34da766e17357059b42`
- One-time authorized discovery trigger: `54cb984eb86d81ad6d13368b5af87d312f3b259b`
- Canonical Discovery run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37917415252
- Discovery artifact 11610656384: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37917415252/artifacts/11610656384
- Published artifact ZIP SHA256 `55a733b8d513752dec085d25e8fc74dbeb3d655b9e0059b557c8d74397ffcf31`
- Canonical GitHub workflow: source-only + Discovery jobs COMPLETED SUCCESS (technical execution).

## Evidence and sample viability (only the count-safe portion)
- Official source ZIPs inspected and SHA256 verified: **73**.
- RLE_NARROW signal candidates (closed hourly bars): **41**.
- RLE_NARROW executed 1m-replayed trades: **37**.
- RLE_NARROW orders expired unfilled: **4**.
- NON_NARROW_CONTROL candidates: **131**.
- NON_NARROW_CONTROL executed 1m-replayed trades: **104**.
- NON_NARROW_CONTROL overlap suppressed: **18**; expired **8**; canceled **1**.
- Primary frozen minimum **100 trades in EACH** group, plus >=70 distinct trade dates and >=24 RLE weeks.
- Therefore the RLE sample **fails by construction** before inferential economic gates are eligible.

**DO NOT READ OR PROMOTE economic returns/PF/bootstraps from this underpowered exact MVE.**
The valid scientific outcome is `SIGNAL_SAMPLE_INSUFFICIENT`, not `NO_EDGE`, `EDGE` or `QUASE_DIAMANTE`.

## Transparent governance / implementation defect
The Discovery program `rle_engine_v01.py` calls `stats(rle)` and `stats(control)` **before** checking the frozen sample gate. Consequently it computed and emitted descriptive gross/net returns even though `economic_gate_unlocked=false` was attached afterward.
This is a **process fault**, not a market edge. The run was requested with outcomes authorized and therefore historical returns have been exposed at a stage when the sample threshold should have stopped their evaluation. We must not retroactively claim that economic outcomes remained entirely sealed.
Do NOT selectively reuse or cite the already-emitted sub-threshold economic metrics for promotion, cost tuning, threshold revision, or a new sibling tested on the same data. This closeout intentionally reports only count/coverage metrics.
Future new research must invert the source/outcome flow: event-only census -> sample viability gate -> immutable separate outcome permission -> load price outcomes. No after-the-fact transformation may cleanse this exposure.

## Anti-rescue / terminal governance
- EXACT `LOR-RLE-001` mechanical strategy is CLOSED AS UNDERPOWERED for the frozen 2022–2024 discovery.
- Do not lower the >=100 sample gate, q25 compression threshold, 80% ignition body, 20-bar force condition or 2R target to claim a rescue.
- Do not re-run on 2025/2026 or different assets/timeframes under the same identity.
- Distinct economic mechanisms need a fresh research ID, explicit prior exposure ledger and a genuinely unexposed prospective/out-of-sample validation universe. Old 2022–24 outcome receipts are non-confirmatory.
- This RLE outcome says nothing dispositive about Lorenz's broader methods.
- Costs 26/40 bps are frozen research haircuts, not observed authenticated execution; no executable edge was demonstrated.
- No orders, wallets, account reads, MEXC mutation, Render deployment, main merge, or live trading occurred.

## Next scientifically meaningful direction
Instead of a lower RLE threshold or a wider time/asset sweep, prioritize independent *mechanism* evidence (e.g., public stop-trigger proxies vs orderbook/aggTrades dynamics with historical point-in-time availability) and require pre-outcome sample census to prove enough episodes **before** any economic outcomes. Use existing `ABSORPTION-FAILED-AUCTION-001` prospective sensor and its sealed outcomes wherever it is the same mechanism; never duplicate/resurrect it as Lorenz RLE.
