# HYPE-BUYBACK-FLOW-001 — FREE 90-DAY SOURCE DISCOVERY FREEZE V0.3
Date UTC: 2026-10-10. Authoritative predecessor: `audits/HYPE_BUYBACK_FLOW_001_SOURCE_ECONOMICS_CORRECTED_VERDICT_V02_2026_10_10.md` on parent branch.
Status: PRE-HTTP PROBE — SOURCE ONLY. No economic outcome access.

## Material new hypothesis — source access, NOT trading alpha
One or more *independent no-cost* indexers may provide AF exact-fill provenance beyond the official per-user last-10,000 cap. Do not assume a vendor's advertised "full trade history" is accessible without a key, covers AF system-account fills, exposes observed-at/publication time, or has enough throughput/pagination for 90 days at no charge.

## Source candidates fixed BEFORE first probe
1. Enigma/Hypedexer public export front page `https://trade-export.hypedexer.com/` — check only public HTML for export and access prerequisites, NEVER login, submit signatures or use undocumented private endpoints.
2. Hypedexer public `https://api.hypedexer.com/openapi.json` schema, check presence and authentication descriptions of `/fills/spot/user/{user_address}` and cursor/time query params. No key generated.
3. Documented public Hypedexer address-fills endpoint `https://api.hypedexer.com/fills/spot/user/{AF}` with NO authentication. HTTP 401/403 or JSON auth error = KEY_REQUIRED, not a source PASS. Only one metadata request, do not retrieve 90 days here.
4. Public ASXN `https://api-data.asxn.xyz/api/data/hl-buybacks` GET — inspect daily row field schema/count/date coverage ONLY. No prices/returns or pattern mining. Even 90+ daily rows of `sz` and `ntl` alone are **NOT exact fill-level causal proof**.
5. Public Hyperliquid official API `userFillsByTime` 10k max and S3 `node_fills_by_block` requester-pays are already authoritative: no repeated pulls, no S3 cost, no AWS creds.

### Read-only probes
Each GET limited to 1 MiB first page; response headers/status, SHA256 of bytes seen, actual content-type and UTC first-seen time, no cookies/auth/identity, HTTP latency, and explicit error. Store raw small responses only if safely public (HTML, OpenAPI, summary JSON) and zero credentials. Do not follow login links, sign transactions, call POST export APIs or subscribe to any paid tier.
NO automatic market-data backtesting, OHLCV calls, HYPE price response, BTC control returns or protected outcome lookups.

### Scientific classification
- `FREE_HISTORICAL_EXACT_FILL_SOURCE_PASS` requires >=90 UTC days, >=60 active days, exact official AF identity, per-fill `coin=@107`, side=B, px/sz, immutable tx and trade IDs, bounded gaps, independent audit against earlier verified recent 5 days, first-published causal timestamps/latency and no paid tier. This initial access-only probe CANNOT earn this classification.
- `CANDIDATE_ACCESSIBLE_UNVERIFIED` for public docs, free tiers or daily aggregated series without exact-fill evidence.
- `AUTH_REQUIRED` for an indexer with documented 0 USD free key but not connected: do not claim API data retrieved.
- `SOURCE_BLOCKED` remains for original 90-day gate until actual proof.

### Known alternatives and economic confounds
- Hyperliquid docs `https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data` S3 is explicitly requester-pays.
- Hypedexer free tier `https://hypedexer.com/pricing`: 5000 credits/month, stop at cap; needs free key and credit cost eligibility verification. Growth advertises full history as premium feature; FREE *may not* cover full history.
- Third-party exporter page `https://trade-export.hypedexer.com/` says no limits, but marketing is not validation.
- ASXN-backed Dune query `https://dune.com/queries/6865921/10758183` currently displays GET failure; if ASXN GET works, daily aggregated proxy is still not raw individual fills.

### Prohibited
No main changes/merge, exchange mutation, trading/orders, any private account/wallet read/credentials, paid API, AWS requester-pays, Render, post-outcome tuning, opening sealed 2026 price outcomes, or cherry-picking of prior signal thresholds. No permanent scheduler until zero-cost source and durable exactly-once storage are established.
