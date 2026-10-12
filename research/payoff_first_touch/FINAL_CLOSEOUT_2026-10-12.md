# PAYOFF-FIRST-TOUCH-RETRO-001 — CLOSEOUT V0.1 (2026-10-12)

**Decision: RETRO_PRICE_TOUCH_SURVIVES_AS_DESCRIPTION / ECONOMIC_4_TO_1_NOT_ESTABLISHED / NO_PROMOTION.**

## Verified provenance and execution

- Original PR #166 base commit: `98454c4516b69fae54526ed37600895f0b6063a9`; historical BTC-CONVEX seed hash as in pinned source manifest.
- Experiment branch: `research/payoff-first-touch-identifiability-2026-10-12`; protocol first frozen as `RETRO_FIRST_TOUCH_FROZEN_PROTOCOL_V0.1.md`, then 2019-only source coverage amendment `SOURCE_COVERAGE_AMENDMENT_001_2026-10-12.md` before the successfully read price paths.
- Completed run: [38269021214](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38269021214); workflow conclusion **success**; commit `a24a9591c435eff92d2917fbe779592c4b50e56f`.
- Artifact: `payoff-retro-001-frozen-source-receipts` #11755773347; artifact ZIP digest `sha256:44a2d9a48f570c09fc72a426da8661104f15eef7fd74581bec7e1af76479cda4`. Runner printed SHA256 `retro_verdict.json`: `1cde30028bd5ae450d266f4c1f8542e0e8049ddba3ec7626a479852d2c777b6a`, `retro_events.json`: `20ee665123663dc8575f66cd50addee52a6fb46c7ed031191214ac804`. Logs show 7/7 synthetic unit tests passed. This is not a CI-backed validation of realistic fills/liquidation.
- Data: Public **Binance USD-M futures BTCUSDT hourly archives** with SHA256 checksum comparison. No account, private API, order or wallet access. The official monthly source returned **404 for 2019-10** and 200 for probe dates 2020-01, 2021-01, 2024-01, 2025-01. Frozen fallback excludes all episodes entering before 2020-01-01. No 2026 candle acquisition.

## Frozen algebra (illustrative MEXC taker fee rate, NOT historical Pine venue)

M = initial margin, N=2M initial notional; taker fee 0.08% on each actual leg at 2x, constant position size, excluding funding/slippage:

`netPnL/M = 2*((1-0.0008)*x - 0.0016)`

Thus, **net +40% margin** corresponds to BTC price **+20.17614%**, and **net -10% margin** corresponds to BTC price **-4.84388%**, conditional on hypothetical exact fills and no other costs. Existing source Pine used commission 0.1%/side, 4% price stop, 12% peak trailing and non-latched +5% close activation. No alteration to that Parent's original trade logic.

## Adjudicated 1h original-entry price-path counts

Original normalized 1h seed: **100 closed, 1 open**. Exclusions: **5 closed 2026**, **1 open 2026**, **6 entries 2019 unsupported by the official archive**. Remaining **89 original-entry windows** during 2020–2025.

Under the two frozen bar inclusion interpretations (entry hour included vs next whole hour), BOTH emitted identical counts:

| Outcome through original historical exit (exclusive) | Count | Interpretation |
|---|---:|---|
| `TARGET_FIRST` | **18/89 = 20.2247%** | First recognized hourly high touches synthetic +40%-on-margin price barrier, before deeper hypothetical stop, within the original hold window |
| `STOP_FIRST` | **0/89** | None touched hypothetical -10%-on-margin price barrier before the original exit |
| `NEITHER_CENSORED` | **71/89 = 79.7753%** | Original source strategy exited before either hypothetical barrier was touched |
| `AMBIGUOUS_SAME_BAR` / gaps / missing path | **0 reported** | Not observed in accepted subset, but not a general guarantee of future ordering or fills |

**Critical asymmetry:** This is *not* 18 winning trades and 71 losing trades of a 4:1 system. The original strategy's -4% price stop is *tighter* than the hypothetical -4.84388% stop. Almost all normal losers therefore exit their original position before the deeper hypothetical barrier can be tested. For 71 censored cases, a counterfactual system holding longer would change position inventory, future signals, cash availability, stop-first frequency and funding duration; unknown outcomes cannot be set to -10% or 0. Hence **no win rate, expectation, profit factor, drawdown, ruin probability or 4:1 net strategy PnL can be inferred** from this exercise.

**Venue/price mismatch:** **7/89** source ledger entry prices differ by more than 1% from the corresponding Binance hourly *open*, and require timestamp/venue/entry-fill reconciliation. This count does not quantify every venue basis or confirm whether any candidate target is impacted. BTC hourly `high/low` is not a MEXC fill price or mark liquidation path. A stop order does not guarantee fill, and mark-price liquidation can occur before stop execution. The archive being checksum-valid certifies bytes/source, not executable economics.

Comparison: Previous PR #166 showed 5/100 closed exits >=40% in original fee-only export and 11/100 with a 2x algebraic threshold; the new 18/89 is a **different metric** (interim intratrade barrier, restricted source coverage), not a validated uplift. It must not be cherry-picked as improvement.

## Binary scientific / economic verdict

- **Descriptive market observation: YES**, 18 original-entry historical windows touched the illustrative price barrier first within their source holding period, with source checksums and deterministic rules.
- **Proof that a pre-registered 4:1 payout strategy has net edge: NO.** 71 censorings, no complete costs or counterpart execution/portfolio accounting, retrospective known entries, 7 source-entry divergences, selection dependence and missing forward/OOS evidence.
- **Viable 2x/5x/10x/20x live leverage: NOT ESTABLISHED** by this run; no sizing or liquidation research with authenticated account data.
- **NO_EDGE for BTC-CONVEX Parent: NOT IMPLIED.** Original Parent SURVIVES/FAIL closeouts across assets preserved intact; source seed has lookahead-correction and distinct prior authority.
- **Promotion, micro-live, main merge and activation: NO.**

**Next legitimate science:** resolve the 7 price timestamp divergences and append historical execution constraints only as clearly labeled retrospective diagnostics. A genuinely new 4:1 system demands a new identifier, parameter freeze *before* an untouched forward horizon, causal signal/exit sequencing, complete taker fees, funding, slippage, mark-based liquidation, margin maintenance, lot constraints, capital availability and independently registered checkpoints. Existing 2020–2025 BTC seed episodes and the 2026 previously seen outcomes are **not untouched evidence**. Do not loosen gate or substitute hypothetical success for economic edge.

This closeout is a **finite verifiable verdict** for the historical first-touch mission, not a promise to revisit until a more favorable outcome appears.
