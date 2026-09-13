#!/usr/bin/env python3
"""
ONCHAIN-CAPFLOW-001 V0.1A — data acquisition only.

Research-only. No live trading. No 2025/2026 outcome access.
Downloads frozen raw inputs with explicit date cutoffs and writes SHA256 manifest.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

USER_AGENT = "ONCHAIN-CAPFLOW-001/0.1A research-only"
COMMUNITY_HOST = "community-api.coinmetrics.io"
COMMUNITY_PATH = "/v4/timeseries/asset-metrics"
STABLECOIN_START = "2020-01-01"
STABLECOIN_END = "2024-12-31"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
INTERVAL = "1d"
START_YEAR, START_MONTH = 2020, 1
END_YEAR, END_MONTH = 2024, 12
HOLDOUT_START = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)


class ExecutionEnvironmentBlocked(RuntimeError):
    """Transport/DNS/timeout failure. Not a scientific DATA_BLOCKED verdict."""


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


def request_bytes(url: str, retries: int = 3) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    last_environment_error = False

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status = getattr(resp, "status", 200)
                if status != 200:
                    raise RuntimeError(f"HTTP status {status}")
                body = resp.read()
            if not body:
                raise RuntimeError("empty response")
            return body
        except urllib.error.HTTPError as e:
            # The remote source answered but did not serve the requested object.
            # This is a source/data gate problem, not a local DNS/transport problem.
            last_error = e
            last_environment_error = False
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_error = e
            last_environment_error = True
        except RuntimeError as e:
            last_error = e
            last_environment_error = False

        if attempt < retries:
            time.sleep(1.5 * attempt)

    if last_environment_error:
        raise ExecutionEnvironmentBlocked(
            f"network/transport request failed after {retries} attempts: {url}: {last_error}"
        )
    raise RuntimeError(
        f"source request failed after {retries} attempts: {url}: {last_error}"
    )


def validate_community_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != COMMUNITY_HOST:
        raise RuntimeError(f"FAIL-CLOSED: unexpected Coin Metrics pagination host: {url}")

    query = urllib.parse.parse_qs(parsed.query)
    end_values = query.get("end_time", [])
    if not end_values:
        raise RuntimeError(f"FAIL-CLOSED: pagination URL lost frozen end_time: {url}")

    frozen_raw = end_values[-1]
    if frozen_raw == STABLECOIN_END:
        return

    # Some providers canonicalize an equivalent date to an ISO timestamp.
    # Accept only a timestamp that remains inside the frozen final UTC day.
    try:
        frozen_end = parse_iso_time(frozen_raw)
    except Exception as e:
        raise RuntimeError(
            f"FAIL-CLOSED: unparseable pagination end_time {frozen_raw!r}: {url}"
        ) from e

    if frozen_end.date() != dt.date(2024, 12, 31) or frozen_end >= HOLDOUT_START:
        raise RuntimeError(f"FAIL-CLOSED: pagination URL changed frozen end_time: {url}")


def first_coinmetrics_url() -> str:
    query = urllib.parse.urlencode({
        "assets": "usdt,usdc",
        "metrics": "SplyCur",
        "frequency": "1d",
        "start_time": STABLECOIN_START,
        "end_time": STABLECOIN_END,
        "page_size": "10000",
        "paging_from": "start",
        "format": "json",
    })
    return f"https://{COMMUNITY_HOST}{COMMUNITY_PATH}?{query}"


def parse_iso_time(value: str) -> dt.datetime:
    text = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def acquire_coinmetrics(root: Path) -> list[dict]:
    entries: list[dict] = []
    url: str | None = first_coinmetrics_url()
    seen_urls: set[str] = set()
    seen_assets: set[str] = set()
    page = 0

    while url:
        validate_community_url(url)
        if url in seen_urls:
            raise RuntimeError("FAIL-CLOSED: repeated Coin Metrics pagination URL")
        seen_urls.add(url)
        page += 1

        body = request_bytes(url)
        try:
            obj = json.loads(body.decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Coin Metrics response is not valid JSON: {e}") from e

        data = obj.get("data")
        if not isinstance(data, list):
            raise RuntimeError("Coin Metrics response missing data[]")

        for row in data:
            if not isinstance(row, dict):
                continue
            asset = str(row.get("asset", "")).lower()
            if asset:
                seen_assets.add(asset)
            t_raw = row.get("time")
            if isinstance(t_raw, str):
                t = parse_iso_time(t_raw)
                if t >= HOLDOUT_START:
                    raise RuntimeError(
                        f"FAIL-CLOSED: provider returned holdout timestamp {t_raw}"
                    )

        dest = root / f"raw/coinmetrics/stablecoin_supply_page_{page:03d}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        entries.append({
            "name": f"coinmetrics_stablecoin_supply_page_{page:03d}",
            "url": url,
            "relative_path": str(dest.relative_to(root)).replace("\\", "/"),
            "bytes": dest.stat().st_size,
            "sha256": sha256_file(dest),
        })

        next_url = obj.get("next_page_url")
        url = str(next_url) if next_url else None

    if not {"usdt", "usdc"}.issubset(seen_assets):
        raise RuntimeError(
            "DATA_BLOCKED: Community API did not return both USDT and USDC for SplyCur"
        )
    return entries


def month_iter() -> Iterable[tuple[int, int]]:
    y, m = START_YEAR, START_MONTH
    while (y, m) <= (END_YEAR, END_MONTH):
        yield y, m
        m += 1
        if m == 13:
            y += 1
            m = 1


def build_binance_specs() -> list[DownloadSpec]:
    specs: list[DownloadSpec] = []
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


def download_file(url: str, dest: Path, force: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        return
    body = request_bytes(url)
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(body)
    if tmp.stat().st_size == 0:
        raise RuntimeError(f"empty response: {url}")
    os.replace(tmp, dest)


def write_gate(root: Path, status: str, detail: str) -> None:
    p = root / "data_gate_status.json"
    p.write_text(json.dumps({
        "lab_id": "ONCHAIN-CAPFLOW-001",
        "version": "V0.1A",
        "stage": "DATA_SOURCE_GATE",
        "status": status,
        "detail": detail,
        "holdout_accessed": False,
        "locked_2026_accessed": False,
    }, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data", help="output directory")
    parser.add_argument("--force", action="store_true", help="redownload existing files")
    args = parser.parse_args()

    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "raw_manifest.json"

    print("ONCHAIN-CAPFLOW-001 — ACQUISITION V0.1A")
    print("Research-only | explicit 2020-2024 cutoff | no outcomes")

    entries: list[dict] = []
    try:
        entries.extend(acquire_coinmetrics(root))

        specs = build_binance_specs()
        for i, spec in enumerate(specs, start=1):
            dest = root / spec.relative_path
            print(
                f"[{i}/{len(specs)}] "
                f"{'GET' if args.force or not dest.exists() else 'KEEP'} {spec.name}"
            )
            download_file(spec.url, dest, args.force)
            entries.append({
                "name": spec.name,
                "url": spec.url,
                "relative_path": spec.relative_path,
                "bytes": dest.stat().st_size,
                "sha256": sha256_file(dest),
            })
    except ExecutionEnvironmentBlocked as e:
        write_gate(root, "EXECUTION_ENVIRONMENT_BLOCKED", str(e))
        print(f"EXECUTION_ENVIRONMENT_BLOCKED: {e}")
        print("This is NOT a scientific DATA_BLOCKED verdict.")
        return 12
    except Exception as e:
        write_gate(root, "DATA_BLOCKED", str(e))
        print(f"DATA_BLOCKED: {e}")
        return 3

    manifest = {
        "lab_id": "ONCHAIN-CAPFLOW-001",
        "version": "V0.1A",
        "protocol_sha256": "1c6c66b7188694bcc2d62cb83ee050a023fba7f97388bc87933ed668d3392b65",
        "status": "RAW_ACQUIRED",
        "allowed_period": "2020-01-01/2024-12-31",
        "holdout_accessed": False,
        "locked_2026_accessed": False,
        "entries": entries,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    write_gate(
        root,
        "PASS",
        "All frozen Coin Metrics and Binance Vision raw inputs were acquired "
        "without holdout timestamps; SHA256 manifest written.",
    )
    print(f"PASS: wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
