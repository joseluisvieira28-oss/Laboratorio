# MEXC EVENT FUTURES LAB — EXACT CURRENT PAYOUT COLLECTOR FREEZE V0.6.3

Date: 2026-10-02
Status: PROSPECTIVE SOURCE COLLECTION / READ-ONLY / FAIL-CLOSED

## Prior source findings

V0.6:
- public Event Futures DOM exposed exact current Up/Down payout values for all five displayed assets.

V0.6.2:
- 10m and 30m exact current payouts were collected for all five assets.

V0.6.2.1 selector census:
- Event Futures horizon selector group is the visible group whose text is exactly:
  10m / 30m / 1H / 1D
- the chart-timeframe group is separate:
  1m / 5m / 15m / 1H / 4H / 1D

Therefore the collector may safely select 1H and 1D only from the exact Event Futures horizon group containing all four labels.

## V0.6.3 mission

Collect exact current payout snapshots for:

Assets:
- BTCUSDT
- ETHUSDT
- NVDAUSDT
- MUUSDT
- SPCXUSDT

Horizons:
- 10m
- 30m
- 1H
- 1D

Fields:
- observed_at_utc
- asset
- MEXC route symbol
- horizon
- Up payout %
- Down payout %
- DOM evidence hash
- public page URL
- Event Futures index-context DOM evidence, if exposed
- standard-futures public index price captured separately and explicitly labeled PROXY_INDEX

## Critical semantic boundary

Exact current payout may be labeled EXACT_CURRENT_PAYOUT because it is read directly from the Event Futures trading page.

The standard public contract index endpoint is NOT automatically the exact Event Futures settlement index. It must be labeled PROXY_INDEX until equivalence is separately proven.

Any index value extracted from the Event Futures DOM is labeled EVENT_DOM_INDEX_CANDIDATE until the relevant numeric field can be mapped unambiguously.

## Read-only guardrail

- navigation GET only;
- horizon-selector clicks only inside the proven Event Futures horizon group;
- abort all POST/PUT/PATCH/DELETE;
- no authentication;
- no Up/Down click;
- no quantity input;
- no order submission;
- no position mutation;
- no strategy signal;
- no merge to main.

## Source gate

PASS_20_OF_20 if all 20 asset × horizon current payout observations are captured with numeric Up and Down payout.

PARTIAL otherwise.

No profitability verdict is permitted from V0.6.3.
