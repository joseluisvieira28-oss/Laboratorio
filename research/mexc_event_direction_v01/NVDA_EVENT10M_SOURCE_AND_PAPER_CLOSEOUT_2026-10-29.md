# CRYPTO LAB — NVIDIA STOCK CASH REFERENCE → MEXC EVENT FUTURES 10M
## Source recovery, pre-forward freeze, hard gates — 29 October 2026

**Final status: HISTORICAL_CASH_SOURCE_PASS + LIMITED_LIVE_SOURCE_FRESHNESS_PASS + SYNTHETIC_MODEL_GUARDS_PASS / NO REAL FORECAST / NO EDGE CERTIFIED / NO LIVE GO.**

### Existing hypotheses — NOT resurrected
- Prior NVIDIA CASHOPEN V0.2 using external Binance/Bitget synthetic NVDA futures consensus, 2m/5m/15m/30m, ended NO_NVIDIA_CASHOPEN_DISCOVERY_CANDIDATE_AT_FROZEN_V02_GATE. Must remain shut; moving a threshold or horizon to 10m is not new evidence.
- Prior NVIDIA regular-session LEAD-LAG V0.5 1-minute discovery had 64/92 = 69.5652% winners, gross signed +3.75875bps, Holm adjusted discovery survivor ONLY. Standard MEXC API fee authority 12/14/16bps round trip blocked that traditional Futures execution. The v0.6 exact 1-minute forward is sealed Oct 5–30 and must NOT be evaluated before Oct31; this project did not open it.
- The 1-minute historical win rate does NOT transfer to a 10-minute binary payout contract.

### V0.1 Historical cash-equity reference source — PASS
[GitHub run #40901805025](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40901805025), artifact 12908583690, sha256:3ce27cd3fdf398cec8279248172ec2e99fe24a9f6020519c08839bf827c4021b, HEAD c98daaeabc5c7a0f27a652e1f09ef65e9dcd2c9b.
- Historical dates **2026-10-01 and 2026-10-02**, both already opened prior NVIDIA Discovery, not independent.
- Yahoo Finance *unofficial* NVDA cash stock public 1-minute (not proprietary NBBO or verified exchange primary quote): **45/45 valid, unique bars for each day 13:30–14:15 UTC**. Response raw sha256 ca03381c6565dc2f6261934dfd0c1e2e6f68a94c2c2a73a13184d224d3f381d6.
- MEXC standard Futures NVIDIA_USDT INDEX 1-minute **61/61 valid bars per date** in 13:20–14:20 UTC; response hashes Oct1 29ceeb520a35d1eb1eb466971b2ccaa0ff29f00b487d5011d5694130a7f9466b and Oct2 8bba503d615abcfd4315917c729e1ed6f6a431d5df4aad7083a3085239f78cd0.
- No stock-index target returns, correlations, PnL, forecast, profitability or price parity tested.

### V0.2 Single as-of freshness smoke — PASS (n=1)
[Run #40902171897](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40902171897), artifact 12908868364, sha256:5de14cd9e83b57d6881e30b68bb217eaa75c8e30f2768dd3dc3ef8367935c3cd.
- Captured 2026-10-29T15:30:05Z = 11:30:05 EDT. Both Yahoo stock and MEXC public INDEX had **last completed minute closed five seconds earlier**, under 120sec frozen gate.
- Yahoo returned Nasdaq NMS (nonofficial source); metadata did NOT specify a verified guaranteed publication delay, so **no independent primary-market custody or microsecond event-time parity claimed**. 5s is *bar close to HTTP acquisition*, not trade-print latency or exchange-side origin timestamp.

### V0.3 Four-sample live as-of clock quality — PASS (n=4)
[Run #40902529055](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40902529055), artifact 12908759197, sha256:07f935bae0d46fcac66ca8fb7fd2432bb70395c6708673f3901646a228429760.
- Four source-only captures in one live NY regular session, 20 seconds apart. Both Yahoo cash and MEXC INDEX freshest **completed 1m candle age** = **10s / 31s / 51s / 12s** (both matched each sample).
- At least two unique complete minute IDs observed; no source/freshness failure and no price returns or trading outcomes computed. Demonstrates a *short* functioning public historical/near-real-time acquisition path, not persistent 20-session availability or true exchange-custody proof.

### Pre-outcome paper forecast protocol (NOV 2026), NOT ACTIVATED
Code freeze: NVDA_EVENT10M_PAPER_FORWARD_FREEZE_V01.md; deterministic evaluator nvda_event10m_forecast_v01.py; synthetic tests test_nvda_event10m_forecast_v01.py.
[GitHub synthetic run #40902920256](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40902920256), **9 tests passed**, including abstention, causal lookahead rejection, stale source and payout rejection, NY holiday and schedule, exact 10m label, direction UP/DOWN fixtures. Synthetic guard PASS is NOT signal or market outcome performance.

Frozen separate *actual-stock-reference* causal feature: last 3 completed 1-minute price changes of Yahoo NVDA cash versus MEXC NVIDIA index, before the decision. Cash impulse >=10bps, same-direction lagged index >=5bps behind cash; otherwise ABSTAIN. Follow the cash sign only. Decision slots 09:35–11:25 NY in 10-minute strides during Nov 2–Nov 30 weekday sessions, Thanksgiving Nov26 excluded. Nasdaq officially lists Thanksgiving closed and Nov27 early close at 1PM; this protocol stops 11:25, so does not overlap early close.
- Require exact contemporaneous product **10m payout observed per side**, ONLINE state, public Event Futures index quote captured within 2s, source receipts and SHA before decision, no lookahead.
- Benchmark cash-only follow, always UP and always DOWN on matched decisions. Collect ALL eligible slots and abstentions; do not tune after outcomes. Frozen prospective batch >=60 resolved non-tie candidates, >=15 distinct signal sessions, lower CI and economic EV gates after multiplicity protection and additional calibration/real execution-price parity.
- **No ingestion/scheduling/outcome collector was created**. The Python module is an offline read-only *decision evaluator*, NOT an active pilot or live agent; no future automatic execution may be inferred from frozen study dates.
- Funding, event orders, account, API private calls, wallets, prices, capital, main merge: NONE. Protected September and old NVDA V0.6 Oct05–30 forward remained unopened.
- Actual Event Futures order openPrice, server settlement equivalence to public MEXC standard index open, payout at decision and independent real market reference custody remain UNSOLVED. Absent these => fail closed, no Event Futures edge claim.

### Final scientific verdict
**SOURCE_FEASIBILITY_PASS, SIGNAL_ECONOMICS_UNTESTED.** 0 actual Event Futures forecasts, 0 payouts scored, 0 trades or orders. The old premarket cash-open mechanism remains statistically rejected; the new post-open actual-NASDAQ stock source is a distinct data leg with an untested 10-minute event-conditioned hypothesis.
Next meaningful step: acquire immutable actual Event Futures product payout+index price snapshots at decision and expiry, and a prospectively timestamped actual NVDA cash reference. Only after Oct30 V0.6 window closes and after source parity passes may independent paper signal/outcome collection begin. All work in research PR draft; main untouched.

### Independent source descriptions
- Nasdaq official hours/holidays https://www.nasdaq.com/market-activity/stock-market-holiday-schedule
- MEXC Event Futures price settlement https://www.mexc.com/support/futures-trading/event-futures
- Yahoo source is undocumented as-of; exact request URLs and hashes are in receipts.
