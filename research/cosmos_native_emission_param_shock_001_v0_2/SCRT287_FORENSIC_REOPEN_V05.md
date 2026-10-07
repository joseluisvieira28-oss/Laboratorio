# SCRT 287 forensic reopening V0.5 — source-only

Date: 2026-10-07. Branch: cosmos-native-emission-param-shock-001-v0.2-t0-remediation-2026-10-07.
Baseline reviewed: ce14db7f47fa266e8d7c8de2ff3c1719ec746a3b. This additive reopening preserves prior receipts and closeouts as historical records.

## Authority and gate

The owner's current request reopens only SCRT Proposal 287 for heavy public-source forensics. No main changes, trading, orders, wallets, private/account endpoints, market/outcome acquisition, economic computation, promoted estimates or post-outcome tuning. No operator messages sent. Public scripts were read as data and never executed.

Pinned authority remains SCRT287_DETERMINISTIC_EXECUTION_SEMANTICS_RECEIPT_V04_2026-10-07.md: V=2023-12-07T02:54:58.930543213Z; H is the first canonical secret-4 block at/after V; T0=H+1. A hash of a downloaded response proves receipt integrity only.

Existing IBC evidence in SCRT287_IBC_PROTOBUF_DECODE_V38B.json supplies discovery anchors 11880917 at 02:54:47.127200661 and 11880922 at 02:55:33.936725313. These do not identify H. No new height is certified here.

Current source gate: SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED; family remains 11/12. Economic opening remains unauthorized. Forensic phase is OPEN_NOT_EXHAUSTED. This is not an economic rejection or a claim that every possible archive is absent.

## New executed routes and reproducibility

V54–V59 scripts, per-stage receipt.json and raw response bytes are committed. Every successful or HTTP-error receipt carries URL, UTC retrieval time, byte count, SHA-256 and acquisition classification. Transport failures are recorded without fabricated responses. Requests use no credentials, GET only, bounded reads, verified TLS and no automatic redirects. Deliberate redirect follow-ups retain their own receipts. Catalog metadata is discovery only.

| Route | Result | Remaining limitation |
|---|---|---|
| Numia independent SQL warehouse | Provider's 2024 announcement explicitly names Secret; current chain coverage names Secret Active. Current Cosmos schema names database secret_4, raw_block_results, block_height, block_timestamp DateTime64(9), hash and JSON header. | No target block rows acquired. Current ObsessionDB is credential-provisioned; legacy BigQuery requires a Google account. Credentials and account endpoints were not used. Legacy Secret table name and December 2023 coverage remain unverified. |
| KYVE mainnet and Kaon immutable-data catalogs | Public pool catalogs acquired; no Secret pool listed. | Current catalogs cannot prove absence of historical/deleted pools. No economic pool data opened. |
| GitHub releases and CI artifacts | Official SecretNetwork releases paginated beyond page 1; docs, chainofsecrets, Notional IPFS, bdjuno and node-status catalogs inspected; Secret3 artifacts are hermes/localsecret software builds. | Catalog names cannot prove a full archive's contents; no historical block dump identified. |
| Historical Notional IPFS source | Corrected documented ipfscync typo to real public ipfsync repository. Repository history and documentation inspected; snapshot table contains placeholder cid strings and no Secret row. | No content address for a Secret archive recovered; cluster configuration was not used to join or authenticate. |
| Old operator and indexer repositories | chainofsecrets and node-status trees preserved, bdjuno moved-repository catalogs followed. | Source code/deployment tooling is not a retained explorer database. No public Postgres/BigDipper dump or telemetry export containing target headers identified. |
| Internet Archive / Hugging Face / AWS registry | Focused Internet Archive Secret data/software catalog returned zero; Hugging Face secret-network catalog returned empty; AWS public blockchain catalog acquired. | secretnetwork Hugging Face query transport blocked. These are bounded catalog checks, not universal exhaustion. |
| POSTHUMAN explorer | Frontend bundle acquired; Secret configuration routes to Lavender and Stakewolle public services. | Frontend is discovery and supplies no historical database dump; known RPC routes were not broadly rerun. |
| Secret3 newer public distribution | Published latest.json and checksum acquired; snapshot is secret-4 at height 27442876, created 2026-10-03, 36.5 GB compressed. Provider explicitly calls it pruned and unsuitable for history. Public RPC request for 11880919 reports lowest retained height 26594224. | No huge pruned tarball downloaded. archive-00/archive-01 appear as node labels, not proof of a public historical download/API. Public archive/RPC docs acquired; no independent archive distribution found. |
| Stakecraft snapshot catalog | DNS acquisition failed, recorded in two stages. | Access failure remains incomplete and is not evidence that a Secret archive never existed. |

## Completion criteria and outstanding sources

Do not close this phase as exhausted while the Numia dataset lead lacks actual source rows, public export, or a verified coverage rejection. Do not bypass the owner's no-account restriction to query BigQuery/ObsessionDB. A public immutable export or an operator-provided, publicly accessible block-header dump could resolve this limitation.

Potential operator-held validator backups, historical explorer DBs, telemetry/log exports and unadvertised IPFS/torrent objects remain unavailable without a public address or file. This pass did not contact operators or guess credentials. Search negatives and inaccessible catalogs do not certify global nonexistence.

If a new artifact arrives, verify secret-4 identity and source provenance, preserve raw bytes and hashes, establish consecutive H-1/H/H+1, retain all header fields and canonical block hashes, check last_block_id adjacency, compare nanosecond timestamps with V (time(H-1)<V<=time(H)), and independently validate canonicality before updating the source gate. Extract only public chain metadata; do not restore a validator, initialize a wallet, run operator scripts, or inspect market/outcome tables.

Manual GitHub workflow scrt287-forensic-public-v54-v59.yml reproduces the scoped metadata checks on this branch, with read-only repository permissions and durable artifact upload. Local acquisition and byte-integrity verification were run; a GitHub Actions execution is not claimed.
