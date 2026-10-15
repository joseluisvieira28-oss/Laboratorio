# POB-15M-CHAINLINK-CFRTI-001 — TERMINAL SOURCE CLOSEOUT V0.1

Date: 2026-09-27
Status: SOURCE_RULE_PROVENANCE_BLOCKED
Scientific verdict: NONE — NOT NO_EDGE
Parent: PREDICTION-ORACLE-BASIS-001
Branch: prediction-oracle-basis-v0.1
Draft PR: #143

## Frozen question
Can a current Polymarket BTC Up/Down 15m contract and a Kalshi KXBTC15M contract be proven equivalent except for the oracle/reference-price construction?

## Public source probe
Run ID: 36328704949
Conclusion: SUCCESS
Polymarket source-shape candidates: 13
Kalshi open KXBTC15M markets: 1
Kalshi executable quote-schema complete: 1
Exact-except-oracle pairs proven: 0
Initial classification: TARGET_INITIALIZATION_UNPROVEN

## First-party regulatory provenance
Follow-up run ID: 36329122030
Conclusion: SUCCESS

Kalshi series metadata:
- contract_terms_url: https://assets.kalshi.com/contract_terms/CRYPTO.pdf
- contract_url: https://assets.kalshi.com/regulatory/product-certifications/CRYPTO.pdf
- settlement source: CF Benchmarks

Preserved official bytes:
- Contract Terms SHA256: fde90b9c0825df277b0b2b2be6239af221eafd01a624c1b2d3a9eaff2d6fe75c
- Product Certification SHA256: 4841dd60f533d857c58e0c338c39d5c1306282c6aa54751439b032d933b4f8a1

## Regulatory reading
The official CRYPTO terms define the Underlying as the spot price in USD at the specified time, using a simple average of the relevant CF Benchmarks index for the 60 seconds before that time.

The official terms and product certification define <price> as a strike/price level listed by the Exchange. They do not define a general rule establishing that the KXBTC15M Target Price is initialized from the opening BRTI value, the prior interval's final BRTI value, or any other reference that is demonstrably equivalent to Polymarket's start-side Chainlink TWAP/reference.

The public Kalshi UI provides Target Price values and final BRTI-based settlement values. Consecutive displayed values may suggest continuity, but the pre-frozen authority explicitly forbids upgrading provenance by inference from displayed target values.

## Adjudication
SOURCE_RULE_PROVENANCE_BLOCKED.

This child does not satisfy EXACT_EXCEPT_ORACLE provenance.

No market-price outcome test is authorized.
No PnL was computed.
No win rate was computed.
No parameter search occurred.
No live trading or exchange mutation occurred.

## Scope of closure
Closed:
POB-15M-CHAINLINK-CFRTI-001 exact-oracle-only identity.

Not closed:
PREDICTION-ORACLE-BASIS-001 parent family.

The parent may investigate a materially distinct contract geometry under a new pre-source child authority, but may not relabel this blocked child as an oracle-only exact match without materially new first-party rule provenance.

## Reopen condition
Only materially new first-party Kalshi documentation that explicitly defines KXBTC15M target initialization can reopen the exact source-identity question.

Third-party descriptions, reverse engineering, target/value matching, or post-outcome inference are insufficient.
