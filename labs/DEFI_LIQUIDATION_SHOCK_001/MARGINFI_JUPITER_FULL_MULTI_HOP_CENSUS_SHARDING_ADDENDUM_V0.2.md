# MARGINFI JUPITER FULL MULTI-HOP CENSUS SHARDING ADDENDUM V0.2

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN BEFORE V0.2 CALIBRATION RESULT

Parent:
MARGINFI_JUPITER_FULL_MULTI_HOP_SIGNED_FLOW_CENSUS_FREEZE_V0.2.md

Purpose:
operational sharding only. No source-semantic, population, threshold or direction rule changes.

Population:
every immutable Jan-2024 Marginfi+Jupiter membership PASS member.

Shard count:
16.

Deterministic assignment:
- compute the existing frozen rank hash
  SHA256(signature + "|" + canonical JSON instructionAddress);
- take the first 16 hex digits as an unsigned integer;
- shard_index = value mod 16.

Each member belongs to exactly one shard.
No source direction, token, amount, price or outcome field participates in assignment.

Each shard:
- uses the exact V0.2 multi-hop decoder and direction semantics;
- must adjudicate every assigned member into:
  DIRECTION_PROVEN,
  DIRECTION_AMBIGUOUS,
  SOURCE_EVIDENCE_INCOMPLETE,
  or CONTRADICTION;
- may not change thresholds or decoder rules.

Global merge requires:
- 16/16 shard receipts present;
- union member count equals membership receipt member_count;
- every member identity unique;
- duplicate count = 0;
- no member omitted.

Global PASS criteria remain exactly:
- non-incomplete evidence rate >= 95%;
- deterministic direction among non-incomplete >= 90%;
- contradictions = 0.

No market data, returns, PnL, 2025/2026 outcomes or trading are authorized.
