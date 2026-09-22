# CRYPTO EDGE RADAR — PRIVATE EVIDENCE BACKUP LOG TRANSPORT V0.2

Date: 2026-09-22
Status: TEMPORARY READ-ONLY BACKUP TRANSPORT

The V0.1 token-gated HTTP route was validated but could not be consumed by the operator runtime because external network access from that runtime is unavailable. The HTTP gate is disabled.

V0.2 authorizes a one-startup private Render-log transport:
- enabled only by RADAR_BACKUP_LOG_EMIT_ON_START=true;
- reads the same verified snapshot builder;
- canonical JSON is gzip-compressed;
- gzip bytes are base64 encoded;
- output is split into bounded indexed chunks;
- each chunk line contains only index/total/data;
- a header contains snapshot SHA256, gzip SHA256, event count and key count;
- no database URL, password, exchange key or environment values are logged.

The transport is not a scientific event source and does not mutate the database.

After one successful reconstruction and independent verification:
- disable RADAR_BACKUP_LOG_EMIT_ON_START;
- remove temporary backup surfaces from runtime code;
- redeploy clean canonical runtime.

Firewalls:
database_mutation=false
science_changed=false
outcomes_changed=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
capital=false
main_merge=false
