# V2.5 source-only compression budget diagnostic (research proposal)

## Status and independence
OFFLINE_DIAGNOSTIC_ONLY / NO_SOURCE_RUN / NO_ECONOMICS / NO_LIVE_GO.

This is an **isolated candidate fix** for the bug documented in original V2.4.
It does **not** modify frozen V2.4 files or their original failure receipts.
There is no authorization to run a new 2-hour source study, change the
original 7200s scientific gate, open outcomes, trade, or merge to main.

## Original defect: exact evidence

Frozen V2.4 protocol allows at most 64 MiB **compressed** and 256 MiB
**uncompressed**, but the unchanged V2.2 collector stopped on:

`if uncompressed > 256*1024**2 or f.tell() > 64*1024**2:`

where `f=gzip.open(raw,"xb",compresslevel=4)`.

On `gzip.GzipFile`, `f.tell()` returns the **logical uncompressed input
position**, not compressed bytes on disk. The original source-only run
#42011008737 ended with STORAGE_CAP after 2,888.38997s; its collector log
reported 67,109,500 uncompressed bytes = 64 MiB + 636 bytes, while
the desired original duration was 7,200s.

Original frozen source:
- `research/source_reliability_v22/compare.py` on
  `research/l50-stress-liquidation-v24-2026-11-05`.
- `research/source_reliability_v24/PROTOCOL_FROZEN.md`.
- GitHub Actions run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/42011008737.

## Proposed source-side technical correction

`compressed_budget.py` exposes a conservative **pre-write** decision for
both separate byte budgets. It checks `gzip_writer.fileobj.tell()` as the compressed output cursor,
not `gzip_writer.tell()`. Because zlib may buffer compressed output, the
candidate also tracks **unflushed raw bytes** and assumes all of them could
be incompressible. It sync-flushes at a bounded raw interval (128 KiB) or
near the compressed limit, leaving a conservative margin for final receipts.
This candidate is *not yet integrated with a collector*.

A future new-source/protocol integration must:
1. Pin a new experiment and code identity first; keep old V2.4 immutable.
2. Check the budget BEFORE every serialized record write; do not advance
   seq/raw SHA when a record is rejected.
3. Set the new terminal reason immediately, stop all streams, and preserve
   the final receipt and a valid gzip trailer.
4. Verify final gzip actual byte size after close, raw SHA, compressed SHA,
   and counted lines independently on Linux and Windows.
5. Preserve quality failures, especially publisher-clock rejects and
   L1/L50 mismatches. A corrected byte cap alone does not confer SOURCE_PASS.
6. For market capture require explicit separate authorization; never
   reuse protected outcomes or tune frozen thresholds.

## Reproduction

`python -m unittest discover -s research/source_reliability_v25 -v`

Six synthetic tests cover: gzip logical vs physical position, strongly
compressible input, incompressible input, raw cap, missing cursor fail closed,
and overlarge source record. No market data, API endpoints or credentials.

## Scientific verdict

DEFECT_CONFIRMED; CANDIDATE_GUARD_UNIT_TESTED; INTEGRATION_NOT_PROVEN.
No PnL, no source pass, no live authority.

## Independent CI regression history

- First GitHub CI run `43768507373`: **FAIL**. The initial guard used
  `fileobj.tell()` without considering pending zlib output; incompressible
  data exceeded the cap. The failure is intentionally preserved.
- Second run `43768672125`: **SUCCESS**, 6 synthetic tests after forcing
  a gzip sync flush before each check.
- Third optimized implementation uses conservative accounting of raw bytes
  pending in zlib and periodic sync (rather than flushing every record).
  A 20,000-record deterministic synthetic local benchmark showed a
  compressed-size ratio ~1.001 vs batched gzip, whereas sync-per-record was
  ~1.41. Benchmarks are illustrative and are **NOT production validation**.
- Additional offline tests cover 20 random high-entropy streams and a
  conservative compression-ratio property. Do not trigger a source capture
  from this audit branch.
