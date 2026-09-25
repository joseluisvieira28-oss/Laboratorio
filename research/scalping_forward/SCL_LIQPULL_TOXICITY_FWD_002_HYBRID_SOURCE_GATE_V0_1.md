# SCL-LIQPULL-TOXICITY-FWD-002 — HYBRID PUBLIC SOURCE GATE V0.1

Date: 2026-09-25
Status: FROZEN SOURCE GATE / NO OUTCOME ACCESS

## Identity
- LAB_ID: SCL-LIQPULL-TOXICITY-FWD-002
- Primary family: MICRO
- Broad mechanism: passive-fill adverse selection associated with pre-fill liquidity withdrawal
- Promotion inheritance: ZERO
- Predecessor: SCL-LIQPULL-TOXICITY-FWD-001, closed SOURCE_FEASIBILITY_BLOCKED on its exact WebSocket-only source contract

## Why a new identity exists
V001 froze WebSocket l2Book + trades only and required a 1,000 ms pre-entry depth measurement. An outcome-blind 120-second probe observed l2Book gaps of 2,728–5,554 ms with median 5,352.5 ms and 0% <=1,500 ms. V001 therefore cannot measure its frozen clock honestly.

V002 changes the measurement/source contract and therefore receives a new LAB_ID under Governance V4. No V001 scientific or promotion status carries over.

## Stage 0 only — source feasibility
This authority does not open markouts, returns, PnL, fees, slopes, quartiles, signals, or trading outcomes.

### Public read-only source stack
1. Hyperliquid mainnet REST info endpoint:
   - POST https://api.hyperliquid.xyz/info
   - payload {"type":"l2Book","coin":"BTC"}
   - target poll cadence: 4 Hz (250 ms)
   - the request is a public read-only info query, not an exchange action.
2. Hyperliquid mainnet WebSocket:
   - wss://api.hyperliquid.xyz/ws
   - subscriptions: bbo BTC and trades BTC
   - public only; no user/account subscriptions.

Official current rate-limit context:
- REST aggregate budget: 1,200 weight/minute/IP.
- l2Book info request weight: 2.
- At 4 Hz the planned l2Book load is ~480 weight/minute, before ordinary connection overhead, leaving substantial headroom below the documented aggregate limit.

## Frozen feasibility probe
Duration: 120 seconds.
No prices, sizes, returns, markouts, PnL, or strategy outcomes may be summarized by the probe report.

The raw capture may preserve full provider payloads for schema/hash audit, but the source-gate report may expose only:
- request/message counts;
- HTTP status/error counts;
- local send/receive timestamps;
- provider timestamps;
- inter-arrival/cycle latency statistics;
- timestamp monotonicity/staleness;
- reconnect/parse-error counts;
- raw hashes.

## REST source gates
Target polls in 120 seconds: approximately 480.

PASS requires all:
1. >=456 successful l2Book responses (>=95% of 480 target);
2. HTTP/error fraction <=1%;
3. valid BTC two-sided book schema on 100% of successful responses;
4. provider timestamp non-decreasing on 100% of successful responses;
5. median local inter-response gap <=400 ms;
6. p95 local inter-response gap <=750 ms;
7. p95 absolute provider staleness at receive time <=1,500 ms.

## WebSocket companion gates
PASS requires:
- successful subscription acknowledgement for both bbo and trades;
- zero parse errors;
- zero reconnects during the 120-second probe, unless the server explicitly closes and the reconnect is cleanly recorded;
- at least one valid bbo message and at least one valid trade message.

BBO/trade message frequency is market-state-dependent and is not itself a fixed cadence gate.

## Source adjudication
- all REST + companion gates pass => SOURCE_DATA_PASS
- schema/timing/rate gate fails => SOURCE_FEASIBILITY_BLOCKED
- transport/environment failure before valid measurement => TECHNICAL_BLOCKED, not source failure
- no scientific edge verdict is permitted in Stage 0.

## After SOURCE_DATA_PASS
Only then may a separate pre-outcome V002 scientific protocol freeze:
- exact 1,000 ms depth-pull measurement from the hybrid source;
- conservative passive-fill proof using BBO + trades;
- markout horizons;
- sample gate;
- statistical gates;
- outcome-access firewall.

No scientific outcome is authorized by this source gate.

## Firewalls
No:
- historical 2026 backfill;
- authenticated endpoint;
- orders/cancels;
- exchange/wallet mutation;
- live trading;
- PnL/fees/returns/markouts;
- threshold tuning;
- main merge;
- Render deployment;
- paid data.
