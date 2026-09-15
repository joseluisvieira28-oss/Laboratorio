# ETF-CME-INSTFLOW-001 — FORWARD SHADOW Q4 2026 — FINAL EVALUATION CONTRACT V0.1A

Status: **FROZEN_PRE_OUTCOME / EXECUTION-FIREWALL ONLY**
Date frozen: 2026-09-15
Parent study: `ETF-CME-INSTFLOW-001-FORWARD-SHADOW-Q4-2026-V0.1A`

## Purpose

Freeze the final-evaluation timing and mechanics before any prospective CFTC observation or BTC forward outcome from the Q4-2026 shadow window is opened. This contract does not change the signal, costs, success criteria, expected sign, sample gate, or candidate tier. It exists only to prevent optional stopping, interim peeking, and implementation drift.

## No-early-outcome firewall

1. Source-only checkpoints may collect or record CFTC state/signal information allowed by V0.1A, but must not fetch BTC forward-outcome prices.
2. No BTC outcome for any forward-shadow observation may be fetched, inspected, logged, summarized, or used before the entire prospectively allowed study has matured.
3. The final economic evaluation may execute only after `2027-01-01T00:00:00Z`, after every included frozen exit through `2026-12-31` has elapsed.
4. There is exactly one final economic evaluation. No sequential testing, early stop, interim promotion/demotion, rolling PnL inspection, or partial-sample verdict is allowed.
5. All eligible prospective observations available under the frozen V0.1A source window are included. No event may be dropped because of signal sign, magnitude, BTC outcome, market regime, volatility, calendar placement, or apparent quality.
6. If fewer than 12 evaluable observations remain because of a genuine pre-defined source/calendar/data-integrity failure, classification is `FORWARD_SHADOW_INSUFFICIENT_SAMPLE`; do not shrink the window, add dates, backfill an alternate category, or lower the sample gate.

## Frozen signal and execution

- CFTC dataset: `6dca-aqww`
- CME BTC CFTC contract code: `133741`
- signal: `delta(non-commercial long - non-commercial short) / open_interest_t`
- first prospective delta predecessor: exact `2026-09-08` CFTC state, signal-construction only
- expected sign: positive
- thresholds: none
- z-score: false
- winsorization: false
- regime filter: false
- alternate COT category: false
- first allowed prospective as-of: `2026-09-15`
- last allowed prospective as-of: `2026-12-15`
- position: long BTC if signal > 0; short BTC if signal < 0; zero signal = no position/no cost
- entry: first BTCUSDT spot 00:00 UTC daily open at or after `as_of + 8 calendar days`
- exit: entry + 7 calendar days
- latest allowed exit: `2026-12-31`
- base round-trip cost: 10 bps
- stress round-trip cost: 20 bps

## Frozen outcome source

BTC outcome prices must come only from official Binance Vision BTCUSDT spot 1d archive bytes. Every archive used in final evaluation must be preserved with SHA256 provenance. No TradingView, REST ticker, exchange UI, alternate venue, mark/index price, interpolation, nearest-neighbor substitution, or reconstructed candle is allowed.

## Frozen metrics

For every non-zero signal:

- `forward_return = exit_open / entry_open - 1`
- `position = +1` for positive signal, `-1` for negative signal
- `gross = position * forward_return`
- `base_net = gross - 0.001`
- `stress20_net = gross - 0.002`

Report at minimum:

- evaluable observation count
- OLS beta of forward return on raw signal and expected beta sign
- mean gross, mean base net, mean stress20 net
- base and stress20 profit factor
- additive cumulative base net
- additive max drawdown on chronological base-net observations
- leave-one-trade-out minimum base-net mean
- maximum single-trade share of positive gross PnL
- complete observation table with as-of, predecessor, signal, entry, exit, prices, returns and costs
- immutable source/result hashes

## Frozen success criteria

`FORWARD_SHADOW_PASS` requires all of the following simultaneously:

- evaluable observations >= 12
- base NET10 mean > 0
- base PF >= 1.0
- stress20 NET mean >= 0
- stress20 PF >= 1.0
- beta sign positive
- leave-one-trade-out minimum base NET mean > 0
- max single-trade share of positive gross PnL <= 0.40
- absolute additive max drawdown < 0.50
- clean provenance, no leakage, and no technical/source-path failure

If sample >=12 and any scientific/economic success criterion fails, classification is `FORWARD_SHADOW_FAIL`. If sample <12 for a legitimate source/calendar reason, classification is `FORWARD_SHADOW_INSUFFICIENT_SAMPLE`. Technical/provenance failures remain technical/provenance failures and are not scientific negatives.

## Tier effect

None automatic. A forward-shadow pass is new independent evidence for the already-existing Tier 2 fragile candidate, but this contract does not itself grant Tier 1, live trading, leverage, capital allocation, exchange mutation, orders, or deployment. Any later tier change must be applied under the frozen Near-Diamonds policy without changing this signal after outcomes.

## Forbidden rescue

After any forward outcome is accessed: no thresholding, sign inversion, long-only/short-only selection, alternative COT category, subperiod selection, alternate entry/exit, alternate hold, cost reduction, outlier deletion, volatility filter, regime filter, asset/venue switch, nonlinear transform, parameter optimization, or event deletion.

Research-only. No live trading. No orders. No exchange mutation. No main merge. No deployment.
