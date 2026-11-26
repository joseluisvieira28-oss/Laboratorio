# 💎 LIQMAP-DIAMANTE-004 — INDEPENDENT ECONOMIC VERDICT
**26 November 2026 | SOURCE PASS | 8/8 TECH PASS | ECONOMIC NO-GO | ZERO REAL TRADING**

## Mission and evidence
Question: after **actually executed** Hyperliquid liquidation cascades, is a profitable next-4-hour continuation or reversal trade predictable after realistic costs, and better than simple MOM4? This is NOT a map of still-open liquidation levels, is NOT Neuron/Coinglass's algorithm and is a different experiment from LIQMAP003.

- Draft PR #402: https://github.com/joseluisvieira28-oss/Laboratorio/pull/402
- Frozen BEFORE source-outcome study: research/liqmap-diamante-004/PROTOCOL.md commit b4c1ed1477cba96651a48e466236972e9d9dd645
- Official source: Ironflow (ironflow.sh) public Hugging Face Parquet, events (one row per liquidated position) https://huggingface.co/datasets/ironflow/hyperliquid-liquidations and OHLCV https://huggingface.co/datasets/ironflow/hyperliquid-candles-1h. Same Hyperliquid BTC-PERP/ETH-PERP exchange source. No accounts, keys or subscriptions.
- July 1..Oct 31 2026 inclusive = **123 days**; eight ORIGINAL Parquet files (4 months x two datasets), all bytes SHA256 checked against Hugging Face LFS OID and sizes, UTC GET receipts in archived inventory and result JSON.
- Source study verified GitHub Actions **SUCCESS** 8/8 causal tests: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45791367216
- Artifact https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45791367216/artifacts/15101969762 — ZIP SHA256 **822dfc686cdacfb58349406eb8bdb508315ce7db2165df37360b841f4c933255**.
- Complete price coverage **2,952 contiguous 1h bars per asset**, no gaps, no duplicated prices, BTC 248,855 original liquidated positions; ETH 67,275; total **316,130**. Event exact-time/position-side/notional fields validated.
- Original candidate extreme hours: BTC 140 / ETH 143; 4h forced non-overlap excluded BTC 40 / ETH 43; **100 non-overlapping per asset**, 200 total (*not* independent across BTC and ETH). 14d lagged 95th percentile, >=3 real liquidations, >=65% one-sided notional, computed ONLY before next-hour open. 0 ambiguous/neutral in the filtered candidates.

## Economic outcomes (4 FULL hours after completed cascade)
Prices: hypothetical entry OPEN t+1, exit CLOSE t+4. Result below is mean nominal directional price exposure per event, not fill-based trade return. Costs: F bps/side fees +5bps/side slippage, 2-sided. Stress: 10,35,80,100bps fees/side. Funding, financing, order book spread, actual trade slippage, trader liquidation, margin/taxes, broken fills all not reconstructed.

| Asset | Hypothesis | Gross mean bps | After 10bps+5 slippage per side | After 80bps+5 slippage per side | Wins at 80bps | Price-direction MOM4 at 80bps |
|---|---|---:|---:|---:|---:|---:|
| BTC | Continuation | +3.945 | **−26.055 bps** | **−166.055 bps** | 6/100 | −165.464 bps |
| BTC | Reversal | −3.945 | −33.945 | −173.945 | 3/100 | −165.464 |
| ETH | Continuation | +9.138 | **−20.862** | **−160.862** | 7/100 | −160.240 |
| ETH | Reversal | −9.138 | −39.138 | −179.138 | 3/100 | −160.240 |

At 35bps+5/side, BTC continuation −76.055, ETH continuation −70.862; at 100bps+5, −206.055 and −200.862. **All fixed cost scenarios negative.**
The original fee stress of 80bps/side should **NOT** be claimed as actual Hyperliquid fee. Hyperliquid's official base Tier 0 perp taker schedule is 4.5bps/side as of official docs https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees. POST-RESULT sensitivity only: if hypothetical 4.5bps fee plus 5bps slippage/side then BTC continuation ~−15.055bps and ETH continuation ~−9.862bps, still negative. If zero slippage unrealistically, BTC continuation ~−5.055bps, ETH continuation ~+0.138bps, **less than MOM4 ETH +0.760bps**, and untested as real fills. This additional sensitivity is explicitly post hoc and does not modify frozen gates.

