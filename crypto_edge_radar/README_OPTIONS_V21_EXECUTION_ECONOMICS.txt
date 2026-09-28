OPTIONS V2.1 — EXECUTION ECONOMICS EVIDENCE-HARDENED BUNDLE
Date: 2026-09-28

PURPOSE
This bundle preserves the frozen OPTIONS-SPOTPERP-001-V2.1 Futures-only execution contract and adds evidence capture / read-only execution-economics auditing.

READ-ONLY AUDIT — NO INSTALL REQUIRED
You can extract this bundle into a separate folder and run:
  windows\Audit_OPTIONS_V21_Execution_Economics.ps1

The script first tries to locate the currently installed executor through the Windows Scheduled Task:
  CryptoLab-OPTIONS-V21-Futures-AutoLive

It then audits that installation's:
  live_receipts\options_v21_futures

No API credentials are loaded. No order, cancel, leverage, margin, transfer, withdrawal, task restart, or exchange mutation occurs.

If automatic discovery is unavailable, run:
  windows\Audit_OPTIONS_V21_Execution_Economics.ps1 -ReceiptRoot "C:\path\to\current\live_receipts\options_v21_futures"

The audit writes:
  EXECUTION_ECONOMICS_TRUTH_GATE.json
inside the selected receipt root.

INSTALL / EXECUTOR REPLACEMENT SAFETY
- Do NOT install/restart/replace the executor while a live position or order is active.
- Building or running the read-only audit does not authorize a new trade.
- No science, signal, direction, 24h horizon, 1x isolated margin, 10 USDT cap, or no-chase rule is changed.

EVIDENCE HARDENING FOR FUTURE TRADES
The hardened executor records PRE_ENTRY_MARKET_SNAPSHOT immediately before entry submit and PRE_EXIT_MARKET_SNAPSHOT before exit, plus entry/exit fill receipts. Capture is evidence-only and must never retime the frozen entry/exit.

TRUTH-GATE ACCOUNTING
The auditor checks immutable signal identity, exact per-leg fee bps, funding, gross/net PnL normalized to entry notional, accounting identity, and entry/exit slippage diagnostics when BBO snapshots exist.

Ten complete attributable closed trades makes the execution-economics sample reviewable. It does not promote the strategy or authorize production.
