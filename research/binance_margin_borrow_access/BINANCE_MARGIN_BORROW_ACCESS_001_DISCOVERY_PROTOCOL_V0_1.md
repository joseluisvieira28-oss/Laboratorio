# BINANCE-MARGIN-BORROW-ACCESS-001 — DISCOVERY PROTOCOL V0.1

Date: 2026-09-17  
Status: **FROZEN BEFORE OUTCOMES / NON-EXECUTABLE RESEARCH**  
Branch: `binance-margin-borrow-access-v0.1`

## Preconditions

- `SOURCE_CENSUS_PASS`
- `EVENT_SOURCE_ADJUDICATION_PASS`
- `PRIOR_SPOT_PRIMARY_PASS`
- execution-cost provenance = `CREDENTIAL_BOUND`

This Discovery is explicitly **pre-cost and non-executable**. It cannot establish after-cost profitability or authorize live trading.

## Economic hypothesis

When an asset already trading on Binance Spot becomes newly borrowable on Binance Cross Margin, the relaxation of short-sale / hedge-access constraints may create incremental adverse price pressure.

Directional alternative fixed before outcomes:

**post-event market-adjusted Spot return < 0**.

No reverse-direction rescue is allowed.

## Frozen candidate universe

Canonical upstream source: prior-Spot run `35269000941`, artifact id `10517374109`.

- upstream asset-event rows: 100
- prospectively excluded `ACCESS_CONFOUND`: 4
- clean upstream asset-events: **96**

The research unit is an **asset-event**. Repeated assets at different events remain separate. Multiple assets in the same Binance announcement are not treated as independent for primary inference; they are aggregated at article level.

No candidate may be added or removed because of market outcomes.

## Protected-period firewall

Scientific market data may cover only:

`2023-01-01T00:00:00Z` through `2024-12-31T23:59:59Z`.

An event is boundary-ineligible if the required primary window `[t0 - 24h, t0 + 24h]` crosses outside that interval. Boundary exclusion occurs in the outcome-source manifest before any market-data value is opened.

2025 and 2026 remain forbidden.

## Frozen event time

Primary event-information time:

`t0_raw = event_information_ms`

from the already frozen official Binance article parser. `event_information_ms` is the official publish timestamp.

The market-data anchor is:

`t0 = first Binance 1-minute bar open timestamp >= t0_raw`

This prevents using any bar that began before the public information time.

Explicit later effective times are retained as metadata only and may not replace `t0_raw` in the primary test.

## Outcome-pair source gate — before values

Primary outcome pair is fixed to:

`<ASSET>USDT`

No BTC/BNB/FDUSD/BUSD/USDC or other pair fallback is permitted for the primary Discovery after outcomes are opened.

Before downloading or parsing any market-data ZIP, an outcome-source manifest must use Binance Vision `.CHECKSUM` metadata only to prove that `<ASSET>USDT` 1-minute archives exist for every UTC calendar day required to cover `[t0 - 24h, t0 + 24h]`.

The same checksum-only requirement applies to `BTCUSDT`.

If the required `ASSETUSDT` archive is unavailable, classify the row `NO_USDT_OUTCOME_SOURCE` before outcomes and exclude it from the primary analyzable universe. No pair substitution is allowed.

The source manifest must be immutable and hashed before outcome ZIP download begins.

## Market-data source

Official Binance Vision Spot 1-minute klines only.

Permitted after the outcome-source manifest is frozen:
- download the exact required daily ZIPs for frozen `ASSETUSDT` pairs and `BTCUSDT`;
- verify each ZIP against its official `.CHECKSUM`;
- parse only timestamps and OHLC fields required for frozen return calculations.

Forbidden:
- alternate exchanges;
- current exchange metadata as historical substitution;
- 2025/2026 data;
- borrow-rate/inventory values;
- authenticated Binance account/API data.

## Frozen returns

For horizon `h` in `{1h, 4h, 24h}`:

