# EVENT10M V0.5 EXACT PUBLIC PAYOUT → FIRST NEXT INDEX SOURCE — FINAL CLOSEOUT
Date 2026-10-30. **SOURCE GATE PASS / ZERO FORECASTS / ZERO MARKET OUTCOMES / NO TRADING EDGE.**

## Source evidence
- Pre-market source freeze committed SHA `51c72e783f8512d6f6b4a62aa8d68bfbdc434a2d`, strictly before workflow run.
- Public read-only GitHub CI [#41043647870](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41043647870), job 124022271264, completed success; artifact ID 12972185384, artifact zip sha256 `ef5cbe1eb5c0659e0befc1d1f9469a8cb93b039305427a344958dd923ca8b6b0`.
- Fresh unauthenticated browser passively captured a **page-generated** 7,082-byte valid HTTP200 product detail JSON from `https://www.mexc.com/api/platform/futures/api/v1/event_contract/detail` at UTC ms **1793357440799**; raw public response SHA256 `e2d3a341e6692a8505cbc22cf645b67389de394359e8583a6f2b8013da8138c1`. The collector did NOT actively request bundle-marked needLogin:true detail.
- Exact captured BTC_USDT: contractId 10, state ONLINE, MINUTE=10 upPayRate=0.80 and downPayRate=0.80, break-even 55.5556% each. Exact captured ETH_USDT: contractId 11, state ONLINE, MINUTE=10 upPayRate=0.80 and downPayRate=0.80, break-even 55.5556% each.
- FIRST MEXC public index tick **after complete source response receipt** arrived BTC **4546.609ms**, ETH **276.828ms**; both within pre-frozen <=5000ms. Bounded same-run public BTC/ETH streams overlapped 99.83s. Valid public Binance USD-M aggTrades BTC 1745, ETH 1201; MEXC public index ticks BTC 74, ETH 84.
- MEXC public app JSON pings sent 6, pongs received 6. No stream errors, no browser errors, no account or order, no private route, no September 2026 holdout, no NVIDIA or main branch write.
- Source identity BSC: Binance USD-M **perpetual trade** prices are not the actual MEXC Event Futures composite index and do not provide equivalent execution prices.

## Crucial dynamic payout discovery
Earlier independent public 2026-10-29 run #40930880041 observed **BTC 10m q=0.70 and ETH q=0.80** in both directions at its observation times; V0.5 observed BTC 0.80 and ETH 0.80 at its later snapshot. This is DIRECT proof across independent public snapshots that qBTC is not constant over history. Do NOT treat a q from one snapshot as effective in another decision or revive historical price-proxy trading PnL. Event Futures payout is fixed for a particular order at actual submission (according to MEXC FAQ), but dynamic beforehand.

## What this PASS does NOT establish
It does NOT demonstrate any 10-minute directional model, calibrated p(UP), exact Event Futures server-assigned actual executed openPrice, true venue expiry index, payout actually executed at exact server acceptance, cost or order availability, independent notarized source custody, human Telegram delivery and action latency, or positive expected value. No Event Futures API trading supported per public official documentation.
The ordinary Event Futures MEXC index public websocket itself was repaired by JSON application-level ping in previous PR #297 (one 180s successful source window), but this 100s test does not establish 30day collection reliability.

## Verdict and authorization
**PAYOUT_FIRST_INDEX_SOURCE_PASS** for both BTC/ETH; source plumbing READY for a separate preregistered prospective SHADOW mechanic test. NO live trading, no strategy promotion, no post-outcome fitting, no capital. PR #275 probability authority remains MODEL_NOT_FROZEN/SOURCE_GATE_REQUIRED. Per that study, genuine promotion requires independent model, as-of custody, 30 calendar days + >=150 non-overlapping resolved forward outcomes per symbol/horizon, matched baselines, calibrated p, Holm and block uncertainty, cost proof and (for manual signals) human latency measurements. The separate V0.6 pre-outcome smoke PR #299 is engineering only and CANNOT be construed as an approved model.
