# EXTREME-STATE ECONOMIC CEILING MVE V0.1 RESULT

Date: 2026-09-25
Workflow run: 36194470291
Status: MEXC_MAKER_ECONOMIC_CEILING_FAIL_SAMPLE

## Scope
Discovery source only:
- Bybit BTCUSDT 2023-01-18
- first 250,000 L2 messages
- 24,419 labeled 1-second anchors
- generic magnitude percentiles 50/75/90/95/99
- horizons 5s / 15s / 30s
- OOS 2025 untouched
- 2026 holdout untouched

## Result
No feature × percentile × horizon combination with n>=100 achieved positive mean MEXC maker-maker net even under the deliberately unrealistic perfect-fill ceiling.

Best observed combination by MEXC maker-maker ceiling:
- feature: imbalance_l10
- magnitude bucket: top 1%
- horizon: 30s
- n: 246
- mean optimistic maker-maker gross: +2.6234 bps
- mean MEXC maker-maker net after fee only: -9.3766 bps
- mean Bybit maker-maker net after fee only: -1.3766 bps
- mean MEXC maker-entry/taker-exit net: -11.6178 bps

The next-best buckets were also materially negative.

## Interpretation
Static book imbalance / microprice displacement shows weak directional information, but not remotely enough magnitude to support current API fee economics in this sample.

Queue realism, failed fills, adverse selection, latency and slippage can only make these results worse.

## Decision
Do not spend further execution-model budget rescuing the static imbalance/microprice family.

This is a SAMPLE economic-ceiling failure, not a universal theorem about all microstructure signals.

Next scientific family must be economically distinct and seek sparse larger moves rather than continuous sub-bps prediction.
