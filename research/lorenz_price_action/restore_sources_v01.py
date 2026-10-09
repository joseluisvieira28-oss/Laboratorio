"""Deterministic, human-auditable extraction of source bundles pinned in the freeze.
No external dependencies, account access or secrets. Decoded .py files are uploaded as CI artifacts.
"""
import base64
import gzip
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = {
    "lor_rf_engine_v01.py": "f0c9ee10800a1a6f2f0693d81f163608cdaab3ff0987119aeae2ff339bcdd692",
    "lor_rf_source_gate_v01.py": "c78207936bea57bd07c5b0cc9323dcbd4ebbe6e99689d2b0380da32d8dd9db2e",
    "test_lor_rf_v01.py": "a2d18ebd69be0e44469566b64839efb1583a66a472269509ac0eab913effd2aa",
}

for filename, expected in FILES.items():
    encoded = (ROOT / "artifacts" / (filename + ".gz.b64")).read_text().strip()
    raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    measured = hashlib.sha256(raw).hexdigest()
    if measured != expected:
        raise SystemExit(f"RESEARCH_SOURCE_INTEGRITY_BLOCKED: {filename}: {measured}")
    (ROOT / filename).write_bytes(raw)
    print(f"RESTORED_VERIFIED {filename} {measured}", flush=True)
