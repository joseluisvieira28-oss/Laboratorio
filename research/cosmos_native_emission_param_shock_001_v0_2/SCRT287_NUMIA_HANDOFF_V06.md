# SCRT287 Numia forensic handoff V0.6

Date: 2026-10-07. Scope: public source-only; no market/outcome acquisition.
Requested baseline: `29ff9fadfaa62f520f1403f605637e3847f1e971`.
The existing checkout matched that baseline. The remote branch had advanced through V69; it was fast-forwarded to `df57b18` before adding these artifacts. Prior receipts and semantics remain unchanged.

## Legitimate verdict

**NUMIA_DIRECT_QUERY_REQUIRES_USER_LOGIN**. Canonical H and T0 remain uncertified; source gate remains **11/12**, `SOURCE_HISTORICAL_EXECUTION_BOUNDARY_BLOCKED`.
Forensic phase remains `OPEN_NOT_EXHAUSTED`. This is an access handoff, not a coverage rejection, source exhaustion, NO_EDGE, or economic verdict.

The best concrete next step is a bounded read-only BigQuery query. No authentication was attempted, no SQL was submitted, and no credentials were inspected or used. No main merge, account mutation, wallet access, trading or outcome work occurred.

## What was acquired

V70/V71 executed 46 unauthenticated GET requests: 45 raw responses preserved and byte/hash verified; one transport failure. Each response has URL, retrieval time, status, byte count, SHA256 and classification. No automatic redirects, credentials or unverified TLS. See `forensic_numia_v70/receipt.json`, `forensic_numia_v71/receipt.json` and `SCRT287_NUMIA_INTEGRITY_V70_V71.json`.

1. Full public Numia docs Git history was cloned and inspected, pinned at `8e67930bee1d99acf933cc4a000b90258b352f68`. Secret paths and commits are retained in `SCRT287_NUMIA_GIT_HISTORY_V70.json`. No historical schema revision contained the searched coverage markers `backfill`, `2023-12`, `genesis`, `min_block`, or `earliest`. This bounded text search does not establish dataset absence.
2. Earliest schema commit found: `e5d7d16f7f580ef6621196a4ba56d73972bbb825`, 2024-12-02. It already names dataset `secret` and `secret_blocks`, but lacks the current `header` and `signatures` fields. That date describes documentation history, not data start or retention. Current schema contains both JSON fields; the official metadata generator pins project `numia-data`.
3. Wayback CDX yielded the exact historical path `overview/sql-access/chains/secret-network`, with captures on 2024-04-17, 2024-07-18, 2024-11-04 and 2025-01-15. All four pages were retrieved and their visible text includes `select * from numia-data.secret.secret_blocks`. This moves public documentation evidence back to April 2024, but does not prove December 2023 rows. No broad example query was executed.
4. `using-numia/chains/secret*` CDX returned an empty list. Broad docs Secret CDX timed out; that route remains incomplete. The guessed live legacy paths returned 404. Exact Git path-history queries returned no records for those guessed paths; the actual historical Git path is documented in the ledger.
5. Public forks catalog returned empty. Numia organization repositories, tools/site/proxy trees and public reports tree were inspected for documentary/export discovery. Public reports catalog listed unrelated dYdX reports; report bodies and images were not opened. A repository search found a Neutron schema dump (`yodablocks/db-n-`), not Secret evidence. No Secret export was identified in these inspected catalogs.
6. Exact public web searches yielded no target-row export or backfill proof. GitHub unauthenticated code search returned 401; grep.app returned 429. These are access limitations, not negative coverage evidence. Search query output is retained in `SCRT287_NUMIA_SEARCH_LEDGER_V70.json`.
7. Exact BigQuery dataset/list/table/data routes under `numia-data.secret`, including `secret_blocks` and `secret_block_events`, returned 401 `UNAUTHENTICATED` / `CREDENTIALS_MISSING`. Legacy `immaculate-355716` metadata routes also require authentication; its sampled data route returned 404. None certifies actual coverage or table existence today.
8. Numia's 2024-02-27 partnership announcement was visible through the web research tool and specifies Google-account access without special Numia approval. Direct raw acquisition returned 403. The referenced Foundation PDF direct route returned 404; neither failure was silently replaced with fabricated raw evidence.

## Exact user action needed

Open https://console.cloud.google.com/bigquery and personally sign in with a Google account. Use BigQuery sandbox with an existing or newly selected sandbox project and no billing enabled. Pin the public project `numia-data`, expand `secret`, and open `secret_blocks`. Make that signed-in browser tab available to the assistant and indicate that login is complete. Do not send passwords, tokens or service-account keys.

Google's sandbox guide documents use without a credit card or billing account: https://docs.cloud.google.com/bigquery/docs/sandbox . If the interface requires billing activation, purchase, an organization approval or Numia-specific permission, stop and report the exact prompt. No bypass or purchase is authorized.

Prepared SQL: `SCRT287_NUMIA_HEADER_WINDOW_V70.sql`. It selects only heights, timestamps, chain ID, validator hash, complete header JSON and signatures for a 90-second window around voting end. It is a retrieval query, not an H certification query. Inspect the query byte estimate before execution, use a bounded maximum bytes billed, and proceed only within the free sandbox allowance. `LIMIT` alone would not bound scan cost, so it is not used as a cost claim. Partition/cluster layout and current schema must be inspected after authorized login; they are not verified by anonymous metadata.

## Certification requirements after retrieval

Keep the complete JSON result, query text, job identity, table metadata, retrieval time and hashes. Preserve duplicates and conflicting versions. Obtain consecutive H-1/H/H+1, preferably also H+2 to expose the next header's `last_block_id.hash` for H+1. Require `secret-4`, exact integer heights, full header fields, computed canonical Tendermint header hashes and linked `last_block_id` adjacency. Cross-check available preserved IBC anchors and independent canonicality evidence. `validators_hash` is not a block hash, and a downloaded response hash is not canonicality proof.

BigQuery `TIMESTAMP` has microsecond precision (Google data-types reference, preserved in V71); it cannot alone certify the nanosecond inequality. Parse original `header.time` as integer nanoseconds without float or microsecond rounding and verify `time(H-1) < 2023-12-07T02:54:58.930543213Z <= time(H)`. If header.time is absent, rounded, inconsistent or provenance/canonicality remains unresolved, keep the gate blocked. Do not infer coverage from the launch announcement or documentation age. An empty window is a source result for that table/window only, not global exhaustion.

Only after these checks actually pass may the frozen rule set T0=H+1. Existing V64 derives time(11880918) before voting end but does not certify the target boundary; this pass does not change that conclusion.

## Reproducibility and publication boundary

`forensic_scrt287_numia_v70.py` and V71 reuse the reviewed unauthenticated acquisition helper. Existing receipt directories cannot be overwritten by these entrypoints. `verify_scrt287_numia_v70_v71.py` verifies every saved raw byte count/SHA256 and extracts documentary text without executing HTML/scripts.
The manual workflow `.github/workflows/scrt287-forensic-numia-v70-v71.yml` uses read-only repository permissions and isolated output, preserving committed receipts. Local acquisition and integrity verification passed. No GitHub Actions execution is claimed.
