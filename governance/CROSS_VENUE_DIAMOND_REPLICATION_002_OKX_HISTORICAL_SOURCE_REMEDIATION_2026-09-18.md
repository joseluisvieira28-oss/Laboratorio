# CROSS-VENUE-DIAMOND-REPLICATION-002 — OKX HISTORICAL SOURCE REMEDIATION — 2026-09-18

Status: FROZEN_BEFORE_OKX_HISTORICAL_EXPORT_SHAPE_PROBE_AND_BEFORE_ANY_OUTCOME_CALCULATION
Branch: cross-venue-diamond-replication-002-avax20
Candidate: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1

## Observed source state

The first outcome-blind AVAX20 source gate produced SOURCE_DATA_BLOCKED.

BYBIT:
- both approved public mainnet hosts returned HTTP 403 from the GitHub-hosted runner;
- classification remains BYBIT_SOURCE_BLOCKED_ENVIRONMENT;
- this is not an economic rejection and no alternative venue/asset may replace it after outcomes.

OKX:
- AVAX-USDT-SWAP instrument existence: PASS;
- 1m trade-price anchors across 2024-09 and calendar 2025: PASS;
- the standard public funding-rate-history route returned no 2024/2025 rows;
- current OKX documentation states the standard funding-rate-history endpoint returns at most three months of data, so this absence is a retention limitation rather than evidence that historical funding never existed.

Sibling source-only work in CROSS-VENUE-DIAMOND-REPLICATION-001 resolved the OKX bulk historical route:
- endpoint: /api/v5/public/market-data-history
- module 2: 1-minute candlestick
- module 3: funding rate
- dateAggrType: monthly

No AVAX historical archive payload or AVAX cross-venue trading outcome has been opened.

## Bounded remediation authority

Before any signal, return, PnL, expectancy, PF, win-rate or direction-performance calculation, execute one metadata-only parameter-shape probe for the exact AVAX OKX source.

Frozen candidates:
- module: 2 and 3
- instType: SWAP
- dateAggrType: monthly
- historical request window: 2025-01-01 inclusive to 2025-02-01 exclusive
- filter shape A: instIdList=AVAX-USDT-SWAP
- filter shape B: instFamilyList=AVAX-USDT

The probe may inspect only:
- HTTP status;
- provider code/message;
- returned row count;
- metadata fields needed to identify request/export status, date aggregation, instrument/family binding and request timestamp.

The probe MUST NOT:
- follow or download any file URL;
- parse price/funding payload values;
- calculate signals, returns or PnL;
- access 2026+;
- substitute another instrument, quote currency, data type or venue.

## Routing

- If neither frozen filter shape is provider-accepted for module 3, classify OKX funding exact-source route SOURCE_BINDING_BLOCKED.
- If a frozen filter shape is accepted, classify only OKX_HISTORICAL_EXPORT_REQUEST_ACCEPTED and freeze a separate payload-acquisition/validation contract before any download.
- A successful metadata request is NOT yet SOURCE_DATA_PASS and does not authorize Stage-B outcome replication.

## Governance

research_only = true
outcome_blind = true
no_live_trading = true
no_exchange_mutation = true
no_authenticated_exchange_api = true
no_orders = true
no_wallets = true
no_alerts_webhooks = true
no_merge_to_main = true
no_2026_plus = true
no_post_outcome_tuning = true
