# PAYOFF-FUNDING-NETSTOP-001 — PRE-OUTCOME CHILD FREEZE
Frozen 2026-10-13 | Science: NEW HYPOTHESIS, ZERO INDEPENDENT EVIDENCE | Trading authority: NONE

## Motivation
An already-open 2020–2025 historical 4R simulation has a 2021 loss of -19.515% of initial margin despite an intended -10% nominal margin stop. Accrued negative funding contributed -9.477% of initial margin. These are observed retrospective results: they CANNOT validate this new child.

## Fixed separate child specification
Keep the exact original BTC-CONVEX long-only confirmed-close signal, next-hour open entry, one position, 10% of current equity as hypothetical isolated margin, 2x leverage, fixed original 4R price target, unchanged BASE/STRESS cost definitions and 60-day expiry. Change only the price STOP calculation to reflect signed realized funding through the last completed settlement.

For entry fill E, quantity q>0, already-paid entry fee C_e, signed realized funding F (negative when long pays), initial margin M, hypothesized taker exit fee rate f and adverse exit slippage rate s, define raw price stop:

  X = (q*E + C_e - F - 0.10*M) / (q*(1-f)*(1-s))

At exactly X, assumed exit fill is X*(1-s). Cash PnL = q*(exit_fill-E) - C_e - q*exit_fill*f + F. Therefore, if executed exactly as assumed, planned loss on initial margin = -10%.

Use conservative frozen STRESS assumptions for the safety stop: exit fee f=0.001 and adverse exit slip s=0.0005. Entry fee cash remains the original scenario's actual amount; no double deduction. Funding F only updates when an actual past funding settlement is confirmed. A new stop becomes eligible only at the next causally available price observation, not before the settlement. When the price is already below the newly computed stop, classify and use the observed adverse market fill; NEVER pretend fill at a better stop.

## Risk boundaries and no false promises
This formula IS NOT a hard loss guarantee: funding and gaps may worsen between checks, real slippage can exceed 5bps, stop orders can fail, the market can liquidate at mark prices, trading constraints and outages exist.

The new stop changes future exit/reentry paths. Historic known 2020–2025 data CANNOT count as independent child-validation. No parameter sweeps, no historical equity optimization, and NO 2026 holdout opening. Any legitimate economic evaluation must use future data first admitted after the 2026-10-14 00:00 UTC boundary, after the frozen 200-hour fresh indicator warmup, without violating the existing 2026 holdout.

Run synthetic mathematics/causal safety tests now. Preserve the authoritative Parent and fixed PAYOFF-40-10-BTC-001 and ratio-sweep freezes untouched. No merge to main, no real orders, wallets, account reads, spending, Render mutation, live capital or private exchange endpoint.

Current classification: PREOUTCOME_HYPOTHESIS_FROZEN / ALGEBRA_PENDING_QA / FORWARD_UNOBSERVED / LIVE_NO_GO.
