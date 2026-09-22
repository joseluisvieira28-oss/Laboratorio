# Radar + MEXC Post-Deployment Hardening Audit — 2026-09-22

## Decision

V0.14.2 was not fully hardened for authenticated MEXC state integration or 24/7 recovery. The corrected build is `v0.14.3-win-mexc-postdeploy-hardening` on branch `radar-mexc-postdeploy-hardening-v0.1`. No scientific rule, threshold, direction, risk budget or promotion state changed. No live order or exchange mutation was performed.

## Material findings and fixes

| Severity | Finding | Correction |
| --- | --- | --- |
| HIGH | ETF watcher exception could escape the candidate boundary and collapse the complete forward-cycle state. | Candidate exception is captured and attributed only to `etf_cme_signal`. |
| HIGH | Radar had no sanitized, versioned, stale-aware consumer for local MEXC receipts. | Added `RADAR_MEXC_LOCAL_STATE_V0.1`, SHA-256 provenance, strict schemas, secret rejection and independent exchange/risk/capital/authority states. |
| HIGH | Deribit `iv=0` on scientifically ineligible rows blocked the entire Options day before frozen DTE/moneyness filtering. | Apply frozen eligibility first; an eligible zero/null IV remains FAIL_CLOSED. Invalid index always remains FAIL_CLOSED. |
| HIGH | The Windows launcher could kill same-named Radar processes not proven to be the packaged executable. | Termination is restricted to the exact approved executable paths owning port 8787. Blanket process termination removed. |
| HIGH | No automatic recovery after process crash or user logon/reboot. | Added singleton 15-second watchdog and current-user scheduled-task installer. |
| MEDIUM | Duplicate launcher clicks could race before port binding. | Added named launcher and watchdog mutexes. |
| MEDIUM | External freshness exception could replace the entire detailed cycle with a generic fatal state. | Failure is persisted as an isolated `external_freshness` error. |
| MEDIUM | Existing MEXC execution work was on a divergent branch and absent from V0.14.2. | Merged the validated V0.2 GET-only preflight, risk firewall, standing authority, immutable live gate, mocked transport and reconciliation tests. |

## Deribit root cause

Official endpoint semantics still include `iv` and `index_price`. A public probe for 2026-09-21 found 62 `iv=0` rows among the first 1,000 option trades. The rows inspected were predominantly short-DTE/deep-ITM and outside the frozen signal universe. With the corrected ordering, the same 1,000-row page produced a valid frozen-universe sample: 9 eligible call instruments, 11 eligible put instruments, 56 eligible rows, skew -3.31, position SHORT. This probe is diagnostic only and was not persisted as forward evidence.

## MEXC state separation

- Exchange authenticated preflight: technically passed on the operator PC, but the supplied 2026-09-21 receipt is now stale and therefore displays FAIL_CLOSED until refreshed.
- Account risk firewall: confirmed PASS at the operator check, but Radar requires its own fresh `mexc_account_risk_state.json`; missing/stale/corrupt files fail closed.
- ETF capital feasibility: BLOCKED independently of exchange authentication. Last authenticated metadata: estimated venue minimum 8.66158 USDT versus frozen validation budget 0.1123763 USDT at 112.3763 USDT equity.
- Options capital feasibility: not activatable; candidate-specific risk/readiness envelope and execution authority are absent and the forward evidence gate is unmet.
- Standing operator authority: active for the two frozen SHORT `BTC_USDT` Futures routes. It does not bypass any other gate.
- Public metadata re-probe on 2026-09-22 returned non-JSON/source failure, so no newer venue-minimum value replaces the authenticated receipt.

## Execution-chain proof

The synthetic gate reaches `TRADE_READY` only when canonical signal identity, source health, motor health, information-safe timing, fresh authenticated preflight, capital compatibility, fresh account risk state, active standing authority, candidate-specific immutable authority, isolated 1x, Auto Margin Add OFF, duplicate key, exact +7d exit and friction rules all pass. Tests independently proved capital, daily halt, authority, API-schema and timing blockers prevent transport. Mock transport tests created no live order.

## Seven-motor operational truth

| Motor | State | Execution truth |
| --- | --- | --- |
| ETF-CME-INSTFLOW-001 | LINE IN WATER | Exchange capable; ETF capital BLOCKED; no current executable signal. |
| BNB-LAUNCHPOOL-DEMAND-001 | LINE IN WATER | Spot-only route; no Futures standing-authority implication. |
| OPTIONS-SPOTPERP-001-V2.1 | BLOCKED at observed V0.14.2 state | Deribit parser fault corrected; must recover only after a genuinely healthy full source cycle. Still not micro-live ready. |
| TFG-DONCHIAN-REGIME-ADAPTATION-V1 | LINE IN WATER | Tier 3 shadow-only. |
| HTF-DH03-12H-STANDALONE-FORWARD-V1 | LINE IN WATER | Shadow collector only; clock failures remain candidate-local. |
| CED1D-0031 | WAITING GATE | External T+3/archive gate; no MEXC execution mapping. |
| EMA6H-50X200-REGIME-DEPENDENCY-001 | LINE IN WATER | Tier 3 shadow-only. |

This table preserves the last confirmed control-room observation. V0.14.3 deployment and a fresh healthy cycle are required before changing the observed Options state.

## Verification

- Focused tests: 37/37 PASS before the Deribit correction.
- Full suite after all fixes: 239/239 PASS.
- Python compileall: PASS.
- Workflow YAML parse: PASS.
- Secret scan: no literal API key/secret assignment found.
- Mutation surface: only exact 1x isolated configuration, Auto Margin Add OFF, BTC_USDT order/create and cancel-by-external are allowlisted; no withdrawal, transfer, Cross margin or leverage >1x method.
- Windows package self-test and PowerShell syntax: delegated to the branch CI; local Linux cannot execute the Windows EXE/PowerShell validation.

## Remaining blockers

1. CI/package job must pass and publish the V0.14.3 Windows artifact.
2. Operator PC must install/run V0.14.3 and copy fresh sanitized MEXC preflight and risk-state receipts into the Radar `data` directory.
3. Options must complete a genuinely healthy post-deploy cycle; the old FAIL_CLOSED state must not be manually cleared.
4. ETF remains capital-incompatible under the frozen 0.1% budget.
5. Options remains without candidate-specific micro-live risk/readiness authority and sufficient forward evidence.

