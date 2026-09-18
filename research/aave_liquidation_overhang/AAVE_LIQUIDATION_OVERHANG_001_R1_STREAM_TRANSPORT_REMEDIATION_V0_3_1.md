# AAVE-LIQUIDATION-OVERHANG-001 — R1 STREAM TRANSPORT REMEDIATION V0.3.1

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE V0.3.1 EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Trigger

The already-frozen borrower-sharded R1 V0.3 execution run `35386365258` passed static preflight and canonical 16-borrower sample derivation.

Audit shard 1 then terminated with:

`RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`

Exact preserved transport exception:

`ChunkedEncodingError: Response ended prematurely`

The shard had already observed 1,360 Portal rows, 69 successful HTTP responses and one transient retry before the streaming response was truncated.

This is a source-transport interruption. It is not a reconstruction reconciliation verdict, provenance contradiction, economic result, health-factor result, liquidation-overhang result, or trading result.

## Scientific invariants

V0.3.1 changes only the handling of an interrupted HTTP response body while reading the exact same frozen Portal query window.

It MUST preserve exactly:

- frozen block envelope `16,490,000..21,525,890`;
- canonical 37-reserve R0 bootstrap;
- exact 16-borrower sample definition and V0.3 canonical-census derivation;
- four contiguous borrower shards of four borrowers each;
- audit blocks `17,748,972`, `19,007,945`, `20,266,917`, `21,525,890`;
- exact Mint/Burn/BalanceTransfer semantics;
- exact Aave ray arithmetic;
- exact 37-reserve token universe;
- exact Portal endpoint and query filters;
- exact independent archive-RPC set;
- minimum two usable RPC endpoints per target;
- exact agreement across usable RPC values;
- exact replay equality;
- no target, borrower, token or block dropping/replacement;
- all 2025/2026 and economic-outcome firewalls.

## Frozen transport retry rule

For each fixed Portal block window:

1. Submit the unchanged request body to the unchanged Portal endpoint.
2. Buffer the complete response window in memory before yielding any row to reconstruction state.
3. If response-body iteration raises a `requests.RequestException` (including `ChunkedEncodingError`, connection reset or read timeout), discard that incomplete window buffer.
4. Retry the exact same request body and exact same block boundaries.
5. Maximum response-body stream attempts per fixed window: **8**.
6. Backoff is deterministic: `min(20.0, 1.5 * 2**attempt)` seconds before the next stream attempt.
7. No alternate source, altered filter, altered block boundary, altered borrower partition or result-dependent scientific retry is permitted.
8. JSON/semantic/provenance errors are not converted into transport retries; they remain fail-closed.

Because an incomplete response window is never yielded, partial streamed state cannot contaminate or double-apply reconstruction deltas.

## Static transport QA before execution

Before V0.3.1 source execution, a deterministic synthetic test MUST prove:

- a first response that yields a valid prefix and then raises `ChunkedEncodingError` is discarded;
- the same window is retried;
- only the complete retry response is yielded;
- the stream retry counter is incremented exactly once;
- the frozen request boundaries remain unchanged.

## Execution lineage

The prior V0.3 run and its shard-1 technical failure remain immutable evidence.

V0.3.1 MUST execute as a new workflow lineage. It must not rewrite or relabel run `35386365258`.

Downstream R1 components remain gated exactly as before:

`R1_AUDIT_PASS`
→ global state + 8 reserve shards
→ canonical adjudication
→ only then `RECONSTRUCTION_DATA_PASS`.

## Hard firewalls

Still forbidden until `RECONSTRUCTION_DATA_PASS`:

- health factor;
- liquidation distance;
- liquidation overhang;
- adverse-shock threshold;
- future liquidation outcome;
- market prices/returns;
- PnL, PF, win rate, Sharpe, drawdown;
- scientific 2025/2026 data;
- live trading;
- orders;
- wallets;
- exchange mutation;
- alerts/webhooks;
- deployment of capital;
- merge to main.

Aggressiveness is permitted only in source engineering, deterministic retry, CI parallelization and reconstruction recovery. Scientific eligibility is unchanged.
