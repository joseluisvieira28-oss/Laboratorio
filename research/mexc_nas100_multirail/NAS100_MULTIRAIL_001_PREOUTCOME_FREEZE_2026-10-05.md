# MEXC-NAS100-MULTIRAIL-001 — PRE-OUTCOME FREEZE

Date: 2026-10-05
Scope: research-only, public market data only. No trading, no private endpoints, no account reads, no main merge.

## Instruments
- NAS100_USDT
- NAS100_USD1
- USD1USDT spot only as a quote-currency normalization control.

## Overlap sample
USD1 rail launch: 2026-06-25 14:00 UTC.
End: freeze/run time on 2026-10-05.

Chronological partitions fixed before outcomes:
- Discovery: 2026-06-25 14:00 UTC through 2026-08-15 23:59 UTC
- OOS-1: 2026-08-16 00:00 UTC through 2026-09-15 23:59 UTC
- OOS-2: 2026-09-16 00:00 UTC through 2026-10-05 run cutoff

OOS-2 is historical untouched holdout, not a true prospective forward sample.

## Costs frozen before outcomes
Official MEXC API fee schedule effective 2026-06-01:
- maker 6 bps per execution
- taker 8 bps per execution
Promotional 0-fee rates on USD1 Web/App are explicitly not assumed for API.

Therefore:
- one-leg taker round trip: 16 bps before spread/slippage/funding
- two-leg pair taker round trip: 32 bps before spread/slippage/funding
- one-leg maker round trip theoretical fee floor: 12 bps
- two-leg pair maker round trip theoretical fee floor: 24 bps

Primary verdict uses taker fees. Maker is diagnostic only and cannot SURVIVE without fill/adverse-selection data.

## Data
For both futures, 1-minute:
- Last OHLCV
- Index OHLC
- Fair OHLC
- funding history
- current contract/detail architecture

For USD1USDT spot:
- 1-minute OHLC from public spot API where available.

No L1/L2 historical fill simulation will be invented.

## Primary hypotheses — frozen

### H1 — Raw cross-rail basis convergence
Raw basis:
`B_raw = 10,000 * (NAS100_USDT / NAS100_USD1 - 1)`

Entry event only when `|B_raw| >= 40 bps` at minute close.
Hypothetical equal-notional two-leg convergence trade begins at next-minute OPEN and exits after 15 minutes.
Primary economic hurdle: 32 bps taker fees before spread/slippage.
Secondary diagnostic exit: 60 minutes, reported separately and not used to rescue failure at 15m.

### H2 — USD1/USDT-normalized basis convergence
Normalize:
`NAS100_USD1_in_USDT = NAS100_USD1 * USD1USDT`
`B_fx = 10,000 * (NAS100_USDT / NAS100_USD1_in_USDT - 1)`

Same 40 bps trigger, next-minute OPEN entry, 15-minute primary exit, 60-minute diagnostic.
Primary hurdle: 32 bps taker fees before spread/slippage.

H2 is the cleaner economic test because it removes quote-stablecoin FX.

### H3 — USDT rail leads USD1 rail
At minute t:
- absolute USDT one-minute return >= 20 bps;
- USD1 normalized one-minute return has the same sign or is near zero;
- absolute USD1 normalized return <= 50% of absolute USDT return.

Signal direction = sign of USDT return.
Trade only NAS100_USD1 at t+1 OPEN, exit at t+1 CLOSE (primary).
5-minute exit is diagnostic only.
Primary hurdle: 16 bps taker fees before spread/slippage.

### H4 — USD1 rail leads USDT rail
Mirror of H3:
- absolute normalized USD1 one-minute return >= 20 bps;
- USDT return same sign or near zero;
- absolute USDT return <= 50% of absolute USD1 normalized return.

Trade only NAS100_USDT at t+1 OPEN, exit t+1 CLOSE.
5-minute exit diagnostic.
Primary hurdle: 16 bps taker fees.

## Anti-overlap rule
After a trigger, suppress new triggers for the duration of the primary holding period for that hypothesis:
- H1/H2: 15 minutes
- H3/H4: 1 minute

## Verdicts

### SURVIVES
Only if:
- OOS-1 and OOS-2 both show positive fee-adjusted mean return for the primary horizon;
- median is non-negative in both OOS partitions;
- no single day contributes >35% of total gross PnL;
- at least 20 independent OOS triggers combined;
- gross edge clears fee floor by >=5 bps average buffer;
- candidate remains only **execution-pending** until L1/L2 forward validation; no live authority.

### NO_EDGE
If:
- no triggers above frozen thresholds, or
- optimistic candle-based gross capture fails even the fee floor, or
- Discovery positive but either OOS partition is non-positive after fees, or
- signal direction reverses/vanishes OOS.

### BLOCKED
If:
- one rail lacks adequate historical 1m data;
- USD1USDT control is unavailable and raw-vs-normalized interpretation cannot be separated;
- timestamp/contract-spec changes make the overlap non-comparable.

## Scientific guardrails
No threshold tuning after outcomes.
No changing primary horizons after outcomes.
No mid-price or close-as-fill fiction: entries use next-minute open.
If candle test survives, a new forward microstructure experiment must be preregistered before L1/L2 collection.
