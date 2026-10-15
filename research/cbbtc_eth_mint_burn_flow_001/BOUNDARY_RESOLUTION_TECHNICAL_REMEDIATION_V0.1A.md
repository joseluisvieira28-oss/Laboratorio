# CBBTC-ETH-MINT-BURN-FLOW-001 — BOUNDARY RESOLUTION TECHNICAL REMEDIATION V0.1A

Frozen: 2026-09-27

Scope: RPC transport/retry only.

Observed source-gate runs terminate before any source window is appended with the unscoped ethers error:
`could not coalesce error`.

The current identity check passes:
- symbol = cbBTC
- decimals = 8

The historical-code check already has its own scoped error wrapper, while the timestamp→block binary search uses repeated `provider.getBlock()` calls without retry. Therefore this remediation targets only boundary resolution robustness.

UNCHANGED:
- token address;
- Ethereum network;
- source windows;
- timestamp boundaries;
- zero-address Transfer mint/burn definition;
- 20,000-block log chunking;
- mint/burn decode semantics;
- duplicate gate;
- SOURCE_PASS criteria;
- no outcomes/PnL/trading.

PERMITTED TECHNICAL CHANGES:
- wrap every boundary block lookup in bounded retry/backoff;
- retain exact first block whose timestamp is >= the frozen timestamp;
- add scoped error labels identifying latest/mid/final boundary lookup failures;
- small deterministic sleep between binary-search calls to avoid public RPC burst rejection.

No block/date substitution or scientific gate relaxation is allowed.
