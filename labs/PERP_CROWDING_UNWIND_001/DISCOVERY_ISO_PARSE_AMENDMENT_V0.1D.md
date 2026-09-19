# PERP-CROWDING-UNWIND-001 — DISCOVERY ISO-STRING PARSE AMENDMENT V0.1D

Date: 2026-09-19
Parent run: `35472028217`

The source coverage gate again passed **48 / 48 FULL months** before outcomes.

The Discovery then reached trade-record construction but stopped while converting already-created ISO timestamp strings into calendar years for year-level summary statistics. Python emitted valid ISO strings with mixed presence/absence of fractional seconds, and pandas inferred a single strict format.

V0.1D changes only that summary conversion to `pd.to_datetime(..., format="mixed", utc=True)`.

No trade selection, timestamp value, feature, threshold, direction, return, cost, bootstrap, gate, sample period or protected-period rule changes. The failed run did not emit a completed Discovery receipt and remains non-adjudicative.
