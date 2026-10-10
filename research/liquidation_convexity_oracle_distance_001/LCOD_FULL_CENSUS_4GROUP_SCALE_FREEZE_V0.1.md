# LCOD FULL-CENSUS 4-GROUP SCALE FREEZE V0.1

Frozen: 2026-09-24
Parent: LCOD_FULL_CENSUS_FORWARD_CURVE_PROTOCOL_V0.1

Shard-0 preflight passed with 127 / 128 debt-bearing borrowers eligible (99.21875%),
above the already frozen >=90% source coverage gate. One borrower failed the
existing <=5e-5 HF reconciliation tolerance. The tolerance is NOT changed.

The remaining source scaling is deterministic and outcome-blind.

Groups:
- 0123
- 4567
- 89ab
- cdef

Selection:
sha256(lowercase_wallet)[0] in the group's four hexadecimal prefixes.

Each group must:
- independently re-enumerate all v4 borrower-index reserves with frozen pagination;
- retain no raw wallet address in durable receipts;
- use the frozen <=5e-5 HF reconciliation tolerance;
- explicitly exclude failures, never impute;
- compute no liquidation shock curve;
- open no liquidation outcome, market return, direction or PnL.

Group PASS:
- >=90% of current debt-bearing borrowers eligible;
- zero census errors;
- zero silent component read errors.

Overall FULL_CENSUS_SOURCE_PASS requires all four groups PASS and the union of
group indexed borrower counts to equal the current frozen census count for that run.
This scaling earns ZERO edge/promotion credit.
