# STABLECOIN-EXCHANGE-FLOW-001 — PRE-DISCOVERY TECHNICAL AMENDMENT 001

STATUS: **FROZEN PRE-OUTCOME / TECHNICAL CLARIFICATION ONLY**

This amendment is made before any BTC outcome candle has been accessed.

It changes no hypothesis, address, signal, horizon, direction, cost, statistical test, promotion gate or eligible signal date.

## Boundary-search clarification

`FINAL_PRE_DISCOVERY_PROTOCOL_V0.1.md` requires the exact last Ethereum block with timestamp `<= 23:59:59 UTC` for each eligible source date and also states that no requested block timestamp may be after `2024-12-29 23:59:59 UTC`.

Those two statements are operationally over-constrained: proving that a candidate is the final block at or before a target timestamp requires observing a later bracketing block.

The authorized deterministic boundary finder may therefore query **Ethereum block metadata only** through `2024-12-31 23:59:59 UTC` for bracketing/binary-search purposes.

Hard limits remain:

- no source state/balance after the frozen `2024-12-29` boundary may enter the signal dataset;
- no signal day after `2024-12-29` is authorized;
- no BTC price/outcome is authorized by this amendment;
- no 2025 or 2026 data of any kind may be requested;
- any bracketing block is metadata-only and may not become a signal observation.

All other frozen protocol terms remain unchanged.
