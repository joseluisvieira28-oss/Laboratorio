# CONVEX V11 — additional research-only signal lanes

Three **experimental** configurations: SOL 4H, BNB 30M and ETH 1H. Original pinned V5 signal function is reused; new lane/timeframe/symbol mapping is the only scientific scope. The three original V07 lanes stay unchanged.

- `experimental.py` exposes a pure signal function taking fully validated completed 5m bars, clock and activation bound, with no network, MEXC methods or Telegram credentials.
- It emits distinct signal IDs and explicit `EXPERIMENTAL_HISTORICAL_ONLY` labels; no filled trade or economic claim.
- `experimental_message` formats Telegram text clearly marked *not an order*.
- `test_experimental.py` covers scope, source continuity, bar closure, activation, message identity and classification.

## NOT DEPLOYED

This branch is a **source-code development increment**, not a Windows installer or an active Telegram monitor. V07 remains unchanged. Before live delivery, add a separate public ETH/SOL/BNB 5m source collector, closed-bar parity fixtures and a persistent outbox; perform end-to-end tests and package a separate read-only Windows executable. Avoid a second process touching V07 SQLite. No new lanes are delivered until separate test and operator-side rollout.

No trading orders, no signed controller, no MEXC private POST, no account mutation, no main merge. Historical 2023–25 positives are not independent OOS economic proof.
