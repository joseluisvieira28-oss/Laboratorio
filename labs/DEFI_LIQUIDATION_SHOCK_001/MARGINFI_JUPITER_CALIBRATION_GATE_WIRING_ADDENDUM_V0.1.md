# MARGINFI JUPITER CALIBRATION GATE WIRING ADDENDUM V0.1

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN BEFORE FIRST SWAP EVENT DECODE

The separate sharded membership workflow has 8 immutable shard artifacts.

The calibration workflow may recompute the already-frozen deterministic V0.2 merge from those exact
8 artifacts inside the calibration job.

Required order:
1. download the 8 shard artifacts from run 36546170744;
2. execute merge_marginfi_jupiter_route_shards_v0_2.py unchanged;
3. require MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS;
4. only then execute the frozen SwapEvent direction calibration.

If the merge step fails or does not produce MEMBERSHIP_PASS, SwapEvent decoding must not execute.

This is workflow wiring only. It does not change population, class membership, decoder, direction rule,
thresholds, or source semantics.
