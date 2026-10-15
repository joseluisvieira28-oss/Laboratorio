# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — PRIMARY READINESS TRANSPORT RETRY V0.1.1

Date: 2026-09-28
Status: TECHNICAL RETRY ONLY / SCIENCE UNCHANGED

V0.1 run 36381672645 failed technically with Blockscout HTTP 429 while requesting individual block timestamps.

The source log payload already contains `timeStamp` for every BuyCollateral event. V0.1.1 therefore derives ISO week directly from the frozen event log timestamp and removes all per-block REST timestamp calls.

Unchanged:
- 2025 source window;
- five frozen primary collateral addresses;
- proxy mappings;
- proxy/block cluster key;
- FLOW_USDC construction;
- >=100 cluster gate;
- >=12 ISO-week gate;
- no market prices/returns/PnL/outcomes.

The V0.1 technical-failure receipt remains preserved.
