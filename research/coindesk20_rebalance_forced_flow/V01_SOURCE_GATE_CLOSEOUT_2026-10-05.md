# COINDESK20-REBALANCE-FORCED-FLOW-001 — V0.1 SOURCE GATE CLOSEOUT
Date: 2026-10-05
Verdict: SOURCE_GATE_PASS

## Boundary
No event-window market price, return, spread, PnL or post-announcement outcome was opened during this source gate.

The CoinDesk 20 launched 2024-01-12. The complete scheduled quarterly reconstitution sequence after launch through end-2025 is therefore:
2024-04, 2024-07, 2024-10, 2025-01, 2025-04, 2025-07, 2025-10.

Official CoinDesk Indices announcement/PDF sources support all seven.

## Census
| Quarter | Publication date | Implementation | Adds | Deletes | Asset-level changes |
|---|---|---|---|---|---:|
| 2024-04 | 2024-03-19 | 2024-04-02 16:00 ET | NEAR | XLM | 2 |
| 2024-07 | 2024-06-18 | 2024-07-02 16:00 ET | HBAR, RNDR | DOGE, SHIB | 4 |
| 2024-10 | 2024-09-18 | 2024-10-02 16:00 ET | XLM | ATOM | 2 |
| 2025-01 | 2025-01-03 | 2025-01-31 16:00 ET | SUI, AAVE | RENDER, ETC | 4 |
| 2025-04 | 2025-04-02 | 2025-04-30 16:00 ET | none | none | 0 |
| 2025-07 | 2025-07-03 | 2025-07-31 16:00 ET | none | none | 0 |
| 2025-10 | 2025-10-03 | 2025-10-31 16:00 ET | CRO | FIL | 2 |

Total quarterly reconstitutions: 7
Total asset-level ADD/DELETE observations: 14
Publication-before-implementation: 14/14 asset-level changes (100%).

Lead time:
- 2024-04 / 2024-07 / 2024-10: 14 calendar days
- 2025-01 / 2025-04 / 2025-07 / 2025-10: 28 calendar days

## Official source URLs
Launch/methodology:
https://downloads.coindesk.com/cd3/CDI/CoinDesk-20-Index-Methodology.pdf

2024-04:
https://downloads.coindesk.com/cd3/CDI/IA/CD20%20Reconstitution%20April%202024%20Announcement.pdf

2024-07:
https://downloads.coindesk.com/cd3/CDI/IA/CoinDesk%2020%20Reconstitution%20202407%20Announcement.pdf

2024-10:
https://downloads.coindesk.com/cd3/CDI/IA/CoinDesk%2020%20Index%20202410%20Reconstitution%20Results.pdf

2025-01:
https://downloads.coindesk.com/cd3/CDI/IA/CoinDesk%2020%20Index%20202501%20Reconstitution%20Results.pdf

2025-04:
https://downloads.coindesk.com/cd3/CDI/IA/CoinDesk%2020%20Index%20202504%20Reconstitution%20Results.pdf

2025-07:
https://downloads.coindesk.com/cd3/CDI/IA/CoinDesk-5-20-Index-202507-Reconstitution-Results.pdf

2025-10:
https://downloads.coindesk.com/cd3/CDI/IA/CD20-Final-2025Q4-Reconstitution-Results.pdf

Official governance/archive:
https://indices.coindesk.com/documentation-and-governance

Official linked-product evidence:
https://indices.coindesk.com/coindesk20
https://downloads.coindesk.com/cd3/CDI/CoinDesk-20-QA.pdf

## Mechanism evidence
CoinDesk describes CD20 as built for trading and investment-product implementation.
Official product documentation identifies linked funds, ETPs, trackers, perpetual futures, CFDs, options, structured products and strategies.

This establishes that the benchmark is not merely academic. It does NOT establish event-specific forced notional for every 2024-2025 rebalance; event-specific tracking capital remains a limitation to report in any later result.

## Frozen source-gate adjudication
- complete post-launch 2024-2025 quarterly sequence: PASS (7)
- >=6 quarterly reconstitutions: PASS
- >=12 asset-level ADD/DELETE observations: PASS (14)
- >=90% publication-before-implementation: PASS (14/14 = 100%)
- linked-product evidence: PASS
- no event-window market outcomes opened: PASS

VERDICT: SOURCE_GATE_PASS

## Exact-time caveat
The official PDFs provide calendar publication dates but this source closeout does not prove an intraday publication timestamp for every event.

A later analysis may not pretend exact intraday announcement timing. The conservative entry boundary must be frozen before opening outcomes.

## Next authority
A separate PRE-OUTCOME ANALYSIS FREEZE is required before any event-window market price is read.