## Adversarial comparisons
- Paired vs MOM4 at 80bps: BTC continuation mean **−0.591bps**, ETH continuation **−0.622bps**. 97.5% temporal weekly bootstrap CIs: BTC **[−4.167,+3.117]bps**, ETH **[−1.871,0.000]bps** — no positive lower bound.
- Reversal v MOM4: BTC −8.481bps CI [−61.564,+41.518], ETH −18.898bps CI [−94.937,+48.605], neither shows an edge.
- Absolute continuation mean 97.5% weekly bootstrap CI at 80bps: BTC [−190.430,−140.713]bps, ETH [−194.303,−123.543]bps; upper bounds negative.
- Negative controls from PRECEDING non-cascade hours at same UTC hour and weekday with same trailing volatility half: matched BTC **75/100**, ETH **57/100** only, so incomplete and not randomized. Hypothetical continuation gross difference BTC +9.008bps CI [−26.653,+49.209], ETH +19.965bps CI [−25.301,+68.150]; both intervals include zero. Missing controls have not been invented.
- Four months JUL/AUG/SEP/OCT: NONE has mean 80bps stress net positive for continuation or reversal on either coin.
- Sequential **hypothetical** close-only portfolio MDD if reinvesting full NAV in every selected event: BTC continuation −81.35%, ETH continuation −80.47%; reversals −82.79% and −83.79%. Not intra-bar worst loss, actual fills or margin liquidation estimate.

## Gate pre-registered, final decision
- Technical/source gate: PASS (four complete months price, 316,130 real liquidated positions, verified original files, 8/8 tests).
- Sample gate: PASS (100 events per coin, 200 total).
- For *both assets*, same A or B must have positive average net returns after 80bps/side+5 slip, positive 97.5% bootstrap lower bound against zero and MOM4, >=3/4 profitable months and maxDD better than −30%. **Both A and B failed across assets**. No candidate passed.
- **SCIENTIFIC VERDICT: ECONOMIC_NO_GO_AFTER_COSTS** for both continuation and reversal under this frozen 4h extreme-liquidation trigger.
- **LIVE TRADING: NO-GO.** Cash benchmark at 0% avoids serial losses (ignores custody), no real trading performed.

## Scientific and economic limitations
1. Retrospective study, hypothesis formed after seeing parts of 2026 market, not genuinely independent prospective OOS; BTC/ETH episodes may overlap and are not 200 independent market regimes.
2. 1h bars cannot resolve microsecond first reaction: price may reverse 2–30 minutes after forced orders. **Do not optimise shorter horizons using this same 4month sample and claim independent proof**.
3. Price candle OPEN t+1 is a hypothetical idealized fill; no queue position, spread depth, latency, margin liquidation, funding or realized commissions. Actual results might differ, often worse.
4. Outlier notional episodes and negative average values do not prove all crypto liquidation strategies fail. These precise fixed hypotheses fail the pre-defined economic gate.
5. Public source dataset published and reconstructed after some historic months; hashes prove data integrity **now**, not immutability of exchange observations at the time. Side direction and timestamp come from Ironflow's recorded liquidation events.
6. Cross-venue transportability (Binance, Deribit, Bybit) not demonstrated and not to be inferred.
7. Existing LIQMAP002 prospective study is a separate *map of open positions*, not this cascade experiment. **Do not retune or alter the standing automation.**

## Operational result
The economically defensible next action is **CLOSE LIQMAP004 as NO-GO for trading**. Avoid writing a production bot, paying for extra data or adding more backtests with tuned parameters on the same 123 days. If a new hypothesis later emerges from independently sourced event microstructure, preregister separate truly fresh period, real executable depth and fees and capital limits first. No such additional experiment was launched.

**100% read-only. No trades, order APIs, subscriptions, payments, accounts, credentials, collateral, leverage, deployment or merges. PR remains DRAFT.**
