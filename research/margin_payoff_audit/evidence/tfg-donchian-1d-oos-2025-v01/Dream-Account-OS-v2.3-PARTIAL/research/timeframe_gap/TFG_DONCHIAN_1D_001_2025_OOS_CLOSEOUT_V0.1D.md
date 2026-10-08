# TFG-DONCHIAN-1D-001 — 2025 OOS Confirmation Closeout — V0.1D

## Status

**OOS_CONFIRMATION_SURVIVES_SHADOW_ELIGIBLE**

This closeout uses the frozen TFG-DONCHIAN-1D-001 rule with no post-outcome parameter changes. It does **not** authorize live trading.

## Frozen rule

- Universe: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT
- Side: long only
- Signal: daily close > maximum high of the prior 20 complete UTC daily bars
- ATR: Wilder ATR14
- Entry: next daily open
- Stop: signal low - 0.25 × ATR14
- Target: 3R
- Maximum hold: 40 daily bars, then next-open time exit
- One active position per symbol
- Same-bar stop/target ambiguity: stop first (conservative)
- BASE round-trip cost: 0.20%
- STRESS round-trip cost: 0.30%

## Source/data audit

Source delivery was prospectively rebound from the non-equivalent retrospective MEXC 1H API to official MEXC Spot bulk Min15 monthly files before OOS outcome evaluation.

Authoritative pre-outcome ZIP identities:

- `BTC_USDT-Min15-2025-05-01.zip` — SHA256 `005fd4b352082f7b8bfd667fdc5f0dbd3c2e3671a895a7b90d9bf026f901409e`
- `BNB_USDT-Min15-2025-12-01.zip` — SHA256 `f45b9babb8c5ac92d93fd2871a65e6f55786c875e03aa5773dacc680758d3a8d`
- `DOGE_USDT-Min15-2025-12-01.zip` — SHA256 `f7c19fc7965138e0453a50b558c1617c60d18f3eb2a0529d2741043410452d58`

Exact ordered 72-file manifest SHA256: `c3946f95fa81033d7566fe1114adb8f9c3ab5f076fb690caea2bb19d64762cbf`.

- Required 2025 Min15 files: 72/72
- Rows per symbol across the 12 MEXC bulk partitions: 35,040
- Internal 15m gaps per symbol: 0
- Duplicate timestamps per symbol: 0
- 2026 partition accessed: NO
- Live trading / orders / exchange mutation: NO

MEXC monthly bulk partitions use a UTC+08 boundary. Complete UTC daily bars were formed from adjacent monthly files. The available bytes provide complete UTC daily bars from 2024-12-01 through 2025-12-30 plus the raw 2025-12-31 00:00 UTC open. The special right-edge time-exit path was frozen before outcomes but was not used by any selected OOS trade.

A post-run clerical correction records that some manually serialized member-file SHA strings in the pre-outcome amendment were transcription errors. The three ZIP SHA256 identities were correctly frozen before outcomes and are the authoritative source identity; no source selection, rule, gate, or outcome changed.

## 2025 OOS result

### BASE — 0.20% round trip

- Selected / resolved trades: **40 / 40**
- Net expectancy: **+0.3510844126 R/trade**
- Profit factor: **1.5851406877**
- Win rate: **40.00%**
- Loss rate: **60.00%**
- Median: **-1.00 R**
- Total net R: **+14.0433765048 R**
- Target reach rate: **30.00%**
- Max single-symbol positive-R share: **30.7740%**
- Unresolved execution paths: **0**
- Exit reasons: STOP 24, TARGET 12, TIME_EXIT_NEXT_OPEN 4

Average positive trade: **+2.3777110315 R**. Average negative trade: **-1.0000000000 R**.

### STRESS — 0.30% round trip

- Net expectancy: **+0.3275204173 R/trade**
- Profit factor: **1.5458673621**
- Total net R: **+13.1008166916 R**

### Day-block bootstrap diagnostic

5,000 repetitions, seed 230911, UTC entry-day blocks:

- Point estimate: **+0.3510844126 R/trade**
- 95% interval: **[-0.4273483181, +1.1005416049] R/trade**
- Distinct entry days: 30

The bootstrap lower bound is negative. Under the frozen OOS confirmation protocol this bootstrap is diagnostic/reporting only, not a promotion gate. It is therefore a material uncertainty flag, not a post-hoc failure condition.

## Cross-asset robustness

BASE per-symbol results:

| Symbol | N | Mean net R | PF | Total R |
|---|---:|---:|---:|---:|
| BNBUSDT | 9 | +0.8563864667 | 2.9268695500 | +7.7074782000 |
| BTCUSDT | 7 | -0.0878724226 | 0.8769786084 | -0.6151069579 |
| DOGEUSDT | 5 | -0.2214108413 | 0.7232364484 | -1.1070542063 |
| ETHUSDT | 5 | +1.3056245009 | 7.5281225044 | +6.5281225044 |
| SOLUSDT | 8 | -0.0304555630 | 0.9593925827 | -0.2436445039 |
| XRPUSDT | 6 | +0.2955969114 | 1.4433953671 | +1.7735814684 |

All leave-one-asset-out portfolio means remain positive and all leave-one-asset-out PFs remain above 1.

## Temporal robustness

BASE quarter results:

| Quarter | N | Mean net R | PF | Total R |
|---|---:|---:|---:|---:|
| 2025-Q1 | 5 | -1.0000000000 | 0.0000 | -5.0000000000 |
| 2025-Q2 | 8 | +0.2149338930 | 1.4298677859 | +1.7194711437 |
| 2025-Q3 | 23 | +0.7579499668 | 2.4527374364 | +17.4328492367 |
| 2025-Q4 | 4 | -0.0272359689 | 0.9636853748 | -0.1089438756 |

This is clear temporal heterogeneity: the OOS year is positive overall, but the result is materially concentrated in Q3 and Q1 was poor. This does not violate a frozen OOS gate, but it is a key reason to require forward shadow rather than live capital.

## Frozen OOS decision gates

- Resolved trades >= 30: PASS (40)
- BASE expectancy > 0: PASS
- BASE PF > 1: PASS
- STRESS expectancy > 0: PASS
- STRESS PF > 1: PASS
- Max single-symbol positive-R share <= 70%: PASS (30.7740%)
- Unresolved execution paths = 0: PASS

Failed conditions: **NONE**.

## Decision

**OOS_CONFIRMATION_SURVIVES_SHADOW_ELIGIBLE**

Shadow eligibility: **YES**.

Live trading authorization: **NO**.

2026 historical outcome access: **NO**.

Post-outcome tuning: **NO**.

The next authorized step is a prospectively frozen forward-only shadow implementation of the exact unchanged 1D rule. Shadow results must not be used to retune this OOS record.

Local run receipt fingerprint: `3f70d649a77b2c8f1afd675acef55b75f200cace512417e98e8eae74375184a1`.

Local ledger fingerprint: `e8838e706cc7d1b0538282253d1aff3811182fb138f451a375b6c0ebef6fac9b`.
