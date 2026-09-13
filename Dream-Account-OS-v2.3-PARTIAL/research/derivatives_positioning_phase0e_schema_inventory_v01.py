from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable

ASSETS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
START = date(2021, 12, 1)
END_EXCLUSIVE = date(2025, 1, 1)
OUTPUT_NAME = "DP_PHASE0E_SCHEMA_INVENTORY_RECEIPT.json"
DATE_PATTERNS = (
    re.compile(r"(?<!\d)(20\d{2})[-_](\d{2})[-_](\d{2})(?!\d)"),
    re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)"),
)
SUPPORTED_SUFFIXES = (".csv", ".csv.gz", ".zip")
TIMESTAMP_FIELD_CANDIDATES = {
    "create_time", "timestamp", "time", "datetime", "date_time", "open_time", "event_time"
}
MAX_HEADER_BYTES = 1024 * 1024


def _is_supported(path: Path) -> bool:
    n = path.name.lower()
    return n.endswith(".csv") or n.endswith(".csv.gz") or n.endswith(".zip")


def _is_checksum_sidecar(path: Path) -> bool:
    return path.name.lower().endswith(".checksum")


def _extension_label(path: Path) -> str:
    n = path.name.lower()
    if n.endswith(".csv.gz"):
        return ".csv.gz"
    if n.endswith(".zip.checksum"):
        return ".zip.checksum"
    if n.endswith(".zip"):
        return ".zip"
    return path.suffix.lower() or "<none>"


def infer_asset(text: str) -> str | None:
    upper = text.upper()
    hits = [a for a in ASSETS if a in upper]
    return hits[0] if len(hits) == 1 else None


def infer_date(text: str) -> date | None:
    for pattern in DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _parse_header_line(raw: bytes, source: str) -> list[str]:
    if not raw:
        return []
    if len(raw) > MAX_HEADER_BYTES:
        raise ValueError(f"header exceeds {MAX_HEADER_BYTES} bytes: {source}")
    text = raw.decode("utf-8-sig")
    try:
        row = next(csv.reader([text]))
    except StopIteration:
        return []
    return [str(x).strip() for x in row]


def read_header_only(path: Path) -> list[str]:
    n = path.name.lower()
    if n.endswith(".zip"):
        with zipfile.ZipFile(path, "r") as zf:
            csv_members = [
                info for info in zf.infolist()
                if not info.is_dir() and info.filename.lower().endswith(".csv")
            ]
            if len(csv_members) != 1:
                raise ValueError(
                    f"eligible ZIP must contain exactly one CSV member; found {len(csv_members)}"
                )
            member = csv_members[0]
            with zf.open(member, "r") as fh:
                raw = fh.readline(MAX_HEADER_BYTES + 1)
            return _parse_header_line(raw, f"{path}!{member.filename}")

    if n.endswith(".csv.gz"):
        with gzip.open(path, "rb") as fh:
            raw = fh.readline(MAX_HEADER_BYTES + 1)
        return _parse_header_line(raw, str(path))

    if n.endswith(".csv"):
        with open(path, "rb") as fh:
            raw = fh.readline(MAX_HEADER_BYTES + 1)
        return _parse_header_line(raw, str(path))

    raise ValueError(f"unsupported candidate container: {path.name}")


