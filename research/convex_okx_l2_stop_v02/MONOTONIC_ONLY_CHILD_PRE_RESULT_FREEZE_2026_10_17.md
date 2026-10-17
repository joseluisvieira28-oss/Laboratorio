# PRE-REPLAY FREEZE: ORIGINAL V5 versus MONOTONIC-ONLY STOP CHILD (DESCRIPTIVE)

Date 17 October 2026. The original 2023–2025 model returns for SOL 1H and BNB 4H are already publicly known; this cannot earn independent OOS credit. Research-only, no 2026, no orders, no exchange credentials.

## Exact new model definition

**All original V5 parameters and chronological source mechanics unchanged** except on a completed timeframe bar where the original V5 would assign the conditional stop:

`old = max(initial, peak_high * 0.88) if close_profit >= 0.05 else initial`

new distinct child:
`stop_t = max(stop_{t-1}, old)` for LONG.
This is the **ONLY** replacement of one code location in the pinned original V5 2023–2025 simulator. It is not the operator stop on MEXC; it is a historical simulated monotonic stop rule. It can end positions early and produce new signals/reentry sequences, so a **full replay** is necessary. No added take-profit, time exit, half reduction, leverage, exchange stop acknowledgement or tightened initial stop.

## Source & original equivalence

- Parent 2023–25 frozen source `research.convex_8alt_common_2023_25.common_3yr` (official Binance USD-M market 5m + funding + 1h independent parity).
- Two and ONLY two assets: `SOLUSDT` 1h and `BNBUSDT` 4h, with frozen BASE 8 bps taker each side +2 bps adverse slippage each side, STRESS +5 bps adverse slippage each side, funding MARKET OPEN proxy, 10k paper independent accounts and 20% current paper equity notional.
- BEFORE running any child simulation, run exact original `base.simulate` and assert original BASE/STRESS closed trade counts and marked returns within 1e-5 percentage points of original locked documented results: SOL 1H BASE 84 and +59.3882875829%, STRESS 84 and +58.2954740759%; BNB 4H BASE 28 and +27.3779278226%, STRESS 28 and +27.0553067071%. Source counts must equal 333216 5m, 27768 1h, 3288 funding per asset; source-manifest 112 and official publisher file checks unchanged. Otherwise **BASELINE_PARITY_BLOCKED** and zero child outcomes.
- Four matched full historical child reports; no arm exclusion. Record original vs child marked return, net closed PnL, max 5m low modeled DD, fees, funding, trades, negative years, top3 concentration, all changed exit/reentry IDs, no live authority.
- No new parameters after outcomes. Child cannot inherit parent's alpha certification. If child positive it remains DESCRIPTIVE-IN-SAMPLE; if child negative, kill child retrospectively but not rewrite original parent.
- Do not merge to main; do not deploy or trade or open protected holdout.

Prior separate early-half/monotonic child results in PR #224 were different exit rules and must not be conflated with this monotonic-only experiment. V5 and child remain unqualified for 10x live regardless of result.

Freeze before child results: **CHILD_OUTCOME_UNSEEN / DESCRIPTIVE_NOT_OOS / NO LIVE GO**.
