# LIQUIDATION-FLOW-FWD-003 — BINANCE USD-M SOURCE GATE PASS CLOSEOUT V0.3

Date: 2026-10-08
Verdict: `BINANCE_LIQUIDATION_SOURCE_PASS`
Status: SOURCE PROVEN / CALIBRATION NOT YET AUTHORIZED / FAMILY NOT ACTIVE

## Canonical source run

- Workflow run: `37728382792`
- Job: `113151658110`
- Head SHA: `5f41adb648bac4ce8bfe6348ccc8111230d5d830`
- Artifact: `v013-binance-liquidation-source-v03-37728382792-1`
- Artifact id: `11529500851`
- Artifact digest: `sha256:a00214ff986f22e164ced6d40529e00500904c0ed46bb79f8bfd6f4a1300f2d9`

## Frozen gate result

600-second public Binance USD-M forceOrder observation:
- subscription acknowledgement: PASS
- raw messages preserved: 33
- source errors: 0
- BTCUSDT valid forceOrder events: **20**
- ETHUSDT valid forceOrder events: **12**

Both frozen target symbols supplied fresh real forceOrder payloads satisfying the predeclared
symbol / side / quantity / price / event-time / trade-time / freshness / raw-hash checks.

Therefore the frozen source gate passes.

## Important source-semantic limitation

Binance's forceOrder stream is a snapshot stream, not a complete all-liquidation tape.
The stream exposes the latest liquidation order per symbol within its update interval.
Therefore these counts establish timestamped source feasibility, but MUST NOT be silently
interpreted as complete forced-flow volume or pooled with Bybit/OKX volume.

Any Binance-based calibration must be prospectively designed around this exact snapshot
semantics and kept a separate family version.

## Scientific boundary

This is a SOURCE PASS only.

It does NOT:
- activate a family;
- define a liquidation-size threshold;
- prove a trading edge;
- pool Binance with Bybit or OKX;
- open MEXC Event Futures outcomes.

Research outcomes opened: **0**.

No login, API key, private endpoint, account read, order, wallet, spending, exchange mutation,
live trading or main merge occurred.
