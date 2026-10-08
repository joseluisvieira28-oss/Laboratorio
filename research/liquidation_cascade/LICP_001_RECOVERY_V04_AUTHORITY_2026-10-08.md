# LICP-001 technical recovery V04 — 2026-10-08

Frozen prospectively before this branch's first observation. Scientific parameters unchanged. Authority remains the five canonical documents; superseded policy and XALT-005 confer no authority.

V03 run 37733650222 succeeded operationally but rejected the complete baseline because two secondary records nest ignition under meta.btc_episode. Its current shard added zero records. Artifact 11534825512 digest: 1fa573388126a6270b71e92f6d65f4efd6ab8bb44ea3ccf2d86ec75785889f32. Its zero-episode cumulative ledger is incomplete and cannot replace baseline run 37311668666.

V04 restores that mandatory baseline and the V03 current shard. Deterministic legacy IDs use the identical config version, ignition venue timestamp and pressure tuple. Record conflict keys additionally include family and propagation asset; secondary records cannot conflict with their primary parent or count as extra primary episodes. Any rejected candidate receipt now blocks aggregation.

Recovery validated against the actual baseline JSON extracted from immutable job 111768312870 logs: eight records, six unique episode IDs, eight record keys, no rejection or conflict. First20=6, one UTC date (2026-10-05), FORWARD_INSUFFICIENT. No new returns or p-values calculated.

The first push-triggered V04 run on licp-canonical-continuation-2026-10-08 is the authorized continuation. It observes thirty real 600-second shards, records restart gaps, and never backfills outcomes. Existing cooldown, source separation, frozen trigger, BBO execution and first-20/date/coverage rules remain unchanged. Only its future primary records add evidence; unrelated concurrent transports are excluded. Repeating this workflow requires an explicit immutable predecessor restore update to preserve its receipts.

The authorized XALT-004 run 37733563875 remains separate and in progress at audit. No duplicate XALT observer is launched. Its restore step uses latest matching artifact without canonical run filtering; this is an unresolved future-restart integrity risk and must be corrected before another continuation.

Seven recovery/execution unit tests passed locally. Broader trigger tests encounter Windows NamedTemporaryFile sharing semantics; Ubuntu preflight runs the same trigger tests before observation. No configuration or outcome changes are authorized by a test failure.

No trading, exchange authentication/mutation, account reads, wallets, capital or main merge.
