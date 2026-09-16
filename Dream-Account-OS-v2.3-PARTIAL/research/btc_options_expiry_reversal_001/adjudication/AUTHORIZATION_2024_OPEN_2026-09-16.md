# BOER-V2-PATH2-2024-001 — Explicit protected-outcome authorization

Date: 2026-09-16

The user explicitly authorized execution of the frozen calendar-2024 independent replication after the V2 Path 2 freeze was completed.

Authorized scope only:
- open calendar-2024 BTCUSDT USD-M 1m price fields required by `V2_PATH2_REPLICATION_2024_FREEZE_V01.json`;
- execute the exact frozen Path 2 rule once;
- persist the result before interpretation.

Still forbidden:
- any signal/cost/timing/horizon/event change;
- any post-outcome rescue or subgroup selection;
- 2025 or 2026 market data;
- live trading, orders, alerts/webhooks, exchange mutation;
- merge to main or Render deployment.
