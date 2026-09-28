# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — SOURCE TRANSPORT BATCH RETRY V0.1.2

Date: 2026-09-27
Status: TECHNICAL RETRY ONLY / SCIENCE UNCHANGED

V0.1.2 is a second transport-only retry. It exists because V0.1 hit Blockscout HTTP 429 and V0.1.1 performs bounded sequential fallback calls that may be slow on public RPCs.

No scientific rule changes.

Frozen invariants:
- same 2023–2024 Comet corpus;
- exact 999 BuyCollateral canary;
- same SHA-256 deterministic first-64 transaction sample;
- same event decoding;
- same exact recipient inference rule;
- same >=95% usable transaction threshold;
- same >=90% recipient inference threshold;
- onward-transfer is diagnostic only;
- no market prices, returns, PnL or protected 2025 market outcomes.

Technical change only:
- request the exact frozen 64 transactions and receipts through a JSON-RPC batch;
- fall back across public Ethereum RPC endpoints if an endpoint does not return a usable batch.

Every previous receipt/run remains preserved.
