# MEXC-NAS100-MULTIRAIL — FINAL 1m CLOSEOUT

Date: 2026-10-05
Branch: nas100-multirail-001-chat-attack-2026-10-05
Scope: research-only. No trading, no private endpoints, no account reads, no main merge.

## Architecture confirmed

Current MEXC contract/detail:
- NAS100_USDT: contractSize 0.00001, maxLeverage 200x, settle/quote USDT
- NAS100_USD1: contractSize 0.00001, maxLeverage 50x, settle/quote USD1
- Both report indexOrigin = HYPERLIQUID
- Both are active (state 0)

This means the rails are not independent price-discovery sources at the index layer; they share the same external index origin and differ primarily in settlement rail, leverage/margin parameters and market microstructure.

## Official API cost authority used

MEXC API Futures fee announcement effective 2026-06-01:
- maker 0.06% = 6 bps per execution
- taker 0.08% = 8 bps per execution
- API fee schedule takes precedence over Web/App promotions.

Frozen hurdles:
- one-leg taker round trip: 16 bps
- two-leg taker pair round trip: 32 bps
- maker theoretical floors: 12 bps one-leg, 24 bps pair
No spread/slippage/funding was added to these floors, so the screen is optimistic.

## 001 — raw cross-rail basis

Common futures coverage: 44,326 matched one-minute bars in the corrected run.
Raw NAS100_USDT vs NAS100_USD1 absolute basis:
- median: 0.6792 bps
- p95: 14.2980 bps
- p99: 19.4746 bps
- max: 29.1111 bps
- count >=20 bps: 355
- count >=40 bps: 0

Frozen H1 entry threshold was 40 bps.
Result: zero triggers across Discovery, OOS1 and OOS2.

More importantly, the maximum observed raw basis (29.1111 bps) is already below the 32 bps two-leg taker fee floor, before spread/slippage.

H1 verdict: NO_EDGE.

FX-normalized hypotheses in 001 were not opened because USD1USDT spot prints, even with a strict 5-minute known-at-T as-of rule, covered only ~48.99% of common futures minutes. They remain BLOCKED_FX_COVERAGE and were not used to rescue H1.

## 002 — index-normalized residuals

Coverage:
- NAS100_USDT: 44,332 minutes
- NAS100_USD1: 44,332 minutes
- common: 44,332
- common ratio: 100%

### H5 — cross-rail premium-spread convergence

Premium spread = (Last_USDT/Index_USDT - 1) - (Last_USD1/Index_USD1 - 1).

Absolute premium-spread:
- median: 3.5648 bps
- p95: 15.9909 bps
- p99: 21.7065 bps
- max: 32.8940 bps
- >=20 bps: 805 minutes
- >=40 bps: 0

Frozen pair threshold: 40 bps.
Pair taker fee floor: 32 bps.

No H5 trigger in Discovery, OOS1 or OOS2.
The absolute maximum spread was only 0.894 bps above the fee floor before spread/slippage and never reached the pre-registered 40 bps safety threshold.

H5 verdict: NO_EDGE.

### H6 — USDT rail Last-to-Index one-leg residual

Frozen trigger: |USDT premium| >=20 bps while |USD1 premium| <=5 bps.
Primary horizon: 1 minute, next-minute open entry.
Fee hurdle: 16 bps.

OOS1:
- n=120
- gross mean +1.3363 bps
- gross median +0.6781 bps
- net mean -14.6637 bps
- net median -15.3219 bps
- net win rate 0%

OOS2:
- n=32
- gross mean +2.9370 bps
- gross median +2.7691 bps
- net mean -13.0630 bps
- net median -13.2309 bps
- net win rate 0%

5m diagnostic remained deeply negative after fees.

H6 verdict: NO_EDGE.

### H7 — USD1 rail Last-to-Index one-leg residual

OOS1 primary 1m:
- n=6
- gross mean +5.4030 bps
- net mean -10.5970 bps
- net win rate 0%

OOS2 primary 1m:
- n=221
- gross mean +3.0096 bps
- gross median +2.6171 bps
- net mean -12.9904 bps
- net median -13.3829 bps
- net win rate 0.45%

5m diagnostic:
- OOS1 gross mean +8.8720 bps, net -7.1280 bps
- OOS2 gross mean +3.9763 bps, net -12.0237 bps

Even the better OOS1 5m gross result is below the 12 bps maker-only theoretical round-trip fee floor, before fill probability/adverse selection.

H7 verdict: NO_EDGE.

### H8 — Last-to-Fair residual

USDT rail 1m:
- OOS1 n=1, net mean -16.3369 bps
- OOS2 n=7, net mean -14.8864 bps

USD1 rail 1m:
- OOS1 n=7, gross mean +1.3045 bps, net -14.6955 bps
- OOS2 n=5, gross mean +1.6199 bps, net -14.3801 bps

5m diagnostics also remained negative after fees.

H8 USDT verdict: NO_EDGE.
H8 USD1 verdict: NO_EDGE.

## Descriptive reality

Large absolute Last-to-Index deviations did occur:
- USDT max |Last-Index|: 106.9191 bps
- USD1 max |Last-Index|: 121.5609 bps

But these large deviations did not translate into a next-minute executable candle edge under the frozen rules. The observed mean reversion after a next-minute entry was only a few bps, far below API fees.

This is the key scientific distinction: a large contemporaneous dislocation is not the same thing as a tradable edge after the signal is known.

## Final verdict

MEXC-NAS100-MULTIRAIL 1m FAMILY = **NO_EDGE**

Killed:
- raw USDT/USD1 basis convergence at 1m
- index-normalized pair convergence at 1m
- USDT-to-Index one-leg mean reversion at 1m/5m
- USD1-to-Index one-leg mean reversion at 1m/5m
- Last-to-Fair one-leg mean reversion at 1m/5m

Do not retune thresholds or horizons to rescue this family.

## What is not claimed

This closeout does not prove that no sub-minute microstructure edge exists at 100ms/500ms/1s/5s. Historical L1/L2 data were not available in this study.

Any sub-minute test must be opened as a new, prospective experiment with immutable pre-registration and live public WebSocket collection. It must not reuse 001/002 outcomes to tune entry thresholds.

Given that next-minute gross capture was typically only ~1–5 bps versus a 16 bps one-leg taker hurdle, sub-minute work should be lower priority than structurally new families unless a fee/fill regime materially changes.

## Decision

Close NAS100 multi-rail historical 1m as NO_EDGE.
Do not spend more historical 1m research budget on this exact family.
