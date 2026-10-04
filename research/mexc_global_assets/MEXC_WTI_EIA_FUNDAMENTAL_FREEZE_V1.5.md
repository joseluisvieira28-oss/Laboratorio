# MEXC-WTI-EIA-FUNDAMENTAL-001 — PRE-DATA FREEZE V1.5

Date: 2026-10-04
Status: FROZEN BEFORE EIA INVENTORY VALUES ARE OPENED

## Why this family exists

V1.4 found no robust edge in using the first five minutes of WTI price action to predict later WTI returns.

V1.5 is economically distinct:
it uses the official petroleum inventory information released by the EIA, not a technical transformation of WTI price.

## Scientific status of historical periods

February-August 2026:
DISCOVERY ONLY.

September 2026:
NOT a pristine holdout. V1.4 already retrieved raw September WTI event windows for source coverage, even though no OOS scoring occurred.

Therefore V1.5 has NO retrospective OOS.

Any candidate that survives Discovery must be confirmed only in a newly frozen future-forward period.

## EIA data source

Official public EIA series:
`WCESTUS1`

Name:
`Weekly U.S. Ending Stocks excluding SPR of Crude Oil`

Unit:
Thousand Barrels.

Public XLS:
`https://www.eia.gov/dnav/pet/hist_xls/WCESTUS1w.xls`

No EIA API key is required for this public file.

## Frozen stock mapping

For each official WPSR release timestamp T0:

1. current stock = the series observation whose week-ending date is the latest Friday strictly before the release date;
2. prior stock = the immediately preceding weekly series observation;
3. `inventory_delta_kb = current_stock_kb - prior_stock_kb`.

This mapping is frozen before the XLS values are opened.

## Frozen economic direction

ONLY the intuitive fundamental mode is authorized:

- inventory DRAW: delta < 0 => LONG WTI;
- inventory BUILD: delta > 0 => SHORT WTI;
- delta = 0 => no signal.

The inverse mode is explicitly NOT authorized as a rescue if this fails.

## Frozen inventory magnitude thresholds

Before reading the EIA values:

- 0 thousand barrels: all non-zero changes;
- 2,000 thousand barrels = 2 million barrels;
- 5,000 thousand barrels = 5 million barrels.

No percentile, quantile, z-score, or data-derived threshold may be added after the XLS is opened.

## Entry and outcomes

MEXC source:
`USOIL_USDT` public Min5 K-lines.

Entry:
open of the Min5 bucket beginning at T0 + 5 minutes.

This gives the public release five full minutes to become known and avoids pretending to fill at the release instant.

Holding horizons:
- 5m
- 15m
- 30m
- 60m.

12 cells total.

## Discovery events

Exactly the 30 frozen WPSR releases from:
2026-02-04 through 2026-08-26.

## Discovery gate

Cell eligibility:
- N >= 12;
- mean gross signed return > 0;
- win rate > 50%;
- every chronological third mean > 0;
- exact one-sided binomial p-value vs 50% defined.

Holm-Bonferroni FWER 0.05 across eligible cells.

Only a Holm-selected cell can be promoted to:
`WTI_EIA_FUNDAMENTAL_DISCOVERY_CANDIDATE__FORWARD_ONLY`

No historical OOS is authorized.

## Economics

Current MEXC metadata snapshot:
- maker=0;
- taker=0.0001 per side.

Report 0 / 1 / 2 / 3 / 5 / 10 bps round-trip cost scenarios.
This current fee snapshot is not historical fee authority.

## No rescue

After EIA XLS values or WTI outcomes are opened, do not:
- invert BUILD/DRAW direction;
- change inventory thresholds;
- change entry delay;
- change horizons;
- weaken N;
- weaken Holm;
- create retrospective OOS from September.

If Discovery survives, confirmation MUST be future-forward under a separate pre-event freeze.

No live trading, accounts, credentials, wallets, private endpoints, orders, mutation, or main merge.
