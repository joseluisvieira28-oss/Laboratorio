# MEXC EVENT FUTURES — MULTI-ASSET SOURCE GATE FREEZE V0.1

Date: 2026-10-02
Status: FROZEN BEFORE HISTORICAL OUTCOME OPEN
Mode: SOURCE/DATA ONLY — NO EDGE CLAIM, NO PNL, NO LIVE TRADING

## Mission

Determine whether MEXC Event Futures can be researched defensibly across the five instruments currently visible in the operator UI:

- BTCUSDT
- ETHUSDT
- NVDAUSDT
- MUUSDT
- SPCXUSDT

The eventual research target is directional prediction for Event Futures settlement horizons:

- 10 minutes
- 30 minutes
- 1 hour
- 1 day

using information available at entry from chart/data horizons including:

- 1 minute
- 5 minutes
- 15 minutes
- 1 hour
- 4 hours
- 1 day

This source gate does NOT test those hypotheses. It only determines whether the required inputs can be sourced without hindsight leakage.

## Product facts frozen before source probing

Official MEXC documentation states:

1. Event Futures settle on whether the underlying index price is above or below the entry/target price at expiry.
2. A correct prediction returns principal plus principal multiplied by the payout shown at submission.
3. An incorrect prediction loses the principal.
4. A tie returns principal.
5. Payout is dynamic and is fixed only when the individual Event Future is submitted.
6. Positions cannot be closed before expiry.
7. Event Futures currently do not support API trading.
8. Officially documented expiry choices include 10m, 30m, 1h and 1d.
9. Minimum order amount is documented as 1 USDT in the current help article.

Consequences:
- Historical directional accuracy alone is NOT enough to establish Event Futures profitability.
- A true economic backtest requires the payout that was available at each entry timestamp.
- Until historical payout provenance is proven, any historical study is classified as DIRECTIONAL-FEASIBILITY only, not PRODUCT-PNL.

## Candidate symbol mapping to probe

Display pair -> public MEXC Futures/index candidates:

- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVDA_USDT, NVIDIA_USDT
- MUUSDT -> MU_USDT, MUSTOCK_USDT
- SPCXUSDT -> SPCX_USDT, SPCXSTOCK_USDT

No alias is accepted by assumption. The source probe must establish which public symbol actually returns valid index-price data.

## Source route

Primary public route:
- MEXC Futures market API
- GET /api/v1/contract/kline/index_price/{symbol}
- no authentication
- no account endpoint
- no order endpoint
- no exchange mutation

Secondary diagnostic route:
- GET /api/v1/contract/kline/{symbol}
- used only to distinguish missing index history from missing contract history

Product-page route:
- public Event Futures page HTML
- used only to confirm public page availability and inspect whether payout/index fields are exposed statically
- no authenticated calls

## Outcome firewall for this gate

The probe MAY:
- request a short schema/capability window;
- count rows;
- validate timestamps;
- validate that OHLC values are finite/positive;
- identify valid symbol aliases;
- record endpoint availability;
- inspect static product-page HTML for field labels.

The probe MUST NOT:
- compute directional returns;
- compute win rate;
- test a strategy;
- rank assets by performance;
- compute Event Futures PnL;
- choose thresholds from observed returns;
- inspect or use account/private order history;
- submit an Event Future;
- submit any other exchange order.

The receipt must not print raw OHLC values.

## Source-gate PASS requirements

Per displayed asset:

- at least one defensible public symbol mapping;
- successful index-price response over the schema window;
- timestamps parse and are monotonic;
- OHLC fields are present and finite/positive;
- requested interval identity is stable enough for a later collector;
- no authentication required.

Global requirements:

- official product mechanics documented;
- historical payout route classified as one of:
  - PROVEN_PUBLIC_HISTORY,
  - PROVEN_FORWARD_ONLY,
  - NOT_PROVEN;
- exact Event Futures automation capability classified separately from research data capability.

## Verdict taxonomy

SOURCE_GATE_PASS_DIRECTIONAL_ONLY:
- public index history is defensible for all target assets,
- but historical Event Futures payout is not proven.

SOURCE_GATE_PASS_FULL_PRODUCT:
- index history and timestamped historical payout at entry are both defensibly available.

SOURCE_GATE_PARTIAL:
- some target assets pass and others fail.

SOURCE_GATE_BLOCKED_TRANSPORT:
- public data routes cannot be reached reliably enough to adjudicate.

SOURCE_GATE_FAIL_DATA:
- source responses exist but fail structural/timestamp requirements.

## Next science stage after PASS

Only after this gate closes, freeze a PRE-OUTCOME DIRECTIONAL SCIENCE protocol before bulk historical data are opened.

That protocol will predefine:
- Development / OOS / holdout date partitions;
- chart lookbacks;
- signals;
- event settlement horizons;
- tie handling;
- overlapping-event handling;
- multiple-testing correction;
- minimum sample requirements;
- promotion thresholds;
- exact payoff sensitivity grid.

No post-outcome rescue is permitted.

## Governance

- no merge to main;
- no live trading;
- no Event Futures order;
- no exchange mutation;
- no account/private endpoint;
- no post-outcome tuning;
- source failure is BLOCKED/FAIL_DATA, never NO_EDGE;
- directional predictability is not equivalent to Event Futures economic edge.
