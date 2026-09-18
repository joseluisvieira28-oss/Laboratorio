# CED-1D-V1 — SOURCE GATE PASS CLOSEOUT — 2026-09-18

Status: **SOURCE_GATE_PASS / BYTE_EXACT_RECOVERY_PASS**

This closeout records only the source/data gate. It does not promote any scientific outcome and does not authorize Confirmation, 2026 access, live trading, exchange mutation, orders, wallets, alerts/webhooks, or merge to main.

## Canonical source identity

- Market: Binance USD-M perpetual futures
- Route: `https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1m/{filename}`
- Registry: `target_registry_R1.json`
- Registry SHA256: `71a5f82a5002e63a9ce06c2d31a35b7aac8be569ce9a782097065f44b3b1fcd4`
- Discovery population: 2021–2024 only
- Expected/complete records: 480 / 480

## Executed evidence

GitHub Actions run: **35322131962**
Job: `byte-exact-recovery`
Conclusion: **SUCCESS**

Terminal assertions:
- `REGISTRY_BINDING_ASSERTIONS_PASS`
- `BYTE_EXACT_RECOVERY_PASS`
- `BYTE_EXACT_480_OF_480_PASS`

Artifact:
- ID: `10536919382`
- Name: `ced1d-byte-exact-usdm-recovery-35322131962-1`
- Artifact digest: `sha256:967d9105fd8f1fe8ccba4a8767afb61cd65b913060f02c9247e73c09b2ca4b31`

## Firewall assertions

- `completed_records = 480`
- `expected_records = 480`
- all 480 source records = PASS
- `year_2025_accessed = false`
- `year_2026_accessed = false`
- `outcomes_computed = false`
- `live_trading_authorized = false`
- `exchange_mutation_authorized = false`

The former blocker `BLOCKED_BY_CANONICAL_WORKSPACE_BYTES_NOT_AVAILABLE_TO_EXECUTION_ENVIRONMENT` is closed for the 2021–2024 Discovery source population.

## Scope boundary

The later reproduction run 35332202275 failed during payload Base64 reconstruction before source preparation or Discovery. That transport-only failure does **not** invalidate this source-gate PASS. Discovery identity remains pending until the frozen V0.3 runner reproduces the expected derived-daily fingerprint.
