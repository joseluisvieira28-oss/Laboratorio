# BTC-OPTIONS-VRP-001 — optionsDX FREE SAMPLE TECHNICAL AMENDMENT V0.1A

Date: 2026-09-19  
Parent probe: `OVRP-EXEC-SOURCE-OPTIONSDX-FREE-SAMPLE-001`  
Canonical first run: `35457931104`  
First-run artifact: `10588696106`

## Reason

The first source-only run successfully retrieved the frozen public sample URL:

- HTTP 200;
- content type `text/csv`;
- 21,385,261 bytes;
- 94,066 data rows;
- 28 columns;
- SHA256 `7483e49d5317f91ad9acb869fadbcb3ad9de7f4c42998f545da3a4209a5e6933`.

The parser classified the sample as schema-insufficient because the CSV encodes column names inside square brackets (for example `[BID_PRICE]`) and uses `[OPTION_RIGHT]` instead of the public field-definition label `RIGHT`.

This is a parser/schema-normalization defect, not a source failure. No strategy return, PnL, expectancy, future realized variance, protected period or trading outcome was opened.

## Authorized technical correction only

1. Strip one outer pair of square brackets from header names before normalization.
2. Map `OPTION_RIGHT` to the already-frozen semantic requirement `RIGHT`.
3. Change nothing else:
   - same exact URL;
   - same required economic fields;
   - same BBO completeness rule;
   - same 25–35 DTE check;
   - same terminal classifications;
   - same zero-cost cap;
   - no 2025/2026;
   - no performance outcomes.

The first run remains preserved as `NON_ADJUDICATIVE_TECHNICAL_PARSE_RUN`. The corrected rerun is V0.1A and may adjudicate only sample-schema feasibility.
