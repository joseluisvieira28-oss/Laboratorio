# TV-FOOTPRINT-CALIBRATION-001 — Telemetry Ingest Deployment Receipt

Date: 2026-09-24
Status: LIVE / RESEARCH-ONLY / TRADING_AUTHORITY_NONE

## Render deployment

- Workspace: Laboratorio
- Service: `tv-footprint-calibration-ingest-v01`
- Service ID: `srv-daqgvt0u01pc7384vsa0`
- Deploy ID: `dep-daqgvtgu01pc7384vu70`
- Region: Frankfurt
- Plan: free
- Branch: `tradingview-telemetry-ingest-v0.1`
- Deployed commit: `8e0319e7ff718ba7736f8b391a7c6810a8b71aa7`
- Public base URL: `https://tv-footprint-calibration-ingest-v01.onrender.com`
- Auto-deploy: OFF
- Final deploy state: `live`

## Transport design

A second free Postgres instance was unavailable because the workspace already has one active free-tier database. The ingest path therefore remains isolated from the canonical Radar database and uses Render application logs as the temporary seven-day transport evidence ledger.

Each accepted real TradingView delivery emits one structured `TVFP_RECEIPT` record containing:

- UTC receive timestamp
- deterministic evidence key
- payload SHA256
- validated raw payload
- explicit `trading_authority=NONE`

Terminal corpus extraction must deduplicate by:

`lab_id|sensor_version|symbol|timeframe|bar_close_ms`

The deduplicated corpus must be archived before log-retention expiry.

## Security

- webhook token exists only in Render environment configuration and operator handoff;
- token is not committed to GitHub or Drive;
- no outbound HTTP client;
- no exchange client;
- no MEXC route;
- no database credentials;
- unknown telemetry fields rejected;
- pre-forward observations rejected;
- execution-like fields rejected by exact-schema validation.

## Validation

GitHub CI unit tests and fail-closed security audit passed before deploy.
Render build completed successfully.
Gunicorn started successfully and listens on the assigned Render port.

No synthetic accepted post-boundary payload was injected, specifically to avoid contaminating prospective calibration evidence.

## Next gate

Operator must create one TradingView alert on the already-running Market Microscope V1 using `Any alert() function call` and the secret HTTPS webhook URL supplied privately in chat.

After creation, the first authentic closed 5-minute TradingView bar must be observed in Render logs as a `TVFP_RECEIPT` before telemetry collection is declared ACTIVE.
