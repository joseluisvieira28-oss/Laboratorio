# CROSS-VENUE-DIAMOND-REPLICATION-001 — SOURCE TRANSPORT REMEDIATION ADDENDUM — 2026-09-18

Status: FROZEN_TRANSPORT_REMEDIATION_ONLY

Observed Stage-A result before this addendum:
- workflow 35360881257 completed technically
- scientific source classification: SOURCE_DATA_BLOCKED
- Bybit requests returned HTTP 403 from the shared GitHub runner IP
- OKX requests intermittently returned HTTP 429 under concurrent shared-IP access
- no signal, return, PnL, expectancy, PF, bootstrap, or directional outcome was calculated

This is a non-scientific infrastructure/source-transport block, not evidence against DH-02-HO1.

Authorized remediation only:
1. remove concurrent venue probing and serialize source requests;
2. throttle shared-IP requests by 0.15 seconds plus retry backoff;
3. for Bybit, permit fallback between the two official mainnet REST hosts documented by Bybit: api.bybit.com and api.bytick.com;
4. preserve the exact same endpoint families, symbols, timestamps, timeframes, funding requirement, frozen 2023-2024 window, and metadata-only receipt.

Forbidden:
- alternate exchange
- spot substitution
- mark/index substitution
- asset deletion
- anchor deletion
- timeframe change
- outcome access
- 2025/2026 access
- rule/cost change
- post-outcome tuning
- live trading / orders / exchange mutation / main merge

The next source run supersedes the prior transport attempt for source-access classification only. The prior receipt remains immutable evidence of the initial transport failure.
