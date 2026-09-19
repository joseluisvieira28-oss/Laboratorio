# BTC-OPTIONS-VRP-001 — optionsDX FREE SAMPLE PROBE CLOSEOUT V0.1

Date: 2026-09-19
Probe: `OVRP-EXEC-SOURCE-OPTIONSDX-FREE-SAMPLE-001`
Initial run: `35457931104`
Corrected technical run: `35457977533`
Initial artifact: `10588696106`

## Final classification

**OPTIONSDX_FREE_SAMPLE_SCHEMA_INSUFFICIENT**

This is a source-sample verdict only. It is not NO_EDGE and does not alter the parent `DISCOVERY_PASS_VRP_EXISTS`.

## Preserved technical history

The first run successfully retrieved the exact public sample but failed to recognize square-bracketed CSV headers. Technical Amendment V0.1A prospectively authorized only header normalization. No URL, required field, DTE gate or outcome rule changed.

## Corrected source evidence

The corrected run proved:

- HTTP 200;
- content type `text/csv`;
- 21,385,261 bytes;
- 94,066 data rows;
- 28 columns;
- SHA256 `7483e49d5317f91ad9acb869fadbcb3ad9de7f4c42998f545da3a4209a5e6933`;
- all frozen required fields present;
- 458 unique instruments;
- all 94,066 rows carried complete bid/ask prices and sizes;
- quote date represented: 2021-06-01;
- complete BBO rows inside the frozen 25–35 DTE band: **0**.

Because the frozen pass rule required at least one complete 25–35 DTE BBO row, the exact free-sample probe fails.

Do not weaken the DTE gate or reinterpret the rich BBO schema as a pass for this exact probe.

## Separate procurement finding

A later procurement-only catalog lookup found a distinct zero-price full-data variation: BTC Deribit **2021-06 / End of Day**, variation ID `1570`, public display price USD 0.00. That finding belongs to a separate source-acquisition lane and does not rewrite this closeout.

## Safety

No returns, PnL, expectancy, PF, drawdown or future realized variance opened.
No 2025/2026 strategy data opened.
No payment, cart, checkout, account, wallet, API key, exchange mutation, live trading or main merge occurred.
