# TMFCB V0.4 source remediation closeout

Date: 2026-10-07. Parent V0.3: `6ab03d3d486ed332eee72272fffe2197eec01c8e`.
Branch: `token-migration-forced-conversion-basis-001-v0.4-source-remediation-2026-10-07`.
Remote V0.4 freeze commit: `b3c2db90603595cdc3217f3e2839d7525e26f019`.
Local pre-probe freeze commit: `ce7c623` (same research rules; local and connector authoring have different commit identities).

## Verdict

**SOURCE_BLOCKED. FULLY_CLOSED: 0; required: >=12 independent programmes.**

This phase reached a new source-gate adjudication, not an economic result. No PRE-OUTCOME ANALYSIS FREEZE was created. No Development, conversion-basis calculation, returns, trading, orders, exchange mutation, wallets/account reads or paid service was used. Main and AAVE-GOV-LT-FORCED-DELEVERAGING-001 were not changed. V0.1–V0.3 freezes and closeouts are unchanged.

Do not interpret this as INSUFFICIENT_SAMPLE: discovery is not exhaustive and no claim is made that fewer than twelve could ever qualify. Fifteen inherited programmes remain in the remediation register; plausibility is not admission.

## Material source progress

The broad V0.3 inference that the public/free history stack is unusable is too strong. V0.4 recovered historical headers and receipts, and queried an anonymous archival event dataset. Archive state, historical receipts, and event logs are different capabilities. The old factory probe gated log discovery on historical eth_getCode and used million-block RPC log requests; failure there did not establish failure of all history routes.

Six preidentified deployment receipts were recovered with successful status and matching historical header hashes: tBTC v2, VendingMachineV2, T, NU vending machine, POL token, POL migration proxy. Header metadata was independently requested from publicnode, 1rpc and SQD; per-request successes/failures are retained. Receipt logs were not inspected or retained. A deployment is not automatically a migration activation or utility cutover.

POL first-party broadcast artifact additionally binds the deployed token and migration proxy to the historical deployment transaction/block. Exact sources and blob/revision hashes are in `evidence/v04/first_party_manifests.json`.

SQD Portal's anonymous finalized-stream endpoint returned factory creation metadata. The broad attempt retained **22 creation records**, but completed only 14 of 26 range tasks before interruption; these ranges themselves were partial. The initial transport-EOF probe had incorrect completeness assumptions and is explicitly superseded. Corrected collection always advances using the last returned header number. HTTP 529, empty responses, interruption and missing intervals remain incomplete, not evidence of absent pools.

The subsequent targeted probe completed all 16 planned source-date window tasks, with **13 complete window/factory scans and 3 incomplete scans**. It recovered **9 additional creation records**. Total retained creation records: **31**, all metadata only. Search brackets are not canonical deployment dates or full-history absence proofs. One HIFI-labelled search window also returned an MPL creation, because the query intentionally covers the whole frozen token allowlist; labels denote search brackets, not token classification.

Examples of newly pinned NEW pool identities:

| Token | Factory | Quote | Pool | Creation block |
|---|---|---|---|---:|
| OGV | Uniswap V3 | USDT | `0x8b496f2ce2cc4e975a89588b3972aab56a4e7b41` | 15125846 |
| SYRUP | Uniswap V3 | WETH | `0x27941a235804f33d81adabb2d56589c5f6ea6556` | 21130083 |
| LBR v2 | Uniswap V3 | WETH | `0x00dce1deb188ee420ea8be0cf95888521fbc13a3` | 18047128 |
| G | Uniswap V2 | USDC | `0x0b731cd250e582375984de5cffb0fb50076a6f28` | 20274629 |
| G | Uniswap V3 | USDC | `0xc4dbe30fecc148a8755c970f3b8b0c9af0db81f5` | 20332208 |
| HIFI | Uniswap V3 | USDC | `0xc4480526e3d64f7ec7d7a6694c52d23aab658ed5` | 16386765 |
| T | Uniswap V3 | WETH | `0x286eb8405231a2201fcb75b6e33098a546216c86` | 13922876 |

These are immutable discovery identities, not admitted outcome-source maps. Pool creation alone does not prove continuous market observability or complete outcome archive coverage. No reserves, swaps, amounts, sqrtPrice, tick, balances, TVL or implied price were read. V3 creation payload's tickSpacing field was not retained/interpreted; it is a static fee-tier parameter, not a market tick.

## Archive and alternative routes tested

Anonymous Binance S3 ListObjectsV2 listings were completed for 29 symbol prefixes. Eighteen had monthly 2022–2025 archive object names. No ZIP, CSV, checksum payload, OHLC endpoint or trade endpoint was downloaded. Object keys, sizes, ETags, response hashes and completeness flags are retained. Names establish nominal archive coverage, not contract identity or nonempty market observations.

Daily transition-month object-name listings refine several apparent same-month overlaps:

