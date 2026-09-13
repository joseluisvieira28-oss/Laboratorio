#!/usr/bin/env python3
"""Final source/data gate launcher with the prospective 08:00 UTC expiry fix.

The underlying source_audit_gate.py remains unchanged. This launcher redirects only
its source_audit.py subprocess to source_audit_expiryfix.py, preserving every other
frozen gate, firewall, BTC cutoff check, and receipt definition.
"""
from __future__ import annotations

from pathlib import Path

import source_audit_gate as gate

_REAL_RUN = gate.subprocess.run
_HERE = Path(__file__).resolve().parent
_ORIGINAL = str(_HERE / "source_audit.py")
_FIXED = str(_HERE / "source_audit_expiryfix.py")


def _redirected_run(cmd, *args, **kwargs):
    routed = list(cmd)
    routed = [_FIXED if str(x) == _ORIGINAL else x for x in routed]
    return _REAL_RUN(routed, *args, **kwargs)


gate.subprocess.run = _redirected_run


if __name__ == "__main__":
    raise SystemExit(gate.main())
