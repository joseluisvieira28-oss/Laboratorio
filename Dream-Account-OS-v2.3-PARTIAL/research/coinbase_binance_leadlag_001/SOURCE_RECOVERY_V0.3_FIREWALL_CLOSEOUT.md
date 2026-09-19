# COINBASE-BINANCE-LEADLAG-001 — SOURCE RECOVERY V0.3 FIREWALL CLOSEOUT

Date: 2026-09-20
Branch: coinbase-binance-leadlag-v0.1
Parent MVE: CBLL-USDT-5M-Z3-001
Scope: SOURCE / PROVENANCE ONLY

## PRESERVED HISTORICAL RESULT

The V0.3 public Advanced Trade historical-trades probe executed with no Authorization header and returned HTTP 200 for all four frozen source-only requests:

- BTC-USDT early 2022
- BTC-USDT late 2023
- ETH-USDT early 2022
- ETH-USDT late 2023

The receipt classified the route as SOURCE_RECOVERY_ROUTE_FEASIBLE at the transport/schema/historical-depth level.

That receipt is preserved unchanged. It must not be rewritten.

## FIREWALL AUDIT AFTER EXECUTION

Official Coinbase documentation for the exact endpoint states that the response is a snapshot containing historical/last trades plus best bid/ask. The endpoint therefore returns fields whose temporal semantics are not restricted by the requested historical start/end interval.

The V0.3 probe deliberately did not persist or analyze best_bid/best_ask values. It persisted only trade metadata, counts, timestamps, schema checks and raw-response SHA256 hashes.

However, under this lab's strict protected-period policy, transport of a response that can contain current best-bid/best-ask data means the route cannot be treated as a clean 2022-2023-only acquisition channel.

Therefore the historical receipt field `year_2026_access=false` is not authoritative for transport-level exposure. It records the runner's intended/parsed scope, not the complete raw response semantics.

## SCIENTIFIC CLASSIFICATION

PROVENANCE_FAILURE — PROTECTED-PERIOD RESPONSE CONTAMINATION RISK

This is NOT NO_EDGE.

The parent scientific state remains DATA_FAILURE / M2 SOURCE.

The V0.3 endpoint is:
- operationally public and historically addressable;
- scientifically ineligible as the canonical full-acquisition route under the current 2025/2026 firewall;
- blocked from full 2022-2023 acquisition unless Coinbase exposes a historical-trades-only response or the frozen authority is explicitly changed by a new prospective authorization.

## WHAT REMAINS VALID

The V0.3 receipt validly proves:
- the endpoint accepts BTC-USDT and ETH-USDT;
- no API key was required in the observed probe;
- historical trade timestamps from both 2022 and 2023 were returned;
- the trade schema was present;
- no duplicate trade IDs, product mismatches or requested-window timestamp violations were observed in the parsed trade arrays.

It does NOT prove:
- full 2022-2023 completeness;
- 99.5% synchronized coverage;
- a protected-period-clean source path;
- SOURCE_DATA_PASS.

## NEXT AUTHORIZED SOURCE RECOVERY

Continue only with routes that can be shown to return historical-only payloads for the frozen 2022-2023 window.

Priority:
1. official Coinbase historical-only archive/download/API route, if any;
2. official Exchange trade route only if a historical cursor can be reached without traversing protected 2024-2026 data;
3. legitimate free/trial/public/academic/cloud archive with provable Coinbase provenance;
4. Coinbase Data Marketplace tick-level purchase as final fallback, still requiring explicit user purchase authorization.

No 2024 outcomes, 2025/2026 data, economics, live trading, exchange mutation, main merge or deployment are authorized by this closeout.
