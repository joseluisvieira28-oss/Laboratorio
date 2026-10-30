# V0.6 PRE-RUN SOURCE-TIMING IMPLEMENTATION NOTE
2026-10-30, recorded BEFORE ANY V0.6 workflow, receipt, target or outcome. Scientific rule unchanged.

The negative-control/shock observer requires complete 15-second BEFORE-decision Binance price history at two as-of timestamps (t and t-15s). Browser payout capture can occur immediately after WebSocket startup (~3s in V0.5), so a completed 15s Binance feature would not exist yet and the intended ONE shadow observation could be falsely blocked due to cold start.

Therefore schedule browser initialization **22 seconds after simultaneous WebSocket listener startup**, within the originally frozen 655s bounded run. Source-causality rule unchanged: the only eligible decision is FIRST MEXC public index tick AFTER fresh payout body; max payout-to-index age 5s; last Binance trade<=5s, 15s history<=5s. No rule/threshold/asset/horizon, payout handling, benchmark, or price target was changed. No market outcomes observed, no production account or trade. This is a pre-first-run source warmup, not post-outcome tuning.

Reject a run if 22s warmup plus browser navigation causes insufficient 10m expiry drain within 655s, no extending horizon after market result. Test workflow must run under prior pre-outcome freeze and this note.
