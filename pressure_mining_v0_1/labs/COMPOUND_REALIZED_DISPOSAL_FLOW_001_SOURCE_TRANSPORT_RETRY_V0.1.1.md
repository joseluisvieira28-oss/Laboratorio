# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — SOURCE TRANSPORT RETRY V0.1.1

Date: 2026-09-27
Status: TECHNICAL RETRY ONLY / SCIENCE UNCHANGED

Run 36346693857 completed operationally but the frozen source gate returned SOURCE_REALIZED_FLOW_PARTIAL because Blockscout rate-limited 61 of the 64 deterministic transaction/receipt probes with HTTP 429.

Preserved successful facts from the first run:
- exactly 999 BuyCollateral logs;
- 899 unique BuyCollateral transactions;
- 47 unique buyers;
- 7 collateral assets;
- deterministic 64-transaction selection rule executed unchanged;
- 3/64 transactions were usable through the initial RPC transport;
- all three usable events permitted recipient inference under the exact frozen transfer rule;
- 2/3 inferred recipients produced a later same-transaction collateral transfer, diagnostic only.

This retry changes **transport only**:
- same Comet;
- same 2023–2024 block window;
- same 999-log canary;
- same deterministic 64-transaction sample;
- same event decoding;
- same recipient inference rule;
- same >=95% transaction usability gate;
- same >=90% recipient inference gate;
- same interpretation boundary.

V0.1.1 adds public JSON-RPC fallback endpoints and bounded retry/backoff for historical transaction/receipt retrieval.

It does NOT change:
- sample membership;
- source PASS thresholds;
- direction;
- horizon;
- assets;
- market outcomes;
- protected evidence;
- any economic claim.

The V0.1 partial receipt remains immutable evidence of a transport failure and is not overwritten.
