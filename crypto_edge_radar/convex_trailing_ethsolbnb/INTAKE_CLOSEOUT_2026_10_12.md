# RADAR CONVEX TRAILING ETH/SOL/BNB — INTAKE RESULT — 2026-10-12

**OPERATOR INTAKE COMMITTED / HISTORICAL TRAILING OUTPERFORMS 4R / RADAR PRODUCTION NOT DEPLOYED / AUTO-LIVE NO-GO.**

## Implemented
- Freeze first: commit `7e88c906dd5350238a2eb22f45f2d0bd32aefcc1`, before the new source probe.
- Isolated Radar branch: `radar/convex-trailing-ethsolbnb-intake-2026-10-12`, base `crypto-edge-radar-postgres-v0.5`. No main mutation, Render deploy or Windows executor change.
- Radar `deployment_registry_v1.json` contains `research_intake_candidates` candidate `BTC-CONVEX-PARENT-V5-NONLATCHED-TRAIL-ETHSOLBNB-001`. The seven canonical active motors and their authority/count remain **unchanged**. Intake queue ≠ operating eighth motor, capital authority, or 24/7 collection.
- `source_probe.py` derives from exact previously validated public MEXC causal source gateway (ETH/SOL/BNB fixed subset only); `exit_logic.py` implements original Parent V5 nonlatched trailing as a pure, stateless, no-order function. It does not manage real position ownership, account or exchange stops.
- 8 new synthetic source/exit tests PASS, 4 registry invariants PASS, compile PASS: canonical GitHub Actions run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38300183122 at checkout `39a8ef21cae5c3d6b00de7dd46047df019787178`. Workflow overall FAIL because the public source-probe all-size safety gate correctly FAIL-CLOSED. Raw observation artifact https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38300183122/artifacts/11769363704, uploaded ZIP SHA256 `6876fd307d3e7a68962c457fe0e4f4ebbf21037dfa25f6b1586627a51ee0ab28`.

## Actual 2026-10-12 19:49 UTC public MEXC evidence (NOT actual orders)
All three 1H candle/signal/contract/book requests were readable and causally parsed. All candidate signal flags **false**, using last COMPLETED 1h candle ending 19:00Z; capture was ~49.6–49.8 minutes after the boundary, so **NOT_SCORABLE_BOUNDARY** for all three; zero prospective trade credit.

- ETH_USDT: public book quote age 904ms; best ask 2517.47 USDT, contract size 0.01 ETH, minimum 1 contract = ~**25.1747 USDT** at this quote; nominal **25 USDT rounds down to 0 contracts: MIN_OR_MAX_LOT_BLOCKED**. The frozen all-25/50/100 sizes source gate fails for ETH; nominal 50 sample 1 contract PASS; nominal 100 sample 3 contracts PASS (75.5241 USDT actual). No signal.
- SOL_USDT: age 423ms; ask 108.23; contract size .1 SOL; min contract ~10.823 USDT; public 25/50/100 size scenarios PASS. No signal.
- BNB_USDT: age 382ms; ask 747; contract size .01 BNB; min contract ~7.47 USDT; public 25/50/100 PASS. No signal.
- Provider clock offset +146ms. This is a single source observation, NOT 24/7 source continuity, exact timely entry price, account fee, filled lot, exchange protection or a strategy result.
- Therefore `SOURCE_GATEWAY_BLOCKED_NO_TRADING` exact overall safety verdict with blocker `ETH_USDT:SIZE_OR_DEPTH`; root cause is **nominal-25 below min lot**, not missing ETH bars or stale depth. Do NOT lower or change the all-size gate post hoc. The observed feasibility of nominal-50 and -100 is descriptive, not a retroactive PASS.
- IMPORTANT: With purely hypothetical 500 USDT account and inherited Radar default 0.1% risk/trade, max $0.50 planned risk. A minimum ETH $25.1747 contract times fee-only 4%-stop modeled risk 0.041568 ≈ $1.0463 > $0.50; ETH not feasible at default per-trade risk. User's real current account equity/risk state NOT observed, so do not claim actual inability. MEXC account fee tier, slippage and gap risk can increase that loss. Do not authorize or increase risk just to make minimum lot.

## Promotion boundary
Historical frozen 2021–2025 first-basket trailing matched comparison: BASE +31.33%, STRESS +28.68%, PF 1.483/1.435, historical proxy and outcome-exposed. Actual forward usable MEXC signals/filled trades: **ZERO** in this new intake. SCIENTIFIC promotion to a new capital tier is NOT demonstrated by this historical same-family comparison, irrespective of operator nomination.
Current missing nontrivial pieces: continuously durable causal 1h public source/watcher with missed windows and idempotency; full deterministic Parent signal parity verification (RSI warmup, boundary cases); latest exact MEXC lot/price/source, authenticated read-only account equity/fee/risk/position owner, isolated/leverage/protective stops; authenticated executor with restart-safe stop and trail mutations; reconciled history of existing positions and duplicate prevention; separate explicit live execution/capital authority following rigorous account risk model, actual exchange-side protective stop.

Operator's trading intent is acknowledged but **no orders** were sent; no account/keys/private endpoints were accessed. No main merge, Render deploy, protected 2026 holdout opening or scientific post-outcome tuning. This is an actual branch-level Radar intake, NOT a claimed active production Radar motor or live trade GO.
