# CRYPTO EDGE RADAR — AGGRESSIVE V0.3 PREP CLOSEOUT — 2026-09-16

Status: **PREPARED / TESTED / NO ORDER PATH**

Branch: `crypto-edge-radar-aggressive-v0.3`

## Completed

- separated aggressive deployment work from the stable shadow branch;
- froze `AGGRESSIVE_DEPLOYMENT_POLICY_V1`;
- created current deployment registry with scientific-state reconciliation;
- added fail-closed deployment gate;
- added default account risk budgets: 0.10% per trade, 0.30% concurrent, 0.30% daily stop, 0.75% weekly stop;
- added advisory stop-based sizing helper;
- added immutable manual-execution receipt template;
- implemented the exact frozen `ETF-CME-INSTFLOW-001` CFTC signal formula;
- implemented public CFTC current-source trap using dataset `6dca-aqww`, contract code `133741`;
- enforced conservative +8-calendar-day information-safe timing;
- enforced `DO_NOT_CHASE` once the exact frozen entry timestamp has passed;
- preserved no authenticated exchange API, no wallet, no autonomous order creation/cancel/mutation.

## CI / public soak

Workflow: `CRYPTO EDGE RADAR V0.3 CI + PUBLIC SOAK`  
Validated run: `35151852887`  
Head: `4de2a17685ce41e6cec36d94acb4a739e0714eda`  

Result:

- compile: PASS;
- unit tests: PASS;
- three-cycle real public Binance data soak: PASS;
- evidence-chain verification: PASS;
- heartbeat verification: PASS;
- public CFTC current-source trap: PASS;
- authenticated exchange API: FALSE;
- orders created: FALSE.

Artifact: `crypto-edge-radar-v03-public-shadow-receipt`  
Artifact ID: `10469671333`  
Artifact digest: `sha256:52c329e2106e355907bbdf83d70db20a6eed25f99e9474386e4e4c678720111c`

## Current ETF-CME source-trap observation

Checked at: `2026-09-16T21:21:27.380091Z`

Previous CFTC observation:
- as-of: `2026-09-01`
- open interest: `19697`
- non-commercial long: `16530`
- non-commercial short: `15827`

Current CFTC observation:
- as-of: `2026-09-08`
- open interest: `21083`
- non-commercial long: `17600`
- non-commercial short: `16076`

Frozen signal:

`((17600 - 16076) - (16530 - 15827)) / 21083 = +0.038941327135606885`

Direction: `LONG`

Frozen information-safe / exact entry time: `2026-09-16T00:00:00Z`  
Frozen exit time: `2026-09-23T00:00:00Z`

At the actual check time the exact entry timestamp had already passed.

Final runtime state:

`ENTRY_WINDOW_PASSED_DO_NOT_CHASE`

`entry_eligible_now = false`

This V0.3 preparation deliberately does not invent a late-entry tolerance after observing a live signal.

## Remaining blockers before first micro-live trade

For `ETF-CME-INSTFLOW-001` specifically:

1. freeze exact execution venue;
2. freeze exact real-money instrument capable of implementing both frozen LONG and SHORT states;
3. record actual fee/slippage assumptions for that instrument;
4. freeze a defensible strategy-specific exposure / maximum-loss model because the historical 7-day strategy has no stop;
5. record account equity snapshot and compute advisory size;
6. generate pre-trade receipt before any manual execution.

Tier 3 candidates remain shadow-only. Rejected/Tier 4 candidates remain blocked.

## Operational conclusion

The machine is technically prepared for aggressive evidence collection and advisory micro-live gating. It will not manufacture a trade, chase an expired entry, silently rescue failed candidates, or create exchange orders.
