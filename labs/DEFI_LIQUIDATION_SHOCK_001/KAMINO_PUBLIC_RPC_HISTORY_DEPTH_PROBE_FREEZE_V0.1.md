# DEFI-LIQUIDATION-SHOCK-001 — KAMINO PUBLIC RPC HISTORY DEPTH PROBE V0.1

Date: 2026-09-22  
Status: FROZEN PRE-EXECUTION / SOURCE-TRANSPORT ONLY / OUTCOME-BLIND

Purpose: determine whether the official public Solana mainnet RPC can paginate Kamino program signatures far enough backward to cover the frozen source-supported boundary at 2023-11-17T13:25:35Z.

Fixed endpoint: https://api.mainnet-beta.solana.com  
Fixed method: getSignaturesForAddress  
Fixed address: KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD  
Starting cursor: immediately before already RAW-verified successful reference signature 37bfneBLcVoWnqWEoP7Y4EnJREUeaHeEYgnQ9kjBGpsN3tMjP2AceURMpbgQDeR8hmxZ4L5JVSokepJ7WhsuTDnK (2024-12-15T07:32:56Z).
Page size: 1000.
Maximum pages: 100.
Pagination direction: strictly backward via the final signature of each returned page.
Stop success condition: oldest returned blockTime <= 2023-11-17T13:25:35Z.
Stop blocker conditions: deterministic RPC history truncation/null page before boundary, repeated cursor, unrecoverable RPC error, or page limit exhausted before boundary.

This probe records signature/slot/blockTime/status metadata only. It does NOT fetch transactions, inspect instruction data, classify liquidation candidates, search market data, compute prices/returns/PnL, or grant a first-success boundary.

If the boundary becomes reachable, a separately frozen exhaustive decoder scan may be authorized using the exact enumerated signature interval. If not, the canonical BigQuery queue remains blocked on source transport.
