# CED-1D-V1 — V3 SOURCE ROUTE AUTHORITY ADDENDUM — 2026-09-17

Status: FROZEN BEFORE OUTCOMES / SOURCE-ONLY CORRECTION

## Reason
The original `CED_PHASE2_WORKSPACE` bytes were recovered after the V3 byte-recovery v0.1 freeze. Those canonical bytes prove that the Phase 2 market/source family is **Binance USD-M Futures**, while the provisional v0.1 recovery implementation incorrectly pointed at Binance Spot monthly klines.

This addendum corrects only the provider route. No hypothesis, signal, universe, timeframe, Discovery window, cost rule, outcome, promotion gate, or trading authority is changed.

## Canonical evidence recovered
- `phase2_dataset_evidence.json`: dataset version `CED-PH2-USD-M-1M-2021-2025-V2.0-R1`, market `USD-M Futures`, provider `Binance official public archive`, SHA256 `3730717187cc48a8e242cce0d8d57bd74df12ecd06b7c85d4b02d111a1a3a657`.
- canonical Phase 1 `contract.json` SHA256 `4a6ee27a8b6fd66dcc89e3d2b4211d3f5d5c8020c151f8908f081108803acfb4` states venue Binance, market USD-M perpetual futures, raw resolution 1m, source family official historical monthly archives plus provider checksums.
- recovered historical A01 repair implementation uses `https://data.binance.vision/data/futures/um/daily/klines` for canonical daily repair inputs.
- `RESEARCH_INPUT_INDEX.json` SHA256 `fb6da37a934468d84ee95f4eaadb663900eb7b9687e4d3e34bc1579d20a2631b` exactly matches historical frozen authority.

## Corrected provider route
Monthly source gate is frozen to:
`https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM}.zip`
and its provider `.CHECKSUM`.

## Gate
Exactly 480 monthly archives: 10 frozen symbols x 48 months, 2021-01 through 2024-12.
For every archive:
1. current provider checksum must validate the downloaded bytes;
2. current downloaded SHA256 must equal the historical `local_sha256` and `provider_sha256` in recovered `target_registry_R1.json`;
3. ZIP CRC must pass;
4. any mismatch => `BYTE_EXACT_RECOVERY_BLOCKED`.

The six amended 2022 source slots remain validated first at their original monthly source bytes, then their canonical repaired composites are replayed using the recovered historical repair code and daily provider hashes and must reproduce the exact historical `composite_sha256`.

## Firewall
- 2025 is not accessed during Discovery recovery/execution.
- 2026+ is hard-blocked.
- No prices/returns/outcomes are evaluated until all source and authority gates pass.
- No live trading, orders, wallets, exchange mutation, alerts, or main merge.

V3 recovery v0.1 remains immutable historical evidence; v0.2 supersedes only its incorrect Spot provider route.
