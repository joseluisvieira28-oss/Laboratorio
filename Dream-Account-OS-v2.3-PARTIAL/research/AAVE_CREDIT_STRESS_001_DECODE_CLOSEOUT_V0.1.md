# AAVE-CREDIT-STRESS-001 — DECODE DAILY SERIES CLOSEOUT V0.1

Date: 2026-09-18
Decode gate: AAVE-CS001-DECODE-DAILY-001

## CANONICAL SCIENTIFIC RESULT

DECODE_DAILY_SERIES_PASS

Parent shard run: 35332026520
Parent shard head: bdab7d481ff7af8fe2334e9b02214a8f77e9c8fd
Shard count: 8/8 PASS

Canonical aggregate completion run: 35333801258
Aggregate head: ae5bb78c443104f46c5c47bf4554b5079365e912
Artifact: aave-cs001-decode-v01-canonical-completion-35333801258-1
Artifact ID: 10541194504
Artifact ZIP SHA256: b15b08d2335c6a15e2547118167b9ebba3ec8d934e1a38ab2f27b0beadee37c1
Structural SHA256: d9fd20432cff441faf7cbc171d904b4dec2cf68b0d10dcdc419522fca5705acc

## RESULT

- valid USDC ReserveDataUpdated events: 183,864
- first Discovery observation date: 2023-01-27
- last observation date: 2024-12-31
- daily rows after first observation: 705
- zero missing calendar dates after first observation
- exact terminal block coverage: PASS
- exact 5-word ABI structure: PASS
- Pool/event/reserve topics: PASS
- duplicate event identity: none

## CI EXCEPTION

The original aggregate job in run 35332026520 failed after all 8 immutable shard artifacts had passed because the aggregate environment omitted the Python requests dependency. The failure occurred before scientific aggregation. Completion run 35333801258 downloaded those exact immutable shard artifacts, installed requests, and ran the unchanged aggregate code. No on-chain acquisition or scientific rule was repeated or changed.

## FIREWALL

BTC market data opened: false
BTC returns computed: false
Regression/bootstrap/PnL: false
2025 accessed: false
2026 accessed: false
Live trading / exchange mutation / wallet access / main merge: false

## RELEASE

This PASS releases only the prospectively frozen 2023-2024 AAVE-CREDIT-STRESS-001 regression Discovery. It does not authorize 2025, PnL or live trading.
