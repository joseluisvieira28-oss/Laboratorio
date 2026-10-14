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


## Isolated CI receipt — final outcome
- [Branch-only GitHub Actions run 38627039126](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38627039126): **SUCCESS** on code commit \`a4a3302672eb51b3bc716263bea11ab3366c0afd\`.
- Python compilation: PASS.
- New hermetic first-cycle tests: **8/8 PASS**.
- Existing HTTP-first single-writer startup regression: **1/1 PASS**.
- Scope comparison to deployed base: 5 commits; 5 changed paths, four added; the only existing production source \`forward_web.py\` changed by **two added lines and one removed line**. No strategy definitions, costs, order routes, credentials, database schema, scheduled tasks, or Render configuration touched.
- This CI proves code-level test behavior only, **not** that the current Render \`STARTING\` incident is fixed. The trace is not deployed.


## 2026-10-14 operational deployment attempt and post-build forensic update

**New user authorization:** "RESOLVE ENTAO" after repeated HTTP 200 \`STARTING\`. This authorized a controlled diagnostic rollout, not trading or scientific substitution.

1. The actual Render branch \`crypto-edge-radar-postgres-v0.5\` was 10 operational/docs/Windows commits ahead of the deployed code. The deploy overlay touched only \`radar/first_cycle_diagnostics.py\`, \`radar/forward_web.py\`, and hermetic tests. Other science files were unchanged. Target service \`srv-dalqkpu1egvs73fhiehg\`, autoDeploy=off.
2. Initial Render deployment \`dep-db7tvh8m7kps73ctaga0\` was **BUILD_FAILED** due to one historical test \`test_persistence_worker_gate\` expecting exactly one transport thread; new read-only diagnostic adds a second non-scientific observer thread. No deployment occurred, prior service preserved.
3. Updated \`test_persistence_worker_gate\` to require exactly the two named non-scientific threads, with \`runtime.run_loop\` and ETF scheduler still strictly never called for a persistence failure. No safety relaxation. Commit \`e21b03b9813f7ee1c76d935d1bf9310a0c3c421b\` to the canonical Radar branch, NOT main.
4. Second deploy \`dep-db7u08mi0phs73cph9gg\` received by Render. Build logs report **354/354 hermetic tests PASS**, \`Build successful\` at 2026-10-14T20:04:27Z. Last inspected Render deployment status still **build_in_progress**, despite successful build. No new \`RADAR_BOOTSTRAP_TRACE\` yet; do not misrepresent as deployed/live. Do not issue a duplicate deploy while pending.
5. The previously deployed original service continued producing true 30-second scientific receipts after startup at 20:04–20:08 UTC. Final actual runtime health \`DEGRADED_FAIL_CLOSED\`, identity \`d645891a...\`, evidence chain OK, canonical Supabase single-writer watchdog PASS, 41 runtime gap receipts. Thus STARTING is not necessarily permanent; the actual persisted CED1D source is blocked.
6. Exact culprit from current source error: \`CED1DRenderShadowRuntimeError:COLLECTOR_FAIL_CLOSED:GateError:FETCH_FAIL:HTTPError:HTTP Error 404\` for frozen \`data.binance.vision/data/futures/um/daily/bookDepth/AVAXUSDT/AVAXUSDT-bookDepth-2026-10-08.zip\`. This isolated provider archive gap had already been verified in \`crypto_edge_radar/receipts/CED1D_EXACT_SOURCE_GAP_2026-10-08_CLOSEOUT_2026-10-10.md\`. Missing frozen source cannot be fabricated, skipped, reclassified as HEALTHY, or substituted post-outcome. CED1D remains SOURCE_BLOCKED (not scientifically NO_EDGE).
7. No main merge, trading action, exchange read/write, wallet interaction, account secret disclosure, deliberate continuity-gap backfill or intentional scientific adjustment. The failed initial deployment did not displace the known live service. New diagnostic rollout is pending explicit Render confirmation.

**Next independent checks:** 1) poll \`dep-db7u08mi0phs73cph9gg\` until terminal status; 2) after successful live confirmation, inspect \`RADAR_BOOTSTRAP_TRACE\` stderr and actual \`runtime_identity.git_commit\`; 3) verify global state and evidence chain, historical gap receipts, and CED1D separately; 4) recheck the exact frozen Binance bookDepth ZIP and checksum at low frequency; if 404 persists, leave CED1D SOURCE_BLOCKED. No second deploy while one pending.
