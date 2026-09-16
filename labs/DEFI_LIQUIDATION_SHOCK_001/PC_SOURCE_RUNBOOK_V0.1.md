# DEFI-LIQUIDATION-SHOCK-001 — PC SOURCE RUNBOOK V0.1

Purpose: acquire the missing 2021-2024 liquidation source evidence without opening market outcomes.

## Safety

- READ-ONLY only.
- Never send the Helius API key in chat, GitHub, Drive, screenshots or ZIPs.
- No wallet/private key is required.
- No exchange credentials are required.
- No transaction submission is required.
- Do not run any price/return/PnL query.
- Do not merge this branch to `main`.

## Part A — update the research branch

Open **PowerShell**.

If the repository is already on the PC:

```powershell
cd C:\PATH\TO\Laboratorio
git status
git fetch origin
git switch defi-liquidation-shock-v0.1
git pull --ff-only origin defi-liquidation-shock-v0.1
```

If `git status` shows uncommitted work, STOP before switching/resetting and preserve it.

If the repository is not on the PC:

```powershell
cd $HOME\Desktop
git clone https://github.com/joseluisvieira28-oss/Laboratorio.git
cd .\Laboratorio
git fetch origin
git switch defi-liquidation-shock-v0.1
```

Then:

```powershell
cd .\labs\DEFI_LIQUIDATION_SHOCK_001
py .\source\test_source_collector_synthetic_v0_1.py
py .\source\test_bigquery_verifier_synthetic_v0_1.py
```

Expected: both commands end in `PASS ... synthetic ... tests`.

## Part B — BigQuery public-data source probe

Use Google Cloud BigQuery. BigQuery Sandbox is sufficient; no credit card is required.

Processing location: **US** (the public Solana dataset is in the US multi-region).

First query:

`source/BIGQUERY_PROGRAM_COVERAGE_PROBE_V0_1.sql`

Before running, inspect the BigQuery editor's bytes-to-be-processed estimate. If it is unexpectedly huge, do not improvise another query; record the estimate.

Run the query and preserve the four-row result.

Expected columns include:

- protocol
- program_id
- instruction_rows
- distinct_transactions
- first_instruction_utc
- last_instruction_utc
- outer_instruction_rows
- inner_cpi_instruction_rows

This result is source coverage only, not an edge result.

## Part C — BigQuery liquidation candidate census

Second query:

`source/BIGQUERY_LIQUIDATION_CANDIDATE_CENSUS_V0_1.sql`

This query:

- reads only Solana instruction source data;
- filters the frozen period 2021-2024;
- filters only the four pre-registered program IDs;
- Base58-decodes raw instruction data inside BigQuery;
- matches only pre-registered reference liquidation prefixes;
- includes inner/CPI instructions through `parent_index`;
- does not query prices or returns.

Before running, inspect the estimated processed bytes. As a safety rule for this first pass:

- if estimate <= 100 GB: run it;
- if estimate > 100 GB: STOP and report only the estimate so the query can be redesigned before consuming more of the free monthly quota.

After it finishes, use **Save results -> CSV (local file)** and save as:

`DLS_BIGQUERY_LIQUIDATION_CANDIDATES_V01.csv`

Do not edit the CSV manually.

## Part D — configure archival RPC locally

Create/use a Helius Free project if needed. Only an RPC API key is needed.

In the same PowerShell window set the key as a temporary environment variable:

```powershell
$env:HELIUS_API_KEY="PASTE_THE_KEY_HERE_LOCALLY"
```

Do NOT paste the value anywhere else.

Optional confirmation that the variable exists without printing the secret:

```powershell
if ($env:HELIUS_API_KEY) { "HELIUS_API_KEY is set" } else { "HELIUS_API_KEY missing" }
```

## Part E — raw-verify BigQuery candidates

Assuming the CSV is in Downloads:

```powershell
$csv = "$HOME\Downloads\DLS_BIGQUERY_LIQUIDATION_CANDIDATES_V01.csv"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = "$HOME\Desktop\DLS_VERIFY_2021_2024_$stamp"

py .\source\verify_bigquery_candidates_v0_1.py --input $csv --out-dir $out
```

The verifier fetches each unique candidate transaction once, preserves raw JSON-RPC bytes/hashes, and reconciles slot, time, success/failure, outer/CPI location, program ID and discriminator bytes.

Expected output files include:

- `RUN_MANIFEST.json`
- `RPC_RECEIPTS.json`
- `CANDIDATE_SUMMARY.json`
- `VERIFICATION_ROWS.jsonl`
- `raw_rpc/candidate_transactions/*.json`

A complete run still does NOT automatically mean `SOURCE_DATA_PASS`; historical decoder/version authority remains a separate gate.

## Part F — package evidence

```powershell
$zip = "$out.zip"
Compress-Archive -Path "$out\*" -DestinationPath $zip -CompressionLevel Optimal
Get-FileHash $zip -Algorithm SHA256
```

Upload the ZIP to Google Drive or attach it to the Crypto project conversation. Share the **ZIP filename and SHA-256**, never the API key.

## If anything fails

Do not reset, tune, alter thresholds or substitute another data source. Preserve:

- exact command used;
- full terminal error;
- generated `RUN_ERROR.json` if present;
- BigQuery error text / bytes estimate.

The failure will be classified technically instead of being confused with `NO_EDGE`.
