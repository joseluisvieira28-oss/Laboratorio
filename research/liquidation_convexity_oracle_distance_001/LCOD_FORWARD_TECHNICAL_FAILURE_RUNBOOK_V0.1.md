# LCOD FORWARD OBSERVATION — TECHNICAL FAILURE RUNBOOK V0.1

Date: 2026-09-25
Scope: operational remediation only
Scientific authority: LCOD_PROSPECTIVE_MECHANICAL_STATE_OBSERVATION_FREEZE_V0.1

## Purpose

Prevent infrastructure failures from being misclassified as scientific results and
prevent technical remediation from silently changing the frozen experiment.

## Classification order

1. SCIENTIFIC PASS
   All frozen source/component/curve gates pass.

2. TECHNICAL_RETRY_ELIGIBLE
   The scientific object was not evaluated because execution infrastructure failed.
   Examples:
   - transient SQD 429/529/5xx;
   - transient Ethereum RPC HTTP/transport failure;
   - GitHub runner/network interruption;
   - artifact upload/download interruption;
   - non-fast-forward receipt persistence after the scientific calculation completed.

3. SOURCE_BLOCKED
   The run completed far enough to evaluate a frozen source gate and the required
   source condition failed.
   Examples:
   - incomplete 16-chunk range coverage;
   - decode errors;
   - unresolved UAD calls after frozen retries;
   - active/inactive partition inconsistency;
   - active-set SHA mismatch;
   - component count/debt coverage below frozen 90% gate;
   - debt reconstruction mismatch or HF tolerance failure causing the gate to fail.

4. GOVERNANCE_BLOCKED
   Provenance or boundary rules are violated.
   Examples:
   - mixed Ethereum block numbers/hashes;
   - latest/current fallback;
   - raw wallet persistence;
   - market returns/liquidation outcomes/PnL opened before authority;
   - snapshot generated from an unpinned scientific code revision.

## Permitted technical remediation

Without changing science:
- retry the same failed job/run;
- exponential backoff/jitter;
- reduce RPC request concurrency;
- split transport work into more operational batches while preserving exact
  contiguous scientific coverage and population semantics;
- retry artifact transfer;
- fetch/rebase/retry a receipt-only git push;
- upgrade deprecated runner runtime where behavior is unchanged;
- increase timeout where the computation itself is unchanged.

## Forbidden remediation

Do not:
- lower coverage gates;
- widen HF tolerance;
- impute failed borrowers;
- drop failing Spokes;
- change the 13-Spoke universe;
- change Borrow event semantics;
- change the finalized-block rule;
- change the frozen shock grid;
- select a shock point because prior curves looked interesting;
- backfill missed forward days;
- reclassify a technical failure as a zero/neutral scientific observation.

## Retry identity

A retry of a failed observation:
- uses the originally selected block N/H when evidence/artifacts make that possible;
- otherwise becomes a new diagnostic run and does NOT pretend to replace the missed
  canonical daily observation.

Canonical missed scheduled observations are not retrospectively manufactured.

## Persistence race

If all scientific gates PASS and only the final git push fails because the branch
advanced:
- preserve the workflow artifact;
- rebase a receipt-only commit onto the current branch;
- do not recompute or alter the scientific receipt;
- record the original run ID/artifact ID.

## Promotion boundary

Technical success or repeated reproducibility earns zero trading-edge promotion
credit. Forward snapshots remain mechanism observations until a separately frozen,
later predictive experiment is legitimately opened.
