# TradingView Research Telemetry Ingest V0.1

Research-only HTTPS receiver for `TV-FOOTPRINT-CALIBRATION-001`.

## Safety boundary

This service has no exchange client, no broker client, no wallet code and no order route. It accepts only the exact frozen Market Microscope V1 JSON schema and persists raw observations for later calibration against Binance BTCUSDT aggTrades.

Unknown fields are rejected. This intentionally rejects execution-like additions such as `action`, `side`, `quantity`, `leverage`, or any other field not present in the frozen schema.

## Environment

- `TELEMETRY_DB_DSN` or `DATABASE_URL`: PostgreSQL connection string.
- `TV_WEBHOOK_TOKEN`: random secret, minimum 24 characters.
- `PORT`: supplied by Render.

## Endpoints

- `GET /health`: public liveness + DB reachability. Does not expose secrets or data.
- `POST /v1/tradingview/<token>`: strict TradingView telemetry ingest.
- `GET /v1/status/<token>`: receipt count and terminal-gate readiness.

## Frozen identity

- Lab: `TV-FOOTPRINT-CALIBRATION-001`
- Sensor: `MM-V1`
- Symbol: `BINANCE:BTCUSDT`
- Timeframe: `5`
- Forward boundary: 2026-09-24 11:00 UTC
- Minimum terminal evidence: 2,016 matched forward bars.

## Idempotency

The database enforces a unique key on:

`lab_id + sensor_version + symbol + timeframe + bar_close_ms`

Duplicate webhook deliveries therefore do not duplicate scientific evidence.

## Deployment rule

Deploy as an isolated Render web service. Do not add this route to the canonical Radar execution service and do not connect the endpoint to MEXC or another exchange.
