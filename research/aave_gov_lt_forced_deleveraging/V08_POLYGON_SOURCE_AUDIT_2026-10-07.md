# V08 Polygon V3 configurator source audit — 2026-10-07

## Scope

Mission `AAVE-GOV-LT-FORCED-DELEVERAGING-001`. Source-only census of the official Polygon V3 PoolConfigurator through 2024-12-31 23:59:59 UTC. No borrower behavior or economic outcomes were opened; development runs remain zero.

## Provenance

- Run: [37540621767](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37540621767)
- Head: `8efe5366df478de4d30025ebb100b3cfc2a375fb`
- Artifact: `aave-gov-lt-polygon-v08`, ID `11455183520`
- Artifact ZIP SHA-256: `faf48452c3aacb3799ed28a9de71d354813bd79bd12202aee5ba7c264f73de1a`
- `RECEIPT.json`: `e9493c40a7e1f06b39265a082f01458e24e879ea40a288d1dac2303f982a728f`
- `checkpoint.json`: `91052040c179d67ed2ef3b4d3b5e14ab688d8bbac67f4c4e35d41a1af365f9d5`
- `requests.jsonl`: `65835d8bcacd10c484b151296d9473f240a15c321935e1692f561c3c10eea288`
- Public unauthenticated source: `https://polygon-bor-rpc.publicnode.com`
- Official PoolConfigurator: `0x8145eddDf43f50276641b55bd3AD95944510021E`

## Coverage audit

- Frozen terminal block: `66158917`
- Terminal timestamp: `1735689599` (2024-12-31 23:59:59 UTC)
- Accepted continuous intervals: `6629`
- Requests: `9979`, all HTTP 200
- Unique raw responses: `9979 / 9979`
- Missing raw responses: `0`
- Decompressed SHA-256 mismatches: `0`
- Coverage gaps/overlaps: `0`
- Coverage hashes absent from request ledger: `0`
- Matching events: `80`

| Event | Count |
|---|---:|
| CollateralConfigurationChanged | 59 |
| EModeCategoryAdded | 5 |
| EModeAssetCategoryChanged | 13 |
| Upgraded | 3 |

## Candidate reductions before governance lineage

Sequential state reconstruction found:

- Base-LT decrease rows: **18**
- Distinct effect transactions containing those rows: **11**
- eMode LT decrease transitions: **1**
- Distinct raw candidate effect transactions including eMode: **12**

The 18 reserve rows are not 18 shocks. Same-transaction reserve changes are one candidate episode before proposal/payload and cross-chain clustering.

### Base-LT candidate effect transactions

| UTC | Block | Effect tx | Reduced reserve rows |
|---|---:|---|---:|
| 2023-07-12 02:23:25 | 44972774 | `0x4fcbf9258c3932cf76d36c83f052f9330c51cffd361ebc66151491481c5f8978` | 1 |
| 2023-08-11 15:19:13 | 46180710 | `0x8d128ca9c637576b6a0d967da565cff139a492a749108fed2ac35f4e9bf888a9` | 1 |
| 2023-10-18 01:18:06 | 48845916 | `0xa76d93fba3c709b11fdde86b1b1b92ac0b47ec978083414987218b1618e93d1d` | 2 |
| 2023-11-19 09:31:07 | 50127249 | `0x02efe2f6e301c2169f94218b338bdcaead73e2bc0bd039c9c440ae50edc5a251` | 1 |
| 2023-11-26 12:03:25 | 50411394 | `0x00bf99a3ba3b014a7753157eb633a54f17bf128c067ba883f10789aabc6c7d2f` | 1 |
| 2023-11-26 15:15:33 | 50416783 | `0x567d257898d99fed55a7c5b69771545f4f8452211f0fefc4e2cc0797f38389df` | 2 |
| 2023-12-21 04:47:39 | 51373556 | `0x4a68392fa153577d9c6a0580979c426bb708448d2c7d1f92b847e6b294cbdef2` | 1 |
| 2024-03-27 14:56:51 | 55141862 | `0x57e0f344b2922a31be65d520024d21ced0ff75f520e528805c600c357381317b` | 1 |
| 2024-04-10 22:12:49 | 55679336 | `0x632883fea7ce5790141cf187beda7181c7029c780bbe3beef30dcea5b78fbdb5` | 4 |
| 2024-04-30 15:41:39 | 56426011 | `0x71bf17962248f4a406c1b3cbb6b927391504832774f1a9175368bc706a977b09` | 1 |
| 2024-05-11 17:03:15 | 56849317 | `0x07eaf8fcfbb4a34bf3bbfb50de2116785eba6d74d5a2ac96a55f85d07fa15e98` | 3 |

### eMode candidate

Category 1 Stablecoins moved from LT 9750 to LT 9500 at block `43299439`, 2023-05-29 19:14:58 UTC, effect tx `0x83afad9ff0c38534100b1a4626f99642d4250e93c04cd289b240c6768c4fe0c9`.

## Scientific status

- Polygon source coverage through 2024: **AUDIT_PASS**
- Raw candidate effect transactions: **12**
- Fully defensible independent economic shocks: **not yet determined**
- Governance advance-anchor eligibility: **pending**
- Cross-chain/proposal clustering: **pending**
- Source gate: **PENDING**
- Hypothesis: **NOT_TESTED**
- Outcomes opened: **0**

No sample-size verdict is authorized from this raw count. The next work must preserve chain order, acquire Avalanche, Arbitrum, Optimism and Base, then reconstruct V2/V3 governance lineage and cluster coordinated payloads across chains.
