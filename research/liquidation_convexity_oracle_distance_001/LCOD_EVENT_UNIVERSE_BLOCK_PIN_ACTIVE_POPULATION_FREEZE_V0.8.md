# LCOD EVENT-UNIVERSE SAME-BLOCK ACTIVE POPULATION V0.8 — FREEZE
Frozen: 2026-09-25
Stage: SOURCE / POPULATION COMPLETENESS
Outcomes: CLOSED

Authority: SQD SDK V0.5 passed with 17,282 Borrow events, 3,650 unique historical borrower×spoke pairs, contiguous coverage, truth fixture present and 100% current-MCP pair coverage. Same-block reconstruction passed 16/16 with max relative HF error 0.

Objective: derive the active debt-bearing population at one finalized Ethereum block N from Borrow history itself. Current-holder MCP is diagnostic only.

Construction: freeze N; split [24720899,N] into 16 contiguous chunks; stream the frozen 13-spoke Borrow event corpus with @subsquid/evm-stream@0.1.5; decode unique (spoke,user); call getUserAccountData(user) at blockTag=N; ACTIVE iff totalDebtValueRay>0; persist only SHA-256(pair), never raw wallets; aggregate/deduplicate active hashes.

PASS requires 16 complete contiguous chunks, zero decode errors, zero eth_call errors, truth fixture present, >=1 active pair, all account-state calls pinned to N, and no raw wallet in durable receipts.

No curve, liquidation outcome, market return, direction, PnL or trading execution is opened.