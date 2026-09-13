#!/usr/bin/env python3
"""
ONCHAIN-CAPFLOW-001 V0.1 — data acquisition only.

Research-only. No live trading. No 2025/2026 outcome access.
Downloads frozen raw inputs and writes SHA256 manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

USER_AGENT = "ONCHAIN-CAPFLOW-001/0.1 research-only"
DEFILLAMA = {
    "usdt": "https://stablecoins.llama.fi/stablecoin/1",
    "usdc": "https://stablecoins.llama.fi/stablecoin/2",
}
SYMBOLS = ("BTCUSDT", "ETHUSDT")
INTERVAL = "1d"
START_YEAR, START_MONTH = 2020, 1
END_YEAR, END_MONTH = 2024, 12


@dataclass(frozen=True)
class DownloadSpec:
    name: str
    url: str
    relative_path: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def month_iter() -> Iterable[tuple[int, int]]:
    y, m = START_YEAR, START_MONTH
    while (y, m) <= (END_YEAR, END_MONTH):
        yield y, m
        m += 1
        if m == 13:
            y += 1
            m = 1


def build_specs() -> list[DownloadSpec]:
    specs: list[DownloadSpec] = []
    for name, url in DEFILLAMA.items():
        specs.append(DownloadSpec(
            name=f"defillama_{name}",
            url=url,
            relative_path=f"raw/defillama/{name}.json",
        ))

    for symbol in SYMBOLS:
        for year, month in month_iter():
            if year >= 2025:
                raise RuntimeError("FAIL-CLOSED: attempted to build 2025+ Binance URL")
            filename = f"{symbol}-{INTERVAL}-{year:04d}-{month:02d}.zip"
            url = (
                "https://data.binance.vision/data/spot/monthly/klines/"
                f"{symbol}/{INTERVAL}/{filename}"
            )
            specs.append(DownloadSpec(
                name=f"binance_{symbol}_{year:04d}_{month:02d}",
                url=url,
                relative_path=f"raw/binance/{symbol}/{filename}",
            ))
    return specs


def download(url: str, dest: Path, retries: int = 3) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp, tmp.open("wb") as out:
                if getattr(resp, "status", 200) != 200:
                    raise RuntimeError(f"HTTP status {getattr(resp, 'status', None)}")
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            if tmp.stat().st_size == 0:
                raise RuntimeError("empty response")
            os.replace(tmp, dest)
            return
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as e:
            last_error = e
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            if attempt < retries:
                time.sleep(1.5 * attempt)

    raise RuntimeError(f"download failed after {retries} attempts: {url}: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data", help="output directory")
    parser.add_argument("--force", action="store_true", help="redownload existing files")
    args = parser.parse_args()

    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "raw_manifest.json"

    specs = build_specs()
    entries = []

    print("ONCHAIN-CAPFLOW-001 — ACQUISITION")
    print("Research-only | 2020-2024 only | no outcomes")

    for i, spec in enumerate(specs, start=1):
        dest = root / spec.relative_path
        if args.force or not dest.exists():
            print(f"[{i}/{len(specs)}] GET {spec.name}")
            download(spec.url, dest)
        else:
            print(f"[{i}/{len(specs)}] KEEP {spec.name}")

        entries.append({
            "name": spec.name,
            "url": spec.url,
            "relative_path": spec.relative_path.replace("\\", "/"),
            "bytes": dest.stat().st_size,
            "sha256": sha256_file(dest),
        })

    manifest = {
        "lab_id": "ONCHAIN-CAPFLOW-001",
        "version": "V0.1",
        "status": "RAW_ACQUIRED",
        "allowed_period": "2020-01-01/2024-12-31",
        "holdout_accessed": False,
        "locked_2026_accessed": False,
        "entries": entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"PASS: wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
