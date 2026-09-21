#!/usr/bin/env python3
"""Outcome-blind source snapshot and point-in-time validator.

This tool downloads only URLs explicitly supplied in a manifest. It never discovers or
loads prices, returns, exchange endpoints, 2025 or 2026 events.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ALLOWED_YEARS = {2021, 2022, 2023, 2024}


def parse_utc(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError("timestamp must use Z/UTC")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def validate_item(item: dict) -> None:
    event_year = int(item["event_id"].rsplit("_", 1)[1][:4])
    if event_year not in ALLOWED_YEARS:
        raise PermissionError("OUT_OF_SCOPE_BLOCKED")
    cutoff = parse_utc(item["cutoff_utc"])
    published = parse_utc(item["published_at_utc"])
    if not published < cutoff:
        raise PermissionError("CONSENSUS_NOT_STRICTLY_PRE_T0")
    if item.get("source_role") != "consensus":
        raise ValueError("probe manifest is consensus-only")
    if not item.get("fields"):
        raise ValueError("explicit fields required")


def snapshot(item: dict, output_dir: Path) -> dict:
    validate_item(item)
    req = Request(item["url"], headers={"User-Agent": "NewsShockSourceGate/0.3"})
    started = datetime.now(timezone.utc)
    with urlopen(req, timeout=30) as response:
        payload = response.read()
        final_url = response.geturl()
        status = response.status
        media_type = response.headers.get("Content-Type")
        last_modified = response.headers.get("Last-Modified")
    digest = hashlib.sha256(payload).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / f"{item['evidence_id']}.{item.get('extension', 'bin')}"
    raw_path.write_bytes(payload)
    return {
        "evidence_id": item["evidence_id"],
        "event_id": item["event_id"],
        "source_role": "consensus",
        "requested_url": item["url"],
        "final_url": final_url,
        "published_at_utc": item["published_at_utc"],
        "cutoff_utc": item["cutoff_utc"],
        "retrieved_at_utc": started.isoformat().replace("+00:00", "Z"),
        "http_status": status,
        "http_last_modified": last_modified,
        "media_type": media_type,
        "fields": item["fields"],
        "sha256": digest,
        "bytes": len(payload),
        "raw_path": str(raw_path),
        "guards": {
            "outcomes_accessed": False,
            "prices_returns_pnl_accessed": False,
            "year_2025_accessed": False,
            "year_2026_accessed": False,
            "exchange_mutation": False,
            "live_trading": False
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    receipts = [snapshot(item, args.output_dir / "raw") for item in manifest["items"]]
    body = {"document_type": "NEWS_SHOCK_V03_SOURCE_PROBE_RECEIPT", "receipts": receipts}
    body["fingerprint"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    (args.output_dir / "receipt.json").write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
