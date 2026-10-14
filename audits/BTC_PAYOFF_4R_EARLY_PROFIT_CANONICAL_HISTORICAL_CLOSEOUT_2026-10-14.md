# BTC PAYOFF 4R — EARLY 50% PARTIAL at +1R — frozen historical diagnostic
2026-10-14 UTC. **SOURCE/PARENT CONTROL PASS, EARLY-HALF INCREMENTAL ECONOMICS WORSE THAN ORIGINAL PAYOFF IN BOTH FEE SCENARIOS, NO NEW OOS, NO LIVE GO.**

## Chronology / source identity
- Candidate queue signed before the tests, 4R PAYOFF child freeze committed BEFORE any new PAYOFF child outcome: `4d59e078ce83361de60968b703d406b0567e5109`, policy exactly operator-selected +1R/+50%/>=0.25R net cash remainder fee/funding-BE. NO threshold was revised after BTC-CONVEX, SOL or BNB results were observed.
- Original PAYOFF 4R comparator code pinned at `2e68dbce5705e4d285f6805933768878fb34dea1`, run original full public official Binance USD-M source 2020-02 through 2025-12: historical 1h prices+mark bars+funding rates, 51,864 bars, 6,483 funding records, original source SHA256 verified. Full original scientific signal and 4R margin stop/target unchanged (not a 40% BTC price move). One isolated 2x hypothetical notional/margin account of 10489.94 USDT starting equity per arm, entry next 1h OPEN, no venue fill or liquidation proof.
- Child tries 50% sell from next completed 1h CLOSE witnessing at least +1R price (approximately +4.84% price), exit at NEXT 1h OPEN if realized half after assumed taker fee/slippage and signed funding >=0.25 full modeled R_cash; unfilled half forfeited, not booked as profit. Remaining stop moves to cost+funding adjusted net BE after an additional completed 1h bar; never loosens. The unmodified original +40% nominal margin take profit, -10% nominal margin stop and 60-day deadline survive for remainder. Intrabar stop-first on double touch.
- Exact canonical [workflow run 38584120729](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38584120729) SUCCESS, original parent parity 111 closed and published economics, signed model and complete trade-leg artifact [11904641244](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38584120729/artifacts/11904641244). Original comparator regression + 9 additional synthetic PAYOFF tests and existing 47 others PASS (56 in total in standalone branch QA run 38583990310). Later automatic historical repeats disabled. Cash/fees/funding included at source modeled prices, not MEXC.

| 2020–25 model | PAYOFF ORIGINAL | EARLY+BE policy | Delta pp |
|---|---:|---:|---:|
| BASE cumulative closed equity return | **+28.3296%** | **+18.7332%** | **−9.5964** |
| STRESS cumulative closed equity return | **+26.3240%** | **+12.6206%** | **−13.7034** |
| BASE closed trades | 111 | 132 | +21 |
| BASE PF closed | 1.2765 | 1.2463 | −0.0302 |
| STRESS PF closed | 1.2560 | 1.1659 | −0.0901 |
| BASE 1h marked DD approximation | **−10.92%** from original PR #194 | **−9.806%** | modest improvement |
| Early 50% realized events | n/a | BASE 66; STRESS 65 | n/a |

One-dimensional conclusion: policy still produces positive historical modeled cumulative net, but reduces profits strongly versus frozen original 4R Parent; improvement to modeled drawdown modest. Losing winners by reducing size as trends progress is one plausible mechanism, but attribution to specific trades, success probabilities and full account execution are not independently proven. Better win rate, high partial count or smaller loss streak would NOT overturn relative net return.

## Exact scientific verdict
**EARLY_HALF_001 PAYOFF 4R historical incremental FAIL at original +1R 50%-exit parameters.** Do not rescue on original 2020–25 opened outcomes by trying +0.5/+1.5/+2R, 25%/75% partial, revised 4R target or post-hoc stop policy. No new OOS / no 2026 protected outcomes. Do not claim stop loss guarantees exact risk when slippage/gaps, liquidation mark differences and exchange outages exist. Ex ante preference for early realized cash is a risk comfort, not demonstrated optimal net alpha.

Source #194 Parent remains research-only, not a safe live execution engine. Next ordered BNB Launchpool / BTC->SOL liquidation cases lack a locked original strategy stop: **cannot honestly apply a '1R' exit yet**, because the invalidation stop is a strategy-specific input that must be defined and frozen rather than reverse-engineered from winning historic trades. Research their price-source and initial-stop feasibility first.
