# MRCR H02 — Frozen-Scope Shadow Operator Runbook V0.1
Status: READY FOR OPERATOR WINDOWS / SOURCE-INFRASTRUCTURE ONLY
Date: 2026-09-26

## What this proves

A successful run proves that the exact frozen H02 public feeds can be persisted,
sequence-checked and independently reconstructed after process restart on the
operator Windows host.

It does not inspect target events or outcomes.

## Files

- h02_frozen_scope_shadow_collector.py
- h02_scope_journal.py
- h02_scope_recovery.py
- verify_h02_frozen_scope_shadow.py
- Run_MRCR_H02_Frozen_Scope_Shadow.cmd
- Verify_MRCR_H02_Frozen_Scope_Shadow.cmd

## Default local storage

%LOCALAPPDATA%\MRCR\h02_frozen_scope_shadow_v01\data\h02_frozen_scope_shadow.sqlite3

Do not upload this SQLite database. It contains exact public-feed raw payloads
and is intentionally local-only under the current boundary.

## Run

From the research folder:

```powershell
.\Run_MRCR_H02_Frozen_Scope_Shadow.cmd
```

Default duration is 60 seconds. For a longer non-target source-hardening run:

```powershell
$env:MRCR_H02_SHADOW_SECONDS = "180"
.\Run_MRCR_H02_Frozen_Scope_Shadow.cmd
```

Maximum accepted duration is 3600 seconds.

## Expected flow

The launcher:

1. creates/uses a dedicated local virtual environment;
2. pins websockets==15.0.1;
3. opens six exact-scope public sessions;
4. writes a local tamper-evident SQLite journal;
5. closes the collector;
6. starts an independent offline verifier process;
7. reopens and reconstructs the latest batch.

## PASS contract

Collector JSON:
- status = PASS;
- batch_recovery_pass = true;
- batch_session_count = 6;
- batch_passed_session_count = 6;
- every session status = PASS;
- authentication/account/signals/outcomes/orders = false;
- target_schedule_used = false;
- target_observation_authorized = false.

Offline verifier JSON:
- status = PASS;
- sqlite_integrity_pass = true;
- batch_recovery_pass = true;
- session_count = 6;
- passed_session_count = 6.

Launcher terminal line:

`MRCR H02 FROZEN-SCOPE SHADOW: PASS`

## If it fails

Share only:
- collector JSON;
- offline verifier JSON;
- final PASS/FAIL-CLOSED line.

Do not share the SQLite database or raw WebSocket payloads.

A FAIL_CLOSED is infrastructure evidence, not NO_EDGE.

## Boundary

A PASS closes source persistence/restart/recovery hardening only. It gives no
scientific edge or promotion credit and does not authorize target observation.
