# DLS PROTECTED-2025 SOURCE CONSOLIDATION FREEZE V0.1

Date: 2026-10-02
Status: FROZEN TECHNICAL CONSOLIDATION / SOURCE ONLY
Branch: dls-field-enrichment-v01

## Purpose
Reuse already completed immutable Protected-2025 monthly source partitions from prior source-only runs before any new acquisition.

Authorized artifact runs:
- 36740555628
- 36733498831

Only artifacts named:
dls-protected-2025-source-v02-{protocol}-{month}

may enter.

## Rules
- protocol set exactly: marginfi, save0c, kamino, save11
- month set exactly 01..12
- receipt classification must equal PROTECTED_2025_PROTOCOL_SOURCE_PASS
- receipt protocol/month window/class must match the canonical V0.2 monthly manifest
- zero receipt errors and zero duplicates
- if more than one PASS receipt exists for the same protocol/month, their canonical scientific payload SHA256 must match exactly or consolidation FAILS CLOSED
- no BLOCKED/failed/cancelled receipt may substitute for PASS
- no new source call is made by consolidation
- no market data, price, return or PnL access

Output:
- immutable selected PASS manifest
- exact missing protocol/month partitions
- deterministic SHA256 over selected canonical payloads

Consolidation PASS does NOT mean Protected-2025 source authority PASS. It only defines what can be reused safely.

Trading authority: NONE.
