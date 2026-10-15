# Crypto Lab V12 — EXACTLY TEN fishing lanes, final expansion

**Historical-science only — signals, not orders.**

The existing three V07 alerts and three V11 experimental alerts stay untouched on the operator's Windows PC. This V12 package adds exactly four additional **separately labeled experimental** LONG signal monitors:

| V12 lane | Symbol | Interval | Historical 2023–2025 modeled BASE / STRESS |
|---|---|---|---|
| BNB_CONVEX_NATIVE_5M_EXPERIMENTAL | BNB_USDT | 5m | +17.5568% / +15.9200% |
| SOL_CONVEX_30M_EXPERIMENTAL | SOL_USDT | 30m | +24.67% / +22.50% |
| BNB_CONVEX_15M_EXPERIMENTAL | BNB_USDT | 15m | +11.04% / +10.49% |
| DOGE_CONVEX_4H_EXPERIMENTAL | DOGE_USDT | 4h | +15.66% / +15.26% |

Backtests are on historical 2023–2025 Binance USD-M 5m, paper 10,000 USDT each, assumed 8bps taker fee per side + 2bps/5bps modeled slip plus archived funding settlement **proxy**. Not real MEXC transactions or statistically independent OOS edge. DOGE's historical positive return depends strongly on top 3 winners; BNB 5m is substantially less efficient than BNB 4h. SOL and BNB timeframes are highly related and **not independent trades**.

## Exact cap (frozen)
- V07: SOL native5m, SOL1h, BNB4h (3)
- V11: SOL4h, BNB30m, ETH1h (3)
- V12: BNB native5m, SOL30m, BNB15m, DOGE4h (4)
- **10 total. No other lanes permitted in this implementation.**

## How it works
- Public Binance USD-M REST 5m candles, including DOGE, hashed original V5 parent functions.
- Complete close-time validation and activation boundary; no replay or prediction.
- Separate V12 cache, per-instance OS lock, persistent SQLite de-dup and outbox.
- Signals older than 180 seconds are **suppressed, not sent as stale trade opportunities**; a crash after Telegram acknowledgment but before durable update can result in a duplicate notification.
- Uses the existing V07 DPAPI **Telegram only**, never any MEXC secrets or private account/order APIs. Telegram **sendMessage** outbound only.
- A separate Windows Scheduled Task named `CryptoLab-CONVEX-V12-FinalFour-ReadOnly`; V07/V11 tasks and SQLite unchanged.

## Installation only after CI PASS
1. Download GitHub Actions artifact `CONVEX_V12_FINAL_TEN_WINDOWS_NOT_INSTALLED` from workflow; extract the artifact ZIP and its enclosed ZIP if applicable.
2. In PowerShell in the folder containing `INSTALAR_V12.ps1`, use:
   `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\\INSTALAR_V12.ps1"`
3. Confirm with `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\\ESTADO_V12.ps1"`
4. To disable **only V12**: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\\PARAR_V12.ps1"`.

The installer checks V07 and V11 task presence, V12 absence (fails closed rather than duplicate installation), package SHA256, and pre-existing Telegram DPAPI files. It does **not** change existing tasks or merge main.

The task's RUN_V12.ps1 unseals only the Telegram DPAPI token under the same Windows user; never paste secrets in chat. A first full public feed warmup may take longer than subsequent cycles.

## Acceptance criteria
- CI tests both OS; Windows PyInstaller smoke-executable `--help` and SHA256 manifest.
- Windows `V12_STATUS.json`: status V12_EXPERIMENTAL_READONLY, sources_ok true, new_lanes 4, total_inventory 10, orders_enabled false, recent UTC. A PASS is **NOT** proof of actual market signal delivery or economic edge.
- Real Telegram delivery only proved if genuine signal recorded in immutable outbox with ACK and checked by operator in Telegram; no forced/fake signal on production.
- NO MEXC orders, no MEXC reads, no wallets, no main merge; no auto-promote historically cherry-picked models.

Source: `audits/CONVEX_V5_8ALT_NATIVE_5M_COMMON_2023_25_CLOSEOUT_2026_10_13.md` on branch `audit/convex-8alt-native-5m-results-2026-10-13` and `audits/CONVEX_8ALT_4TF_COMMON_2023_25_FINAL_CLOSEOUT_2026_10_13.md` on branch `research/convex-sol1h-bnb4h-economic-source-gates-2026-10-13`.
