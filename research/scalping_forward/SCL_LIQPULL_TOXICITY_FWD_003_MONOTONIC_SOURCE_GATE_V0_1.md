# SCL-LIQPULL-TOXICITY-FWD-003 — MONOTONIC HYBRID SOURCE GATE V0.1

Date: 2026-09-25
Status: FROZEN SOURCE GATE / NO OUTCOME ACCESS

## Identity
- LAB_ID: SCL-LIQPULL-TOXICITY-FWD-003
- Primary family: MICRO
- Broad mechanism: passive-fill adverse selection associated with pre-fill liquidity withdrawal
- Promotion inheritance: ZERO
- Predecessor V002: SOURCE_FEASIBILITY_BLOCKED due two small provider-time regressions under a frozen 100%-monotonicity requirement.

## Scientific reason for a new identity
V003 changes the source acceptance semantics before any outcome access.
A REST L2 response is admissible only if its provider timestamp is greater than or equal to the last accepted provider timestamp.
A response with an older provider timestamp is STALE_REJECTED and is never used to construct a state.

This is a fail-closed source filter, not interpolation and not an outcome-selected rule.

## Public read-only source stack
1. Hyperliquid public REST info endpoint:
   - POST https://api.hyperliquid.xyz/info
   - payload {"type":"l2Book","coin":"BTC"}
   - target cadence: 4 Hz
2. Hyperliquid public WebSocket:
   - bbo BTC
   - trades BTC

No account/user streams, keys, orders, cancels, wallet calls, or exchange mutation.

## Frozen 120-second source gate
Target REST polls: 480.

For every valid HTTP 200 two-sided BTC book:
- parse provider time;
- if provider_time < last_accepted_provider_time: count STALE_REJECTED and exclude it;
- otherwise accept it and advance last_accepted_provider_time.

No price, size, return, markout, PnL, signal, threshold or strategy result may appear in the source-gate report.

## PASS requirements
REST after the monotonic filter:
1. >=456 accepted L2 snapshots;
2. total HTTP/transport/schema error fraction <=1%;
3. stale-rejected fraction <=1%;
4. accepted provider timestamps non-decreasing by construction and independently verified;
5. median accepted local inter-response gap <=400 ms;
6. p95 accepted local inter-response gap <=750 ms;
7. p95 absolute provider staleness <=1,500 ms.

WebSocket:
8. bbo and trades subscription acknowledgements both observed;
9. zero parse errors;
10. zero reconnects;
11. at least one valid bbo and one valid trade message.

All required gates pass => SOURCE_DATA_PASS.
Any required gate fails => SOURCE_FEASIBILITY_BLOCKED.
Transport/environment failure preventing a valid probe => TECHNICAL_BLOCKED.

## After SOURCE_DATA_PASS
Only a separate pre-outcome scientific protocol may arm the MVE. It must freeze:
- exact state alignment between REST L2, BBO and trades;
- the 1,000 ms pre-entry liquidity-pull calculation;
- conservative fill proof;
- sample gate;
- markout horizons;
- statistical gates;
- outcome-access firewall.

## Firewalls
No historical 2026 backfill.
No outcomes.
No threshold tuning.
No live trading.
No main merge.
No Render.
No paid data.
