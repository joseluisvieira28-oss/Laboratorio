# DLS ROUTE A2 — PUBLIC-RPC BOUNDARY LOCATOR PROBE V0.1

Date: 2026-10-02
Status: FROZEN SOURCE-ONLY TECHNICAL PROBE

Problem:
Helius archival getBlock is rate-limited (HTTP 429) on the current plan. This prevents using Helius
getBlock solely to obtain arbitrary time-boundary cursor signatures.

New technical probe:
- SQD timestamp endpoint remains the slot locator.
- Solana public RPC https://api.mainnet-beta.solana.com may be used ONLY for getBlock with
  transactionDetails=signatures to obtain arbitrary signatures outside a frozen time interval.
- Helius standard archival getSignaturesForAddress remains the signature census source.
- No public-RPC transaction payload, decoder field, token metadata or economic field is authoritative.

Validation interval and expected result are unchanged:
2024-07-19T19:30:52Z <= blockTime < 2024-07-20T00:00:00Z
Target address: So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo
Expected exact unique in-window address signatures: 1,868.

PASS only if:
- boundary cursors straddle START/END;
- Helius getSignaturesForAddress returns exactly 1,868 unique in-window signatures;
- zero duplicates/missing blockTime;
- deterministic lower-bound termination.

A PASS validates the public endpoint ONLY as a generic boundary-cursor locator. It does not validate
it as a transaction/source substitute and does not change any scientific semantics.

No protected-2025 acquisition, prices, returns, PnL, 2026 outcomes, paid API purchase, trading,
orders, wallets, exchange mutation or main merge.

Trading authority: NONE.
