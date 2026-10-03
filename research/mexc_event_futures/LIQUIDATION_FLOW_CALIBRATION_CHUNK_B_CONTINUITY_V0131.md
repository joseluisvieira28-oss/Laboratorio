# LIQUIDATION-FLOW-FWD-001 — CALIBRATION CHUNK B CONTINUITY FREEZE

Date: 2026-10-03
Status: PRE-COLLECTION / TECHNICAL CONTINUITY

Parent scientific rules remain unchanged.

Canonical Chunk A final minute:
`1791054660000`.

Chunk B first full UTC minute MUST be strictly greater than Chunk A final minute.
Equality or earlier => FAIL CLOSED.

A gap is allowed and remains missing/unobserved time.
No gap may be backfilled.

Chunk B remains source-only:
- Bybit public linear websocket;
- dedicated BTCUSDT and ETHUSDT liquidation topics;
- frozen 60s healthy-bin construction;
- frozen heartbeat/ACK/grace rules;
- no MEXC;
- no outcomes;
- no threshold computation.

No teardown modification is introduced because Chunk A completed normally once the actual runner start time is respected.
