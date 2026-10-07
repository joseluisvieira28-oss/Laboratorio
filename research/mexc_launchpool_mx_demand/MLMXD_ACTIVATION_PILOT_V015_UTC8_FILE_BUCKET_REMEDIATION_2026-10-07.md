# MLMXD ACTIVATION PILOT V0.1.5 — UTC+8 FILE-BUCKET REMEDIATION
Date: 2026-10-07
Status: TECHNICAL REMEDIATION; SCIENCE UNCHANGED

V0.1.4 proved the official MEXC daily Min15 files use a UTC+8 file-day boundary:
- file YYYY-MM-DD begins at previous UTC date 16:00;
- file ends at YYYY-MM-DD 15:45 UTC.

Therefore the deterministic filename bucket for an immutable UTC timestamp t is:
file_date = date(t + 8 hours).

The prior V0.1.3 N=0 is a transport mapping failure and has no scientific meaning.

Permitted correction:
- map each exact frozen T0/+1h/+6h/+24h timestamp to the official file whose date equals UTC timestamp + 8h;
- all 14 events, timestamps, horizons, metrics, seed and gates remain unchanged.

Forbidden:
- no scientific rule change;
- no event addition/deletion;
- no interpolation;
- no alternate venue;
- no gate change.
