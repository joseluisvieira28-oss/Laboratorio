# EVENT-10M MU V0.4 — LOCKED TWO-DAY OPENING WINDOW DIAGNOSTIC
Date 2026-10-29, FROZEN BEFORE ANY DIRECTIONAL OUTCOMES.

Scientific signal rule, immutable from PR #285:
- Only MU Nasdaq 1-minute CLOSE and MEXC standard Futures MUSTOCK_USDT index 1-minute OPEN. Exclude NVIDIA (separate study), SPCX and screenshot MLIUSDT (identity unresolved).
- Exactly Oct26 and Oct27 2026, decisions at 09:40, 09:50, 10:00, 10:10, 10:20 America/New_York per day (10 non-overlapping decisions).
- MU sign = sign(CLOSE[t-3min] - CLOSE[t-5min]); MEXC sign = sign(INDEX_OPEN[t-3min] - INDEX_OPEN[t-5min]). On opposite nonzero signs, predict the MU sign. On agreement or zero: ABSTAIN. No other filter, weights, thresholds or fit. Features are completed source bars (minimum ~2min old).
- Match 3 diagnostic baselines on the SAME triggered decision instants: ALWAYS_UP, ALWAYS_DOWN and MEXC_MOMENTUM. Target is INDEX_OPEN[t+10min] - INDEX_OPEN[t] (not actual Event Futures contract entry/settle). Distinguish tie. Payoff q=0.80 or q=0.85 WIN, LOSS -1, tie 0; illustrative only and not historical MEXC direction/time-specific payout. No real PnL.
- Every scheduled slot accounted for. Preserve by-day evidence, all triggered event timestamps, baseline comparisons, missing/flat/agreement/trigger counts, original exact frozen scientific rule.

STRICT NEW source evidence before opening those historical price outcomes:
- Prior PR #286 V0.3 runs [40907599978] and [40907759684] were independent CI jobs with identical FULL opening minute fingerprints. They did NOT open any outcome. Query1 Yahoo MU 60 CLOSE bars: 2026-10-26 SHA256 d47ed00b747bc37f8e6b557d151496015b8f7b0776ca8e3476bf9a8bf04288d2; 2026-10-27 SHA256 95060301367034d6b33b9f5633d4a5779938cf5574c5eaa305640b74bf294528. MEXC MUSTOCK index 61 OPEN bars: 2026-10-26 SHA256 6d263827363061ccb8f30a08b32a4472874b5a021ad16f1278f01fd4006a43db; 2026-10-27 SHA256 3fc8f721b9028be5452d7583f99fdb0360ea42aeaad7c4f586c73ec3cdc205d6.
- Re-fetch same source scope in V0.4; reject mismatch of any of those per-day opening digest or <60 stock / <61 index bars, no substitution, no outcome. Do not retune/dynamically accept new hash. Old PR #285 failures remain documented as source drift, NOT retroactively PASS.

SCIENTIFIC STATUS:
- Four calendar dates were already inspected for earlier different hypotheses, including both Oct26/27; this is HISTORICAL DISCOVERY NOT independent OOS, cannot certify edge, regardless of measured accuracy.
- Historical Yahoo prices are unofficial, backfilled and DO NOT establish an as-of live collector latency; MEXC Futures index proxy != Event Futures entry or settle. Real Event Futures payout at decision unknown. N <= 10, any positive number is statistically weak.
- No new attempt to rescue if zero triggers or negative EV. Verdict after this pilot is purely descriptive; stop development for this historical pair; consider only a NEW forward sealed experiment with official time-of-availability proofs and actual Event Futures payoff/index semantics. No protected September, trading, real orders, account reads, API keys, money, main merge, or live activation.
