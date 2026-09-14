# BTC-FEE-PRESSURE-001 — SOURCE-REMEDIATION V0.3 CLOSEOUT

Status: TERMINAL — PROVENANCE_FAILURE  
Date: 2026-09-14 UTC  
Run: 34880810011  
Branch: btc-fee-pressure-v0.3-source-remediation-chunked  
Head tested: 41fbbd23bbf0de3bc39965c9532c57febacb4a53

## Verdict
PROVENANCE_FAILURE.

This is a source/provenance gate failure, not NO_EDGE, not NEGATIVE_EXPECTANCY, and not a market-outcome result. Discovery remained prohibited and no BTC prices, returns, PnL, 2025, 2026, live trading or exchange mutation were opened.

## Source acquisition result
- source: https://mempool.space
- canonical window: 2021-01-01 through 2024-12-31 UTC
- four deterministic shards: all CHUNK_PASS
- final merge: completed successfully
- canonical blocks indexed: 213347
- requested height anchors: 21335 / 21335 expected
- daily observations: 1461
- first valid day: 2021-01-01
- last valid day: 2024-12-31
- missing days: 0
- missing heights: 0
- malformed blocks: 0
- hash conflicts: 0
- outside-window blocks: 1

## Exact provenance defect
The timestamp boundary route resolved start height 663912, but the canonical block at height 663912 is dated 2020-12-31 UTC. Because the frozen acquisition window begins 2021-01-01T00:00:00Z and V0.3 required fail-closed handling of any outside-window canonical block, the terminal classification is PROVENANCE_FAILURE.

Outside record:
- height: 663912
- UTC date: 2020-12-31

## Evidence
- final artifact ID: 10364463317
- final artifact ZIP SHA256: 03df1bf7d146243be3d398ea9fecd1b6d83f5e08a5ee01ee7c1fc9ab36080a41
- manifest SHA256: 08454a435c4fef2727919b54b481f1b75ef302fa4decf783096a66466e8a38ca
- final TAR SHA256: 8c089a0445481ff3c16f61cbe212a326cbe356f82581481a856dd69d65c6051c
- Drive archive: 1oATxb2-HqwQF1HMufTpBfUivOXjHJ49v
- V0.3 authority Drive ID: 1SetlZMVpXCpXdtF9NfRT4fhP3oswKVZq08eF3yE-Td4

## Governance consequence
V0.3 is closed and must not be retrospectively reclassified or silently repaired. The fee-pressure family remains scientifically open because no market outcomes were tested. Any attempt to normalize the source boundary (for example selecting the first canonical block whose timestamp is >= the frozen start timestamp while preserving the same source, window, MVE and all outcome firewalls) requires a new prospective remediation authority/version before execution.
