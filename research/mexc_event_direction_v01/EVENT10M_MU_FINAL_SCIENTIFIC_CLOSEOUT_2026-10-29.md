# EVENT-10M MU V0.4 — FINAL ECONOMIC / SCIENTIFIC CLOSEOUT
Date 2026-10-29. **Research-only, historical discovery**, not a claim of tradeable MEXC Event Futures edge.

## Scope and evidence chain
- User requested NVIDIA exclusion; **NVIDIA not touched**. Only Micron stock MU Yahoo 1m CLOSE vs public standard MEXC Futures MUSTOCK_USDT INDEX Min1 OPEN. Screenshot MLIUSDT mapping remains UNPROVEN; SPCX excluded (no ordinary Nasdaq-listed underlying stock auction).
- PR #284 / run #40905532432 initial 40/40 matched 1m source window each day; PR #285 original Yahoo full-series drift blocked before any label.
- PR #286 independent source-only [runs #40907599978](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40907599978) and [#40907759684](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40907759684) proved identical exact 60 Yahoo CLOSE and 61 MEXC index OPEN minute values during each opening hour on Oct26 and Oct27. Their per-day frozen SHA256 are in EVENT10M_MU_SOURCE_FORENSICS_CLOSEOUT_2026-10-29.md. Full 780-row Yahoo history previously drifted and original changed minute(s) remain unknowable because only old hashes were saved. Two independent opening-window passes do NOT prove the stock quotes were available at historical decision times.
- V0.4 scientific rule was frozen before this branch's outcomes. [Run #40908190805](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40908190805) failed at first source-hash validation BEFORE labels because `...d16f...` was manually copied instead of the *source-only established* `...d16b...`. PRE-OUTCOME errata documented in EVENT10M_MU_V041_HASH_TRANSCRIPTION_ERRATA.md; no model, feature, decision time or threshold changed.
- Authoritative successful [run #40908386750](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40908386750), head f3b42b833a37c24da4aa954005c869f7635baf75, job 123569302479, artifact ID 12911149000, digest sha256:c7fe448a410dcfeca4cab2cea1103a2f5455017ff1f98164e845a471991af1c4. **Both frozen price-window hashes validated BEFORE outcome analysis.** No protected September 2026 data accessed.

## Frozen ten-minute diagnostic
Exactly five 10-minute separated decision instants per day (Oct26/27, 09:40,09:50,10:00,10:10,10:20 America/New_York). MU sign = sign(completed MU stock CLOSE[t-3m] - CLOSE[t-5m]); MEXC sign = sign(INDEX OPEN[t-3m] - OPEN[t-5m]). Only opposite nonzero signs -> forecast MU sign, otherwise ABSTAIN. Target is standard Futures INDEX OPEN[t+10m] relative to OPEN[t], **not** actual Event Futures server-assigned entry/settlement. Compare fixed ALWAYS_UP, ALWAYS_DOWN, INDEX_MOMENTUM on identical triggered timestamps. Hypothetical symmetric payouts q=.80,.85 are NOT historical product payouts. No param tuning.

**Gate and signal counts**
- 2026-10-26: five scheduled, **zero triggers**, all five agreement, zero source missing, zero flat.
- 2026-10-27: five scheduled, **four triggers**, one agreement, zero missing/flat.
- Aggregate: 10 scheduled, **4 eligible**, six abstained. All four eligible are from ONE day.

| Rule on the exact same 4 decisions | W | L | T | Accuracy | EV at illustrative 80% | EV at illustrative 85% |
|---|---:|---:|---:|---:|---:|---:|
| **MU cross-source sign** | 3 | 1 | 0 | **75%** | +0.3500 units/decision | +0.3875 units/decision |
| ALWAYS DOWN | 3 | 1 | 0 | **75%** | +0.3500 | +0.3875 |
| ALWAYS UP | 1 | 3 | 0 | 25% | -0.5500 | -0.5375 |
| MEXC INDEX MOMENTUM | 1 | 3 | 0 | 25% | -0.5500 | -0.5375 |

**Decision receipts (UTC)**
- 2026-10-27 13:40: MU UP, MEXC DOWN, MU signal LOSS, ALWAYS_DOWN WIN.
- 2026-10-27 14:00: MU DOWN, MEXC UP, MU signal WIN, ALWAYS_DOWN WIN.
- 2026-10-27 14:10: MU DOWN, MEXC UP, MU signal WIN, ALWAYS_DOWN WIN.
- 2026-10-27 14:20: MU UP, MEXC DOWN, MU signal WIN, ALWAYS_DOWN LOSS.

## Statistical and economic interpretation
- Payout 80% requires win probability > 1/1.8 = **55.5556%** to have positive theoretical EV assuming win +.8, loss -1, tie zero. A posterior observed 3/4 is NOT a reliable forecast of the underlying probability.
- Unadjusted exact one-sided binomial p-value at p0=55.5556% for at least 3 wins among 4 observations is **about 0.40009** (no multiplicity correction). The sample is drastically underpowered, all signals one day.
- MU did not outperform the trivial ALWAYS_DOWN benchmark in aggregate on the same four decisions. Its trades differ on two instants, but their net outcomes were identical. No independent incremental mechanism certified.
- Most crucial: Yahoo historical quotes carry **no as-of receive-time custody or verified provider latency**. MEXC standard futures INDEX OPEN(t) may NOT equal actual Event Futures contract trade openPrice/settlement, and contemporaneous actual side- and horizon-specific Event Futures payouts are unavailable in these historical dates. Therefore even the hypothetical +0.35 figure is **not an executable PnL, not an independently certified EV, and not a diamond**.
- Historical Oct26/27 price outcomes had been studied for earlier different families and are not an untouched holdout; no outcome integrity or independent forward certification.

## FINAL VERDICT AND ACTION
**TECHNICAL-SOURCE PASS (specific opening windows), FROZEN HISTORICAL PILOT PASS, INDEPENDENT ECONOMIC EDGE NOT CERTIFIED, NO LIVE GO.**

Stop re-running these old dates, rehashing until favorable, selecting only one profitable day, changing thresholds, or calling 3/4 a live signal. Preserve previous failures and scope. To genuinely revisit MU, open a **new forward-only preregistration** with independently timestamped as-of stock-market data (official/licensed or independently validated feed), contemporaneous MEXC Event Futures product availability and exact direction-dependent payout, as well as index/entry/expiry parity. Then accumulate independent days and evaluate calibrated probabilities and multiple-testing-adjusted EV. No further historical optimization on these two dates is justified.

No trading, orders, account reads, keys, money, private endpoints, NVIDIA research, SPCX, MLI alias, protected September holdout, merge or main changes.
