# Source Reliability V2.1

Independent, public-only source study on #335. Read PROTOCOL.md and VERDICT.md before interpreting signals. A qualified observation is not a fill or a return.

Offline reproduction (Python 3.12; standard library only):

    python -m unittest discover -s research/source_reliability_v21 -v
    python research/source_reliability_v21/audit_zip.py research/source_reliability_v21/evidence-20261104.zip audit-reproduced.json

The auditor opens the ZIP itself, verifies compressed/raw/protocol/code SHA256, checks receipt clocks and sequence, and separately reconstructs source validity, joint coverage, episodes and signals. It never imports the collector. No network needed. Compare ZIP SHA256 with evidence-20261104.zip.sha256 before audit. ZIP contains exact raw gzip, original capture report/manifest, frozen source/protocol, provenance and auditor. Tests use clearly separate synthetic fixtures, never merged into public raw.

Collection authority is consumed by the one bounded capture in this PR. Do not invoke source.py again, extend this window, schedule it, or turn a signal into PnL under this authority. Source code has no order transport. Optional capture dependency was websockets==15.0.1; not needed for offline audit.

Time representation uses nanosecond integer fields but Windows runtime clock resolution was 15.625ms, recorded in PROVENANCE.json. No nanosecond accuracy or exchange-wide liquidation census is certified. Per-venue book gaps, quarantines and interruption records are evidence, not zero-filled periods.
