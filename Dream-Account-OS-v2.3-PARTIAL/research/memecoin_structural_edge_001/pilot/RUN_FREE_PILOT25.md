# MSEL-001 — RUN FREE PILOT-25

Status: RESEARCH-ONLY / READ-ONLY / OUTCOMES LOCKED

## Requirement

One archival Solana RPC credential/URL. A free Helius project key is sufficient for the standard blockscan route according to current Helius documentation.

Do **not** commit the key to GitHub and do not place it in logs.

## macOS / Linux

```bash
cd Dream-Account-OS-v2.3-PARTIAL/research/memecoin_structural_edge_001/pilot
export HELIUS_API_KEY='YOUR_KEY_IN_LOCAL_SHELL_ONLY'
python3 collect_25_creates_blockscan_free.py
```

## Windows PowerShell

```powershell
cd Dream-Account-OS-v2.3-PARTIAL/research/memecoin_structural_edge_001/pilot
$env:HELIUS_API_KEY='YOUR_KEY_IN_LOCAL_SHELL_ONLY'
python collect_25_creates_blockscan_free.py
```

Alternative provider:

```bash
export MSEL_RPC_URL='https://your-authorized-archival-rpc.example'
python3 collect_25_creates_blockscan_free.py
```

## Expected outputs

Default output directory:

`data/msel001_pilot25_blockscan/`

Expected evidence:

- `cohort_25.jsonl`
- `source_manifest.json`
- `rpc_receipts.json`
- `raw_rpc/*.json`

The script prints the final cohort SHA-256 and manifest SHA-256.

## PASS requirements

- exactly 25 unique CREATE events;
- exactly 25 unique mints;
- blockTime strictly greater than frozen timestamp;
- successful transactions only;
- historical CREATE schema decodes;
- canonical block transaction order preserved;
- exact raw RPC response bytes retained and hashed;
- manifest states `outcomes_opened=false`.

## FAIL-CLOSED classes

Do not repair by changing sample rules.

- `PROVIDER_HISTORY_STARTS_AFTER_FROZEN_TIME`
- `BOUNDARY_PAD_INSUFFICIENT`
- `NON_MONOTONIC_BLOCKTIME`
- `GET_BLOCK_NULL_OR_BAD`
- `GET_BLOCK_MISSING_FULL_TRANSACTIONS`
- `MULTI_CREATE_TX_UNSUPPORTED`
- `INSUFFICIENT_SOURCE_WINDOW`
- `DUPLICATE_MINT_IN_FROZEN_COHORT`
- RPC auth/rate-limit/provider failures

Any failure is a source/technical issue, not `NO_EDGE`.

## After PASS

Do not open future returns yet.

Next authorized sequence:

1. reconcile 25 mint/signature/slot identities against an independent source;
2. reconstruct Pump trades + direct SPL transfers only through T+5;
3. build point-in-time creator/funder/entity evidence;
4. freeze feature matrix + hashes;
5. only then open the predefined outcomes.