| OLD/NEW | Last OLD object day in bracket | First NEW object day in bracket | Interpretation |
|---|---|---|---|
| PLA/PDA | 2024-02-26 | 2024-03-01 | No same-day archive names in tested brackets |
| MATIC/POL | 2024-09-10 | 2024-09-13 | Sequential archive coverage |
| GAL/G | 2024-07-15 | 2024-07-19 | Sequential archive coverage |
| MFT/HIFI | 2023-01-03 | 2023-01-12 | Sequential archive coverage |
| KEEP or NU/T | 2022-02-16 | 2022-02-25 | Sequential archive coverage |
| RNDR/RENDER | 2024-07-22 | 2024-07-26 | Sequential archive coverage |
| AGIX or OCEAN/FET | OLD includes 2024-07-01 | FET includes 2024-07-01 | Same-day names; no intraday claim |

This is a statement about tested archive metadata, not a universal listing/delisting or market-absence verdict. Monthly names alone must not be used to fabricate simultaneous OLD/NEW trading.

Other routes:
- SQD legacy gateway returned a height but the tested worker route returned 403; Portal is the operational alternative. Documentation: https://docs.sqd.dev/en/api/evm/finalized-stream .
- The Graph legacy Uniswap hosted endpoint failed DNS resolution. Current official Uniswap gateway documentation requires an API key; no credentials were provisioned or used. Metadata-only GraphQL query is saved. https://developers.uniswap.org/docs/ecosystem/subgraphs/overview .
- AWS public blockchain bucket anonymously listed blocks/contracts/logs/traces/transactions partitions. Raw mixed log datasets were not fetched: they can include prohibited swap payloads, and a server-side event projection was not established. https://github.com/awslabs/open-data-registry/blob/main/datasets/aws-public-blockchain.yaml .
- Envio documentation says HyperSync requests require an API token. Classified as credential-gated, not silently bypassed or paid. https://docs.envio.dev/docs/HyperSync/hypersync-clients .
- Public RPC probes record range limits (1rpc 50 blocks, Cloudflare 800 in tested replies), pruned-history errors, nulls and transport failures separately. Responses vary by endpoint/request; do not generalize to all providers.

## A-F programme adjudication

Legend: closed refers to the stated component only; supported/partial is not closed. Inherited mechanism claims retain their V0.2/V0.3 status unless the new source evidence below requires caution. Every row remains NOT_FULLY_CLOSED. No sample-count change or ratio substitution is authorized.

| Programme | A identity | B conversion | C activation | D boundary | E contemporaneous observability | F source map and historical feasibility |
|---|---|---|---|---|---|---|
| OGV→OGN | supported | fixed ratio verified in historical code | deployment-manifest execution time is not proven start tx | OPEN: migrate does not enforce endTime | both token pool metadata partially pinned; common-quote/window incomplete | OPEN; OGV Binance prefix empty, OGN archive nominal |
| MPL→SYRUP | inherited closed | inherited 100:1 + contract scalar design | OPEN: no exact activation receipt | inherited finite final window; distinguish announced disable from on-chain proof | MPL and SYRUP WETH creation metadata found; window proof incomplete | OPEN; MPL Binance prefix empty, SYRUP begins 2025-05 |
| CUDOS→FET | inherited supported; native/ERC20 distinction unresolved | inherited 118.344:1 | OPEN: converter/snapshot provenance | OPEN: exact halt block/timestamp | CUDOS prefix empty; FET archive found; no paired market proof | OPEN; targeted first-party GitHub discovery did not locate manifest |
| LBR v1→v2 | frozen addresses + NEW pool confirmed | inherited 1:1 supported | OPEN: no activation receipt | inherited deadline needs complete canonical package | NEW WETH pool found; OLD matching history not closed | OPEN; Binance prefix empty; named official repo now 404 |
| RAINI→RST | inherited bridge/NEW identity; complete OLD package open | inherited 1:1 supported | OPEN | inherited 2024-03-01 rule; exact package incomplete | both Binance prefixes empty; Beam/ETH pool map open | OPEN; no usable first-party deployment manifest discovered |
| PLA→PDA | inherited supported; PDA first-party repo confirmed | inherited 1:1 supported | OPEN: repo has deploy script, not deployment receipt | inherited snapshot/utility claim, exact package open | Binance object days sequential | OPEN; cross-venue or DEX proof still needed |
| MATIC→POL | closed identities reinforced by broadcast | inherited 1:1 supported | deployment/proxy receipts independently verified; study activation not yet pinned | OPEN: exact utility boundary | Binance sequential; OLD DEX creations found, POL search incomplete | OPEN |
| GAL→G | frozen identities; G pools confirmed | inherited 1:60 supported | OPEN | OPEN: at-least-one-year portal wording is not a finite deadline | Binance sequential; NEW USDC/WETH pools found, matching OLD timeline incomplete | OPEN |
| MFT→HIFI | frozen identities; HIFI pool confirmed | inherited contract 100 MFT→1 HIFI | OPEN: pool creation is not converter activation | OPEN: exact rights cutover | Binance sequential; DEX identities partial | OPEN |
| KEEP+NU→T | identities reinforced by canonical manifests | inherited deterministic architecture; exact factors not re-derived | T/NU deployment receipts independently verified; programme activation incomplete | OPEN: indefinite converter, exact utility cutover required | legacy pools and T/WETH creation found; Binance sequential | OPEN; counts once |
| tBTC v1→v2 | canonical constructor identities verified | inherited 1:1 supported | inherited VendingMachineV2 manifest closure strengthened by receipt/header match | OPEN: exact v1 sunset | creation search partial for paired assets; Binance prefix empty | OPEN |
| RNDR→RENDER | inherited cross-chain identities | inherited 1:1 supported | OPEN: no canonical activation receipt | OPEN: RNP-006 explicitly allows transitional RNDR utility | Binance sequential | OPEN; permissionless upgrades are not sufficient economic cutover |
| ASI AGIX/OCEAN→FET | inherited supported; symbol/contract binding incomplete | inherited deterministic factors | OPEN | OPEN: long-lived conversion; exact rights transition missing | same-day names plus earlier FET archive do not finish event-window proof | OPEN; counts once |
| CQT→CXT | first-party token/migration source found; deployment package incomplete | inherited snapshot 1:1; distributor does not itself encode ratio | OPEN | inherited snapshot block 20279064; implementation tie incomplete | both Binance prefixes empty; pre-boundary NEW overlap unproven | OPEN |
| BIT→MNT | inherited partial | BLOCKED: canonical-ratio conflict unresolved | OPEN | OPEN | both Binance prefixes empty | OPEN; not admissible |

