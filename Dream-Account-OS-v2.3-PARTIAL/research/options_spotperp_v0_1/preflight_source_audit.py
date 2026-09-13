#!/usr/bin/env python3
"""Outcome-blind static preflight for OPTIONS-SPOTPERP-001 V0.1."""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import py_compile
from pathlib import Path

HERE = Path(__file__).resolve().parent
UTC = dt.timezone.utc


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    src = HERE / "source_audit.py"
    gate_path = HERE / "source_audit_gate.py"
    protocol_path = HERE / "PROTOCOL.json"

    py_compile.compile(str(src), doraise=True)
    py_compile.compile(str(gate_path), doraise=True)

    source = load("options_source_audit", src)
    gate = load("options_source_audit_gate", gate_path)

    binding = gate.protocol_binding(protocol_path)
    assert binding["pass"] is True
    assert binding["authority_sha256"] == "138cee737d75d27b43d9f377fc9a77e823e8fb2015f360b300cdc4a16cf67cfa"

    months = gate.months()
    assert len(months) == 45
    assert months[0] == (2021, 4)
    assert months[-1] == (2024, 12)

    expiry, strike, typ = gate.parse_name("BTC-25JUN21-50000-C")
    assert expiry.isoformat() == "2021-06-25"
    assert strike == 50000.0
    assert typ == "C"

    start_ms = int(dt.datetime(2021, 4, 1, tzinfo=UTC).timestamp() * 1000)
    end_ms = int(dt.datetime(2021, 4, 2, tzinfo=UTC).timestamp() * 1000) - 1
    url = source.build_url(start_ms, end_ms)
    assert "history.deribit.com" in url
    assert "kind=option" in url
    assert "currency=BTC" in url

    blocked = False
    try:
        source.build_url(
            int(dt.datetime(2025, 1, 1, tzinfo=UTC).timestamp() * 1000),
            int(dt.datetime(2025, 1, 2, tzinfo=UTC).timestamp() * 1000) - 1,
        )
    except RuntimeError:
        blocked = True
    assert blocked, "2025 Deribit request firewall did not fail closed"

    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    assert protocol["holdout_2025"] == "LOCKED"
    assert protocol["year_2026"] == "LOCKED"
    assert protocol["source_audit_only"] is True
    assert protocol["status"] == "FROZEN_QUEUED_NOT_AUTHORIZED_FOR_DISCOVERY"

    text = gate_path.read_text(encoding="utf-8")
    assert "forward_returns_computed\": False" in text
    assert "pnl_computed\": False" in text
    assert "holdout_2025_accessed\": False" in text
    assert "year_2026_accessed\": False" in text

    print("OPTIONS_SOURCE_AUDIT_PREFLIGHT_PASS")
    print("NO NETWORK | NO MARKET DATA | NO SKEW | NO RETURNS | NO PNL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
