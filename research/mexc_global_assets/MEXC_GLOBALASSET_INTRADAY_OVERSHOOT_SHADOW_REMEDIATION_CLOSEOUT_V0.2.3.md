# MEXC GLOBAL-ASSET INTRADAY OVERSHOOT — SHADOW REMEDIATION CLOSEOUT V0.2.3

Date: 2026-10-05  
Branch: `mexc-globalasset-intraday-overshoot-shadow-v0.2.3-remediation-2026-10-05`

## Authority

Scientific authority is unchanged:

- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_FREEZE_V0.2.md`
- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_AMENDMENT_V0.2.2.md`
- technical amendment `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_AMENDMENT_V0.2.3.md`

Historical classification remains:

`ROBUST_API_FEE_SURVIVOR`

with 143 admitted historical event baskets across 17 triggered days and frozen primary 16 bps fee-only mean net +4.0820 bps/day.

## Technical findings and corrections

V0.2.2 used `threading` and `ws_connect` at runtime without importing them. The previous self-test did not instantiate `BinanceKlineCache`, so compile-only coverage did not expose the defect.

V0.2.3:

- imports `threading`;
- imports `websockets.sync.client.connect` as `ws_connect`;
- instantiates the frozen 35-symbol Binance cache in self-test;
- verifies the official Binance market WebSocket namespace;
- preserves same-contract entry/exit invariant testing;
- preserves empty-sample underpowered behavior;
- binds the capture workflow to this remediation branch;
- installs `websockets` in the capture job;
- calls the V0.2.2 collector and V0.2.2 artifact path;
- uses a new trigger namespace `shadow_trigger_v023/**`.

GitHub Actions self-test run `37311076979` completed SUCCESS. The strengthened cache-instantiation step, compile step, fill invariant, empty prospective aggregate, Binance route probe and frozen transport proof all passed.

## Scientific invariance

No science changed. In particular:

- 35 frozen assets unchanged;
- MEXC / Binance / Bitget identities unchanged;
- 5m lookback unchanged;
- external leader dispersion <=10 bps unchanged;
- abs MEXC move >=40 bps unchanged;
- abs excess >=35 bps unchanged;
- FADE_MEXC_EXCESS unchanged;
- +5m exit unchanged;
- global cooldown 10m unchanged;
- scan window 13:35–19:55 UTC unchanged;
- 10/25/50/100 USDT notionals unchanged;
- 16 bps primary round-trip fee scenario unchanged;
- minimum >=30 admitted forward baskets and >=5 distinct session dates unchanged;
- PASS / FAIL / BLOCKED gates unchanged.

## Current forward state

No new economic forward outcome is claimed by this remediation.

Current scientific verdict:

`EXECUTION_SHADOW_UNDERPOWERED`

Reason: the frozen minimum prospective sample has not yet been accumulated.

The remediated collector is technically capture-ready, but a final execution-feasibility verdict requires future in-session observations. No retrospective backfill is authorized.

No orders, private endpoints, account reads, wallets, exchange mutation or live trading.
