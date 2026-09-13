#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import json
import tempfile
from pathlib import Path

from source_gate_required_field_guard_v01 import audit_required_fields


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_root(row: dict) -> Path:
    root = Path(tempfile.mkdtemp(prefix="options_required_field_guard_"))
    raw = root / "raw"
    raw.mkdir()
    page = raw / "response_000001.json.gz"
    with gzip.open(page, "wb") as f:
        f.write(json.dumps({"result": {"trades": [row]}}).encode())
    (root / "source_manifest.json").write_text(json.dumps({
        "probe_mode": False,
        "source_fetch_complete": True,
        "holdout_accessed": False,
        "locked_2026_accessed": False,
        "raw_pages": [{"page": page.name, "sha256": sha(page)}],
    }))
    return root


def base_row() -> dict:
    return {
        "timestamp": 1617278400000,
        "trade_id": "t1",
        "instrument_name": "BTC-01MAY21-110-C",
        "iv": 60.0,
        "index_price": 100.0,
        "mark_price": 0.01,
        "direction": "buy",
        "amount": 1.0,
    }


def test_all_present_pass() -> None:
    x = audit_required_fields(make_root(base_row()))
    assert x["required_field_presence_pass"] is True
    assert x["missing_required_field_key_total"] == 0


def test_missing_mark_key_blocks() -> None:
    row = base_row(); row.pop("mark_price")
    x = audit_required_fields(make_root(row))
    assert x["required_field_presence_pass"] is False
    assert x["missing_required_field_keys"]["mark_price"] == 1


def test_zero_mark_is_diagnostic_not_missing() -> None:
    row = base_row(); row["mark_price"] = 0
    x = audit_required_fields(make_root(row))
    assert x["required_field_presence_pass"] is True
    assert x["mark_price_nonfinite_or_nonpositive_diagnostic"] == 1


def main() -> None:
    test_all_present_pass()
    test_missing_mark_key_blocks()
    test_zero_mark_is_diagnostic_not_missing()
    print("REQUIRED_FIELD_GUARD_TESTS_PASS")
    print("MISSING MARK KEY BLOCKS | PRESENT ZERO MARK DIAGNOSTIC ONLY")
    print("NO SKEW / NO RETURNS / NO PNL / NO 2025 / NO 2026")


if __name__ == "__main__":
    main()
