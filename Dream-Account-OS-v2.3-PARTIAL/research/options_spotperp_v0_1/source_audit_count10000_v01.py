#!/usr/bin/env python3
"""
OPTIONS-SPOTPERP-001 — acquisition-only pagination wrapper.

Deribit History API officially supports count up to 10,000 when include_old=true.
The frozen scientific protocol does not freeze page size. This wrapper changes only
COUNT from 1,000 to 10,000 before calling the existing source_audit.py main().

No source, date, instrument, eligibility, signal, outcome, cost or decision rule is
changed. No skew, return or PnL is computed by this wrapper.
"""

import source_audit as base

OFFICIAL_HISTORY_MAX_COUNT = 10_000


def main() -> int:
    base.COUNT = OFFICIAL_HISTORY_MAX_COUNT
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
