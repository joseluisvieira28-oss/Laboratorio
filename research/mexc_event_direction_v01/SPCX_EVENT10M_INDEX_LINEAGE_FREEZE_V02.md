# SPCX Event-10M INDEX LINEAGE GATE V0.2
2026-10-30 FREEZE before probing MEXC product/index metadata. Zero future return labels, zero Event Futures outcomes. This is NOT an attempt to bypass the V0.1 source-only gate.

Hypothesis: Nasdaq SPCX cash equity may anticipate the price of a MEXC tokenized stock-linked tracker/contract index SPCXSTOCK_USDT. MEXC calls the product SPCXON tokenized tracker. Separate legal/price identities. Need authority to map source and expiry.

Stage 2 probes exactly:
1. Public official futures contract detail for SPCXSTOCK_USDT, parse exact symbol/state/indexOrigin. Publish raw HTTP SHA256 and an indexOrigin source list, never infer that an exchange/oracle named in that list is Nasdaq or an Event Futures server price unless expressly specified.
2. Public MEXC standard futures index REST source, exact SPCXSTOCK_USDT symbol and server timestamp/hash, merely a transport sanity check.
3. Public MEXC Event Futures page /en-GB/futures/event-futures/SPCXSTOCK_USDT with anonymous GET-only Playwright capture of /api/platform/futures/api/v1/event_contract/detail, identify exact SPCXSTOCK_USDT product and 10-minute MINUTE payout/ONLINE status, record public response hash and select field names. No accounts/private operations, non-GET blocked and cookies cleared. If product missing/disabled/10m unsupported gate BLOCKED.
4. Source authority mapping and event server entry/expiry parity MUST be separately proven from exact provider docs/fields. Generic MEXC Event Futures article only states it settles by underlying index at expiry; a ticker match or high historical correlation is insufficient.

Acceptance for SOURCE_REFERENCE_CERTIFIED demands exact defined reference identity from official MEXC Event product and standard index, and public evidence actual Event server start and expiry use same timestamped index. In absence of these, result MUST be REFERENCE_AUTHORITY_NOT_CERTIFIED (not a strategy PASS) even if product/index source transport succeeds. Do NOT compute past signed 10minute outcomes or EV on Oct28/29. No numeric tuning, asset substitution, main merge, money, trading, exchange account or keys, September holdout, or protected NVIDIA Oct05–30 forward.
Official supporting docs:
https://www.mexc.com/support/article/how-to-use-event-futures-on-mexc-a-simple-and-accessible-futures-trading-method-395277582692768768
https://www.mexc.com/futures/information/contract_detail/SPCXSTOCK_USDT
https://www.mexc.com/futures/SPCXSTOCK_USDT
https://www.mexc.io/api-docs/futures/market-endpoints/get-index-price
https://www.mexc.fm/api-docs/futures/market-endpoints/get-contract-info
