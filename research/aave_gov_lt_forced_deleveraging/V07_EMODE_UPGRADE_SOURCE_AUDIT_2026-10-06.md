# V07 PRE-2025 eMode / upgrade source audit — 2026-10-06

## Scope and authority

Mission: `AAVE-GOV-LT-FORCED-DELEVERAGING-001`.

This receipt is source-only. It preserves `V01_SOURCE_MECHANISM_FREEZE_2026-10-06.md`, `V02_SOURCE_REMEDIATION_AUTHORITY_2026-10-06.md`, all prior receipts, the terminal result of `AAVE-RISK-PARAMETER-SHOCK-001`, and the 2026 holdout. No economic outcomes or borrower behavior were opened. Development runs: 0.

## Provenance

- Workflow run: [37489229358](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37489229358)
- Workflow head: `65dfa253434d57b038785e25aae186d1e25840e7`
- Conclusion: `success`
- Artifact: `aave-gov-lt-emode-v07`
- Artifact ID: `11440573974`
- Artifact ZIP SHA-256: `f001676443edda9c5ebf4643511733c85e9afd63ce31f99ad5cfc610938e9528`
- `RECEIPT.json` SHA-256: `7a4eab22f1e96faff97539cc075032fb19c73ab05271671fcd623197da506c01`
- `checkpoint.json` SHA-256: `5569c8752856dc7f0a96d3e6d09f4e96cedab4da5343f1ee530e1e6a534d108f`
- `requests.jsonl` SHA-256: `c780617500c12f988542503319b364a4ebf6baea0c47d9e65c4a966949d7f9e9`

## Acquisition audit

- Configurator first-code block: `16291130`
- Frozen terminal: `21525890`
- Coverage intervals: `26174`
- Continuous frontier: `21525890`
- Gaps/overlaps: `0`
- Request receipts: `26200`, all HTTP `200`
- Unique raw response hashes: `26177`
- Raw gzip files present: `26177 / 26177`
- Missing raw responses: `0`
- Decompressed SHA-256 mismatches: `0`
- Coverage hashes absent from request receipts: `0`
- Unique matching events: `33`

## Decoded event census

| Event | Count |
|---|---:|
| `EModeCategoryAdded` | 4 |
| `EModeAssetCategoryChanged` | 27 |
| configurator proxy `Upgraded` | 2 |

### eMode category states

| UTC effect | Block | Category | Label | LTV | LT | Bonus | Interpretation |
|---|---:|---:|---|---:|---:|---:|---|
| 2023-01-27 07:53:23 | 16496783 | 1 | ETH correlated | 9000 | 9300 | 10100 | first observed state |
| 2024-01-31 14:38:47 | 19127109 | 1 | ETH correlated | 9300 | 9500 | 10100 | LT increase 9300→9500 |
| 2024-11-18 11:25:23 | 21214289 | 2 | sUSDe Stablecoins | 9000 | 9200 | 10300 | first observed state |
| 2024-11-21 11:58:11 | 21235953 | 3 | rsETH LST main | 9250 | 9450 | 10100 | first observed state |

Pre-2025 eMode LT decreases found: **0**.

The 27 asset-category assignment events do not themselves change the category liquidation threshold. They remain source evidence for eligibility/state reconstruction but are not counted as independent LT shocks.

### Upgrades

| UTC effect | Block | Implementation |
|---|---:|---|
| 2024-07-27 15:06:35 | 20398674 | `0x419226e0ad27f3b2019123f7246a364622b018e5` |
| 2024-10-08 12:52:23 | 20920979 | `0x4816b2c2895f97fb918f1ae7da403750a0ee372e` |

## Scientific status

- PRE-2025 Ethereum eMode/upgrade source coverage: **AUDIT_PASS**
- New eligible eMode-LT decreases: **0**
- Prior compatible base-LT evidence remains: 16 decreases clustered into 5 known 2023–2024 episodes.
- Exact cross-chain independent economic shock universe: **UNKNOWN**
- Source gate: **PENDING**
- Hypothesis: **NOT_TESTED**
- Economic outcomes opened: **0**
- Development executions: **0**

This audit does not establish fewer than 12 shocks for the frozen multi-chain universe. The next source-only work must complete the ordered-chain census and governance V2/V3 lineage, applying economic clustering without reserve-row inflation. No pre-outcome analysis freeze is authorized yet.
