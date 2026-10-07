# FOREX-MACRO-SHOCK-001 — EUR/ECB FORWARD SOURCE STATUS V0.2

Date: 2026-10-07

Parent historical verdict remains: `SOURCE_BLOCKED` for historical Development/OOS. No historical rescue or backfill was performed.

V0.2 source freeze commit: `68e2deb269c3021e6ced4a1ee5ef75d8991295a3`.

Outcome-blind public source probe workflow run `37637954029` completed SUCCESS. It confirmed: MEXC `EUR_USDT` public `push.kline` with exchange timestamp; Binance Spot `EURUSDT` public best bid/ask stream; ECB monetary-policy decisions page HTTP 200; ECB Governing Council calendar HTTP 200. The probe printed no market prices and calculated no basis, return or PnL.

ECB first-seen watcher: `research/forex_macro_shock/ecb_first_seen_watcher_v02.py`. Trigger-driven workflow: `.github/workflows/forex-ecb-first-seen-v02.yml`. The watcher is restricted to 2026-10-29, records the first observed official decision URL/body hash and explicitly does not treat the scheduled clock as T0.

Protected event: 2026-10-29. Official ECB policy decisions are scheduled for 14:15 Europe/Berlin (13:15 UTC on that date); the press conference at 14:45 local is a separate mechanism.

Current verdict: `FORWARD_SOURCE_PROBE_PASS__WATCHER_ARMED`.

This is not an economic edge verdict and not trading authorization. Before any 2026-10-29 market outcome is opened, a separate immutable economic-signal freeze must define the dislocation formula, calibration procedure, threshold, holding horizon, execution model, fees/spread/slippage, missingness rules and PASS/FAIL gates.

No orders, private endpoints, account reads, wallets, trading, main merge, consensus fabrication or post-outcome tuning.
