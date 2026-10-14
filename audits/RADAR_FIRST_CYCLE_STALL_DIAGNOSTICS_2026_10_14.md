# Radar first-cycle stall diagnostics — research-only handoff — 2026-10-14

## Scope and immutable boundary
- BASE: exact currently deployed Render commit \`d645891a588c594b69f41938263cc4066652aa9b\` on \`crypto-edge-radar-postgres-v0.5\`.
- TARGET: isolated \`ops/radar-first-cycle-stall-diagnostics-2026-10-14\` only.
- DIAGNOSTICS ONLY. No merge into main or canonical branch; no Render deploy, restart, environment updates, database or evidence mutation, exchange/account calls, orders, science or strategy parameter changes.
- Existing \`run_cycle\` is invoked once in exactly the same place, on the same startup thread. Errors propagate unchanged. HTTP-first binding and single-writer startup order remain identical.
- The maintenance/quiesced code path is untouched.

## Read-only evidence before patch
1. User saw HTTP 200, valid JSON, \`health=STARTING\`, \`mode=PUBLIC_SHADOW_ONLY\`, with identity, evidence and heartbeat fields not yet available.
2. Render service \`crypto-edge-radar-v05-canary\`, ID \`srv-dalqkpu1egvs73fhiehg\`, continues to show deployed commit \`d645891a588c594b69f41938263cc4066652aa9b\` (deployed 2026-10-10).
3. The consulted Render log window after 2026-10-14 19:38 UTC showed process start at 19:38:42 UTC and no completed first-cycle JSON; CPU/memory metrics indicated startup activity. This does NOT identify whether a particular network call, database operation, or CPU work blocked the cycle.
4. Historical issue: first CED1D cycle once took roughly seven minutes before the HTTP-first bootstrapping patch. A current \`STARTING\` state must NOT be treated as healthy.
5. Render Free availability, historical gaps, persistent CED1D source issues, and any independent MEXC/Windows executor state are outside this patch.

## Implementation: secret-free watchdog
- Added \`radar/first_cycle_diagnostics.py\`.
- Called around the **one** initial \`runtime.run_cycle()\` in \`serve_forward_shadow\` (non-quiesced path only).
- Emits \`RADAR_BOOTSTRAP_TRACE\` diagnostic records to **stderr**, preserving the existing scientific JSON stdout and state writes.
- Events: \`FIRST_CYCLE_STARTED\`, \`FIRST_CYCLE_STILL_RUNNING\` (after 45 seconds, then every 45 seconds while blocked), \`FIRST_CYCLE_FINISHED\` or \`FIRST_CYCLE_FAILED\`.
- WAITING events contain a bounded list of **radar Python source file basenames, function names, and line numbers** for the startup thread. Stack **locals, source lines, tokens, paths, URL, exception messages, environment values, and response bodies are never logged**.
- Completion logs use only a known health status; failure logs use exception TYPE, never message. Log output failure cannot affect the real collector. The observer is daemonized and stops as soon as the cycle returns.
- This is NOT timeout enforcement: it does not cancel a call, retry a request, alter watchdog decisions, grant live authority, or complete an interrupted first cycle.

## Interpretation after separate future approved deployment
- \`FIRST_CYCLE_STILL_RUNNING\` + top radar frames shows the step at which the initial cycle was blocked at sample time. Use the exact function and line to inspect only that read-only source path.
- \`FIRST_CYCLE_FINISHED\` with \`health=OK\` means only initial cycle completed; verify CED1D persistent status, source time, database identity and gap review independently.
- \`FIRST_CYCLE_FINISHED\` with \`DEGRADED_FAIL_CLOSED\` is not a healthy radar.
- \`FIRST_CYCLE_FAILED\` means real exception propagated as previously; the patch did not hide or retry it.
- If no trace is emitted despite process startup, blockage is earlier than the wrapped \`run_cycle\`, e.g. runtime construction or before first-cycle call. A subsequent diagnostic version must be frozen separately.

## Test boundaries
- New hermetic tests cover exactly-once invocation, result identity, long-call watchdog, secret exclusion, exception identity, interrupt propagation, invalid cadence, stack field whitelist, and logging failure isolation.
- Existing HTTP-first start and \`test_forward_web*.py\` regressions must pass in isolated branch CI.
- No test uses real market feeds, accounts, Render mutation, or credentials.
- A green CI test is NOT a successful Render fix, and this branch should remain UNDEPLOYED until separately reviewed and explicitly authorized.
