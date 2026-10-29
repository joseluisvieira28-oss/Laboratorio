# EVENT FUTURES DIRECTION LAB V0.1 — SOURCE-FIRST FREEZE

Date: 2026-10-29. Parent: mexc-event-futures-event-conditioned-v0.13-prereg-2026-10-03 at 3d8b0062068d5d7c3ce206a429007f8f04836aca.

**STATUS: SOURCE_GATE_REQUIRED / MODEL_NOT_FROZEN / RESEARCH_OUTCOMES_OPENED=0 / NO_EDGE / NO_LIVE**

## Narrow research identity
A new *prospective forecast probability-calibration + asymmetric payout admission* feasibility layer. NOT a resurrection of failed Event Futures technical V0.3.1, V0.4/V0.16, ETF-CME, Options V2.1, or V0.13 imported frozen signals. Do not reuse their tested cells/outcomes as a fresh experiment. Protected September 2026 historical holdout stays CLOSED.

## Sources and target
BTC_USDT, ETH_USDT; 10, 30 and 60 minutes. Reuse V0.13 shadow source semantics: public Event Futures detail payout at decision (up/down distinct, dynamic, raw hashed); first public MEXC push.index.price tick at/after payout response within 5s. At target + horizon, first valid index tick at/after target within 5s. Product must be ONLINE. No interpolated candles; no inferred historical payout. This SHADOW index is not proven identical to executed order openPrice.

## Candidate model authority: BLOCKED
No candidate predictor, causal features, calibrated probability model, feature source, training boundary or rule is presently activated. A separately timestamp-anchored immutable future freeze must approve ALL of those plus model hash, symbols, horizon, minimum sample, analysis batch, source integrity, benchmark and abstention logic before any target outcomes. The offline program cannot generate predictive signals. A manually invented p is not evidence.

## Deterministic admission rule only
For p=P(UP) and observed q_UP/q_DOWN:
EV_UP = p*q_UP - (1-p).
EV_DOWN = (1-p)*q_DOWN - p.
Abstain if both <=0; otherwise choose larger. Validate model+rule source hashes, source time <= decision time, freshness, no overlap per model/symbol/horizon. This is hypothetical EV dependent on model calibration; neither EV nor a synthetic unit win rate proves an edge.

## Predeclared downstream survival requirements (NOT implemented, NO PROMOTION)
After genuine source and model gates, first 30 calendar days as fixed prospective batch, >=150 independent resolved non-tie events per model-symbol-horizon cell. Score actual directional payout per event with V0.13 Monte Carlo null, 95% lower CI, Holm multiple comparison and positive chronological thirds. Require *additional* time-block robustness, calibration (Brier/log loss) and a paired incremental advantage against preregistered simple baselines before scientific promotion. Evaluation logic for those additional tests is not implemented, so this V0.1 can never itself claim a surviving edge.

## Evidence/custody limits
This module accepts normalized, self-reported receipts; local SHA256/timestamps alone cannot prove pre-outcome custody or price/order parity. An external trustworthy timestamp-anchor and fresh real public-source capture are prerequisites. Previous V0.11.6/V0.12/V0.12.1 source passes establish historical feasibility, not today's real-time service state. Zero actual captures or forecasts collected in this run.

## Operational prohibitions
NO API keys, private endpoint, logins, accounts/balances, orders, trades, wallets, paid source, auto-deploy, Render, protected history, main merge or target outcome peeking. No scheduled GitHub workflows are created. Existing V0.13 constraints remain authoritative.

**Next gate: fresh read-only source liveness + immutable point-in-time custody + prospective model/source feasibility; only after that, a new pre-outcome model activation freeze.**