def header_sha(columns: Iterable[str]) -> str:
    canonical = "\x1f".join(columns).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def inventory(root: Path) -> dict:
    root = root.resolve()
    audit_dir = root / "AUDIT"
    extension_counts: Counter[str] = Counter()
    per_asset_files: Counter[str] = Counter()
    per_asset_schema_hashes: dict[str, Counter[str]] = {a: Counter() for a in ASSETS}
    schemas: dict[str, dict] = {}
    unknown_date_files: list[str] = []
    unknown_asset_in_window: list[str] = []
    unsupported_in_window: list[str] = []
    empty_header_files: list[str] = []
    header_errors: list[dict] = []
    forbidden_year_files_seen = {"2025": 0, "2026": 0}
    forbidden_year_files_opened = {"2025": 0, "2026": 0}
    outside_window_files_skipped = 0
    files_opened_header_only = 0
    data_rows_read = 0
    recognized_sidecar_count = 0
    recognized_sidecar_examples: list[str] = []

    all_files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            p.relative_to(audit_dir)
            continue
        except ValueError:
            pass
        all_files.append(p)

    for p in sorted(all_files):
        rel = p.relative_to(root).as_posix()
        extension_counts[_extension_label(p)] += 1
        d = infer_date(rel)
        asset = infer_asset(rel)

        if d is not None:
            if d.year == 2025:
                forbidden_year_files_seen["2025"] += 1
            elif d.year == 2026:
                forbidden_year_files_seen["2026"] += 1

        # CHECKSUM files are provenance metadata, not signal-data candidates.
        # They are inventoried by name only and never opened in Phase 0E.
        if _is_checksum_sidecar(p):
            recognized_sidecar_count += 1
            if len(recognized_sidecar_examples) < 12:
                recognized_sidecar_examples.append(rel)
            continue

        if d is None:
            if _is_supported(p):
                unknown_date_files.append(rel)
            continue

        if not (START <= d < END_EXCLUSIVE):
            outside_window_files_skipped += 1
            continue

        if asset is None:
            if _is_supported(p):
                unknown_asset_in_window.append(rel)
            else:
                unsupported_in_window.append(rel)
            continue

        if not _is_supported(p):
            unsupported_in_window.append(rel)
            continue

        try:
            columns = read_header_only(p)
            files_opened_header_only += 1
        except Exception as exc:
            header_errors.append({"path": rel, "error_type": type(exc).__name__, "message": str(exc)[:300]})
            continue

        if not columns:
            empty_header_files.append(rel)
            continue

        h = header_sha(columns)
        per_asset_files[asset] += 1
        per_asset_schema_hashes[asset][h] += 1
        if h not in schemas:
            lower = [c.lower() for c in columns]
            schemas[h] = {
                "columns": columns,
                "column_count": len(columns),
                "timestamp_fields_present": sorted(set(lower).intersection(TIMESTAMP_FIELD_CANDIDATES)),
                "file_count": 0,
                "example_paths": [],
            }
        schemas[h]["file_count"] += 1
        if len(schemas[h]["example_paths"]) < 3:
            schemas[h]["example_paths"].append(rel)

    all_six_assets_present = all(per_asset_files[a] > 0 for a in ASSETS)
    nonempty_headers = not empty_header_files and not header_errors
    pass_gate = (
        all_six_assets_present
        and not unknown_date_files
        and not unknown_asset_in_window
        and not unsupported_in_window
        and nonempty_headers
        and forbidden_year_files_opened["2025"] == 0
        and forbidden_year_files_opened["2026"] == 0
        and data_rows_read == 0
    )

    receipt = {
        "program": "DERIVATIVES POSITIONING LAB",
        "phase": "PHASE0E_SCHEMA_INVENTORY",
        "version": "0.1A",
        "authority_amendment": "DERIVATIVES_POSITIONING_PHASE0E_ARCHIVE_CONTAINER_AMENDMENT_V01A.json",
        "status": "DP_PHASE0E_PASS_SCHEMA_INVENTORIED" if pass_gate else "DP_PHASE0E_FAIL_CLOSED",
        "root": str(root),
        "allowed_window": "2021-12-01/2025-01-01 exclusive",
        "supported_candidate_containers": list(SUPPORTED_SUFFIXES),
        "files_seen_excluding_audit_dir": len(all_files),
        "extension_counts": dict(sorted(extension_counts.items())),
        "recognized_checksum_sidecar_count": recognized_sidecar_count,
        "recognized_checksum_sidecar_examples": recognized_sidecar_examples,
        "files_opened_header_only": files_opened_header_only,
        "data_rows_read": data_rows_read,
        "forbidden_year_files_seen_but_not_opened": forbidden_year_files_seen,
        "forbidden_year_files_opened": forbidden_year_files_opened,
        "outside_window_files_skipped": outside_window_files_skipped,
        "unknown_date_supported_files": unknown_date_files,
        "unknown_asset_in_window_files": unknown_asset_in_window,
        "unsupported_in_window_files": unsupported_in_window,
        "empty_header_files": empty_header_files,
        "header_errors": header_errors,
        "per_asset": {
            a: {
                "in_window_header_files": per_asset_files[a],
                "schema_hash_counts": dict(sorted(per_asset_schema_hashes[a].items())),
            }
            for a in ASSETS
        },
        "schema_variant_count": len(schemas),
        "schema_variants": dict(sorted(schemas.items())),
        "guards": {
            "outcomes_calculated": False,
            "returns_calculated": False,
            "pnl_calculated": False,
            "profitability_calculated": False,
            "threshold_selection_performed": False,
            "2025_opened": False,
            "2026_opened": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
        "next_gate": "PHASE0F_FIELD_SEMANTIC_AND_UNIT_FREEZE_PRE_OUTCOME" if pass_gate else "TECHNICAL_OR_DATA_REMEDIATION_ONLY",
    }
    audit_dir.mkdir(parents=True, exist_ok=True)
    out = audit_dir / OUTPUT_NAME
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt["receipt_path"] = str(out)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=r"C:\Users\José\Desktop\DERIVATIVES_POSITIONING_DATA_V0.1")
    args = parser.parse_args()
    result = inventory(Path(args.root))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "DP_PHASE0E_PASS_SCHEMA_INVENTORIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
