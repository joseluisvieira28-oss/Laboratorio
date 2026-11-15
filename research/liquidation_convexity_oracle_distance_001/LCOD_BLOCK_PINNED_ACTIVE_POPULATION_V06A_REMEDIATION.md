# LCOD BLOCK-PINNED ACTIVE POPULATION V0.6A — TECHNICAL REMEDIATION

Date: 2026-09-25
Science change: NONE

V0.6 failed before producing a scientific receipt because 16 SQD streams were
opened concurrently inside one GitHub-hosted process and SQD returned HTTP 429.

No population, HF, debt, curve or outcome result was observed.

V0.7 preserves:
- same 13 official lending Spokes;
- same historical Borrow semantics;
- same one finalized block N;
- same ACTIVE_DEBT_N iff totalDebtValueRay > 0;
- same raw-wallet non-retention requirement.

Technical change only:
- use the already-proven V0.5 pattern of 16 independent GitHub jobs;
- each job streams one deterministic contiguous block chunk;
- each job classifies its raw in-memory pairs at the common finalized N;
- each job persists only SHA256 pair identities;
- aggregate deduplicates pair hashes and checks ACTIVE/INACTIVE partition
  completeness.

This avoids one-process SQD request bursts without changing the scientific
population definition.
