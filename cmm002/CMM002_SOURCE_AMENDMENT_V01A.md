# CMM-002 — SOURCE AMENDMENT V0.1A — HOLDOUT-SAFE STABLECOIN TRANSPORT

Status: FROZEN BEFORE ANY CMM-002 2025 OUTCOME ACCESS

## Trigger
The CMM-002 pre-OOS authority preserved the CMM-001 liquidity definition:
aggregate DefiLlama stablecoin market cap, transformed as a lagged 30-calendar-day log change.

Before acquisition, audit found that the live /stablecoincharts/all endpoint returns the complete history through the present. Calling it now could expose 2026 feature rows, violating the explicit CMM-002 2026 no-fetch boundary.

No CMM-002 2025 BTC return, PnL, PF, event outcome or 2026 source has been accessed.

## Amendment scope
SOURCE TRANSPORT ONLY.

The liquidity variable, 30-day transformation, one-day lag, normalization, G construction, q95 trigger, funding gate, direction, horizon, costs and adjudication are unchanged.

## Authorized holdout-safe route
1. Query the Internet Archive CDX index for the exact URL:
   https://stablecoins.llama.fi/stablecoincharts/all
2. The CDX query MUST be bounded with to=20251231235959.
3. Select the latest valid HTTP-200 JSON snapshot with archive timestamp < 20260101000000.
4. Fetch the raw archived response using the corresponding /web/{timestamp}id_/ replay URL.
5. Reject any archive payload containing a data timestamp >= 2026-01-01.
6. Use only 2024-01-01 through 2025-12-31 after payload validation.

## Semantic continuity gate
Because CMM-001 used the same DefiLlama aggregate semantic variable, the archived snapshot must reproduce its 2024 liquidity-state history sufficiently closely BEFORE any CMM-002 outcome is opened.

Using the preserved CMM001_DAILY_STATE_LEDGER_V01.csv:
- derive archived L_raw(d) = ln(supply<=d-1 / supply<=d-31);
- compare against parent L_raw on 2024 dates where both exist;
- overlap N >= 300;
- Pearson correlation >= 0.995;
- median absolute difference <= 0.002;
- 95th-percentile absolute difference <= 0.010.

These are source-semantic checks only; no BTC return or PnL is involved.

## Fail closed
If:
- CDX/replay is unavailable;
- no bounded 2025 snapshot exists;
- payload includes 2026;
- schema/coverage is insufficient;
- semantic continuity fails;

classify CMM-002 as SOURCE_BLOCKED and STOP.

Forbidden fallbacks:
- live DefiLlama full-history endpoint;
- changing aggregate-all-stablecoins to USDT+USDC;
- a different provider semantic definition;
- inspecting 2026;
- changing CMM-002 economics to evade the blocker.

END SOURCE AMENDMENT V0.1A
