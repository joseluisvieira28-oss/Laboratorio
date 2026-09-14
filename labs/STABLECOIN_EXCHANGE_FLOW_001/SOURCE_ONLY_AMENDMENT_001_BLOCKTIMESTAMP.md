# STABLECOIN-EXCHANGE-FLOW-001 — SOURCE-ONLY AMENDMENT 001 — LOG `blockTimestamp`

STATUS: FROZEN PRE-OUTCOME SOURCE IMPLEMENTATION AMENDMENT

This amendment is based only on source-schema evidence observed before any BTC price, return, PnL or performance outcome was accessed.

## New source fact

MEV Blocker historical `eth_getLogs` responses include a `blockTimestamp` field on each log. The protected schema gate classified `LOG_SCHEMA_PASS` and observed keys including `blockNumber` and `blockTimestamp` on 2022 historical USDT logs.

## Effect on acquisition implementation

`DATA_ACQUISITION_PROTOCOL_V0.1.md` required exact UTC-day assignment and proposed proving every daily block boundary with `eth_getBlockByNumber`.

Because the selected primary source directly supplies the canonical log block timestamp, the implementation SHALL instead:

1. prove only the global protected start and terminal block boundaries using historical block metadata;
2. extract logs in the frozen 3,200-block base chunks with adaptive splitting;
3. parse each log's `blockTimestamp` as an integer Unix timestamp;
4. fail closed if `blockTimestamp` is missing, malformed, or outside `2022-11-11 00:00:00 UTC` through `2024-12-30 23:59:59 UTC`;
5. aggregate each external transfer directly to `date_utc = UTC(blockTimestamp).date()`;
6. preserve zero-flow days by materializing the complete protected date calendar after aggregation.

This removes unnecessary metadata calls but does **not** change the basket, token, flow definition, direction, protected dates, chunk base, thresholds (none), or any market-outcome rule.

## Governance

This is a source-efficiency amendment made before outcome access. No BTC market data, returns, PnL, 2025 or 2026 were opened. No post-outcome tuning is permitted.
