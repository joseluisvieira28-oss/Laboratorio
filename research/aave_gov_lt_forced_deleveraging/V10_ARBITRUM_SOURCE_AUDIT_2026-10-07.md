# AAVE-GOV-LT-FORCED-DELEVERAGING-001 — V10 Arbitrum source audit

Date: 2026-10-07  
Branch: `aave-gov-lt-forced-deleveraging-v0.1`  
Run: [37574003868](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37574003868)  
Run head: `c73599e6d2ac336e34bf1e4a3163722e8736f270`

## Scope and governance

This audit is SOURCE-ONLY. It preserves `V01_SOURCE_MECHANISM_FREEZE_2026-10-06.md`, `V02_SOURCE_REMEDIATION_AUTHORITY_2026-10-06.md`, every earlier receipt, the terminal prior for `AAVE-RISK-PARAMETER-SHOCK-001`, and the closed 2026 boundary.

No economic or borrower-behaviour outcome was opened. Development runs remain 0. This document does not declare SOURCE_GATE_PASS, INSUFFICIENT_SAMPLE, NO_EDGE_DISCOVERY, or SURVIVES_MECHANISM_DISCOVERY.

## Artifact identity

- Artifact ID: `11464402918`
- Name: `aave-gov-lt-arbitrum-v10`
- GitHub artifact digest: `sha256:70a4d8ec2c527ad80768ec27e3de690466110c09d8f4b4dcfe48c471f01756be`
- Artifact size: `6,515,739` bytes
- `RECEIPT.json`: `ca9f849f6a26ec07d0e8678d39f8638b4c5d98cfc8ed407b13198fdbf6037b8f`
- `checkpoint.json`: `de2bdd9b0e38203a8d86835dedbf3a86bbaf76a44120de7edccc4f2b590ed7d5`
- `requests.jsonl`: `032b54b16978856ac40f7186d8f6011aa9b0ab1d39f8c52da0c694a9b029c7e2`
- ZIP integrity: PASS
- Raw response bodies: `14,566/14,566` present and matching the SHA-256 encoded in their filenames after gzip decompression

## Coverage audit

- Chain: Arbitrum
- Official Aave V3 PoolConfigurator proxy: `0x8145edddf43f50276641b55bd3ad95944510021e`
- Public unauthenticated RPC: `https://arb1.arbitrum.io/rpc`
- Terminal block: `290,687,173`
- Terminal timestamp: `1735689599` = 2024-12-31 23:59:59 UTC
- Intervals: `14,535`
- Coverage: block `0 → 290,687,173`
- Contiguity: PASS, zero interval gaps
- Requests: `14,567/14,567` HTTP 200
  - `eth_getLogs`: 14,535
  - `eth_getBlockByNumber`: 31
  - `eth_blockNumber`: 1
- Configurator events: `66`
- Unique effect transactions across all four watched topics: `35`

## Event census

| Event family | Topic0 | Count |
|---|---|---:|
| CollateralConfigurationChanged | `0x637f...0995` | 44 |
| EModeCategoryAdded / updated configuration | `0x0acf...b3cb` | 5 |
| BorrowableInIsolationChanged | `0x5bb6...6264` | 14 |
| Upgraded | `0xbc7c...d3b` | 3 |

The watched-topic census is complete for this proxy and interval. It is not yet a complete governance-lineage proof.

## Eligible LT transitions observed on-chain

Reconstructing state chronologically per reserve from the 44 collateral configuration events yields:

- 15 base-LT decreases
- 7 unique effect transactions carrying those decreases
- 0 inferred economic outcomes

Reconstructing state chronologically per eMode category from the 5 eMode configuration events yields:

- 1 LT decrease after the first observed state
- 1 unique effect transaction
- category 1: LT `9750 → 9500`, effect transaction `0x62124c8c75643d3d65cc7001628ee29eb13c5e8d3b25b51b79d9601b423224d3`

The eMode decrease transaction does not overlap the 7 base-LT decrease transactions.

Therefore the Arbitrum chain contributes a **provisional maximum of 8 candidate effect transactions** before governance timing eligibility and economic clustering. This is not a count of independent defensible shocks.

## Current scientific state

- Arbitrum acquisition and source-integrity audit: PASS
- Provisional candidate effect transactions: 8
- Governance V2/V3 lineage to approved/queued pre-effect parameters: pending
- Risk Steward/direct-execution timing eligibility: pending; fail closed if no anticipatory anchor exists
- Cross-reserve, proposal/payload, and cross-chain economic clustering: pending
- Exact independent-shock universe for 2022–2025: UNKNOWN
- Source gate: `SOURCE_GATE_PENDING`
- Hypothesis: `NOT_TESTED`

The next permissible work is SOURCE-ONLY governance lineage and coordinated-event clustering across Ethereum, Polygon, Avalanche, and Arbitrum. These 8 Arbitrum transactions must not be added arithmetically to other chain counts as independent shocks before that work is complete.
