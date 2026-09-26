# RETH-NAV-DISLOCATION-001 — RUNNER IMAGE REMEDIATION V0.1D

Frozen: 2026-09-26
Scope: GitHub Actions execution environment only.

Observed:
- repository public and active;
- GitHub public status reports Actions operational;
- multiple Laboratorio ubuntu-latest jobs are queued;
- zero Laboratorio jobs are actively running.

Permitted technical remediation:
- replace ubuntu-latest with explicit ubuntu-22.04 for the single-run continuation workflow;
- pin Python to 3.12 via actions/setup-python;
- retain Node 24 via actions/setup-node;
- keep the exact continuation scripts, source definitions, block grids, gates and frozen outcomes unchanged.

Concurrency:
Use the same continuation concurrency group with cancel-in-progress=true so a newer remediation run supersedes an older pending/running continuation attempt rather than creating concurrent scientific executions.

No scientific or promotion credit is attached to runner selection.
