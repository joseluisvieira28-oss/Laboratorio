#!/usr/bin/env python3
"""Persist an already captured receipt; never fetch or reconstruct source data."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("receipt", type=Path)
    args = ap.parse_args()
    data = args.receipt.read_bytes()
    payload = json.loads(data)
    name = payload["observed_at_utc"].replace(":", "-") + ".json"
    if "/" in name or "\\" in name or ".." in name:
        raise SystemExit("FAIL: unsafe receipt timestamp")
    existing = sorted((ROOT / "observations").glob("*.json"))
    if existing and payload["observed_at_utc"] <= json.loads(existing[-1].read_text())["observed_at_utc"]:
        raise SystemExit("FAIL: receipt must be a new prospective capture after the last durable observation")
    target = ROOT / "observations" / name
    if target.exists():
        raise SystemExit("FAIL: receipt already exists; append-only")
    with tempfile.TemporaryDirectory() as td:
        staged = Path(td) / "study"
        shutil.copytree(ROOT, staged)
        (staged / "observations" / name).write_bytes(data)
        subprocess.run([sys.executable, str(staged / "validate_forward_receipts.py")], check=True)
        # Exclusive creation prevents replacement, including a concurrent writer.
        with target.open("xb") as out:
            out.write(data)
            out.flush()
            import os
            os.fsync(out.fileno())
    print(f"PERSISTED_LOCALLY: {target.name}; durable Git receipt requires commit and successful CI")

if __name__ == "__main__":
    main()
