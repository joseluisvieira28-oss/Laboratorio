# BTC-OPTIONS-VRP-001 — FREE ROUTE STAGE C EXTERNAL RESEARCH V0.1

Date: 2026-09-19
Scope: SOURCE-ONLY / OUTCOME-BLIND / ZERO-CASH-COST RESEARCH

## Route A — Cryptarbitrage free Deribit parquet

Deribit Insights' article "Option Backtest – Selling Weekend Vol" explicitly states that the author recorded more than six months of Deribit BTC option data and made it available for free. It states that the parquet file linked in the associated X post contains hourly snapshots of all Deribit BTC options from 2024-01-13 through 2024-07-27.

Canonical public article:
https://insights.deribit.com/education/option-backtest-selling-weekend-vol/

Canonical associated X post:
https://x.com/cryptarbitrage/status/1817888742650085616

Current research result:
- provenance claim: PASS at publisher/article level;
- exact free-file object URL: not recovered from indexed public web surfaces;
- direct payload/hash/schema validation: still pending;
- no performance data from the free parquet was opened.

Classification remains:
`FREE_ROUTE_EXISTS_LINK_RECOVERY_PENDING`

## Route B — Blockchain Research Center (BRC)

The paper "Pricing Kernels and Risk Premia implied in Bitcoin Options" states:
- 8,444,664 order-book snapshots;
- collection window 2021-04-01 through 2022-04-01;
- collected via Deribit API V2;
- high-frequency order-book changes and trades for BTC options and futures;
- fields include timestamps, Greeks, implied volatility, tick direction, order type, volume, instrument price, strike and spot;
- database reported as available through the Blockchain Research Center.

Paper:
https://www.mdpi.com/2227-9091/11/5/85

Current BRC request page:
https://blockchain-research-center.com/blockchain-explorer/request-data/

Current public catalogue requires BRC member access/accreditation for research datasets. Its current catalogue description visibly lists a Deribit BTC futures/order-book dataset and a generic "Deribit LOB" feed, but does not unambiguously expose the exact 2021-2022 BTC-options dataset described by the paper.

Current research result:
- historical existence/provenance of options dataset: PASS at paper level;
- current member-access route: EXISTS;
- exact options dataset currently exposed to new members: UNRESOLVED;
- account/accreditation/user identity submission: NOT performed;
- cash spend: 0.

Classification:
`RESEARCH_ROUTE_PLAUSIBLE_DATASET_IDENTITY_PENDING`

## Route C — Public code companion

The paper's public companion code is available at:
https://github.com/QuantLet/BitcoinOptions

This is useful for future schema/field interpretation if the BRC dataset becomes accessible. It does not itself supply the full historical quote database and therefore does not satisfy the execution-data source gate alone.

Classification:
`PUBLIC_CODE_AVAILABLE_DATA_NOT_BUNDLED`

## Decision

Continue zero-cash attack in this order:
1. let the independent Binance source lane finish its geometry adjudication;
2. continue recovering the Cryptarbitrage parquet direct object URL without opening any strategy result;
3. if needed, inspect the public QuantLet code only for source/schema expectations;
4. ask the user for BRC membership/accreditation only if public link recovery fails and exact BRC options availability can be justified first;
5. no commercial purchase while any legitimate zero-cash route remains unresolved.

No return, PnL, expectancy, VRP, future realized variance, 2025/2026 protected outcome, live trade, wallet, exchange mutation or main merge is authorized by this note.
