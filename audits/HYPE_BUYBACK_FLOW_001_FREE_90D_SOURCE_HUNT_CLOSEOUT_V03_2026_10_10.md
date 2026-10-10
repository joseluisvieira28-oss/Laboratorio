# HYPE-BUYBACK-FLOW-001 — FREE HISTORICAL 90-DAY SOURCE HUNT V0.3.3 CLOSEOUT
Date: 2026-10-10 UTC
Scientific status: **SOURCE_BLOCKED_90D** (official public 5-day fills remain verified, no conclusion about trading edge).
Scope: PUBLIC SOURCE ACCESS RECONNAISSANCE ONLY. NO ALPHA RETURNS / NO TRADING AUTHORITY.

## Canonical authority and source identity
Parent `research/hype-buyback-flow-001-source-gate-2026-10-10`, corrected closeout `audits/HYPE_BUYBACK_FLOW_001_SOURCE_ECONOMICS_CORRECTED_VERDICT_V02_2026_10_10.md`.
Official AF address = `0x` + 20 × `fe` (42 chars), HYPE spot pair = `@107`; original truncated address failures already corrected on parent. Exact 5d 5,228 AF buy fills / 10,934,714.86554 USDC, SOURCE-ONLY, **not independent impacts**.
Official `userFillsByTime`: 2,000 response cap, latest 10,000 AF fills. Exact 90d cannot be reconstructed from this existing public API history. Official S3 `node_fills_by_block`: requester pays, not used.

## Free source candidate adjudication
### 1. Enigma/Hypedexer FULL TRADE EXPORT — **PUBLIC FRONTEND PASS / EXPORT DATA UNVERIFIED**
- Official Hyperliquid historical docs link the independent trade export: https://trade-export.hypedexer.com/
- Public page supports wallet input, date range (3 months), CSV/JSON export, advertises unlimited free trade-history export. This is a **provider claim**, not proof AF-address full coverage.
- Independent publicly readable HL-Viewer methodology at https://hl-viewer.vercel.app/details says exporter returns .csv.gz columns `time,coin,dir,px,sz,ntl,fee,feeToken,closedPnl,hash`, limits one full export per wallet per UTC day, and falls back to official API. The listed CSV columns do NOT explicitly include `tid`; trade identity must be independently audited, not inferred.
- PUBLIC JS source map (only client script GET, no wallet request): 
   * run 38047132039: first 3 framework assets; artifact 11668420871 sha256:4e9eac56152967c36459ad3cf3b27634175d87bf51bb498ce637106de0851566.
   * run 38047191549: all 10 public JS assets. App bundle `/_next/static/chunks/1a4537d13be41f02.js` explicitly reveals exact public exporter request URI template `https://api.hypedexer.com/fills/user/${w}/export/csv?mode=distributed&start_time=${m}&end_time=${h}` using GET with `X-Turnstile-Token` and `CF-Turnstile-Token` request headers. Response creates an export job ID, later polled via `https://api.hypedexer.com/fills/export/jobs/`. Script includes user-facing errors "Daily export quota exceeded" and "Rate limit exceeded for export".
   * run 38047265699: static API client contract snippets preserved, artifact 11668356127 sha256:a2cde3ec3191543d5ec6eebfae9316f6bcc157ec7e1739cfec3ec0495569a427.
- **A Cloudflare Turnstile challenge must be completed through the normal site UI.** No challenge bypass, fabricated token, hidden account access or export-job quota use was performed. A browser-driven user-authorized export is the next access dependency; it cannot be silently represented as having happened.
- No .csv.gz/JSON file is currently in the repo or audited. 90d and 60 active day / PIT latency source thresholds remain UNMET.

