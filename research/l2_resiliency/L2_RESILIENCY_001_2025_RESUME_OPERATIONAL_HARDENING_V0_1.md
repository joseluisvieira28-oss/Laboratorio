# L2-RESILIENCY-001 — 2025 RESUME OPERATIONAL HARDENING V0.1

Status: SIDE-CAR QA ONLY / SCIENTIFIC RULES UNCHANGED / NO OUTCOMES

## Purpose
Harden the already-frozen V0.1.1 resumable 2025 source acquisition without modifying or replacing it.

This sidecar is explicitly NOT a new validation runner.

## Canonical frozen artifacts
- V0.1.1 package: L2R_2025_BTC_VALIDATION_PIPELINE_V011_RESUME.zip
- package SHA256: 3da0f466b1db170f8aedc7d45f7b757bb4e843cc7695bffc9953908c21449ba6
- runner SHA256: 80347c42e1893fbe0284ccc5779fdd841362a3feb24644d39777144f15be2a55

## Incident snapshot
- expected: 8,760 hours
- PRESENT: 4,889
- MISSING: 360
- ERROR/unresolved: 3,511

## Resume invariant
A legitimate resumed state may only move ERROR/unresolved rows into PRESENT or MISSING.
Previously resolved PRESENT or MISSING counts may not decrease.
Total hourly universe remains exactly 8,760.

## Sidecar checks
1. exact frozen package SHA256;
2. optional exact runner SHA256;
3. inventory universe shape;
4. monotonic resume-state invariant;
5. AWS CLI identity/auth readiness through read-only STS identity lookup;
6. fail closed before source acquisition if any prerequisite fails.

The PowerShell sidecar never prints AWS credentials and never launches the frozen validation automatically.

## Boundaries
- no 2025 market outcome access;
- no 2026 access;
- no L2 parsing;
- no PnL;
- no economic layer;
- no exchange mutation;
- no scientific parameter changes;
- no main merge.

The existing SOURCE_AUTH_BLOCKED_RESUMABLE classification remains authoritative until the exact V0.1.1 acquisition resumes successfully.
