# LOCAL OPERATOR NODE V0.13.2

Status: **PUBLIC SHADOW / GATED OBSERVATION ONLY — NO CAPITAL — NO ORDERS**

Build identity: `v0.13.2-win-six-motor-runtime-truth`

V0.13.2 is the canonical Windows operator node for the six-motor Crypto Edge Radar control plane.

## Active / gated motor set

1. ETF-CME-INSTFLOW-001
2. BNB-LAUNCHPOOL-DEMAND-001
3. OPTIONS-SPOTPERP-001-V2.1
4. TFG-DONCHIAN-REGIME-ADAPTATION-V1
5. HTF-DH03-12H-STANDALONE-FORWARD-V1
6. CED1D-0031

CED1D remains an external T+3 archive-shadow motor and is represented in the registry/control plane. It is not converted into a local execution engine.

## DH03 V0.13.2 hardening

DH03 uses Binance USD-M public data only.

Before the DH03 collector can persist its prospective `collector_activation_ms` boundary, the Windows node performs a Binance public server-time preflight.

Fail-closed budgets:

- maximum absolute Binance-vs-local clock midpoint offset: 500 ms
- maximum public request RTT: 1000 ms
- outside either budget: DH03 does not arm

Cockpit runtime truth is taken from the local DH03 status file rather than registry readiness alone:

- `MISSING` / `BOOTSTRAPPING` => **GATED**
- `COLLECTING` => **SHADOW**
- `FAIL_CLOSED` => **BLOCKED**

This prevents dashboard status inflation if the local collector is unavailable or fails after startup.

## Local runtime

- DH03 12H: Binance USD-M public 1m / 15m / mark-price and funding collector.
- BNB Launchpool: official Binance Support CMS + BNBBTC public spot binding.
- TFG Regime: MEXC Spot public watcher.
- OPTIONS-SPOTPERP V2.1: Deribit public daily watcher with frozen forward gate.
- ETF-CME EXEC-V2: public Spot/Perp execution mapping and friction preflight.
- CED1D-0031: external GitHub T+3 archive-shadow state represented in the six-motor registry.

## Startup

1. Close any older `CryptoEdgeRadarNode.exe`.
2. Extract the V0.13.2 ZIP into a new folder. Do not overwrite a running folder.
3. Verify `CryptoEdgeRadarNode.exe` SHA-256 against the release receipt supplied with the build.
4. Keep Windows clock synchronization enabled.
5. Disable sleep and hibernation while DH03 shadow collection is required.
6. Prefer Ethernet or a stable wired connection.
7. Start `CryptoEdgeRadarNode.exe`.
8. Open `http://127.0.0.1:8787`.
9. Confirm system health is OK and registry shows 6 / 6 focus motors.
10. Inspect the DH03 card. It must reflect the runtime state described above.

## Local files

The node materializes operational files under its local `data` directory, including:

- `data/dh03_clock_preflight.json`
- `data/dh03_local_status.json`
- `data/forward_local_evidence.sqlite3`
- `data/forward_local_status.json`
- `data/forward_local_notifications.jsonl`
- `data/forward_local_supervisor_status.json`

DH03 minute-path market/evidence databases remain isolated from the shared local forward evidence store.

## Hard safety

- no API keys required
- no authenticated exchange API
- no order creation
- no exchange mutation
- no wallet access
- no live capital
- no automatic micro-live authorization
- no scientific gate changes
- no retrospective forward evidence
- no DH02 rescue
- no merge to main

V0.13.2 hardens operational truth and timing. It does not weaken or bypass any forward-sample, account-specific fee/state, execution-authority, statistical, or micro-live gate.
