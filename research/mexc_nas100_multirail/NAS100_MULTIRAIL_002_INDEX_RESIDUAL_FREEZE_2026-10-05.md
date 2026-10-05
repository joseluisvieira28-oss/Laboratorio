# MEXC-NAS100-MULTIRAIL-002 — INDEX-NORMALIZED RESIDUAL FREEZE

Date: 2026-10-05
Relationship to 001: new experiment opened only after H1 raw pair was closed NO_EDGE. No 001 threshold is changed or rescued.

## Structural basis
Current MEXC contract/detail reports both NAS100_USDT and NAS100_USD1 with the same indexOrigin: HYPERLIQUID. Therefore compare each rail's executable Last price to its own Index price to remove underlying level and quote-currency scale.

## Dataset
Common 1-minute timestamps of:
- NAS100_USDT Last / Index / Fair
- NAS100_USD1 Last / Index / Fair

Same chronological partitions as 001:
- Discovery through 2026-08-15 23:59 UTC
- OOS-1 2026-08-16 through 2026-09-15
- OOS-2 2026-09-16 through run cutoff

No USD1USDT spot normalization is required.

## Frozen costs
- one-leg taker round trip: 16 bps
- two-leg taker round trip: 32 bps
- maker floors diagnostic only: 12 bps one-leg / 24 bps pair

## Frozen definitions
USDT premium = 10,000 * (Last_USDT / Index_USDT - 1)
USD1 premium = 10,000 * (Last_USD1 / Index_USD1 - 1)
Premium spread = USDT premium - USD1 premium.

## H5 — Cross-rail premium-spread convergence
Trigger at minute close when |premium spread| >= 40 bps.
Enter next-minute open:
- if spread > 0: short USDT rail, long USD1 rail
- if spread < 0: long USDT rail, short USD1 rail
Primary exit: 15 minutes.
Diagnostic exit: 60 minutes.
Pair taker cost hurdle: 32 bps.
Anti-overlap: 15 minutes.

## H6 — USDT rail one-leg residual reversion
Trigger when:
- |USDT premium| >= 20 bps
- |USD1 premium| <= 5 bps
Trade only NAS100_USDT toward its Index direction at next-minute open.
Primary exit: 1 minute.
Diagnostic exit: 5 minutes.
One-leg taker hurdle: 16 bps.
Anti-overlap: 1 minute.

## H7 — USD1 rail one-leg residual reversion
Mirror H6:
- |USD1 premium| >= 20 bps
- |USDT premium| <= 5 bps
Trade only NAS100_USD1 toward its Index direction at next-minute open.
Primary exit 1 minute; diagnostic 5 minutes.
One-leg taker hurdle 16 bps.

## H8 — Fair-normalized one-leg residual
For each rail separately:
Fair premium = 10,000 * (Last / Fair - 1).
Trigger when |Fair premium| >= 20 bps while the other rail's |Fair premium| <= 5 bps.
Trade the deviating rail toward Fair at next-minute open.
Primary exit 1 minute; diagnostic 5 minutes.
This is reported separately for USDT and USD1 and cannot rescue H6/H7.

## Verdict
SURVIVES_CANDLE_EXECUTION_PENDING only if a primary hypothesis has:
- OOS-1 and OOS-2 net mean >= +5 bps after taker fees
- OOS medians >= 0
- >=20 combined OOS triggers
- no positive-PnL day >35% of positive gross PnL
Then L1/L2 forward validation is mandatory before any execution authority.

NO_EDGE if no triggers, optimistic candle gross fails fee floor, or OOS fails.
BLOCKED only for genuine data/timestamp insufficiency.

No threshold/horizon changes after outcomes.
