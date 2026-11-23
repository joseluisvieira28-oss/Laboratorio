# BINANCE-DIAMANTE-004 — ABSORPTION-RESILIENCE SPOT PROSPECTIVE PILOT (NO TRADES)

**Scientific freeze dated 2026-11-23; frozen BEFORE the first BINANCE-004 public-source observation.**
**GitHub branch:** `research/binance-diamante-004-absorption-forward-20261123`, stacked on the read-only BINANCE-003 branch, never merged to main without separate approval.

## Objective / identity
Independent experiment `BINANCE-004-SELL-AGGRESSION-BID-RESILIENCE-V01`: Can a strongly sell-initiated 30-second interval, when the quoted bid-side liquidity persists and the midpoint resists the selling, precede a **positive 60-second long-Spot net price return**, relative to flow-only controls and zero-trade? This is **NOT** the rejected 2025 BTC 10min spot-vs-perp flow study (#313). No futures, cross-venue predictions, macro events or altered legacy thresholds.

**Prior evidence** (NOT Discovery): BINANCE-003 PR #374 succeeded in one independent 45s source/replay capture, but its outcomes were never examined to select this rule. No fitting on that capture. New timestamps only.

## Prospective one-shot data capture
- One anonymous public Binance Spot combined WS, exactly BTCUSDT, ETHUSDT, SOLUSDT, channels `@depth@100ms` and `@aggTrade`; fixed `wss://data-stream.binance.vision` endpoint. Exactly one initial public REST book `limit=1000` per asset from `data-api.binance.vision`. 3 GETs maximum; **no retry, reconnect, credential, private endpoint, payment or geographic bypass**.
- Single **480-second post-bridge** capture, followed by immediate close; a source-only failed capture is reported as blocked, not replaced by cherry-picked data. Up to 40,000 WS frames / 50 MB original journal; one SHA256, arrival wall-clock ns, monotonic ns and tamper-evident chain for every frame and REST snapshot.
- Source must reconcile all U/u intervals into three local books with zero uncovered sequence gaps, zero crosses and valid as-of clocks. Use only information available to a collector when each event arrives; neither the vendor's event clock alone nor future updates can determine past state. Temporal source-age bounds: `E` and `aggTrade.T` must be at most 3s old upon receipt, never >1s in the future; mark entire interval invalid on violation; no retrospective source repair.
- No historical depth backfilling; never silently use 003 pilot raw bytes, 2025 BTC10m returns, CPI/NFP holdouts, or 2026 frozen prospective outcomes.

## Frozen event rule (exact; NO post-hoc choices)
- Start time `T0` = monotonic collector arrival time of the third completed and gap-safe REST snapshot bridge. All three books **SYNCED** before opening observations.
- Split time into non-overlapping `30-second` collector-arrival intervals `[T0+30k,T0+30(k+1))`. For each symbol use only previous frames received within that exact interval and the final local book state timestamped strictly before the boundary. A message that first arrives after the boundary is NEVER used to decide that earlier interval.
- Minimum total quote notional of aggregated trades **5,000 USDT** in the interval; aggressive-sell share **>=65%**. Trade side: Binance `m=true` (buyer was maker) => sell-initiated. Aggregates are not independent individual orders.
- `bid_depth_10bps` = sum `price × quantity` at bid price levels from `mid×(1-0.001)` up to `mid`, based on each available local book. Book depth is a **visible 1000-level+diff proxy only**.
- **Resilience proxy:** `depth_end / depth_start >= 0.80`; midpoint displacement `(mid_end/mid_start-1)×10000 >= -3 bps`; both start and end depth positive, start and end book readings fresh within **2 seconds** of interval start/end; and minimum 1 valid depth frame in the interval. This is **NOT direct identification of absorption, canceling orders or maker identity**.
- **Primary signal** = sell-flow threshold AND resilience proxy; LONG hypothetical Spot. **Flow-only control** = same sell-flow threshold but fails either resilience criterion, still long counterfactual, not selected after returns.
- **Baseline** = unconditional long hypothetical on every fourth fully valid 30s interval per symbol; the baseline may overlap a primary signal and is reported separately, not counted as independent.
- Each type of event has fixed **120-second cooldown per symbol per type**, with time from decision; NO rescue/re-tuning of events. Stop creating new decisions at `T0+360s`; hold capture to `T0+480s` so all 60s exits mature without future data beyond the captured session.
- Even when a required source check fails, preserve row as CENSORED/SOURCE_INVALID, never silently drop as an unfavorable outcome.

## Economic falsification (hypothetical, NO fills)
- Decision formed at end of 30s interval using only prior received messages; **entry** = first subsequent fresh depth update (not within prior interval), maximum 3-second delay; **exit** = first fresh depth update at or after `entry_monotonic+60s`, maximum 3s after target. Otherwise CENSORED.
- Marketable static-quoted 100-USDT **and** 1,000-USDT buy on ask depth at entry and sell EXACT acquired base on bid depth at exit; insufficient visible depth -> CENSORED. These quotes are **NOT actual fills**, order-book queue priority is unknowable; market may move between request and execution.
- Scenario BASE: 10 bps taker fee EACH leg plus **2 bps adverse slippage each leg**; STRESS: 10 bps fees + **5 bps adverse slippage each leg**. Fee proxy only, not account-verified (Swiss account eligibility and actual fees unknown). Calculate percent net as `(exit_quote×(1-fee-slip_exit))/(entry_quote×(1+fee+slip_entry))-1`. Also zero-cost gross price movement, no live or paper order.
- Do not claim profits from a single successful event or a CI PASS. **Primary economic GO requires at least 200 independent matured primary events across at least 20 UTC days**, positive mean net after stress and lower bound of day-cluster bootstrap 95% above zero; no excessive payoff concentration; benchmark relative to unconditional/no-trade and flow-only; follow with independent 2027 prospective replication. This 480s pilot necessarily cannot meet those gates and can only test source/candidate feasibility.

## Statistical safeguards and verdict
One pre-registered threshold family and two horizons? **Only ONE forecast horizon (60 seconds)**, LONG only, no stop/TP optimization, no alternative subgroups, symbols retained jointly (BTC/ETH/SOL), no protected period or selective winner promotion. Baseline and control prespecified above. No L2 "cancel detection" or maker-fill assumptions.
- `SOURCE_BLOCKED`: any transport, checksum, replay, chronology or gap problem.
- `SOURCE_PASS_ZERO_OR_SMALL_SAMPLE`: source/replay worked but sample cannot satisfy economic gate.
- `ECONOMIC_NO_EDGE` only if minimum prospective coverage satisfied and pre-registered gate rejects; never declare no-edge from 8 minutes.
- `LIVE_NO_GO` throughout pilot.

**Absolutely prohibited:** automatic exchange orders, test orders, API keys, paid endpoints, logging in, funds, deposits, wallets, leverage, futures, Render/Telegram/production changes, main merge, scheduling beyond this one shot or editing closed protocols. This study is limited to publicly visible feeds; personal Swiss Binance trading eligibility is untested.

Official sources: https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md ; https://www.binance.com/en/fee/trading .
