# IPG-001 HISTORICAL CORE SOURCE BOUNDARY CLOSEOUT V0.1

Date: 2026-09-25
Lab: INFORMATION-PROPAGATION-GRAPH-001
Stage: SOURCE

## Verdict

HISTORICAL_CORE_SOURCE_BLOCKED
FORWARD_COLLECTION_REQUIRED_FOR_OPTIONS_GRAPH
EDGE NOT TESTED

## Evidence

### Binance official archive

A frozen 2024-01-01 fixture passed for:
- BTCUSDT spot aggTrades: 863,403 rows, checksum PASS;
- BTCUSDT USD-M futures aggTrades: 761,222 rows, checksum PASS;
- nondecreasing event timestamps and aggregate-trade IDs;
- zero rows outside fixture day.

This establishes defensible historical spot/perp trade timing from Binance's
official archive for the fixture.

### Deribit official public API

Frozen 2024-06-01 source probe:
- no June-2024 expired option instrument was exposed by the current inventory;
- BTC-PERP funding returned 23 hourly rows;
- BTC-PERP mark history returned zero rows for the 2024 day;
- DVOL call returned zero rows for the 2024 day.

Retention-boundary remediation:
- the earliest expired BTC option currently exposed was a 2026-09 expiry;
- option trade and option mark-history calls returned zero rows even inside the
  objectively observed retention boundary;
- BTC funding history remained available;
- DVOL returned current-boundary history;
- classification RETENTION_BOUNDARY_PARTIAL.

## Scientific consequence

The frozen core IPG graph begins with OPTIONS_STATE and requires event-time
ordering against PERP_STATE and SPOT_STATE.

The current free official historical sources do not provide a defensible
2024 option-state surface with the event-time semantics required by the frozen
experiment. Funding-only or DVOL-only substitution would materially change the
upstream node and is not allowed after the graph was frozen.

Therefore:
- do not run 2024 OPTIONS -> PERP -> SPOT Discovery;
- do not reinterpret Binance-only PERP -> SPOT as the main IPG hypothesis;
- do not use a mutable third-party reconstruction without a separate source gate;
- do not call this NO_EDGE.

## Forward state

Forward public source smoke already established:
- Deribit BTC-PERPETUAL: PASS;
- Deribit option markprice packets: PASS;
- Deribit DVOL: PASS;
- Binance Spot market-data-only stream: PASS;
- Binance USD-M Futures stream: BLOCKED in GitHub-hosted runner by source/access geography.

Therefore the core hypothesis remains SOURCE_PARTIAL / PRE-DISCOVERY and needs
an authorized execution environment that can collect the official Binance USD-M
stream without proxying or timing distortion.

OpenMarket negative control remains PASS / CLOCK_OFFSET_SENSITIVE and earns
zero promotion credit.

No market outcome, signal, PnL, live trading, exchange mutation or merge occurred.
