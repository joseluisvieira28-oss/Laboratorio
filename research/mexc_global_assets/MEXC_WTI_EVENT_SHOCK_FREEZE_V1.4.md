# MEXC-WTI-EVENT-SHOCK-001 — MIN5 PRE-OUTCOME FREEZE V1.4

Date: 2026-10-04
Status: FROZEN BEFORE ANY WTI PERFORMANCE SCORING

## Why V1.4 exists

V1.3 failed closed on Min1 historical retention:
- Discovery usable: 0/30;
- OOS usable: 4/5;
- no performance statistic was calculated;
- no Holm selection occurred;
- no OOS result was opened.

V1.4 is therefore a pre-outcome transport-resolution successor.

## Scientific invariants preserved

UNCHANGED from V1.3:
- exact 35 EIA release timestamps;
- Discovery = first 30 releases through 2026-08-26;
- OOS = five September releases;
- EIA official schedule authority;
- 5-minute initial event shock;
- thresholds 0 / 10 / 20 / 40 bps;
- modes CONTINUATION and REVERSAL;
- horizons 5 / 15 / 30 / 60 minutes;
- Discovery minimum N=12;
- positive mean / win rate >50% / all thirds positive;
- Holm-Bonferroni FWER 0.05;
- OOS minimum N=5;
- OOS exact one-sided binomial p<0.05;
- both OOS halves non-negative;
- October protected;
- no consensus or inventory-surprise input;
- no parameter rescue.

## Resolution correction

Source:
MEXC public contract K-lines, interval `Min5`.

A raw Min5 candle timestamp `s` is its bucket start.
Its close becomes observable only at `s + 300 seconds`.

Because every frozen EIA release timestamp is aligned to a 5-minute boundary, the event shock is exactly the first Min5 candle beginning at T0.

`shock_bps = 10000 * (close[T0 bucket] / open[T0 bucket] - 1)`

Shock is observable at T0+5m.

## Entry proxy

Entry is the OPEN of the immediately following Min5 bucket:
`T0 + 5 minutes`.

This is a next-bar-open proxy, not a same-bar fill.

It remains a price-only research proxy. Forward BBO/depth evidence is required before any execution claim.

## Holding horizons

Measured from the next-bar open:
5 / 15 / 30 / 60 minutes.

## Fee reporting

Current source-gate metadata snapshot:
- maker = 0
- taker = 0.0001 per side

Report 0 / 1 / 2 / 3 / 5 / 10 bps round-trip scenarios.
The snapshot is not historical fee authority and does not control the scientific gate.

## Hard boundary

No raw or observable price at/after:
`2026-10-01T00:00:00Z`

## No rescue

After V1.4 opens outcomes, do not alter:
- event list;
- Min5 resolution;
- next-bar-open entry;
- thresholds;
- modes;
- horizons;
- N gates;
- Holm;
- OOS rules.

Promotion ceiling:
`WTI_EIA_EVENT_SHOCK_OOS_SIGNAL_CANDIDATE`

No live trading, account reads, credentials, wallets, private endpoints, orders, mutation, or main merge.
