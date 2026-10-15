# BTC-OPTIONS-VRP-BINANCE-001 — SOURCE PARSER TECHNICAL AMENDMENT V0.1A

Date: 2026-09-19  
Parent source gate: `BOVRP-BINANCE-EOH-SOURCE-001`  
Canonical first run: `35460906740`  
Artifact: `10589349428`

## First-run evidence

The frozen source census proved:
- 147 available calendar days between 2023-05-18 and 2023-10-23;
- exactly 12 missing days;
- all three frozen sample dates downloadable and parseable;
- 26 columns on each frozen sample;
- no economic outcomes opened.

The first run failed only because the semantic alias table did not recognize Binance's actual EOH field names. The observed headers include:
- `best_bid_price`
- `best_ask_price`
- `best_bid_qty`
- `best_ask_qty`
- `symbol`
- `strike`
- `type`
- `date`
- `hour`
- `mark_iv`

This is a source-parser/schema-mapping issue, not a strategy result.

## Authorized technical correction only

1. Map `best_bid_price` -> bid price.
2. Map `best_ask_price` -> ask price.
3. Map `best_bid_qty` -> bid size.
4. Map `best_ask_qty` -> ask size.
5. Map `type` -> option right.
6. Reconstruct the point-in-time clock only from the existing `date` + `hour` source columns.
7. Derive expiry only from the option `symbol` if the symbol follows a deterministic Binance option-contract date token. Report only parse success/counts; do not emit prices or strategy outcomes.

No pass threshold, date envelope, sample date, economic hypothesis or performance gate changes. The original run remains preserved as a non-adjudicative schema-parser failure.
