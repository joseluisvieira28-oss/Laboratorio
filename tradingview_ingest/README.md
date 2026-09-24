# TradingView Research Telemetry Ingest V0.2

Research-only HTTPS receiver for `TV-FOOTPRINT-CALIBRATION-001`.

## Safety boundary

This service has no exchange client, no broker client, no wallet code, no database credential, and no outbound HTTP client. It accepts only the exact frozen Market Microscope V1 JSON schema.

Unknown fields are rejected. This intentionally rejects execution-like additions such as `action`, `side`, `quantity`, `leverage`, or any other field not present in the frozen schema.

## Evidence ledger

Each accepted delivery is written as one structured Render application-log line:

`TVFP_RECEIPT {canonical JSON record}`

The record contains:

- UTC receive timestamp;
- deterministic evidence key;
- SHA256 of the canonical TradingView payload;
- untouched validated payload;
- explicit `trading_authority=NONE`.

The evidence key is:

`lab_id|sensor_version|symbol|timeframe|bar_close_ms`

Duplicate deliveries may reappear after a process restart, so the terminal extraction **must** deduplicate by evidence key. In-process duplicates are additionally detected by a bounded LRU cache.

This transport ledger is deliberately temporary. The calibration window is seven days and the final deduplicated corpus must be extracted and archived to GitHub/Drive before provider log retention expires.

## Environment

- `TV_WEBHOOK_TOKEN`: random secret, minimum 24 characters.
- `PORT`: supplied by Render.

## Endpoints

- `GET /health`: public liveness. Exposes no token or payload.
- `POST /v1/tradingview/<token>`: strict telemetry ingest.
- `GET /v1/status/<token>`: process-local counters only; authoritative count comes from final log extraction.

## Frozen identity

- Lab: `TV-FOOTPRINT-CALIBRATION-001`
- Sensor: `MM-V1`
- Symbol: `BINANCE:BTCUSDT`
- Timeframe: `5`
- Forward boundary: 2026-09-24 11:00 UTC
- Minimum terminal evidence: 2,016 unique matched forward bars.

## Deployment rule

Deploy as an isolated Render web service. Do not add this route to the canonical Radar execution service and do not connect the endpoint to MEXC or another exchange.
