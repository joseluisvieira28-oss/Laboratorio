# Crypto Lab Windows Radar V0.14.4 — LOCAL SHADOW RESTORED / SUPERVISION NOT YET PROVEN
**Operator receipt observed 2026-10-11T07:26:33Z.**
**Status: LOCAL_SERVICE_RESTORED_FIRST_BOOT_VERIFIED / NO_CANONICAL_CUTOVER / 24X7_NOT_PROVEN.**

## Source of truth: operator-supplied local V0.7 receipt
- Schema `CRYPTO_LAB_WINDOWS_MANUAL_LOCAL_SHADOW_RECOVERY_V0.7`.
- `phase=LOCAL_SQLITE_PUBLIC_SHADOW_UP_NOT_CANONICAL_CUTOVER`, `mode=OPERATOR_EXPLICIT_LOCAL_START`.
- Installed executable present, operator-pinned SHA256 `EFA25C10C9901A62173250BF147F8206D2A63722F815895AAE18FC73DA7FA5BD` matches V0.6 local backup baseline. `independently_verified_release_signature=false`; no publisher provenance inferred.
- `packaging_selftest_pass=true`; local HTTP loopback `127.0.0.1:8787/api/state` verified identity `v0.14.4-win-cirv-eight-motor`, registry **3.7**, **8/8** focus loaded at first verification.
- `launched_node_pid=3212` at first boot (process may terminate later; no continuous process/collector uptime attested by one boot receipt).
- Initial count `existing_node_process_count=0`, `existing_port_8787_listeners=0`; `v0144_task_state=Ready` rather than task RUNNING. Thus started manually from V0.7, **not supervised** under legacy V0.14.4 scheduled watchdog.
- Existing V0.6 snapshot **44 files** confirmed; old original stdout/stderr logs untouched by V0.7 launcher, 12.22 GiB disk free and 1.56 GiB memory free at start. Actual free memory is narrow and should be monitored.
- `live_trading_enabled=false`, `exchange_mutation_performed_by_launcher=false`, `scheduled_task_mutated=false`, `render_supabase_writer_touched=false`.
- `one_canonical_scientific_writer_proven=false`: the newly restored **local SQLite public-shadow node is NOT the canonical Render/Supabase writer**. No Postgres cutover or election occurred.
- Receipt `next_step=REVIEW_OR_FIX_PRECHECK` is an **outdated static field in V0.7 script**, not a reversal of successful `phase`, package selftest and identity verification. Do not repeat startup based on this misleading `next_step`.

## Historical continuity
- Last historical local forward record before recovery: **2026-10-08T20:13:53Z**. Missing elapsed observation window until Oct11 startup **must remain missing**, not backfilled or given false precise entry/fill evidence.
- Previous string regex count 300/300 `error|FAIL_CLOSED` was invalid as crash count. Last sampled 8 pre-stop JSON states were `health=OK` and error field count 0.
- No verified reason for Oct8 stop. A clean first boot does not prove root cause has been fixed.

## Remaining gates, in order
1. **Live read-only two-snapshot proof**: verify PID 3212 (or current approved node PID), port 8787, same build/registry 8/8, and `forward_local_status.json` mtime advancement over >30 seconds. DH03 and CIRV status files may not update every 30 seconds; label stale without inventing a crash.
2. **Resource budget**: PC had only ~1.56 GiB RAM free at startup; if it drops below 1 GiB, protect existing local node by addressing unrelated workload, not killing MEXC-related processes. Avoid blanket task/disabling scripts.
3. **Replace the unsafe legacy scheduled watchdog design** after verified live stable state: original `START_RADAR_RECOVERY_V0141.ps1` may delete old stdout/stderr and forcibly replace a process if deemed noncanonical. New watchdog must be non-destructive, single-instance, avoid duplicate writers, preserve all old logs, never kill existing approved node, and fail closed on unknown process/port/authority. A logon trigger alone is not continuous service monitoring until triggered; verify actual task and recovery behavior in non-production fixture before touching operator PC.
4. Soak test across several hours then days; record explicit heartbeat freshness, disconnect/restart recovery and gaps. Do not claim 24/7 proven before observation.
5. No live MEXC trading changes, order API, new brokerage credentials, Render redeploy, main merge, or post-outcome scientific tuning.

## Governance
Local restore operation performed by operator on own Windows host; GitHub tools were used only to prepare and document read-only/manual local software; no remote code executed against Windows by assistant.
