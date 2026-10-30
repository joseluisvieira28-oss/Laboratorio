# BTC Event Futures 10m — SINGLE-HYPOTHESIS SOURCE PREFLIGHT V0.4
Date: 2026-10-30 UTC. Freeze **BEFORE** any V0.4 execution. BTC only. This does not replace or modify V0.3 science, which remains frozen to November 2026 and has zero real outcomes.

**Why**: previous independent market-depth source gate proved OKX spot and MEXC perpetual depth work separately, but did not prove these six raw book bodies, exact contract payout and index can be obtained together, within the November V0.3 source-timing limits. NO forward 10m labels or returns may be opened by this experiment. A PASS means as-of feasibility for ONE observed instant, not calibrated direction, execution parity, profitability or scheduled prospective collection.

Source-only fields to audit, all before the as-of timestamp:
- 3 pairs of BTC-USDT OKX spot books and BTC_USDT MEXC Futures books; top-five USD/USDT notional imbalance from sorted noncrossed books, raw exact HTTP byte SHA256 and preserved response files, 4–8s between pair local receipt times; last source receipts <=2s, OKX server ts within <=2s; no change to V0.3 signed thresholds. NO candidate UP/DOWN may be computed from this source-only preflight.
- Anonymous public exact MEXC Event Futures BTC_USDT MINUTE 10 ONLINE payout up/down >0, raw exact response file and SHA, locally received within <=10s.
- Public MEXC standard Futures BTC_USDT index price with server timestamp, raw bytes and SHA; server and local receipt <=2s, final index price positive. This index is NOT proven identical to the Event Futures actual server openPrice or settlement index.
- Strictly monotonic fresh product response after a new anonymous GET. All non-GET browser requests and potentially sensitive URLs blocked; no cookies, accounts, wallet, private endpoints.
- Exactly one real-time source-only attempt per GitHub push. Run outside November may never compute or output a signed forecast. If any gate fails, save receipts, emit SOURCE_BLOCKED, do not silently try other thresholds/assets/exchanges.
- Python smoke tests source clock arithmetic with synthetic fixtures, not market proof. Public source run is not a prospective strategy runner and is not scheduled.
Original V0.3 rule: 3 persistent OKX |imbalance| >=0.25 and MEXC opposite >=0.25, else ABSTAIN, decision 10m aligned minute, UTC seconds20–40 only Nov1–30, payout and index as-of. 300 resolved/20 days plus proper independent tests still required. NO account/trading/money, main merge, protected September or old NVDA Oct05–30 forward reads.
