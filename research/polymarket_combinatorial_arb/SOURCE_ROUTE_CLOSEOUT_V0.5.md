# POLY-COMBINATORIAL-ARB-001 — SOURCE ROUTE CLOSEOUT V0.5

Date: 2026-09-27
Status: SOURCE_ROUTE_PASS / ECONOMICS STILL SEALED
Branch: prediction-combinatorial-arb-v0.5-source-route

## Canonical run
Workflow: POLY-COMB Bounded Source Route V0.5
Run ID: 36333289493
Job ID: 108659234745
Conclusion: SUCCESS
Head commit: 5cb199ed8db5308c61ca2c5210ef9b828815e822
Artifact ID: 10936671674
Artifact ZIP SHA256: b58f33dddc2aa10a51c193cf277503f35fc9ec771436c3b9010d24d9c2e32f35

## Frozen fixture identity
Metadata-only V0.3 identified before CLOB economics:
- 32228 — Balance of Power: 2026 Midterms — 5 markets
- 48292 — OpenAI IPO Closing Market Cap — 7 markets
- 51456 — How many Fed rate cuts in 2026? — 13 markets

## Source result
- official docs provenance: PASS
- fixture identity: 3/3 PASS
- YES legs probed: 25
- legs source-complete under the strict bid+ask rule: 18/25
- full package-complete events: 2/3
- SOURCE_ROUTE_PASS = true

The 13-market Fed event failed the deliberately strict two-sided package gate because 7 YES books had zero bids while exposing asks, timestamp and fee schema. This is source geometry only; no package price was summed.

## Firewall
PASS:
- no package-price sum;
- no arbitrage spread;
- no PnL/profitability;
- no authenticated endpoint;
- no order;
- no future-nearest join;
- no silent imputation.

## Prior transport note
V0.4 complete-population census hit Gamma HTTP 422 during deep offset pagination. This is preserved as TECHNICAL_SOURCE_PAGINATION_FAILURE and does not affect the bounded V0.5 route verdict.

## Scientific meaning
This is NOT an edge verdict.
It proves only that a public, reproducible, executable-book source route exists for multiple standard negative-risk event structures.

Next legitimate action: freeze prospective economic geometry before computing the first package sum.
