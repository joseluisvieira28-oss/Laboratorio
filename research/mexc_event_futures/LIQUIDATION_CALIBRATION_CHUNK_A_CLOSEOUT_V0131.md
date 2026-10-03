# LIQUIDATION-FLOW-FWD-001 — CALIBRATION CHUNK A CLOSEOUT

Date: 2026-10-03
Verdict: `CHUNK_PASS__CALIBRATION_INCOMPLETE`

## Authority and evidence

- Run: `37123311409`
- Job: `111203531731`
- Artifact: `v0131-liquidation-calibration-chunk-a`
- Artifact id: `11277529165`
- Artifact digest: `sha256:cbb18ac560aead300a532f8856f03c31a4bfc5b5e88f430ac9962c0311ddd179`
- Head SHA: `6371a003f0b554935c7d5fc736bd4929a3349be5`
- Frozen source gate anchor: `run=37100077597;artifact=11268610332;digest=sha256:a144f33f12e31c9f948fdaf609078122119899368fb136cb3ed0f6cf8eb48098;closeout=5ee9e53296ea52f5df61ec10d6e9a40b7a5cb381`

## Forward-only calibration result

Window:
- first full minute: `1791030900000`
- final minute start: `1791041640000`
- 180 unique one-minute bins per symbol.

Counts:
- BTCUSDT: 180 healthy / 180; 3 nonzero healthy.
- ETHUSDT: 180 healthy / 180; 3 nonzero healthy.

Safety:
- research outcomes opened: 0
- MEXC subscriptions: 0
- threshold computed: false
- activation allowed: false
- no auth/private/account/orders.

## Scientific verdict

Chunk A is valid forward source-only evidence, but numeric activation remains forbidden.

Frozen activation requirement remains unchanged:
- >=1440 healthy bins per symbol;
- >=100 nonzero healthy bins per symbol;
- only then compute the sole nearest-rank P95 threshold.

Chunk A therefore contributes 180 healthy bins and 3 nonzero healthy bins per symbol.
No threshold is frozen from this chunk alone.
