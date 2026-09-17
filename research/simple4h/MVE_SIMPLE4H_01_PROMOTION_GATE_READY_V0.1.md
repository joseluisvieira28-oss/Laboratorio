# MVE-SIMPLE4H-01 — PROMOTION GATE READY — V0.1

Date: 2026-09-17
Status: PROMOTION_GATE_READY / 2025 STILL LOCKED / OUTCOMES NOT OPENED
Repository: joseluisvieira28-oss/Laboratorio
Branch: simple4h-recovery-v0.2

## Executive decision
The historical SOURCE_RULE_RECOVERY_BLOCKED condition is resolved.
The exact original Simple Trading V0.1 source package and machine-readable results were recovered, byte-verified, and reconciled without opening protected 2025/2026 outcomes.

MVE-SIMPLE4H-01 is ready for an explicitly authorized, one-shot 2025 independent confirmation run after the remaining data-access authorization link is created against the final frozen branch HEAD and the official source manifest.

This document DOES NOT itself authorize opening 2025.
2026 remains locked.
No live trading or exchange mutation is authorized.

## 1. Contamination audit
Historical Discovery exposed: 2021-01-01 <= signal < 2025-01-01.
Historical OOS/confirmation for this MVE: none found.
2025 status for this MVE: UNTOUCHED based on the recovered canonical prep/closeout chain and current reconciliation.
2026 status: LOCKED / UNTOUCHED.

Checks performed before this gate:
- recovered historical closeout states 2025/2026 were not opened;
- canonical MVE prep states 2025 remained untouched;
- Drive reconciliation found no Simple4H 2025 outcome closeout;
- GitHub reconciliation found no pre-existing Simple4H branch, PR, or indexed commit before the new recovery branch was created;
- later Donchian/EMA/mean-reversion labs are separate hypotheses and are not used as authority or outcomes for this MVE.

If any previously unknown 2025 Simple4H outcome evidence is later discovered, STOP and re-adjudicate contamination before opening the protected cohort.

## 2. Recovered authority PASS
Original package ZIP SHA256:
`2bd1fa5170f2464445164caa7cf5f8b9df4808464cbd3aef30978f445771873e`

Original results ZIP SHA256:
`b23798fbe6b8f674be94014add8d2b00278cffdcf7889a01b2ec0917fd89134d`

Recovered event ledger: 32,243 completed historical trades/events.
Recovered primary summary: 36/36 cells.
Historical classifications remain immutable:
- 27 NEGATIVE_EXPECTANCY
- 9 NO_STATISTICAL_EDGE
- 0 SURVIVES_DISCOVERY

Authority preflight performed on recovered bytes:
- package ZIP hash: PASS
- package internal hashes: PASS
- results ZIP hash: PASS
- results internal hashes: PASS
- historical closeout identity: PASS
- 36-cell summary identity: PASS
- 32,243-event ledger identity: PASS
- recomputed N / NET10 mean / NET14 mean / NET10 win rate: 36/36 PASS
- protected 2025 read: NO
- protected 2026 read: NO

## 3. Frozen seven-cell replication family
All seven are frozen jointly. No post-outcome dropping or substitution is allowed.

### Donchian Breakout 4H
- BNBUSDT
- DOGEUSDT
- SOLUSDT
- XRPUSDT

### EMA Pullback 4H
- SOLUSDT
- DOGEUSDT

### Extreme Mean Reversion 4H
- DOGEUSDT

The historical seven-cell set is a hypothesis-generating cohort, not a retroactive set of survivors.

## 4. Frozen economic implementation
All entry/indicator/stop/target/time-exit semantics are inherited byte-for-byte from the recovered Simple Trading V0.1 authority.

Key invariants:
- timeframe: 4H only;
- bars: exactly 240 native 1m observations;
- no interpolation / forward fill;
- completed-bar signals only;
- entry: next-bar OPEN;
- one position active per cell;
- conservative stop-first ambiguous intrabar handling;
- Donchian: previous 20 bars, 2 ATR stop, 4R target, max 20 held bars;
- EMA Pullback: EMA20/EMA50, 1.5 ATR stop, 2R target, max 10 bars;
- Extreme MR: EMA20 +/- 2 ATR signal, 1.5 ATR stop, frozen EMA20 target, max 8 bars;
- BASE costs: 10 bps round trip;
- STRESS costs: 14 bps round trip;
- no maker rebates;
- no cost reduction rescue.

## 5. Protected confirmation cohort
Target cohort:
`2025-01-01T00:00:00Z <= signal < 2026-01-01T00:00:00Z`

Official source contract:
Binance public-data USD-M Futures monthly 1m kline ZIP archives plus adjacent `.CHECKSUM` sidecars.

Assets needed by the seven frozen cells:
- BNBUSDT
- DOGEUSDT
- SOLUSDT
- XRPUSDT

