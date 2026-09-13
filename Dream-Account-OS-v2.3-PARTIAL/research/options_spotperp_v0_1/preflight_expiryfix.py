#!/usr/bin/env python3
"""Outcome-blind preflight for expiry and deterministic raw snapshot corrections."""
from __future__ import annotations

import datetime as dt
import gzip
import py_compile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
UTC = dt.timezone.utc


def main() -> int:
    py_compile.compile(str(HERE / "source_audit.py"), doraise=True)
    py_compile.compile(str(HERE / "source_audit_gate.py"), doraise=True)
    py_compile.compile(str(HERE / "source_audit_expiryfix.py"), doraise=True)
    py_compile.compile(str(HERE / "source_audit_gate_expiryfix.py"), doraise=True)

    import source_audit_expiryfix as fixed

    expiry, strike, typ = fixed.parse_instrument("BTC-25JUN21-50000-C")
    assert expiry == dt.datetime(2021, 6, 25, 8, 0, 0, tzinfo=UTC)
    assert strike == 50000.0
    assert typ == "C"

    # Frozen lower DTE boundary: exactly 30 days must remain eligible.
    lower_trade = dt.datetime(2021, 5, 26, 8, 0, 0, tzinfo=UTC)
    assert (expiry - lower_trade).total_seconds() / 86400.0 == 30.0

    # At 00:00 on the same UTC date, 30 days + 8 hours remain; this confirms
    # the contract is not silently treated as expiring at midnight.
    midnight_trade = dt.datetime(2021, 5, 26, 0, 0, 0, tzinfo=UTC)
    assert (expiry - midnight_trade).total_seconds() / 86400.0 > 30.0

    # Canonical raw snapshot requirement: identical provider response bytes must
    # produce byte-identical gzip files and must round-trip to the original body.
    body = b'{"stable":true,"source":"deribit"}'
    with tempfile.TemporaryDirectory() as td:
        p1 = Path(td) / "a.json.gz"
        p2 = Path(td) / "b.json.gz"
        fixed.write_gz(p1, body)
        fixed.write_gz(p2, body)
        assert p1.read_bytes() == p2.read_bytes(), "gzip bytes are not deterministic"
        assert gzip.decompress(p1.read_bytes()) == body

    print("OPTIONS_EXPIRY_0800_PREFLIGHT_PASS")
    print("DETERMINISTIC_GZIP_PREFLIGHT_PASS")
    print("NO NETWORK | NO MARKET DATA | NO SKEW | NO RETURNS | NO PNL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
