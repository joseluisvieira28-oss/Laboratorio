# CRYPTO EDGE RADAR — RENDER CANARY V0.4 CLOSEOUT — 2026-09-17

Status: **CANARY_PASS / NOT_DURABLE_24_7_READY**

## Scope

This closeout records the isolated Render canary validation of CRYPTO EDGE RADAR V0.4. It does not authorize main merge, authenticated exchange access, order creation, cancellation, amendment, wallet access, real-money execution, or live trading.

The pre-existing Render service `Laboratorio` was not modified or replaced.

## GitHub authority

- Repository: `joseluisvieira28-oss/Laboratorio`
- Branch: `crypto-edge-radar-render-v0.4`
- Runtime code commit validated in CI and deployed to canary: `06ce0a381280e2c4af3eedcd71dbdd5d7a170d45`
- Commit message: `radar v0.4: emit compact runtime heartbeat logs`
- GitHub Actions run: `35201109870`
- CI conclusion: `SUCCESS`
- Offline compile/tests: `33/33 PASS`
- Public bounded soak: `3/3 cycles health=OK`
- CI provider: `BINANCE_SPOT_DATA_API_PUBLIC`
- CI registered strategies: `0`
- CI valid signal count: `0`
- Evidence-chain verification: `verified 9 events / ok=true`
- CI artifact ID: `10487344174`
- CI artifact SHA-256: `45fa9444cbc23158e8b205ea553bf3e8572873e334c39abd36b9261ff071946c`

## Render canary

- Workspace: `Laboratorio`
- Workspace ID: `tea-daffqvgu01pc73a9sad0`
- Canary service: `crypto-edge-radar-canary-v04`
- Service ID: `srv-dalqe4f40ujc73etuvp0`
- Region: `frankfurt`
- Plan: `free`
- Auto-deploy: `off`
- Branch: `crypto-edge-radar-render-v0.4`
- Final canary deploy ID: `dep-dalqg9ek1f9s73950im0`
- Deployed commit: `06ce0a381280e2c4af3eedcd71dbdd5d7a170d45`
- Deploy status: `LIVE`
- Runtime command: `cd crypto_edge_radar && python -m radar web-service --interval 30`

## Real runtime heartbeat evidence

The actual Render instance `srv-dalqe4f40ujc73etuvp0-8fg5g` emitted three consecutive real runtime cycles after deployment:

1. Cycle 1 completed `2026-09-17T08:43:59.545898Z`
2. Cycle 2 completed `2026-09-17T08:44:34.554291Z`
3. Cycle 3 completed `2026-09-17T08:45:09.254886Z`

All three reported exactly:

- `health=OK`
- `mode=PUBLIC_SHADOW_ONLY`
- `provider=BINANCE_SPOT_DATA_API_PUBLIC`
- `registered_strategies=0`
- `valid_signal_count=0`
- `consecutive_failures=0`
- `version=0.4`

No runtime crash/restart or signal fabrication was observed in this canary window.

## Resource observation

The canary remained lightweight during the observation window. Render metrics showed low CPU use and memory in the tens-of-megabytes range. The short canary window is sufficient for deployment-path validation only; it is not a long-duration soak claim.

## Safety boundary

- Authenticated exchange API: **NOT IMPLEMENTED / NOT USED**
- Order create/cancel/amend path: **NOT IMPLEMENTED**
- Wallet access/signing: **NOT IMPLEMENTED**
- Real-money execution: **NOT AUTHORIZED**
- Main merge: **NOT PERFORMED**
- Existing `Laboratorio` Render service: **UNTOUCHED**

## Remaining blockers before durable 24/7 status

1. **Persistent storage is not attached to the canary.** Current canary files use ephemeral `/tmp/crypto-edge-radar/*`; evidence/status can be lost on restart/redeploy.
2. **Python runtime drift must be pinned.** GitHub CI validates Python 3.12, while Render selected Python 3.14.3 by default for this canary. The current build/tests pass, but production should use one explicitly frozen interpreter version.
3. **Render health-check path is not yet configured at the service platform level.** The application exposes `/health` and `/status`, but the create-service connector did not set a platform healthCheckPath.
4. A longer durability/soak gate is required after persistent storage and runtime pinning.

## Verdict

**RENDER CANARY V0.4: PASS.**

The service build path, start command, HTTP runtime, continuous public-data loop, fail-closed semantics and compact heartbeat observability are operational on Render.

**Durable 24/7 production readiness is NOT yet granted.** The next legitimate engineering gate is runtime hardening: persistent evidence storage + pinned Python + platform health-check wiring, followed by a controlled soak. No scientific strategy promotion or live-capital permission is implied by this infrastructure result.
