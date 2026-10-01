# TV-FOOTPRINT-CALIBRATION-001 — TERMINAL CALIBRATION CLOSEOUT

Date: 2026-10-01
Classification: **PASS_STRONG**
Status: TERMINAL
Authority: MEASUREMENT FEATURE ONLY
Edge authority: NONE
Trading authority: NONE

## Frozen terminal interval

- First bar open: 2026-09-24 12:35:00 UTC
- First bar close: 2026-09-24 12:40:00 UTC
- Final bar close: 2026-10-01 12:35:00 UTC
- TradingView terminal bars: 2,016
- Binance bars in interval: 2,016
- Matched bars: 2,016
- Matched coverage: 100%
- Binance source completeness: 100%

No post-terminal TradingView receipt entered this verdict.

## Frozen primary metrics

- Median absolute relative total-volume error: 3.025204563714369e-14
- Delta sign agreement: 0.8526785714285714 (85.267857%)
- Comparable delta-sign bars: 2,016
- Spearman(TV delta, Binance aggressor delta): 0.8403088547066349
- Pearson(TV delta, Binance aggressor delta): 0.9279539402657925

## Frozen gate comparison

PASS_STRONG required all:
- matched coverage >=99% -> PASS (100%)
- median volume error <=1% -> PASS (~0%)
- sign agreement >=70% -> PASS (85.27%)
- Spearman >=0.65 -> PASS (0.8403)
- Pearson >=0.60 -> PASS (0.9280)

Therefore the only legitimate classification is:

**PASS_STRONG**

## Source provenance

Historical 2026-09-24 through 2026-09-30:
official Binance Vision BTCUSDT spot daily aggTrades archives, each verified against its official .CHECKSUM.

2026-10-01 terminal-day segment:
official unauthenticated Binance public market-data endpoint:
https://data-api.binance.vision/api/v3/aggTrades

- aggregate-trade rows: 339,014
- first aggregate trade ID: 4078050863
- last aggregate trade ID: 4078389876
- first timestamp ms: 1790812800072
- last timestamp ms: 1790858099380
- raw JSONL SHA256: a18853e9e3570923b7530a0b18fe1b14d49b764b82f6c315b896d01c6e77dfbc

GitHub Actions:
- workflow run: 36865095179
- workflow conclusion: SUCCESS
- artifact ID: 11163421403
- artifact SHA256: f0e5a731188d4ed4bac650b80b333b0f2a2a3d4c8e0765ba752b4aa556d3aef8
- terminal TV sample SHA256: 83ee7153c8e285caf9bba27d92da1aaf84304fde494c90f0735129b8ab8b687e

## Interpretation

MM-V1 may now be used as a calibrated measurement feature in separately preregistered research under the frozen identity.

PASS_STRONG is **not** evidence of profitability, an edge, a trading strategy, candidate promotion, or live-execution authority.

No parameter was changed after Binance comparison outcomes were opened.
No lag shift, session filter, row-size change, venue swap, timeframe swap, or subgroup rescue was used.

This terminal verdict must not be re-adjudicated by extending the sample.