### 2. Hypedexer API — **FREE PLAN EXISTS / KEY REQUIRED / HISTORICAL ACCESS UNPROVEN**
- Public current pricing: https://hypedexer.com/pricing — $0/mo, 5,000 credits/month, one request per second, free stops when credits exhausted; Growth plan uniquely advertises "full history" so the free plan's 90d eligibility cannot be presumed.
- OpenAPI GET `https://api.hypedexer.com/openapi.json`: HTTP200, 268130 bytes, SHA256 e05131a4158db249bad1e7b4ccfffdb532521a3b459f2b118c440ac77a52bdaf. Route `/fills/spot/user/{user_address}` with `start_time`, `end_time`, `limit`, `offset`.
- Exact official AF GET with no key: HTTP401 `missing api key`. A public rate-limited/free key requires explicit legitimate provider account access not provided here; no account was created and no key accessed.

### 3. ASXN/Dune — **AGGREGATES, CURRENT TRANSPORT FAILURE**
- Public Dune query https://dune.com/queries/6865921/10758183 sources aggregate buybacks via `https://api-data.asxn.xyz/api/data/hl-buybacks`; current Dune query displays external fetch failure.
- Lab one-shot unauthenticated GET timed out at 16 seconds. Not equivalent to a complete raw-fill source; even working aggregate daily `sz`/ `ntl` rows have no per-execution `tid` and first-available timestamps.

### 4. Quicknode indexed SQL — **PAID, EXCLUDED**
- Quicknode SQL Explorer stores Hyperliquid full fills/trades but official documentation says available on paid Quicknode plans, with metered API credits; not admissible in the zero-dollar mission.
- Official Hyperliquid S3 requester-pays similarly excluded.

## Immutable source-only receipts, changes and economics firewall
- Branch: `research/hype-buyback-flow-001-free-90d-probe-2026-10-10` (forked from corrected parent).
- Pre-GET freeze: `FREE_90D_SOURCE_DISCOVERY_FREEZE_V03.md`.
- Canonical public eligibility probe run `38047009676`, head `4bff98ca2f021ff2e9624dbe850c0139bca85a62`, artifact `11667029323` SHA256 `f40cbe0811dd61f562629125462f1201775c9f3ee109a1fe7d6a7b3d56f1a534`.
- Public frontend pre-GET freezes `EXPORTER_FRONTEND_SOURCE_MAP_PREPROBE_V031.md`, `EXPORTER_STATIC_EXTENDED_PREPROBE_V032.md`, `EXPORT_CLIENT_CONTRACT_PREPROBE_V033.md` before new static requests.
- No shell commands executed against paid S3. No provider login, API keys, user private account reads, third-party full export job, trading order, exchange mutation, main merge, market price outcomes, future protected holdout or return computation.

## Scientific consequence and authorized continuation
**FINAL THIS SOURCE-HUNT STATUS = SOURCE_BLOCKED_90D**, NOT NO_EDGE, not confirmed missing buybacks, not `INSUFFICIENT_SAMPLE` because 90d source collection hasn't passed integrity/coverage.
To unlock next:
1. Legitimate browser UX export of the official **public system address** on `trade-export.hypedexer.com` with dates 2026-07-10 through 2026-10-10 UTC (90+ calendar days), no wallet connecting/private key, complete any normal Turnstile challenge, single quota-compliant CSV or JSON request. Verify vendor displays $0 before initiating. Save bytes, exact UTC receipt, source format and SHA256. Do NOT fabricate or bypass the challenge.
2. Compare overlapping last five 24h AF fills to canonical 2026-10-10 official source receipts on parent, matching tid if present, otherwise require strong unique event identity from provider. Validate 90d and >=60 active days, no missing/censored windows and provider historical ingestion/publication-time facts.
3. If full free exact-fill history cannot be obtained, preserve source-blocked gate. A prospective append-only no-cost collector can begin separately, but cannot retroactively create before-first-seen provenance and must not be advertised as continuously scheduled unless a real durable scheduler exists. Never lower original source thresholds because a convenient partial proxy exists.
4. Only after gate PASS, preregister ONE economic hypothesis, signal, horizon, control, fees/spread/slippage/capacity and minimum sample **BEFORE** price outcomes. Protected 2026 outcomes remain sealed.

No background action has been scheduled in this source hunt, and no future export completion is promised.
