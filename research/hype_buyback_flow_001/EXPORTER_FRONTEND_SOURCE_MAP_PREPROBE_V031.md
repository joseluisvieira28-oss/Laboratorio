# HYPE-BUYBACK-FLOW-001 — PUBLIC EXPORTER FRONTEND SOURCE MAP V0.3.1 PRE-GET
2026-10-10 UTC. STATUS SOURCE_ONLY. Scientific family unchanged.

## Trigger and evidence
- V0.3 run 38047009676 source-only: public exporter homepage HTTP200, 19,825 bytes, SHA256 d460312ed46df38e47e4a51bdb18fd8687f30d69f26c710e0dbff3820ee50c4e; no API key.
- Hypedexer public openapi GET HTTP200 (268,130 bytes); /fills/spot/user/{user_address} params include address, start_time, end_time, limit/offset, X-API-Key.
- No-key AF public fills GET HTTP401 "missing api key"; this is access requirement, **not source/data failure**.
- ASXN public aggregate GET TimeoutError after 16 seconds; unverified. Paid/official S3 never touched.
- Third-party public HL Viewer docs https://hl-viewer.vercel.app/details explicitly describe exporter `.csv.gz` and one export per wallet per UTC day. No such export request has been sent in this lab.
- The provider website `https://trade-export.hypedexer.com/` is linked from Hyperliquid docs (independently maintained).

## Predeclared, read-only follow-up
One GET public exporter landing, parse only public JS `<script src>` URLs on same origin, GET no more than 3 same-origin static JS assets (max 1 MiB each), identify only *published* API route/field names and whether export needs credentials or uses a specific `/api/` URL; report captures, exact SHA256 and lexical source evidence **WITHOUT triggering export** or wallet-address quota.
No POST, no `/export` request with AF, no signing, no login, no access token, no account state, no paid data. Ignore third-party static hosts, redirects and JS execution.
No HYPE price returns or other economic outcomes, no preoutcome freeze or account trading.
If client script is inaccessible/inconclusive, STOP with `EXPORT_TRANSPORT_UNVERIFIED`. Do not invent a vendor route.
