# MRCR H02 — Exact Source Coverage Runbook V0.1
Status: READY FOR OPERATOR WINDOWS / SOURCE-ONLY / TARGET OUTCOMES LOCKED
Date: 2026-09-25

## Purpose

Prove that every public market-data leg required by the frozen H02 ruleset is
reachable and schema-compatible on the operator Windows environment.

Frozen scope:

- Binance Spot BTCUSDT: aggTrade + depth@100ms
- Binance Spot ETHUSDT: aggTrade + depth@100ms
- Coinbase Advanced Spot BTC-USD: market_trades + level2
- Coinbase Advanced Spot ETH-USD: market_trades + level2

This probe is source/infrastructure evidence only.

It does not persist raw payloads, print economic values, compute signals, compute
future outcomes, use authentication, access accounts or place orders.

## Run

From the MRCR research folder on Windows:

```powershell
.\Run_MRCR_H02_Source_Coverage.cmd
```

The launcher creates a dedicated local venv if needed and pins
`websockets==15.0.1`.

## PASS contract

Overall receipt:

`"status": "PASS"`

Each Binance symbol must show:

- transport = PASS
- aggtrade_messages > 0
- depth_messages > 0
- aggtrade_schema_pass = true
- depth_schema_pass = true
- status = PASS

Each Coinbase product must show:

- transport = PASS
- subscription_messages > 0
- market_trade_messages > 0
- level2_messages > 0
- market_trade_schema_pass = true
- level2_schema_pass = true
- l2_snapshot_seen = true
- l2_update_seen = true
- status = PASS

Global boundary fields must remain:

- economic_values_printed = false
- raw_payloads_persisted = false
- authentication_used = false
- account_endpoints_used = false
- signals_computed = false
- outcomes_computed = false
- orders_enabled = false

## Sharing rule

Share only the single sanitized JSON receipt printed by the probe.

Do not capture or upload raw WebSocket messages for this gate.

## Scientific boundary

A PASS closes exact source coverage only. It does not open target observation,
does not alter the frozen H02 ruleset and creates no edge/promotion credit.
