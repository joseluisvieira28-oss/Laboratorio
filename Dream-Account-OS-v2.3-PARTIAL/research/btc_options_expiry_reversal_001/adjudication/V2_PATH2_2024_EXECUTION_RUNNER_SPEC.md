# BOER-V2-PATH2-2024-001 — Execution Runner Specification

This file defines implementation constraints only. It does not authorize outcome access.

A future 2024 runner must:
- revalidate the exact 12 official Binance Data Vision monthly BTCUSDT USD-M 1m archives and provider CHECKSUMs;
- read only the four frozen bars per event: 04:00 open, 07:59 close, 08:05 open, 10:05 open on the last Friday of each month;
- calculate the exact parent reversal signal and unchanged base/stress costs;
- reject missing bars without interpolation or substitution;
- calculate the six frozen Path-2 gates without any additional model selection;
- preserve event-level records and source hashes;
- never request 2025/2026;
- never place an order, alert, webhook or exchange mutation;
- persist the one-shot result before interpretation;
- classify source/technical failures separately from economic failure.

No implementation may be executed against 2024 until separate explicit authorization is recorded after this freeze.
