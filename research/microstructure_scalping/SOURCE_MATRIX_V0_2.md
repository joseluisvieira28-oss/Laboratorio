# MICROSTRUCTURE SCALPING LAB — SOURCE MATRIX V0.2

Date: 2026-09-25
Status: SOURCE GATE / NO OUTCOMES OPENED

## Decision

### Primary historical L2 candidate: Bybit linear perpetual archive
Observed public directory:
- https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/
- Daily files visible from 2023-01-18 onward in the current directory index.
- Historical filenames transition from ob500 to ob200.
- Archive naming encodes date, symbol and depth.

Current Bybit V5 orderbook semantics:
- snapshot + delta model
- update id u
- cross-sequence seq
- exchange system timestamp ts
- matching-engine timestamp cts
- linear/inverse public websocket depths up to 1000, with documented push frequencies by depth

Scientific implication:
This is the strongest currently identified public/free candidate for deterministic historical L2 replay, but replay validity is NOT promoted until raw archives are inspected directly and sequence/timestamp integrity is measured.

### Binance
Official public archive is strong for trades/aggTrades and checksums.
Historical futures L2 documentation explicitly states:
- T_DEPTH can contain gaps
- S_DEPTH was a temporary BTCUSDT snapshot solution
- T_DEPTH_BACKFILL was beta and production stopped historically
Therefore Binance remains useful for executed-flow validation but is not the preferred L2 replay authority for this lab.

### MEXC
MEXC public futures API exposes:
- REST depth snapshot with version + timestamp
- WebSocket incremental depth with version
- public trade stream
This is sufficient for prospective forward capture.

No defensible public historical L2 archive has yet been established for MEXC.
Because the intended execution venue may be MEXC, a Bybit-only historical edge MUST NOT be treated as executable on MEXC without a separate MEXC forward replication gate.

## Cost gate — MEXC API futures
Latest official API fee update found as of this source-gate pass:
- effective 2026-06-01 08:00 UTC
- maker: 0.06%
- taker: 0.08%
These API rates override promotional/web/app rates according to MEXC's announcement.

For a taker-in/taker-out round trip, fee-only hurdle = 0.16% = 16 bps before spread/slippage/latency.
For maker-in/maker-out, fee-only hurdle = 0.12% = 12 bps before adverse selection/fill uncertainty.
Mixed maker/taker = 0.14% = 14 bps before other costs.

Consequence:
Any ultra-short edge targeting only a few bps is economically dead on the present MEXC API fee schedule unless execution economics change materially. This is a first-order gate, not a detail.

## Current state
- Historical executed flow: AVAILABLE
- Historical deterministic L2: PROVISIONAL / BYBIT CANDIDATE
- MEXC historical L2: NOT PROVEN
- MEXC forward L2: AVAILABLE
- 100ms labels: require source timestamps and replay cadence that support them
- No strategy outcome tests authorized until source receipt is PASS
