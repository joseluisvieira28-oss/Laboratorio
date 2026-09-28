# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — EXPLORER REST TRANSPORT RETRY V0.1.3

Date: 2026-09-27
Status: TECHNICAL RETRY ONLY / SCIENCE UNCHANGED

Reason:
- V0.1 reconstructed the 999-event corpus but Blockscout JSON-RPC rate-limited most receipt calls.
- V0.1.2 batch RPC preserved the corpus but public RPC endpoints did not return usable historical tx/receipt pairs.
- V0.1.3 changes only the transport for the exact same frozen 64 transaction hashes.

Transport:
- transaction metadata: Blockscout explorer REST /api/v2/transactions/{hash}
- transaction logs: Blockscout explorer REST /api/v2/transactions/{hash}/logs
- bounded retry/backoff for HTTP 429/5xx
- pagination followed when the endpoint supplies next_page_params.

Scientific invariants remain unchanged:
- same Compound III USDC Comet;
- same 2023-2024 source corpus;
- exact 999 BuyCollateral parent canary;
- same SHA-256 deterministic first-64 unique transaction sample;
- same exact event decoding;
- same exact-amount Transfer-from-Comet recipient inference rule;
- same >=95% usable-transaction gate;
- same >=90% recipient-inference gate;
- same diagnostic-only onward-transfer measure;
- no prices, returns, PnL, funding or protected 2025 market outcomes.

Prior partial/technical receipts remain immutable.
