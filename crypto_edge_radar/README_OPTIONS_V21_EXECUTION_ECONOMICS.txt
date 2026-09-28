OPTIONS V2.1 — EXECUTION ECONOMICS EVIDENCE-HARDENED BUNDLE
Date: 2026-09-28

PURPOSE
This bundle preserves the frozen OPTIONS-SPOTPERP-001-V2.1 Futures-only execution contract and adds evidence capture / read-only execution-economics auditing.

IMPORTANT SAFETY
- Do NOT install/restart the executor while a live position is active.
- The audit executable itself is read-only and requires no API credentials.
- Building/downloading this bundle does not authorize a new trade.
- No science, signal, direction, 24h horizon, 1x isolated margin, 10 USDT cap, or no-chase rule is changed.
- Main branch is not touched.

READ-ONLY AUDIT
Run:
  windows\Audit_OPTIONS_V21_Execution_Economics.ps1

It scans:
  live_receipts\options_v21_futures

It writes:
  live_receipts\options_v21_futures\EXECUTION_ECONOMICS_TRUTH_GATE.json

The audit checks immutable signal identity, exact per-leg fee bps, funding, gross/net PnL normalized to entry notional, accounting identity, and entry/exit slippage diagnostics when BBO snapshots exist.

EVIDENCE HARDENING FOR FUTURE TRADES
The executor records PRE_ENTRY_MARKET_SNAPSHOT immediately before entry submit and PRE_EXIT_MARKET_SNAPSHOT before exit, plus entry/exit fill receipts. Capture is evidence-only and must never retime a frozen entry/exit.

INSTALLATION
Do not replace/restart the installed executor during ACTIVE_WAITING_EXIT or while MEXC reports any open OPTIONS V2.1 position/order. Wait for a fully reconciled idle state before changing the installed executable.
