# MEXC GLOBAL-ASSET OVERSHOOT — PUBLIC EXECUTION ROUTE SOURCE CLOSEOUT V0.1

Date: 2026-10-05
Run: 37284578918
Artifact ID: 11333556859
Artifact ZIP SHA256: `ca31a330675db2eebb4aedf1655d3520ee35dfdb038f6a5e7c250c58666e6c10`
Report SHA256: `660efe95ebcc959d70f56b26c1e489aee3292d7e055f7af58e97ef8050ae2e1a`

Result:
- 35/35 public MEXC depth routes PASS
- median public depth-request latency: 189.43 ms
- max observed latency: 318.69 ms
- median top-of-book spread: 3.3429 bps
- max observed spread: 51.4342 bps

Important limitation:
These snapshots were collected outside the frozen 13:30–20:00 UTC strategy session. They validate route availability and parsing only. They are not accepted as execution-cost evidence for the strategy.

Verdict:
`PUBLIC_EXEC_ROUTE_SOURCE_PASS__IN_SESSION_MICROSTRUCTURE_REQUIRED`

No authenticated endpoint, account read, order, wallet operation, exchange mutation or live trading was used.
