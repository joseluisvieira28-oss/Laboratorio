# CBBTC-ETH-MINT-BURN-FLOW-001 — RUNNER IMAGE REMEDIATION V0.1B

Frozen: 2026-09-27

Scope: GitHub Actions runner image only.

The source probe is pure Node.js + public Ethereum JSON-RPC and has no macOS-specific dependency.

Permitted technical change:
- move source-gate runner from macos-14 to ubuntu-22.04;
- keep Node 24;
- keep exact branch SHA checkout;
- keep source semantics, windows, token, topics, chunking and gates unchanged.

Concurrency remains cancel-in-progress=true so the newer technical retry supersedes the older queued source-gate attempt rather than creating concurrent scientific executions.

No scientific/promotion credit is attached to runner choice.
