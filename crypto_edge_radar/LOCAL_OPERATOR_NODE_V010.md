# Crypto Edge Radar V0.10 — Local Operator Node

Status: READ-ONLY / PUBLIC SHADOW / FAIL-CLOSED.

This Windows build preserves the existing Radar local node and adds the prospectively frozen
HTF-DH03-12H-STANDALONE-FORWARD-V1 collector.

## Startup behavior

- Control Room remains loopback-only at http://127.0.0.1:8787.
- No API keys are required or accepted by the DH03 collector.
- No orders or exchange mutations are implemented by the DH03 collector.
- The collector stores local state under the user's LOCALAPPDATA/CryptoEdgeRadar directory.
- data/dh03_local_status.json reports BOOTSTRAPPING, COLLECTING, or FAIL_CLOSED.

## DH03 source chain

1. Checksum-verified Binance USD-M public archives are warmup/state only.
2. The local node may use official Binance USD-M public REST 15m data for recent causal bootstrap.
3. If REST is unavailable or returns a geographic/transport block, no alternate venue is substituted.
4. Official Binance USD-M public WebSocket streams collect 15m, 1m, and mark-price/funding observations.
5. Exact entry is bound from the minute-open event; missing the exact minute is a deviation, not reconstructed evidence.
6. Minute-path gaps remain unresolved and cannot be repaired into valid forward evidence.

## Frozen strategy identity

- Universe: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT
- Timeframe: 12H UTC
- Direction: LONG only
- Donchian lookback: 40 complete 12H bars
- ATR: Wilder 28
- Entry: next 12H open
- Stop: signal low - 0.25 * ATR28
- Target: 3R
- Maximum hold: 80 x 12H
- BASE round-trip cost: 0.20%
- STRESS round-trip cost: 0.30%
- One active trade per symbol

This build does not authorize micro-live or real-money execution.
