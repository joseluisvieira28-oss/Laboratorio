# BTC-OPTIONS-VRP-001 — FREE ROUTE STAGE A RECEIPT V0.1

Date: 2026-09-19
Authority: `OVRP-EXEC-FREE-ROUTE-001-SOURCE`
Scope: source-only / outcome-blind / zero-cash-cost discovery

## Stage A result

### Route 1 — Cryptarbitrage / Deribit Insights free parquet
**Classification: FREE_ROUTE_EXISTS_LINK_RECOVERY_PENDING**

Deribit Insights states that the author recorded more than six months of Deribit BTC options data and made a parquet file available for free. The described payload contains hourly snapshots of all BTC options from 2024-01-13 through 2024-07-27.

The article points to X status `1817888742650085616`. The public search/index surface confirms the tweet target but did not expose the underlying parquet URL in this environment. No file bytes were opened and no performance data from the dataset was inspected.

Scientific use if recovered: source/schema/coverage validation only under this authority.

### Route 2 — Blockchain Research Center
**Classification: RESEARCH_ROUTE_PLAUSIBLE_DATASET_IDENTITY_PENDING**

Published research ("Pricing Kernels and Risk Premia implied in Bitcoin Options") reports 8,444,664 Deribit order-book snapshots collected from 2021-04-01 through 2022-04-01, with high-frequency order-book changes and trades for BTC options and futures; the paper states the database is available on BRC.

The current BRC request-data page requires BRC membership/accreditation for research datasets, and its current public catalogue labels the principal Deribit dataset as BTC futures/order-book data while separately describing a generic "Deribit LOB" feed. Therefore the exact options subset currently downloadable by a member is not proven from the public catalogue. Do not infer access from the paper alone.

No account was created and no user identity was submitted.

### Route 3 — optionsDX public sample
**Classification: SCHEMA_PASS_PAYLOAD_RETRIEVAL_PENDING**

The public Deribit chain schema exposes:
- quote timestamp;
- instrument identity;
- underlying/index price;
- expiry and DTE;
- call/put right and strike;
- BID_SIZE / BID_PRICE / ASK_PRICE / ASK_SIZE;
- OI, volume, Greeks and mark IV.

The public "Download Sample" link resolves to:
`https://www.optionsdx.com/wp-content/uploads/2022/01/btc_sample.csv`

The browser surface exposed the CSV target but the current runtime could not retrieve its bytes because of file-content handling. This is not a payload/coverage pass.

The product catalogue advertises monthly Deribit BTC option-chain data from 2021-06 through 2024-09 at EOD, 30m, 15m, 5m and 1m frequencies, with displayed product pricing spanning $0-$50 depending on selection. No purchase was made.

### Route 4 — CoinAPI
**Classification: ZERO_CASH_POSSIBLE_BUT_USER_CREDENTIAL_GATED**

The already-frozen CoinAPI probe remains valid. It requires a user-controlled API key/account and therefore is not executed autonomously. No paid overage is authorized.

### Route 5 — Tardis
**Classification: PAID_SOURCE_ROUTE_FEASIBLE / HOLD**

The existing Tardis V0.2 source probe already proves historical Deribit BTC option BBO feasibility across fixed 2021-2024 samples. Keep commercial access as fallback only.

Public pricing observed on 2026-09-19 shows historical options access is materially more expensive than a bounded sample route, with a stated minimum order of USD 300 and plan pricing depending on tier/billing. This receipt deliberately does not declare a final `X`, because the required data bill of materials has not yet been minimized.

## Stage A decision

Continue zero-cost attack in this order:

1. recover the Cryptarbitrage parquet direct object and hash it;
2. verify whether BRC accreditation currently exposes the options snapshots described in the published paper;
3. retrieve and inspect the optionsDX free sample bytes;
4. only then consider a user-supplied CoinAPI credential using free signup credits;
5. if all zero-cash routes fail, produce an exact minimal paid bill of materials before requesting authorization.

No strategy outcome was opened in Stage A.
