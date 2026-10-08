#!/usr/bin/env python3
"""Verify previously durable receipt bytes and the original freeze."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "persistence_baseline.json").read_text())
for path, expected in manifest["sha256"].items():
    p = ROOT / path
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
        raise SystemExit(f"FAIL: immutable baseline changed: {path}")
print("PASS: durable baseline receipts and freeze unchanged")
