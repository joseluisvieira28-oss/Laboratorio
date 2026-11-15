# LCOD BLOCK-PINNED ACTIVE POPULATION PIPELINE V0.6

Frozen: 2026-09-25
Prerequisite: LCOD_SQD_SDK_PARALLEL_UNIVERSE_RECEIPT.json =
SQD_SDK_PARALLEL_BORROW_UNIVERSE_PASS.

## Purpose

Resolve the canonical block-N active borrower×Spoke population without using
the current Aave MCP holder list as the scientific population.

## Procedure

1. Read one Ethereum finalized block N and hash at run start.
2. Re-stream Aave V4 Borrow history from pinned deployment boundary 24720899
   through N for the same 13 official lending Spokes using
   @subsquid/evm-stream@0.1.5.
3. Keep raw (Spoke,user) identities in process memory only.
4. Deduplicate every historical Borrow pair.
5. At exactly N, call Spoke.getUserAccountData(user) for every pair.
6. ACTIVE_DEBT_N iff totalDebtValueRay > 0.
7. Persist only SHA256(Spoke::user), counts and source hashes. Raw wallet
   addresses must never be written to disk or uploaded as artifacts.

## Technical partitioning

The historical block range is divided into 16 deterministic contiguous chunks
inside the single Node process. The chunks may stream concurrently, but the
scientific range remains one exact contiguous interval 24720899..N.

## PASS

BLOCK_PINNED_ACTIVE_POPULATION_PASS requires:
- source prerequisite already PASS;
- all 16 stream chunks complete exactly to their boundaries;
- zero Borrow decode error;
- at least 3,650 distinct historical Borrow pairs (the already-proven V0.5
  universe floor; later finalized blocks may only add pairs);
- every deduplicated pair receives one successful getUserAccountData call at N;
- active + inactive = candidate universe;
- active pair count > 0;
- zero current/latest fallback;
- raw wallet addresses retained = false.

No curve, return, liquidation outcome, PnL or trading action is authorized.
