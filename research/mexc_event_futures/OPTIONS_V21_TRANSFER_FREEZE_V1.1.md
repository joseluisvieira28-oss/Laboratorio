# MEXC EVENT FUTURES LAB — OPTIONS V2.1 EXTERNAL-SIGNAL TRANSFER FREEZE V1.1

Date: 2026-10-02
Status: PRE-NEW-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## Independent signal authority

Transfer source:
`OPTIONS-SPOTPERP-001-V2.1`

The daily signal was frozen independently before this Event Futures investigation.

Signal identity:
- CALL IV minus PUT IV;
- positive skew => UP / LONG BTC;
- negative skew => DOWN / SHORT BTC;
- zero/invalid => FLAT.

Frozen eligible options universe from the source strategy:
- BTC options;
- DTE 30–120;
- call moneyness 1.05–1.20;
- put moneyness 0.80–0.95;
- minimum 5 distinct eligible instruments per side.

V1.1 uses only the already-produced `signal_date` and `position`.
It does NOT use skew magnitude, RV weight, prior PnL, prior forward return, or any outcome field to select Event Futures observations.

## Immutable prior-artifact provenance

Discovery signal ledger source:
- workflow run: `34858777691`
- artifact id: `10354131731`
- artifact digest: `sha256:a810a6eaa7a1f476ab265a9f2bb614eb9f4bf251c58d43037bb2ca414ce6e5cd`
- file: `OPTIONS_SPOTPERP_001_DISCOVERY_LEDGER_V01.csv`

Only signal dates from 2022-01-01 through 2024-12-31 are eligible.

OOS signal ledger source:
- workflow run: `35231711508`
- artifact id: `10504812106`
- artifact digest: `sha256:dbbcb7ca0bd1a4fdc759b5ec0211743cfb9b441b304d23692094b148bdcfbf82`
- file: `OPTIONS_SPOTPERP_001_V21_2025_OOS_LEDGER_V01.csv`

Only signal dates from 2025-01-01 through 2025-12-29 are eligible.

## Contamination disclosure

The original source ledgers contain a previously evaluated **daily t+1 to t+2 BTC outcome** for the source strategy.

Therefore the 1-day Event Futures horizon is NOT treated as a new independent V1.1 discovery endpoint and is excluded from V1.1 promotion logic.

The 30-minute and 60-minute post-entry outcomes were not part of the original source-strategy evaluation and are the only primary endpoints in V1.1.

Historical 10-minute MEXC index-price data is not available on the frozen historical source route and must not be approximated.

Thus:

- 10m = `SOURCE_UNOBSERVABLE`
- 30m = PRIMARY
- 60m = PRIMARY
- 1d = `NONINDEPENDENT_REFERENCE_NOT_TESTED`

## Frozen transfer timing

For source signal date `D`:

Event transfer entry:
`D + 1 day at 00:00:00 UTC`

This preserves the independently frozen source-strategy execution timing.

Price proxy:
MEXC public standard-futures BTC_USDT index-price K-lines.

Raw interval:
`Min30`

Clock rule:
a Min30 close stamped `s` is observable at `s + 1800 seconds`.

Required entry and expiry prices must exist exactly.
No interpolation.

Outcome:
- source position +1 wins when proxy expiry > proxy entry;
- source position -1 wins when proxy expiry < proxy entry;
- equality = tie.

No direction inversion is permitted.

## Historical partitions

Discovery signal dates:
2022-01-01 through 2024-12-31.

Retrospective OOS signal dates:
2025-01-01 through 2025-12-29.

2026:
LOCKED / NOT FETCHED / NOT SCORED.

## Source integrity gates

Before outcomes:
- downloaded artifact IDs must match the frozen IDs;
- SHA256 digest of downloaded ZIP is validated by GitHub artifact identity;
- required CSV columns: signal_date, position;
- signal dates unique;
- position must be only -1, 0, +1;
- discovery and OOS periods may not overlap;
- no 2026 signal date accepted;
- no prior forward-return/PnL column may be used in scoring.

## Statistical gate

Primary family size:
2 horizons.

Reference payout:
80%.

Break-even accuracy:
55.5555556%.

Discovery basic gate:
- non-tie N >= 800;
- accuracy >55.5555556%;
- Wilson 95% lower bound >50%;
- one-sided exact binomial p-value vs p0=55.5555556%;
- each calendar year 2022, 2023, 2024 accuracy >50%.

Apply Benjamini-Hochberg FDR q=0.05 across the primary discovery horizons that satisfy the basic gate.

Only BH-selected horizons may open the 2025 Event-transfer OOS outcomes.

## OOS gate

No parameter change.

Pass requires:
- non-tie N >=250;
- accuracy >55.5555556%;
- Wilson 95% lower bound >50%;
- one-sided exact binomial p-value vs p0=55.5555556% <0.05;
- EV at illustrative 80% payout >0.

Also report EV at 70/75/80/85/90% payout and the payout required for EV=0.

## Interpretation

An OOS survivor is:
`OPTIONS_V21_TO_EVENT_FUTURES_SHORT_HORIZON_PROXY_CANDIDATE`

It is NOT proof of exact MEXC Event Futures profitability because:
- historical Event Futures payout-at-entry is unavailable;
- standard-futures index-price equivalence to Event Futures settlement is not proven;
- the current product has no official Event Futures trading API.

## Hard boundaries

- No 10m approximation.
- No 1d promotion claim.
- No skew-magnitude filter.
- No RV/weight filter.
- No direction inversion.
- No post-outcome tuning.
- No 2026 data.
- No authenticated exchange API.
- No orders.
- No account mutation.
- No merge to main.
