# MEXC-HL-NAS100-DISLOCATION-001 — V0.6 SOURCE COVERAGE CLOSEOUT

Date: 2026-10-04
Canonical coverage run: 37194941101
Head: `a8d3bc332800e0f4ef6bb3b16c4cbdf23adabf1e`

## Frozen rule status

Pre-outcome freeze passed:
- rule SHA256: `51d7ac10d5c8476f5b4223205dfb956e91fec21218495b160858325c5780185d`
- binding SHA256: `1cd51e873faf39d91a665d23868d8bf5859864aecc95d40c7fd05f102eb386ea`

## Source coverage result

The runner failed closed BEFORE scoring.

Log receipt:
- `SOURCE_COVERAGE_ONLY=true`
- `SCORING_NOT_YET_STARTED=true`
- MEXC rows: 39,238
- Hyperliquid `xyz:XYZ100` rows: 291
- exact overlap rows: 291
- alignment ratio on available rows: 1.000
- calendar coverage ratio: 0.0067361111
- first overlap: `2026-09-30T19:09:00Z`
- last overlap before V0.6 hard boundary: `2026-09-30T23:59:00Z`

## Verdict

`SOURCE_BLOCKED_HISTORICAL_COVERAGE__NO_OUTCOMES_OPENED`

This is NOT a NO_EDGE verdict.

The Hyperliquid NAS100 market is simply too recent for the frozen September Discovery/OOS windows.

## Scientific consequence

Because scoring never started, no threshold, horizon, direction, win rate, return or p-value was observed.

A boundary-only successor may preserve every scientific parameter and move the historical windows to the first period where the bound source actually exists.

Allowed successor:
- keep `FADE_LEVEL_DISLOCATION`;
- keep thresholds 10/20/40/80 bps;
- keep entry delay = 1 minute;
- keep horizons 1/2/5/15 minutes;
- keep Discovery/Holm/OOS gates;
- move windows only to source-valid post-listing data that was untouched by V0.6.

No live trading, account reads, wallets, private endpoints, orders or mutation.
