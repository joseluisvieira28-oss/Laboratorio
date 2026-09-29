# CCLM-CCTP-SETTLED-FLOW-002 — 7-DAY SOURCE SCALE FREEZE V0.1

Frozen: 2026-09-24
Parent source semantics: CCLM_CCTP_SETTLED_FLOW_002_FREEZE_V0.1

The one-day 2023-08-20 destination-settlement smoke passed with 7 canonical
completed flows and zero semantic mismatches.

This scale test extends the same source-method fixture forward by six calendar
days only. It does not use any market outcome to choose the window.

Window:
2023-08-20T00:00:00Z through 2023-08-26T23:59:59Z

Routes and canonical completed-flow rules are unchanged:
- Ethereum -> Avalanche
- Avalanche -> Ethereum
- CCTP V1 native USDC only
- destination MessageReceived + same-transaction MintAndWithdraw
- exact source-domain, sender, burn token, mint token, recipient and amount
- no 2025/2026 access.

PASS:
- >=1 canonical completed flow;
- zero semantic mismatch among accepted events;
- both chain transports complete without unresolved technical failure.

This earns SOURCE scalability evidence only and ZERO predictive/promotion credit.
No market return, liquidity outcome, PnL or trading signal is opened.
