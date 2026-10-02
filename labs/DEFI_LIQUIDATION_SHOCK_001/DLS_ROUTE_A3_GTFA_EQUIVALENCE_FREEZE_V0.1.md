# DLS ROUTE A3 — HELIUS gTFA EQUIVALENCE FREEZE V0.1

Date: 2026-10-02
Status: FROZEN SOURCE/TRANSPORT ONLY — PROTECTED 2025 MARKET OUTCOMES CLOSED
Branch: dls-field-enrichment-v01

## Purpose
Test whether Helius getTransactionsForAddress (gTFA) can replace the blocked SQD transport for
Protected-2025 source acquisition while preserving the already-validated canonical transaction semantics.

This is a transport equivalence probe only. It changes no scientific event, decoder, account role,
cluster rule, source role, strategy, cost, timing or holdout gate.

## Preconditions
- DLS Route A2 archival pair recovery run 36900517788:
  - FOUR_CLASS_ARCHIVAL_PAIRED_EVIDENCE_PASS
  - ALTERNATIVE_SOURCE_EQUIVALENCE_PASS
- exact frozen references remain unchanged:
  - save0c: slot 110526981 / signature 3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V
  - save11: slot 278496102 / signature WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L
  - marginfi: slot 177590210 / signature 2aW2TWwxxzTTFixuYnvaA2NpentUDu6vCLxPjkvYBJWcrmB9TcRYu63uAswCrAjHJt7VXZxYUBaJsp3SGH3zNBmK
  - kamino: slot 230572965 / signature 2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv

## Authorized gTFA request
For each exact frozen reference only:
- address = frozen program ID
- transactionDetails = full
- sortOrder = asc
- limit <= 100
- filters.slot.gte = exact frozen slot
- filters.slot.lte = exact frozen slot
- filters.status = succeeded

No 2025 request is authorized by this probe.

## Mandatory equivalence
PASS requires for all 4 frozen references:
1. exact signature found exactly once;
2. exact slot;
3. explicit successful transaction;
4. canonical RAW normalizer accepts payload;
5. frozen protocol match is unique at the frozen instruction;
6. canonical shape PASS;
7. normalized RAW fidelity equals the already-pinned A2 Helius getTransaction RAW for the same signature;
8. Save11 canonical unit metadata equals the A2 RAW semantics;
9. zero decoder/source conflicts.

## Classification
PASS:
ROUTE_A3_GTFA_EQUIVALENCE_PASS

BLOCKED:
ROUTE_A3_GTFA_EQUIVALENCE_BLOCKED

A capability/plan rejection is BLOCKED, not NO_EDGE. Do not purchase or upgrade anything.

## Downstream boundary
Only PASS permits a new source-only 2025 gTFA acquisition workflow.
Protected 2025 market prices, returns, PnL and direction remain closed.
No 2026 acquisition.
No main merge.
No trading/orders/wallet/exchange mutation.
Trading authority: NONE.
