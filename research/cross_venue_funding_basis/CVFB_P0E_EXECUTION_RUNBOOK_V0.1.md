# CVFB P0E — bounded `replica_cmds` requester-pays execution runbook V0.1

**Status: PREPARED / NOT AUTHORIZED.**

This runbook does not authorize requester-pays charges, AWS credential use, historical object access, economic outcomes, 2026 data, live trading, exchange mutation, or merge to `main`.

## Scientific authority

- Parent primary remains `CLOSED / REPLICATION_INCONCLUSIVE / UNPROVEN`.
- P0E freeze: `CVFB_NATIVE_ORACLE_PROVENANCE_P0E_REPLICA_CMDS_REQUESTER_PAYS_FREEZE_V0.1.json`.
- Frozen Git blob SHA: `3f4e3a43636ea9a17a1c9cbc60e25410bff6a6fe`.
- Source: `s3://hl-mainnet-node-data/replica_cmds` only.
- Frozen height range: `280538152..280538452`, exactly 301 heights.
- Historical economic outcomes remain closed.

## Mandatory activation gates

P0E may execute only after **all** of the following are true before the first S3 request:

1. The user has separately and explicitly authorized requester-pays charges and AWS credential use for this exact P0E probe.
2. A new immutable file exists at the exact path:
   `research/cross_venue_funding_basis/CVFB_NATIVE_ORACLE_PROVENANCE_P0E_REQUESTER_PAYS_AUTHORIZATION_V0.1.json`.
3. That authorization file pins the frozen blob SHA above and has all of these exact values:
   - `status = AUTHORIZED_BEFORE_FIRST_REQUESTER_PAYS_S3_REQUEST`
   - `requester_pays_charges_authorized = true`
   - `aws_credentials_authorized = true`
   - `execution_authorized = true`
   - `economic_outcomes_authorized = false`
   - `primary_replication_reopened = false`
   - `2026_authorized = false`
4. Runtime confirmation equals exactly:
   `I_EXPLICITLY_AUTHORIZE_CVFB_P0E_REQUESTER_PAYS`.
5. AWS credentials are supplied through a secure runtime secret/environment mechanism. Never commit access keys, secret keys or session tokens to Git, the authorization file, an artifact, a log, or chat.
6. Credentials should be dedicated/temporary and restricted to the policy in `CVFB_P0E_AWS_MINIMAL_READONLY_POLICY_V0.1.json`.

If any gate is missing, the runner must stop with `BLOCKED_NO_AUTHORIZATION` before creating the source receipt or making an S3 request.

## Least-privilege AWS scope

The prepared policy allows only:

- `s3:ListBucket` on `hl-mainnet-node-data`, restricted to `replica_cmds` prefixes.
- `s3:GetObject` on `hl-mainnet-node-data/replica_cmds/*`.

There is no write, delete, ACL, bucket-policy, lifecycle, object-tagging, or other mutation permission.

## Frozen cost/completeness envelope

Before body downloads, the runner must resolve the canonical key shape and HEAD all 301 frozen objects.

Hard caps:

- LIST requests: 1100 maximum.
- HEAD requests: 301 maximum.
- GET requests: 301 maximum.
- Single compressed object: 1 MiB maximum.
- Total compressed object bodies: 32 MiB maximum.

If key resolution is ambiguous, a frozen object is missing, a decoder is unsupported, or a request/byte cap would be exceeded, stop fail-closed.

Planning-only cost file: `CVFB_P0E_COST_ENVELOPE_V0.1.json`.
The conservative planning math is USD 0.017852 and the planning ceiling is USD 0.05. This is not an AWS invoice guarantee and is not authorization to incur charges.

## Frozen parsing surface

Only these decoder paths are admitted:

- raw UTF-8 JSON;
- UTF-8 JSON Lines;
- LZ4 frame → JSON/JSON Lines;
- MessagePack stream;
- LZ4 frame → MessagePack stream.

Synthetic no-S3 CI passed 7/7 before this runbook was finalized.

## Source-only output policy

Allowed receipt material:

- resolved object keys;
- compressed byte counts;
- SHA256 fingerprints;
- record counts;
- decoder labels;
- JSON/message key paths;
- action/type/variant/kind labels;
- non-HIP-3 oracle-schema candidate yes/no;
- completeness/request-count diagnostics.

Forbidden:

- raw object bodies in the receipt;
- oracle numeric values;
- mark/mid/price numeric values;
- funding cashflow;
- basis PnL;
- full-mechanism return;
- orientation comparison;
- asset ranking;
- 2026 market data.

HIP-3 `perpDeploy/setOracle` is explicitly insufficient as native BTC/ETH validator-oracle evidence.

## Manual execution path

Prepared workflow: `.github/workflows/cvfb-native-oracle-p0e-execute-v01.yml`.

It is `workflow_dispatch` only. It must never have a `push` or `pull_request` trigger.

The manual workflow expects repository/environment secrets for AWS credentials and the exact runtime confirmation input. The runner itself remains the final authority gate.

## Decision semantics

- `PASS_NATIVE_ORACLE_SCHEMA_CANDIDATE`: only permits a separately frozen P1 reconstruction audit. It does **not** reopen the primary replication or establish an edge.
- `FAIL_NO_NATIVE_ORACLE_SCHEMA_VISIBLE`: closes the frozen `replica_cmds` schema path under P0E.
- `TECHNICAL_BLOCKED_COST_OR_COMPLETENESS_CAP`: no economic inference.
- `BLOCKED_NO_AUTHORIZATION`: no source access occurred.

## Post-run security hygiene

After an authorized P0E run:

1. remove/rotate the temporary AWS credential as appropriate;
2. preserve the immutable authorization amendment, workflow run ID and receipt artifact hashes;
3. do not promote or merge automatically;
4. adjudicate only the frozen P0E source-schema decision;
5. keep 2026 and all economic outcomes closed unless a later, separate authority explicitly opens a new gate.
