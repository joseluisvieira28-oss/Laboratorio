# Crypto Edge Radar V0.14.1 — Local Recovery

Scope: Windows operational recovery only. No scientific rules, candidate classifications, costs, thresholds, forward boundaries or execution authority are changed.

## Use

1. Extract the bundle into a fresh folder.
2. Double-click `windows\START_RADAR_RECOVERY_V0141.bat`.
3. Do not manually open 127.0.0.1:8787 first.
4. The launcher opens the browser only after the local HTTP service actually responds.
5. If startup fails, the console stays open and the exact logs are stored under `logs\`.

The launcher:
- detects port 8787 before startup;
- never kills unrelated processes using that port;
- stops only stale `CryptoEdgeRadarNode.exe` instances;
- starts the canonical V0.14.1 node with stdout/stderr redirected;
- probes localhost for up to 60 seconds;
- displays process-exit or timeout evidence instead of hiding the failure behind a browser error.

## Diagnostic

Run:

`powershell -ExecutionPolicy Bypass -File .\windows\CHECK_RADAR_V0141.ps1`

This prints process, port, HTTP, local status JSON and recent log tails.

## Safety

This is public-shadow infrastructure. It contains no authenticated exchange order transport and does not authorize capital or orders.
