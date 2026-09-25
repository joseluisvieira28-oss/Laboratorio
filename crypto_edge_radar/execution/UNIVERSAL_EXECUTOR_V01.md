# MEXC UNIVERSAL EXECUTOR V0.1 — ACCELERATION LAYER

Date: 2026-09-25
Branch: `mexc-universal-executor-v0.1-2026-09-25`
Base: `mexc-tier2-microlive-v03-2026-09-25@fb6d255afd3613c4c0b7361361e47ecbdb82a612`

## Purpose

Remove duplicated execution engineering without weakening any scientific, source, risk or authority gate.

The new flow is:

`canonical signal -> candidate manifest -> universal dispatcher -> already validated candidate executor -> venue`

The dispatcher is deny-by-default. A manifest may be prepared before its candidate is live-authorized, but preparation does not create authority.

## Current dispatch truth

- OPTIONS-SPOTPERP-001-V2.1 LONG: adapter READY. It delegates to the existing validated MEXC Spot V0.3 executor and still requires the local candidate authority, fresh preflight, fresh risk state, kill-switch checks and the existing execution token.
- OPTIONS SHORT: LOCKED until unattended account identity binding is preserved.
- BNB-LAUNCHPOOL-DEMAND-001: execution manifest prepared; adapter still TO_BUILD and candidate-specific authority remains required.
- CED1D-0031: source-blocked; manifest prepared only.
- ETF-CME-INSTFLOW-001: Q4/no-peek protected; research mappings may be represented but cannot dispatch.
- TFG, DH03 and EMA6H: prospective/scientific gates remain authoritative; plumbing may be prepared but cannot dispatch.
- CIRV: forecast/shadow only; no order path.

## Invariants

- No scientific threshold changed.
- No source acceptance rule changed.
- No forward boundary changed.
- No promotion rule changed.
- No risk cap increased.
- No live order is created by a manifest or by the dispatcher in dry-run mode.
- Existing candidate-specific executors retain final authority, venue, risk and kill-switch validation.
- Unknown candidates, missing routes, missing immutable signal keys, non-ready adapters and all non-authorized states fail closed.

## Next engineering slices

1. Generalize the existing Spot execution transport behind the same dispatcher for BNB without changing BNB science or timing.
2. Bind CED1D only after source recovery and an exact side/entry/exit mapping is frozen.
3. Prebuild transport-only adapters for TFG/DH03/EMA6H behind locked manifests.
4. Preserve ETF no-peek and CIRV forecast-only boundaries.
5. After every adapter addition, require a targeted CI receipt before changing adapter_status to READY.