- `P0_asset` = open of first 1m `ASSETUSDT` bar with open time >= `t0_raw`;
- `Ph_asset` = open of first 1m `ASSETUSDT` bar with open time >= `t0_raw + h`;
- asset log return = `ln(Ph_asset / P0_asset)`.

Benchmark uses the same two timestamps on `BTCUSDT`:

- BTC log return = `ln(Ph_btc / P0_btc)`.

Market-adjusted return:

`MAR_h = asset_log_return_h - btc_log_return_h`.

### Pre-event placebo

`PRE24_MAR` is the asset-minus-BTC log return from the first 1m bar at or after `t0_raw - 24h` to `P0`.

The placebo is frozen before outcomes and is not a trading rule.

## Primary statistical unit

For each article code and each horizon, average all eligible asset-event `MAR_h` values from that article with equal asset weight.

Primary inference is performed on these **article-level equal-weight means**, giving every Binance announcement one observation regardless of how many assets it contains.

This prevents pseudo-replication from multi-asset announcements.

## Primary endpoint

**Article-level mean `MAR_24h`.**

Directional hypothesis:
- H0: mean `MAR_24h >= 0`
- H1: mean `MAR_24h < 0`

Primary p-value: one-sided one-sample t-test across article-level means.

A deterministic article-level bootstrap with seed `20260917` and 50,000 resamples produces a 95% confidence interval for the mean as a robustness diagnostic.

A one-sided exact binomial sign test on the share of negative article-level `MAR_24h` values is also reported as robustness, not as a rescue test.

## Secondary endpoints

Reported without multiplicity-based promotion rights:

- article-level mean `MAR_1h`;
- article-level mean `MAR_4h`;
- median article-level `MAR_24h`;
- fraction of negative article-level `MAR_24h`;
- source-frozen confound strata using flags already recovered before outcomes.

No secondary endpoint can rescue a failed primary endpoint.

## Pretrend guard

Article-level `PRE24_MAR` is tested with the same one-sided t-test for negative pretrend.

If `PRE24_MAR` is significantly negative at `p < 0.05`, a negative post-event primary result is classified `DISCOVERY_PRETREND_CONFOUNDED` rather than promoted. This guard is frozen before outcomes.

## Minimum sample

Primary Discovery requires after source/boundary filtering:

- at least **50 analyzable asset-events**;
- at least **25 distinct article codes**.

Otherwise: `DISCOVERY_DATA_INSUFFICIENT`.

## Frozen Discovery promotion criterion

`DISCOVERY_SIGNAL_PASS` requires all of:

1. minimum sample satisfied;
2. mean article-level `MAR_24h < 0`;
3. primary one-sided t-test `p < 0.05`;
4. article-level mean `MAR_4h <= 0` as directional-consistency guard;
5. negative pretrend guard does **not** trigger (`PRE24_MAR` one-sided p >= 0.05).

The sign test and 1h endpoint are reported but are not mandatory promotion criteria.

If criteria 2–4 fail: `DISCOVERY_NO_SIGNAL`.
If the primary post-event criterion passes but the pretrend guard triggers: `DISCOVERY_PRETREND_CONFOUNDED`.

No threshold, horizon, benchmark, subset, pair, direction or event timestamp may be changed after outcomes to rescue a result.

## Terminal classifications

- `DISCOVERY_SIGNAL_PASS`
- `DISCOVERY_NO_SIGNAL`
- `DISCOVERY_PRETREND_CONFOUNDED`
- `DISCOVERY_DATA_INSUFFICIENT`
- `DISCOVERY_DATA_PROVENANCE_FAILURE`
- `DISCOVERY_TECHNICAL_FAILURE`

`NO_EDGE` is not synonymous with a technical/data failure.

## Consequence of a pass

A `DISCOVERY_SIGNAL_PASS` is **not a diamond and not an executable strategy**. It permits only creation of a separately frozen validation/OOS protocol. Historical margin-interest/inventory costs remain unresolved because execution-cost provenance is `CREDENTIAL_BOUND`.

## Safety

No orders, wallets, exchange mutation, alerts/webhooks, live trading or merge to main. No authenticated Binance account/API access. No 2025/2026 scientific data.
