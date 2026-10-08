# GLOBAL-ASSET-SP500-BASIS-001 — CURRENT MEXC API EXECUTION FEASIBILITY CLOSEOUT V0.3

Date: 2026-10-08
Status: EXECUTION_FEASIBILITY_FAIL_CURRENT_MEXC_API_FEES
Scope: execution-cost adjudication only; frozen signal unchanged

## Upstream frozen scientific result

The untouched September holdout remains:
`HOLDOUT_PASS_FORWARD_SHADOW_ELIGIBLE`

Frozen SPX500_USDT FADE_BASIS_ONLY holdout:
- N = 654
- mean gross signed return = +0.5177567737 bps
- median gross = +0.2603421158 bps
- exact one-sided binomial p = 0.0128735220
- both chronological halves positive
- scientific classification = REPLICATED_SIGNAL_SURVIVOR__EXECUTION_FEASIBILITY_UNPROVEN

This closeout does not rewrite that signal result.

## Current intended automated execution route

Official MEXC announcement, effective 2026-06-01 08:00 UTC:
https://www.mexc.com/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742

API Futures fees:
- maker = 0.06% per side = 6 bps
- taker = 0.08% per side = 8 bps
- API fee schedule takes precedence over website/app promotions
- applies to Futures trading pairs except Innovation Zone pairs

Official MEXC product page identifies SPX500_USDT as a USDT-margined perpetual Futures contract:
https://www.mexc.com/futures/SPX500_USDT

## Deterministic fee-only feasibility

Frozen holdout gross mean:
`+0.5177567737 bps`

Fee-only round trips, before spread/slippage:

- maker + maker = 12 bps
- maker + taker = 14 bps
- taker + taker = 16 bps

Therefore:

- best fee-only mean under maker+maker = `0.5177567737 - 12 = -11.4822432263 bps`
- maker+taker mean = `-13.4822432263 bps`
- taker+taker mean = `-15.4822432263 bps`

Break-even all-in round-trip cost from the frozen holdout is only ~0.5178 bps.

The current API fee floor alone exceeds that by more than 23x even under maker+maker.
Spread, slippage, queue non-fill risk and latency can only worsen executable economics.

## Verdict

`EXECUTION_FEASIBILITY_FAIL_CURRENT_MEXC_API_FEES`

Interpretation:
- the statistical SPX500 basis signal remains a replicated gross-market phenomenon;
- the intended automated MEXC API execution route is not economically viable under the current fee schedule;
- no live BBO/spread study is required to establish this fee-floor failure;
- this is NOT a claim that the gross signal is false;
- this is NOT authority to retune threshold, horizon, direction, venue or cost assumptions to rescue it.

## Governance

No order.
No account/private endpoint.
No wallet/capital.
No exchange mutation.
No live trading.
No main merge.
