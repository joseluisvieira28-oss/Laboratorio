# AAVE-LIQUIDATION-OVERHANG-001 — DISCOVERY 2023 RESERVE-DECIMALS ELIGIBILITY REMEDIATION V0.1

Status: **FROZEN BEFORE DISCOVERY PREDICTOR / BEFORE LIQUIDATION OUTCOMES**
Date: **2026-09-18**

## Observed failure

Discovery run `35393804723` passed:
- preflight;
- canonical 2023 calendar;
- global/eMode/oracle replay.

Reserve shards then emitted `DISCOVERY_RECONSTRUCTION_FAILURE` before any health factor, overhang predictor or future liquidation outcome was opened.

Failed shard receipts consistently reported:

`missing reserve decimals`

for reserves whose canonical Aave V3 `init_block` is later than the frozen 2023 Discovery event ceiling.

Canonical 2023 Discovery calendar:
- first snapshot block: `16,530,248`;
- last snapshot block: `18,901,758`;
- 2023 event ceiling: `18,908,894`.

Every reserve named by the observed missing-decimals failures has:

`init_block > 18,908,894`.

Therefore those reserves did not yet exist as active Aave reserves in the frozen Discovery partition.

## Root cause

`discovery_reserve_shard_v01.py` correctly excludes a reserve from daily state targets and emitted rows whenever:

`init_block[reserve] > snapshot_block`.

However, the preliminary aToken `Initialized` / decimals census incorrectly required a decoded decimals value for **every reserve assigned to the shard**, including reserves initialized only after the entire 2023 Discovery ceiling.

This creates a false reconstruction failure for temporally ineligible future reserves.

## Frozen remediation

Change only decimals eligibility:

- a reserve requires aToken `Initialized` decimals in Discovery 2023 iff
  `init_block <= discovery_event_to_block`;
- reserves with `init_block > discovery_event_to_block` remain in the canonical 37-reserve master identity but are not required to have Discovery-period decimals and cannot contribute state, borrower rows, HF or overhang in 2023;
- all existing snapshot-level `init_block <= snapshot_block` guards remain unchanged.

No reserve active during 2023 is removed.
No reserve is added early.
No decimals value is inferred, copied, guessed or taken from present-day state.

## Scientific invariance

Unchanged:
- 37-reserve canonical master;
- 2023 date range and daily 00:00 UTC clock;
- borrower population rules;
- token-native replay;
- Aave ray arithmetic;
- oracle source;
- health-factor definition;
- 10% primary stress;
- overhang predictor;
- 24h liquidation outcome;
- sample gates;
- Spearman statistic;
- bootstrap;
- pass/fail gates;
- 2024 seal;
- 2025/2026 firewall.

No future liquidation outcome was opened before this remediation.

## Re-execution

A new workflow run must execute from a commit containing this remediation.

The failed run `35393804723` remains preserved as the technical diagnostic and must not be reclassified as scientific evidence.

If any active-2023 reserve still lacks decimals after this correction, fail closed with `DISCOVERY_RECONSTRUCTION_FAILURE`.
