# MSEL-002 — Source Schema / Code Audit Freeze V0.1

Status: `SOURCE_SCHEMA_AUDIT_AUTHORIZED / RECORD_ROWS_LOCKED`

S0 inventory completed without opening record-level data.

S0 facts:

- public deposit DOI: `10.1184/R1/33420628.v1`
- article id: `33420628`
- 139 files
- total provider-advertised bytes: approximately 352.97 GB
- database dump distributed as multi-part `dump.pgcustom.part-*` files (~5 GiB each for most parts)
- S0 inventory SHA-256: `229c0b0c668945985161df5aecfc7aa19fe56b12ae420ed74a685498147f58b9`
- S0 workflow run: `35101589037`
- S0 workflow artifact: `10448766036`
- S0 artifact digest: `sha256:294c9affe292e401f6da09e545888f7b354259290b242b98ed67423dd2e90825`

## Authorized small-file reads

Before any DB dump part or record-level dataset is opened, download and hash-verify ONLY the following public deposit files:

1. `README.txt`
   - file id `68211631`
   - size `6616`
   - MD5 `1180ae616fc9bfdb5616820efcbdee51`
2. `analyze_copy_tokens.py`
   - file id `68208451`
   - size `27971`
   - MD5 `4580d164cd298ab69d8597c2996908f4`
3. `create_labels.py`
   - file id `68208463`
   - size `19679`
   - MD5 `ac0e52e6c8904a68ae0f785c15707a16`
4. `requirements.txt`
   - file id `68208472`
   - size `318`
   - MD5 `3446684d859f29193044da27129d0b04`

These files are source documentation/code, not candidate outcome rows.

## Audit questions

The audit may determine only:

- exact DB/table names used by copycat analysis;
- exact columns/fields used by the strict copycat detector;
- how original-vs-copy order is determined;
- whether creator equality/cluster equality is excluded;
- whether image identity is a content-addressed hash or mutable URL;
- whether strict labels are materialized in a compact table that could be extracted without restoring all 352+ GB;
- whether the published code exposes a bounded extraction path for September–October 2025;
- whether SQL/table-of-contents metadata can be obtained without opening row values.

## Still forbidden

- no `dump.pgcustom.part-*` download;
- no record-level row inspection;
- no prevalence calculation;
- no copycat counts for our intended candidate window;
- no graduation/price/return/trade outcomes;
- no candidate selection;
- no MSEL-001 rescue or threshold tuning.

After this audit, issue a Source Gate classification before any record rows are opened.
