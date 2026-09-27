# BNB-LAUNCHPOOL-DEMAND-001 — RED TEAM PHASE B CLOSEOUT V0.1

**Protocol freeze:** `c6a38ba84566eb7ed52da46c43a0606e43fac0d1`  
**Status:** EXECUTED ON CANONICAL HISTORICAL RAW / NO 2026 OUTCOMES OPENED  
**Red Phase B verdict:** **CHALLENGED — EVENT TIMING SIGNAL SURVIVES RANDOM PLACEBO, BUT PRE-EVENT EFFECT IS STRONGER**

## Integrity

The three original GitHub Actions market-source artifacts were recovered before this execution.

- Discovery artifact 10460668190: SHA256 `06ab4dee...28984dbf`; 27/27 Binance monthly archive CHECKSUMs verified.
- 2025 OOS artifact 10464554979: SHA256 `f777558a...8c575fcd`; 12/12 monthly CHECKSUMs verified.
- Pre-Discovery artifact 10467734255: SHA256 `51f7b09d...8b8980dd9`; 15/15 monthly CHECKSUMs verified.

The exact original 66 selected historical trades recomputed from those raw bytes at BASE20 to:

- mean = **+80.16394 bps/trade**
- PF = **1.67266**
- total = **+5290.81990 bps**

This exactly matches the preserved pooled ledger arithmetic.

## RT-004 — Random matched-time placebo

Frozen before execution:

- 10,000 replications;
- deterministic seed 20260927;
- same YYYY-MM;
- same UTC quarter-hour;
- actual date ±1 day excluded;
- entry and +24h exit required;
- one-active-trade overlap preserved.

Result:

- actual = **+80.164 bps/trade**
- placebo mean = **−4.292 bps/trade**
- placebo median = **−6.195 bps/trade**
- placebo 5th–95th percentile = **[−72.135, +69.478] bps**
- placebo >= actual = **3.17%**
- actual percentile = **96.83%**

**RT-004: PASS.** Random calendar timing matched by month and UTC clock does not reproduce the observed post-Launchpool effect.

This is adversarial diagnostic evidence, not new promotion credit.

## RT-005 — Fixed time-shift placebo

All six fixed offsets satisfied the pre-frozen >=90% coverage gate.

| Offset vs signal | N | BASE20 mean | PF |
|---|---:|---:|---:|
| −7d | 64 | −31.489 bps | 0.722 |
| −3d | 65 | −34.275 bps | 0.757 |
| **−1d** | **65** | **+221.024 bps** | **7.934** |
| +1d | 66 | +27.224 bps | 1.271 |
| +3d | 65 | −48.305 bps | 0.654 |
| +7d | 63 | +33.880 bps | 1.384 |

**RT-005: CHALLENGE.**

The striking result is `T−1d → T0`: the 24 hours immediately preceding the normal post-announcement entry clock show a substantially stronger positive BNBBTC effect than the frozen `T0 → T+1d` trade.

This does **not** prove leakage, informed trading or manipulation. It does mean the simplest causal story — “the public Launchpool announcement creates the subsequent BNB/BTC move” — is incomplete. Plausible explanations now include pre-positioning/anticipation, correlated regime effects, information diffusion before the official timestamp, or another pre-event mechanism.

No pre-event trading rule may be created from this result under the current candidate.

## RT-007 — Parameter perturbation

The four pre-frozen diagnostics all remained positive:

| Variant | N | BASE20 mean | PF |
|---|---:|---:|---:|
| Entry +15m | 66 | +67.082 | 1.595 |
| Entry +30m | 66 | +71.124 | 1.622 |
| Hold 12h | 66 | +52.693 | 1.661 |
| Hold 36h | 66 | +142.068 | 1.938 |

**RT-007: PASS.** The historical effect is not a narrow cliff at one exact 15m entry or exactly 24 hours.

These variants remain diagnostic only. The stronger 36h result cannot replace the frozen 24h rule.

## RT-017 — Volatility-matched placebo

The pre-frozen test required >=5 same-month/same-clock controls within ±20% of each event's pre-entry 24h realized volatility.

Twenty-two events failed that exact availability gate.

**RT-017: BLOCKED.**

Per the frozen protocol, the ±20% band is not widened after the result.

## Phase B interpretation

Phase B strengthens one part of the candidate and attacks another:

- **Against “random coincidence”: stronger.** Random matched timing rarely reaches the actual historical mean.
- **Against “parameter cliff”: stronger.** Small entry/holding perturbations remain positive.
- **Against “clean post-announcement causal shock”: weaker.** The −1d arm is substantially stronger than the actual post-announcement arm.
- **Against tail dependence:** the Phase A remove-best-5 failure remains unresolved and material.
- **Against volatility/regime explanation:** not closed; RT-017 remains BLOCKED.

Therefore the candidate is **not falsified**, but Red still returns **CHALLENGED**.

Existing V3 Tier-2 / Quase-Diamante classification is preserved. Diamond V0.2 remains unproven until its frozen prospective first-25 parent+causal gate matures and the remaining adversarial blockers are adjudicated.

No live trading, capital, order, exchange mutation, strategy change or main merge is authorized.
