# PAYOFF fast-start evidence and scope

Existing BTC-CONVEX V0.2 had immediate 1h forward signals using historical indicator warmup. Source: `ops/btc-convex-v02-readonly-verdict-2026-10-09` and `PROSPECTIVE_SHADOW_V0.2_FIRST_SIGNAL_OPEN_POSITIONS_RECEIPT_2026-09-24_115343Z.md`.

The new PAYOFF comparison shall use earlier complete 1h bars **only for SMA200/RSI indicator initialization** if and only if those bars are traceable to data already permissible under the Parent V0.2 forward authority. **No 2026 sealed holdout content may be opened to fill missing warmup.** All PnL, positions, trade entries and evaluations must start after `2026-10-14T00:00:00Z`.

Fast-start code and source binding are NOT published yet. This document is an alternative frozen research protocol, not a changed version of the existing 200-new-hour experiment. If verified prior-source warmup is absent, source gate fails closed. We do not need to wait for economic conclusions to audit the source or compare known retrospective fees and risks.
