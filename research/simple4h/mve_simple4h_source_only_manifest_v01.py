#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, shutil, urllib.request
from pathlib import Path

MVE_ID = "MVE-SIMPLE4H-01"
GATE_COMMIT_SHA = "26b32dc31d2bc844b49e5c0c0ce340f1968c70c1"
BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
ASSETS = ["BNBUSDT", "DOGEUSDT", "SOLUSDT", "XRPUSDT"]
MONTHS = ["2024-12"] + [f"2025-{m:02d}" for m in range(1, 13)]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def download(url: str, dst: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "crypto-lab-source-gate/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r, dst.open("wb") as f:
        shutil.copyfileobj(r, f)


def parse_checksum(text: str, filename: str) -> str:
    hits = []
    for line in text.strip().splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == filename:
            hits.append(parts[0].lower())
    if len(hits) != 1 or len(hits[0]) != 64:
        raise RuntimeError(f"FAIL_CLOSED bad checksum sidecar for {filename}")
    return hits[0]


def main() -> None:
    ap = argparse.ArgumentParser(description="Source-only 2025 checksum gate. Never opens CSV payloads or computes market outcomes.")
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    work = Path(a.work); out = Path(a.out)
    work.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)

    items = []
    for asset in ASSETS:
        adir = work / asset
        adir.mkdir(parents=True, exist_ok=True)
        for month in MONTHS:
            if month.startswith("2026"):
                raise RuntimeError("FAIL_CLOSED 2026 month encountered")
            filename = f"{asset}-1m-{month}.zip"
            url = f"{BASE}/{asset}/1m/{filename}"
            checksum_url = url + ".CHECKSUM"
            z = adir / filename
            c = adir / (filename + ".CHECKSUM")
            download(checksum_url, c)
            expected = parse_checksum(c.read_text(encoding="utf-8-sig"), filename)
            download(url, z)
            actual = sha256_file(z)
            if actual != expected:
                raise RuntimeError(f"FAIL_CLOSED checksum mismatch {filename}: {actual} != {expected}")
            items.append({
                "asset": asset,
                "month": month,
                "filename": filename,
                "sha256": expected,
                "size": z.stat().st_size,
            })

    payload = {"mve_id": MVE_ID, "items": items, "2026_opened": False}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    (out / "MVE_SIMPLE4H_01_SOURCE_MANIFEST_V0.1.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    receipt = {
        "mve_id": MVE_ID,
        "gate_commit_sha": GATE_COMMIT_SHA,
        "status": "SOURCE_ONLY_CHECKSUM_PASS",
        "source": "Binance Data Vision USD-M Futures monthly 1m klines",
        "assets": ASSETS,
        "months": MONTHS,
        "verified_files": len(items),
        "source_manifest_sha256": payload["manifest_sha256"],
        "csv_payload_opened": False,
        "prices_or_returns_computed": False,
        "economic_outcomes_computed": False,
        "2026_opened": False,
        "live_trading_authorized": False,
    }
    (out / "MVE_SIMPLE4H_01_SOURCE_ONLY_RECEIPT_V0.1.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
