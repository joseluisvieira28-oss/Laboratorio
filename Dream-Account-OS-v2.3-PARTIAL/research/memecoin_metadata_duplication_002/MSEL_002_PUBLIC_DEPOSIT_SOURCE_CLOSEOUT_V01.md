# MSEL-002 — Public Deposit Feature-Source Closeout V0.1

Classification: `FEATURE_SOURCE_BLOCKED / MECHANISM_NOT_TESTED`

No record-level candidate rows, prevalence, prices, trades, graduation outcomes, or MSEL-002 economic outcomes were opened.

## Evidence

S0 public-deposit inventory:

- DOI `10.1184/R1/33420628.v1`
- 139 files
- ~352.97 GB compressed/provider-advertised bytes
- 66 multipart PostgreSQL custom-dump chunks
- README states uncompressed DB is over 1 TB and possibly near 2 TB
- S0 inventory SHA-256 `229c0b0c668945985161df5aecfc7aa19fe56b12ae420ed74a685498147f58b9`

S1 hash-pinned source/code audit:

- `README.txt` SHA-256 `a3da352d54345004a5e10a3edda3274a7b69a863e4bc75f76c589f83617cb953`
- `analyze_copy_tokens.py` SHA-256 `2bbe346a5930990151c5df9c70abfda846a5bdee181e1db1823395038c52c50a`
- `create_labels.py` SHA-256 `57c10285d1df11a51004f4c858d54880efb94be7ce7a45287ca8f676b984650a`
- `requirements.txt` SHA-256 `d0925492e7ee3935b4e811e421d3ceab4800dd7e6d77e0c4e382556acf00a1ac`
- S1 report SHA-256 `18d346298a30bfcb2e43ab4484407eb049a46b92c20a9010eebe031eafbdd083`

The deposit README states that the database archive contains the on-chain analysis tables for sections 3–6. It separately states that the data used by scripts for sections 7–8 are NOT available because pump.fun prohibits redistribution of data collected through its API.

The authors' strict copycat-label code reads:

- `website_coin_meta` fields including `name`, `symbol`, `description`, `image_uri`, `creator`, `created_timestamp`;
- strict heuristic 1 = exact `name + symbol + description + image_uri`;
- same exact creator is treated as clone, not copycat;
- same 3-hop creator cluster is also treated as clone;
- candidate/original ordering uses `created_timestamp`; timestamp ties are sorted with `usd_market_cap` and mint in the source implementation.

Those `website_coin_*` data are external pump.fun API data and are not in the redistributable on-chain dump. Therefore downloading/restoring the 352.97 GB public archive cannot, by itself, reproduce the strict primary feature.

## Scientific interpretation

This is a SOURCE classification only. It is NOT `NO_EDGE`, `NO_CAUSAL_EDGE`, or an economic result.

Do not restore the 1–2 TB database merely to search for unavailable website metadata. Do not substitute fuzzy name/symbol matching after discovering this limitation.

## Authorized remediation frontier

A source-remediated, stricter point-in-time variant may use only immutable information committed at CREATE time on-chain. It must be frozen before prevalence is inspected and must remain materially narrower than the unavailable website strict-copycat detector.
