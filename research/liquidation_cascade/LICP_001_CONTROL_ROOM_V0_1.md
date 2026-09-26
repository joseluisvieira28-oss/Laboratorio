# LICP-001 — CONTROL ROOM V0.1

Date: 2026-09-26
Branch: liquidation-cascade-propagation-v0.1
PR: #107

## Scientific state

| Gate | State |
|---|---|
| Core public liquidation source gate | PASS_SAMPLE |
| Binance BTCUSDT BBO source | PASS_SAMPLE |
| Bybit BTC/ETH/SOL allLiquidation subscription | PASS_SAMPLE |
| MEXC BTC_USDT target depth | PASS_SAMPLE |
| MEXC ETH_USDT target depth | PASS_SAMPLE |
| MEXC SOL_USDT target depth | PASS_SAMPLE |
| Hyperliquid BTC/ETH/SOL OI context | PASS_SAMPLE |
| Trigger-engine fail-closed tests | PASS |
| Mechanical calibration→config freezer tests | PASS |
| Executable LONG/SHORT fee/spread math tests | PASS |
| First 5m feature calibration | CALIBRATION_SPARSE |
| Second 10m feature calibration | RUNNING at last update |
| Numeric trigger config | UNFROZEN |
| MEXC post-trigger outcomes | NOT OPENED |
| MEXC 2025 public history | SOURCE_BLOCKED |
| Live trading | NOT AUTHORIZED |

## Frozen causal chain

1. Bybit BTC liquidation ignition:
   - 5s notional p95
   - 5s side-concentration p75

2. Binance BTC confirmation:
   - 5s notional p75
   - same normalized forced-pressure direction
   - observable within 5s of ignition

3. Open-interest context:
   - Hyperliquid public BTC OI
   - recorded causally
   - NOT a V0.1 trigger gate

4. ETH/SOL second wave:
   - Bybit 5s notional p95
   - same pressure direction
   - within 30s after confirmed BTC ignition

5. MEXC executable targets:
   - BTC_USDT
   - ETH_USDT
   - SOL_USDT

6. Horizons:
   - 1s / 2s / 5s / 15s / 30s / 60s

7. Economics:
   - taker/taker: executable BBO + 16 bps API fees
   - maker/maker: optimistic economic ceiling + 12 bps API fees

## Fail-closed state

Forward observer is wired to run only when
`LICP_001_TRIGGER_CONFIG_V0_1.json` changes to a valid `FROZEN` configuration.

Sparse or missing calibration values do not unlock it.
