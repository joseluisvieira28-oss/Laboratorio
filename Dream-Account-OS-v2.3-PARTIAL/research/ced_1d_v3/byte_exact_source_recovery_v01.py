#!/usr/bin/env python3
"""CED-1D-V1 V3 byte-exact source recovery.

SOURCE-ONLY. No market outcomes. No 2025/2026.
The complete historical target_registry.json is required as machine-readable
input; this runner never reconstructs it from partial evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
import zipfile
from pathlib import Path

SYMBOLS = [
    "ADAUSDT","AVAXUSDT","BNBUSDT","BTCUSDT","DOGEUSDT",
    "ETHUSDT","LINKUSDT","LTCUSDT","SOLUSDT","XRPUSDT",
]
YEARS = {2021, 2022, 2023, 2024}
EXPECTED = 480
UA = "CED-1D-V1-V3-BYTE-RECOVERY/0.1 source-only"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def month_year(month: str) -> int:
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", month):
        raise RuntimeError(f"invalid month: {month}")
    return int(month[:4])


def load_registry(path: Path) -> dict[tuple[str, str], dict]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, list):
        raise RuntimeError("registry must be a JSON array")
    selected = []
    for row in obj:
        if not isinstance(row, dict):
            raise RuntimeError("registry contains non-object row")
        symbol = str(row.get("symbol", ""))
        month = str(row.get("month", ""))
        year = month_year(month)
        if year not in YEARS:
            continue
        if symbol not in SYMBOLS:
            raise RuntimeError(f"unexpected Discovery symbol: {symbol}")
        selected.append(row)
    if len(selected) != EXPECTED:
        raise RuntimeError(f"registry Discovery population != {EXPECTED}: {len(selected)}")
    out = {}
    for row in selected:
        key = (str(row["symbol"]), str(row["month"]))
        if key in out:
            raise RuntimeError(f"duplicate registry key: {key}")
        if row.get("status") != "PASS" or row.get("classification") != "PASS":
            raise RuntimeError(f"historical source row not PASS: {key}")
        if row.get("provider_checksum_match") is not True:
            raise RuntimeError(f"historical provider checksum not PASS: {key}")
        hashes = [str(row.get(k, "")).lower() for k in ("local_sha256", "provider_sha256")]
        if any(not re.fullmatch(r"[0-9a-f]{64}", x) for x in hashes):
            raise RuntimeError(f"invalid historical SHA256: {key}")
        if hashes[0] != hashes[1]:
            raise RuntimeError(f"historical local/provider SHA mismatch: {key}")
        z = row.get("zip_sha256")
        if z is not None and str(z).lower() != hashes[0]:
            raise RuntimeError(f"historical zip/local SHA mismatch: {key}")
        out[key] = row
    expected_keys = {(s, f"{y:04d}-{m:02d}") for s in SYMBOLS for y in sorted(YEARS) for m in range(1, 13)}
    if set(out) != expected_keys:
        missing = sorted(expected_keys - set(out))
        extra = sorted(set(out) - expected_keys)
        raise RuntimeError(f"registry coverage mismatch missing={missing[:5]} extra={extra[:5]}")
    return out


def fetch(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        path.write_bytes(r.read())


def parse_checksum(text: str, expected_filename: str) -> str:
    line = text.strip().splitlines()
    if len(line) != 1:
        raise RuntimeError("malformed provider checksum file")
    parts = line[0].split()
    if len(parts) < 1 or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
        raise RuntimeError("malformed provider SHA256")
    if len(parts) >= 2 and Path(parts[-1].lstrip("*")).name != expected_filename:
        raise RuntimeError("provider checksum filename mismatch")
    return parts[0].lower()


def run(registry_path: Path, out: Path, execute: bool) -> int:
    registry = load_registry(registry_path)
    out.mkdir(parents=True, exist_ok=True)
    preflight = {
        "status": "REGISTRY_BINDING_PASS",
        "registry_path": str(registry_path),
        "discovery_records": len(registry),
        "symbols": SYMBOLS,
        "years": sorted(YEARS),
        "expected_monthly_archives": EXPECTED,
        "year_2025_accessed": False,
        "year_2026_accessed": False,
        "outcomes_computed": False,
    }
    (out / "registry_binding_receipt.json").write_text(json.dumps(preflight, indent=2, sort_keys=True), encoding="utf-8")
    if not execute:
        print("REGISTRY_BINDING_PASS__DOWNLOADS_NOT_EXECUTED")
        return 0

    rows = []
    raw = out / "raw"
    raw.mkdir(exist_ok=True)
    failure = None
    for symbol in SYMBOLS:
        for year in sorted(YEARS):
            for month_i in range(1, 13):
                month = f"{year:04d}-{month_i:02d}"
                key = (symbol, month)
                hist = registry[key]
                expected = str(hist["local_sha256"]).lower()
                name = f"{symbol}-1m-{month}.zip"
                base = f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1m/{name}"
                zpath = raw / name
                cpath = raw / f"{name}.CHECKSUM"
                rec = {"symbol":symbol,"month":month,"filename":name,"expected_sha256":expected}
                try:
                    fetch(base, zpath)
                    fetch(base + ".CHECKSUM", cpath)
                    provider_now = parse_checksum(cpath.read_text(encoding="utf-8"), name)
                    local_now = sha256_file(zpath)
                    rec["provider_sha256_now"] = provider_now
                    rec["local_sha256_now"] = local_now
                    rec["provider_checksum_matches_download"] = provider_now == local_now
                    rec["byte_exact_matches_historical"] = local_now == expected == str(hist["provider_sha256"]).lower()
                    with zipfile.ZipFile(zpath) as zf:
                        bad = zf.testzip()
                        rec["zip_crc_pass"] = bad is None
                    rec["status"] = "PASS" if all([
                        rec["provider_checksum_matches_download"],
                        rec["byte_exact_matches_historical"],
                        rec["zip_crc_pass"],
                    ]) else "FAIL"
                except Exception as e:
                    rec["status"] = "FAIL"
                    rec["error"] = f"{type(e).__name__}: {e}"
                rows.append(rec)
                if rec["status"] != "PASS":
                    failure = rec
                    break
            if failure: break
        if failure: break

    status = "BYTE_EXACT_RECOVERY_PASS" if failure is None and len(rows) == EXPECTED and all(r["status"] == "PASS" for r in rows) else "BYTE_EXACT_RECOVERY_BLOCKED"
    receipt = {
        "status": status,
        "completed_records": len(rows),
        "expected_records": EXPECTED,
        "first_failure": failure,
        "records": rows,
        "year_2025_accessed": False,
        "year_2026_accessed": False,
        "outcomes_computed": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
    }
    (out / "byte_exact_recovery_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(status)
    return 0 if status == "BYTE_EXACT_RECOVERY_PASS" else 4


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--execute-downloads", action="store_true")
    args = ap.parse_args()
    raise SystemExit(run(Path(args.registry), Path(args.output), args.execute_downloads))
