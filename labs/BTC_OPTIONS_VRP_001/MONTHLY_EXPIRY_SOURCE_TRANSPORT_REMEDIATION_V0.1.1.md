# BTC-OPTIONS-VRP-001 — MONTHLY EXPIRY SOURCE TRANSPORT REMEDIATION V0.1.1

Date: 2026-09-18
Parent source gate: OVRP-MONTHLY-EXPIRY-SOURCE-001
Parent run: 35310172555

The first canonical attempt exposed a transport assumption before any performance outcome:
Deribit public/get_delivery_prices returned HTTP 200 but only 100 rows despite count=1000.
Those rows were the most recent delivery records, so historical 2021/2022 expiries were falsely reported as DELIVERY_DATE_MISSING.

Evidence from immutable parent receipts:
- 2021: many Tardis 25–35 DTE call/put pairs with BBO were present, but delivery_date_present=false.
- 2022: same pattern.
- delivery route itself returned HTTP 200 and exactly 100 distinct dates.

Remediation is source-transport only:
- preserve authority, 45 sample dates, 25–35 DTE, BBO rules and all coverage gates unchanged;
- request Deribit delivery prices in deterministic 100-row pages with offsets 0,100,...;
- stop after crossing 2021-01-01, a short/empty page, or hard offset 4900;
- retain only delivery dates and page receipts/hashes, never delivery-price values;
- no returns, premium values, PnL, 2025/2026 or paid/API-key access.

The parent run remains valid evidence of the pagination defect and is not rewritten.
