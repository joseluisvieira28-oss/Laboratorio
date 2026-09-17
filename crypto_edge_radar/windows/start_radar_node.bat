@echo off
setlocal
cd /d "%~dp0\.."
set RADAR_PROVIDER=mexc_futures_public
set RADAR_UNIVERSE_MODE=core5
set RADAR_DB=data\radar_evidence.sqlite3
set RADAR_STATUS=data\radar_status.json
set RADAR_NOTIFICATIONS=data\radar_notifications.jsonl
if not exist data mkdir data
python -m radar local-node --port 8787 --interval 30
endlocal