Source months:
- 2024-12: warm-up only
- 2025-01 through 2025-12: protected confirmation data
- 2026: forbidden

Boundary-state policy:
- cohort starts FLAT at 2025-01-01;
- 2024-12 may seed indicators only;
- no pre-2025 signal/position is inherited;
- signals whose deterministic maximum horizon/time-exit would require a 2026 bar are excluded prospectively before their outcome is evaluated.

## 6. Statistical and economic gates — prospectively frozen
The 2025 multiplicity family is exactly seven cells.
BH-FDR: 5% across the seven 2025 cell p-values.
Bootstrap: circular moving-block, 3,000 reps, block length 5, deterministic seed family.

Promotion-eligible sample floor remains N >= 100 per cell.
This floor is inherited from the parent lab and is not lowered because the confirmation cohort is only one year.

STRONG_CELL_PASS requires all:
1. N >= 100
2. mean NET10 > 0
3. mean NET14 > 0
4. BH-FDR q < 0.05
5. bootstrap lower-95% mean NET10 > 0
6. positive NET10 in at least 3 of 4 calendar quarters

Concentration red flags:
- largest winning trade > 25% of total positive NET10 bps; or
- largest positive quarter > 60% of total positive NET10 bps.

Family routing:
- TIER_2_PROMOTED_CANDIDATE: >=2 STRONG_CELL_PASS cells across >=2 strategy families, family median NET14 > 0, no concentration red flag on promoted cells.
- TIER_3_WATCHLIST: exactly 1 STRONG_CELL_PASS OR >=4/7 cells with N>=50 and positive NET14, if TIER_2 is not met.
- REJECTED_STONE: zero STRONG_CELL_PASS, >=5/7 cells with N>=100, median NET14 <= 0.
- NO_EDGE: zero STRONG_CELL_PASS, >=5/7 cells with N>=100, but REJECTED_STONE condition not met.
- INSUFFICIENT_SAMPLE: fewer than 5/7 cells reach N>=100 and neither TIER_2 nor TIER_3 is met.

QUASE_DIAMANTE is not automatic from a TIER_2 machine result. It additionally requires clean provenance, realistic costs, no fatal concentration and human scientific review confirming the 2025 cohort is valid independent OOS evidence.

## 7. Expected sample warning — known BEFORE holdout access
Using only 2021-2024 historical counts divided by four years gives rough annual planning counts:
- Donchian BNB: ~75
- Donchian DOGE: ~69
- Donchian SOL: ~76
- Donchian XRP: ~68
- EMA SOL: ~107
- EMA DOGE: ~112
- Extreme MR DOGE: ~77

This creates a material possibility that the 2025 run will be scientifically informative but insufficient for TIER_2 under the unchanged N>=100 gate.
If that happens, the correct result is INSUFFICIENT_SAMPLE or TIER_3 where the frozen criteria permit it — NOT a lowered sample threshold and NOT automatic NO_EDGE.

## 8. Implementation readiness
Prepared on branch `simple4h-recovery-v0.2`:
- prospective replication freeze;
- recovered authority hash manifest;
- authority-only fail-closed preflight;
- one-shot 2025 runner;
- one-shot decision receipt schema;
- inert GitHub Actions preflight that compiles and self-tests without protected data.

Local protected-data-free implementation checks:
- runner compile: PASS
- runner `--self-test`: PASS
- authority preflight against recovered package/results: PASS
- 2025 market data opened: NO
- 2026 market data opened: NO

## 9. Remaining authorization chain
Completed:
PREP DOCUMENT -> PROSPECTIVE FREEZE -> IMPLEMENTATION/PREFLIGHT PASS

Still required before protected outcomes:
1. Freeze exact final branch HEAD.
2. Acquire/verify the 2024-12 + 2025 official source archives and `.CHECKSUM` sidecars in SOURCE-ONLY mode, without running strategy outcomes.
3. Generate the source manifest SHA256.
4. Create explicit 2025-only authorization bound to BOTH the frozen branch HEAD and source manifest SHA256.
5. Execute exactly one confirmation run.
6. Machine closeout.
7. Human scientific review.

No rule, threshold, asset, cost, strategy or cell may change after this Promotion Gate.

## PROMOTION GATE VERDICT
`PROMOTION_GATE_READY`

Source-rule blocker: RESOLVED.
Protocol: FROZEN.
Implementation: PREFLIGHT PASS.
2025 outcomes: STILL UNOPENED.
2026: LOCKED.
Live trading: NOT AUTHORIZED.

Exact next safe action:
`SOURCE-ONLY 2025 COHORT ACQUISITION + CHECKSUM/MANIFEST GATE`

Do not execute economic outcomes until the explicit protected-data authorization file is bound to the final branch HEAD and verified source manifest.
