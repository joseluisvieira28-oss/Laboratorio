# LOR-RLE-001 — ANTI-DUPLICATION & CAUSAL SOURCE AUDIT
Date 2026-10-09 — Research-only, no trading
Status: PARTIAL_OVERLAP / DISTINCT CONDITIONAL COMPRESSION HYPOTHESIS; NOT PROOF OF EDGE

## Source facts (not laboratory assumptions)
Official course syllabus https://lorenzfabricio.com.br/epa-tp-a/ has a dedicated 7-minute Rompimento de Lateralização Estreita lesson (premium content unavailable for full verification).
Public third-party transcription https://pt.scribd.com/document/874836582/Estrategias attributes to Fabrício Lorenz:
* 8+ small-amplitude consolidation candles;
* a **closed** candle of force / ignition as breakout;
* favorable EMA9/SMA21 and SMA200 not obstructing target;
* stop entry past signal bar extreme; protective stop at opposite extreme; target 2R.
The same transcription elsewhere describes ignition as a candle bigger than the preceding 20 candles and 80% body. The exact lecture's literal interpretation and precise width test are **not independently authenticated**. We must describe the experiment as a *Crypto Lab mechanical adaptation*, not exact author replication.

## Explicit laboratory definitions before outcome access
The hypothesis is **narrow 8-bar range, relative to 120 prior completed 8-bar envelopes (nearest-rank q25), THEN an 80%-body ignition candle with range > prior20 individual-bar ranges, close outside 8-bar envelope, EMA9/SMA21 favorable and SMA200 behind price**.
The 120-window narrow quantile, 1h BTCUSDT USD-M venue, 3-hour pending expiry and 24h stop/target hold are *lab choices*. They are not source facts.
Full freeze committed **before economic outcome access**:
`research/lorenz_rle_001/LOR_RLE_001_PREOUTCOME_FREEZE_V0_1.json` @ `4dcbbba0a81782a2ccdcabb60c7267852651a0a8`.

## Prior laboratory family distinctions
1. `TFG-DONCHIAN-1D-001`: prior 20 DAILY bars high-break close, next-day-open entry, ATR14-adjusted stop, 3R target and long only; different universe/time scale/signal, with no 8-bar compression plus ignition condition. Source branch `tf-gap-donchian-1d-v0.1`, runner `Dream-Account-OS-v2.3-PARTIAL/research/tfg_donchian_1d_discovery_runner_v01.py`.
2. `TFG-PBR01-4H-001`: 96 prior 4h-bar breakout, **2-bar defended retest**, 3R target, long-only. Different requirement (retest vs ignition entry) and fixed 4h. Freeze: https://github.com/joseluisvieira28-oss/Laboratorio/blob/tf-gap-pbr01-4h-v0.1/Dream-Account-OS-v2.3-PARTIAL/research/TFG_PBR01_4H_PROSPECTIVE_FREEZE_V0.1.json
3. `GEOMETRIC-TRENDLINE-001`: causal sloping pivot line third touch, Discovery 2021-24 failed. Not a horizontal 8-bar range/ignition.
4. `ABSORPTION-FAILED-AUCTION-001`: parent-tested sensor, extreme aggTrades, POC migration and path efficiency; RLE does not claim inferred order-flow absorption from OHLC.
5. `SWEEP-003`/`SWEEP-CONT-003`: sub-second L2 aggressive sweep, economically negative even under optimistic fills. RLE is hourly OHLC-based breakout, no L2 assumption.
6. `LOR-RF-001`: source-authored 3-bar correction continuation with 1R target, 2024 Discovery NO_EDGE. Separate price sequence and economic estimand; 2025/2026 remain sealed for RF.
7. `BPC-001`: *premium-index* dislocation compression, not price 8-bar narrow-range ignition.
8. Broader Donchian/HTF breakout literature exhibits substantive generic overlap; **do not call every RLE event a new market anomaly**.

## Unique information claim and positive control
The single conditional claim is **the narrowness of the immediately preceding 8 bars adds measurable, executable continuation beyond a comparably strong ordinary breakout**. The control has the SAME ignition strength (body >=80%, range > prior20), breakout high/low, same EMA/SMA and 2R mechanics; it differs ONLY in narrowness >q25 (non-narrow controls).
Trading/rolling lookbacks are causal and known at signal-bar close. Control and RLE events never overlap as classifications. Per-group executions serialize independently; this is not a single joint portfolio simulation, so it does not validate risk/capital netting.
Even if incremental uplift were statistically positive, differing volatility regimes may confound causal interpretation; actual volume, aggressor flow and contingent stops are unobserved by OHLC alone.

## Costs and no historical rescue
Primary fixed research hurdle 26bps, stress40bps, informational fee floor16bps (all round-trip). These are **not authenticated venue fees**. No claim of MEXC fill/latency/funding validation.
Discovery 2022-24 is exploratory in context of prior Crypto Lab historical reuse. Conditional survival would warrant NEW independent 2025 OOS authority (not automatic) and later forward evidence. 2026 and RF's 2025 remain sealed.
No parameter tuning from any RLE returns. If sample short, `SIGNAL_SAMPLE_INSUFFICIENT`; if net gates fail, `NO_EDGE_DISCOVERY`. Neither permits reading 2025 to rescue.

## Technical pre-outcome history
Source-only CI first synthetic tests flagged a fixture at boundary and a hard-coded minimum-length guard inconsistent with frozen SMA200. The fixture was changed away from float equality and the program guard was set to 201 points. These were repaired **before archive price outcomes** and do not modify any frozen signal/economic criterion. Separate commits record history.
