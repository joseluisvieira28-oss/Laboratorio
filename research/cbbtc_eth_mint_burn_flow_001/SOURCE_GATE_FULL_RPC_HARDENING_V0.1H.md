# CBBTC-ETH-MINT-BURN-FLOW-001 — SOURCE GATE FULL RPC HARDENING V0.1H

Frozen: 2026-09-27
Parent: FULL_CENSUS_RPC_TIMEOUT_REMEDIATION_V0.1G
Scope: TRANSPORT ONLY — Gate 1 source acquisition.

## Trigger

Canonical single-run #36286148021 was cancelled at the 240-minute job limit while the frozen Source Gate was still executing. No SOURCE_PASS/SOURCE_BLOCKED scientific gate verdict was reached and no downstream gate or market outcome was opened.

Static inspection found remaining unbounded RPC calls in Gate 1: current token identity calls and the historical eth_getCode check still used ethers provider calls without an explicit HTTP timeout. The source log transport also used 20,000-block outer chunks with long retry budgets, allowing provider stalls to consume the full runner budget before a gate verdict.

## V0.1H transport remediation

Science and source semantics are unchanged.

Transport-only changes:
- all Gate-1 JSON-RPC calls use explicit HTTP AbortSignal timeouts;
- current symbol/decimals checks use raw eth_call with ABI decoding instead of unbounded provider calls;
- historical eth_getCode uses bounded deterministic public/keyless RPC failover;
- timestamp-boundary headers retain deterministic public/keyless failover;
- eth_getLogs remains on the frozen primary PublicNode route;
- outer log chunk size is reduced from 20,000 to 2,000 blocks;
- per-range retry budget is reduced before exact midpoint splitting;
- progress logging is added; no event/count/value is skipped or sampled.

## Immutable scientific contract

UNCHANGED:
- official Ethereum cbBTC contract;
- ERC-20 Transfer zero-address mint/burn semantics;
- Window A and Window B timestamps;
- timestamp-derived exact block boundaries;
- exact log provenance fields;
- SOURCE_PASS criteria;
- no price outcomes;
- no 2026;
- no PnL;
- no live trading;
- no exchange/wallet mutation;
- no main merge;
- promotion credit = 0.

If this bounded transport completes with source_gate_evaluated=true and SOURCE_BLOCKED, the frozen governance decision tree applies and the exact Gate-1 path closes. If transport itself still cannot finish or returns an unevaluated receipt, the state remains technical/source transport blocked rather than NO_EDGE.