Nominal repository lookups returning 404 were discovery tests, not proof that no official repository exists: LybraFinance/LybraV2, LybraFinance/lybra-contracts, mantlenetworkio/mantle-token, cudosnetwork/cudos-node, singnet/token-migration and fetchai/asi-token-migration. Web discovery also failed to identify a usable RAINI/RST deployment manifest. Do not relabel these as exhaustive searches.

## Mechanism corrections without changing science

OGV: historical `Migrator.sol` at commit `db9d7baa3c3df57c882da80fec5aa35b9e655b6e` (2024-06-05) sets endTime to start +365 days, but comments and implementation expressly allow migrate until decommission. A finite endTime is not itself a mechanically enforced conversion closure. The prior freeze is preserved; this phase leaves D unresolved pending decommission/rights-cutover evidence. Likewise the build execution timestamp must not be silently substituted for governance execution of start().

RNDR: first-party RNP-006 says RNDR remains usable during a transitional period, migration may be undertaken whenever holders wish, and the final BME date will be announced separately. Proposal approval alone does not prove the exact termination of OLD utility. No fabricated T_end is adopted.

CXT: public CovalentMigration code is an administrator-controlled batch distributor, not an OLD-token burn/exchange function with an embedded ratio. The historical snapshot/allocation rule still needs its own canonical binding; no recipient/account files were opened.

Some current first-party repository revisions were fetched in 2026 solely to reproduce historical deployment artifacts. Their revision/blob hashes are preserved and independent historical receipt/header checks corroborate the recovered blocks. Current repository timestamps are not historical T_signal/T_end. Origin's contract caution is independently anchored to the 2024 source revision.

## Audit exception: documentation sample values

There was one accidental disclosure on a documentation read: the Binance public-data README returned generic example OHLC/trade values while documenting archive schema. Source: https://github.com/binance/binance-public-data/blob/master/README.md . These samples were not requested as candidate market data; they have no reliably identified candidate asset in the exposed rows. No values are copied into evidence, analyzed, or used for source selection. No candidate receives admission based on them. Under the inherited candidate-linked contamination rule, no specific programme can be identified for exclusion from these unlabelled examples; this is not permission to use them or a claim that the disclosure was acceptable.

**Do not claim global zero OHLC exposure.** Accurate accounting: intentional market-value endpoint requests 0; market/archive file downloads 0; candidate price/basis/return analyses 0; accidental documentation-sample disclosure 1. Any later phase must preserve this audit exception and adjudicate contamination before admission. No additional candidate outcomes were opened and no 2026 market endpoint request was made.

The local investigation was intentionally interrupted during the broad archive run; its process was stopped and partial output retained. Network connections were refused after the interruption; later permission restoration and fresh processes recovered the six receipts and daily object listings. Transport failures are not economic missingness. No automated workflow or paid runner was dispatched.

## Validation and stopping rule

Offline checks pass for last-header pagination, empty/error fail-closed handling, the 2026 timestamp guard, six receipt/header hash matches, successful receipt status, preidentified tx identity and creation-field allowlists. Creation hash signatures were checked against Keccak test vectors and first-party Uniswap ABI. All old tracked files are preserved; only this family's V0.4 files are added.

Remaining source routes are precise: pin OGV decommission/start, Polygon's exact rights cutover, tBTC v1 sunset, remaining programme activation/termination evidence; finish common-quote OLD/NEW creation coverage with checkpointed pagination; bind exchange symbols to canonical assets and establish intraday listing/coverage metadata or another frozen valid stack. These are unresolved remediations, not automatic follow-ups, not outcome authorization, and not claims of universal source impossibility.

Next legitimate gate would require >=12 A-F packages, then a separate committed PRE-OUTCOME ANALYSIS FREEZE. This phase stops at SOURCE_BLOCKED with evidence and implementation available for review.
