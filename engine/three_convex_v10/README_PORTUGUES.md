# CONVEX V10 — Telegram signals only (no orders)

This branch builds **only** on the existing V07 read-only Telegram operator. It is NOT an auto-trader, does not change the pinned V5 decision logic, and does not replace the already functioning Windows scheduled task.

## Already implemented in V07
- Three signal lanes: SOL_CONVEX_NATIVE_5M, SOL_CONVEX_1H, BNB_CONVEX_4H; LONG *candidate* on completed candles from Binance USD-M public OHLCV.
- Notifications explicitly say **SINAL DETETADO (NÃO É ORDEM)**; include lane, symbol, completed UTC close, signal ID. No execution price, stop or PnL is invented.
- SQLite outbox + deterministic signal ID avoids repeated event enqueue, with a rare duplicate Telegram message possible after ACK-before-commit crash.
- Both SOL lanes share one physical market; simultaneous lane collisions are signalled rather than presented as independently executable.
- MEXC authenticated GET-only observation is separate from signal determination. Telegram V07 already tested on operator Windows; **real future signal delivery not yet independently witnessed**.
- No automatic orders. Human makes independent discretionary choices.

## How to verify without reinstalling anything
Run this diagnostic in a PowerShell session on the SAME Windows account as the V07 task, from this branch:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\engine\three_convex_v10\VERIFICAR_SINAIS_V10.ps1
```

The diagnostic reads only V07 local task and status. It does not call Telegram, Binance or MEXC and does not require Python.

Interpretation:
- `SIGNAL_DELIVERY_READINESS: MONITOR_RUNNING_NOT_PROOF_OF_SIGNAL_DELIVERY` means V07 is running with recent public data and no queued Telegram messages. It **does not** establish that any new CONVEX signal has occurred or been delivered.
- `SIGNAL_DELIVERY_READINESS: INVESTIGATE` or exit code 2: stale state, failed source, unstarted task, or pending outbox. Do not interpret missing messages as zero signals.
- To prove a real signal, record the received Telegram alert (source close UTC, signal_id, lane) and compare with local V07 events database, without opening positions or changing task.

## Scientific limits
The original V5 source is pinned but V07 recent Binance REST feed parity against the historical canonical archive is not independently proved. No confirmed 2026 profitable forward results for minimum-lot MEXC execution; signal != recommendation/guarantee.

## Non-goals / invariants
Do not install a second Telegram polling consumer, request bot updates, modify existing V07 task, arm V06 order transport, change wallets or merge main. This branch does not deploy into the operator's local Windows installation remotely.
