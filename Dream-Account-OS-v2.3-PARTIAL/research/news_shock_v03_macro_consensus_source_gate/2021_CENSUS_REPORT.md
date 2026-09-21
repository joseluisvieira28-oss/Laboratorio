# News Shock Lab V0.3 — 2021 Macro Consensus Census

**Decision: 2021 CENSUS: BLOCKED**

## Scope and frozen universe

The event manifest was committed before consensus research. It contains exactly 24 releases:
12 CPI and 12 Employment Situation releases, all in 2021, all scheduled for 08:30
`America/New_York`. UTC conversion is DST-aware: 13:30Z in EST and 12:30Z in EDT.

No price, return, volume, yield reaction, PnL, backtest, 2025, or 2026 data is present.

## Result

| Metric | Result |
|---|---:|
| Complete events | 0 / 24 |
| Complete CPI | 0 / 12 |
| Complete NFP | 0 / 12 |
| Accepted consensus fields | 0 / 108 |
| Official actual/revision fields preserved | 108 / 108 |
| Conflicting eligible events | 0 |
| Events without defensible consensus timestamp | 24 |
| Events without accepted consensus | 24 |
| Mean evidence age before T0 | N/A |
| Reuters dependency | 0% of accepted fields |
| Single-source dependency | N/A (no accepted consensus) |
| Independent consensus validation | 0 / 24 |

Every event is classified `CONSENSUS_PROVENANCE_INCOMPLETE`. No null was imputed, and no
post-release article was promoted to pre-release evidence.

## Authorities and evidence handling

- BLS archived releases are the authority for first-release actuals and the payroll revisions
  known at T0.
- Reuters public pages were evaluated as discovery. Accessible examples carried post-release
  timestamps and therefore could not establish that a forecast was public before T0.
- Institutional public research did not yield a stable, field-complete, timestamp-defensible
  record for the frozen specification.
- FRED/ALFRED remain vintage validators, never consensus authorities.
- Historical calendar aggregators were rejected where historical values could be mutable or
  provenance/timestamp could not be demonstrated.
- No Wayback snapshot after T0 was treated as proof of pre-T0 availability.

The CSV evidence hashes for official actuals cover normalized evidence records (event, field,
value, canonical BLS URL), not raw BLS bytes. Direct scripted retrieval returned HTTP 403;
this limitation is explicit in the receipt and prevents the hashes from being misrepresented
as raw-page preservation.

## Field coverage

All frozen consensus fields have 0% accepted coverage. There is therefore no statistically
meaningful “weakest” field: they are tied. The strongest source is BLS, but only for actuals
and release-time revisions; it contributes no consensus.

## Scaling assessment

The methodology scales mechanically: manifest-first enumeration, DST-aware T0, field-level
evidence, null preservation, source classification, hashes, and automated leakage checks all
generalize. The evidence supply does not yet scale. A 2022 extension would reproduce the same
known blocker without first adding a defensible historical expectation archive.

## Decision summary

- Coverage: 0/24 complete.
- CPI coverage: 0/12 complete.
- NFP coverage: 0/12 complete.
- Weakest field: all consensus fields (tie, 0%).
- Strongest source: BLS archived first releases, actuals/revisions only.
- Single-source dependency: not measurable; no consensus accepted.
- Conflicting events: 0 eligible conflicts.
- Unresolved events: 24.
- Evidence that methodology scales: deterministic manifest, schema, receipts, hashes, tests.
- Main scaling risk: free/public historical consensus lacks immutable pre-T0 timestamps and
  field-complete provenance.

## Smallest authorized next step

Obtain read-only access to one historical institutional news/poll archive and probe **one**
frozen 2021 CPI event plus **one** frozen 2021 NFP event against the unchanged rules. Do not
extend to 2022 unless that two-event probe yields preserved pre-T0 timestamps and all required
fields.
