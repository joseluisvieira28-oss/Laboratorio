# LL-0017 — SOURCE NORMALIZATION AMENDMENT V0.1A

Date: 2026-09-18
Status: **FROZEN BEFORE REMEDIATED SOURCE RERUN / OUTCOME-BLIND**

Parent V0.1 authority and failure remain immutable.

Observed evidence:
- Parent source run `35365438710`: `PROVENANCE_FAILURE` due duplicate timestamps on 2021-01-15.
- Frozen diagnostic run `35365589487`: `EXACT_PROVIDER_ROW_DUPLICATION_CONFIRMED`.
- 576 raw rows, 288 unique timestamps.
- Every timestamp had multiplicity exactly 2.
- All 288 duplicate groups had exactly one raw-row SHA-256.
- Zero duplicate groups contained non-identical rows.
- No ratio values, prices, returns or PnL were opened.

## Narrow normalization rule

For the remediated source gate only:

1. Group rows by exact timestamp.
2. If a timestamp occurs once, keep the row.
3. If a timestamp occurs more than once:
   - compute SHA-256 of the complete original raw CSV line bytes;
   - PASS normalization only if every row in that timestamp group has the same raw-line SHA-256;
   - retain exactly one representative row.
4. If any duplicate timestamp group contains more than one raw-line SHA-256, fail `PROVENANCE_FAILURE`.
5. No field-level preference, averaging, last-write-wins, first-value selection or metric comparison is allowed.
6. No metric numeric field may be parsed to perform deduplication.

This amendment changes only provider-byte normalization. It does not change:
- dates;
- symbol;
- source;
- schema requirements;
- timestamp cadence gate;
- protected periods;
- any future hypothesis or economic rule.

The original V0.1 provenance failure remains preserved as historical evidence.

## Remediated pass rule

After exact-row deduplication, all original V0.1 source gates apply to the normalized structural rows.

A V0.1A pass authorizes only the separately frozen 2021-2024 source coverage census. It does not authorize ratio-value inspection, predictor construction, market outcomes or Discovery.
