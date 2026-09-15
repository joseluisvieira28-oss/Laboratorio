from __future__ import annotations

"""Filename-only locator for original H180 RAW outer archives.

The recovered Run03C authority expects six outer ZIPs named <SYMBOL>.zip under a
raw_inputs directory. This diagnostic never opens ZIP contents, never hashes file
bytes, never parses candles, and never inspects any market rows. It only walks
filesystem names/metadata and reports candidate paths/sizes.
"""

import argparse
import json
import os
from pathlib import Path

LAB_ID = "TFG-VWAP-15M-001"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
EXPECTED = {s: f"{s}.zip" for s in SYMBOLS}


def roots(project_root: Path) -> list[Path]:
    home = Path.home()
    raw = [
        project_root / "research" / "local_data",
        home / "Documents" / "Codex",
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "OneDrive",
    ]
    out: list[Path] = []
    seen: set[str] = set()
    for p in raw:
        try:
            key = os.path.normcase(os.path.abspath(str(p)))
        except OSError:
            continue
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def run(project_root: Path) -> dict:
    exact: dict[str, list[dict]] = {s: [] for s in SYMBOLS}
    raw_input_dirs: set[str] = set()
    h180_data_dirs: set[str] = set()
    errors: list[str] = []
    seen_files: set[str] = set()
    scanned: list[str] = []

    for root in roots(project_root):
        if not root.exists():
            continue
        scanned.append(str(root))
        try:
            for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
                dirnames[:] = [d for d in dirnames if d.lower() not in {".git", "node_modules", "__pycache__", ".venv", "venv", "appdata"}]
                base = Path(dirpath)
                lname = base.name.lower()
                if lname == "raw_inputs":
                    raw_input_dirs.add(str(base.resolve()))
                if "h180-0001_data" in lname or lname == "h180-0001_data":
                    h180_data_dirs.add(str(base.resolve()))
                by_name = {name.lower(): name for name in filenames}
                for symbol, expected in EXPECTED.items():
                    actual = by_name.get(expected.lower())
                    if actual is None:
                        continue
                    path = base / actual
                    try:
                        resolved = str(path.resolve())
                        key = os.path.normcase(resolved)
                        if key in seen_files:
                            continue
                        seen_files.add(key)
                        size = int(path.stat().st_size)
                    except (OSError, PermissionError) as exc:
                        errors.append(f"STAT_ERROR:{path}:{type(exc).__name__}")
                        continue
                    exact[symbol].append({
                        "path": resolved,
                        "parent": str(path.parent.resolve()),
                        "size_bytes": size,
                        "parent_name": path.parent.name,
                    })
        except (OSError, PermissionError) as exc:
            errors.append(f"WALK_ERROR:{root}:{type(exc).__name__}")

    parent_map: dict[str, set[str]] = {}
    for symbol, rows in exact.items():
        for row in rows:
            parent_map.setdefault(row["parent"], set()).add(symbol)
    six_dirs = [
        {"directory": d, "symbols": sorted(v)}
        for d, v in sorted(parent_map.items())
        if v == set(SYMBOLS)
    ]
    symbols_found = [s for s in SYMBOLS if exact[s]]
    missing = [s for s in SYMBOLS if not exact[s]]
    if six_dirs:
        status = "FOUND_SIX_RAW_OUTER_ARCHIVES_COLOCATED"
    elif symbols_found:
        status = "FOUND_PARTIAL_OR_DISPERSED_RAW_OUTER_ARCHIVES"
    else:
        status = "NO_RAW_OUTER_ARCHIVES_FOUND"

    return {
        "status": status,
        "lab_id": LAB_ID,
        "recovered_authority_expected_layout": "raw_inputs/<SYMBOL>.zip",
        "scanned_roots": scanned,
        "exact_matches": exact,
        "symbols_found": symbols_found,
        "symbols_missing": missing,
        "six_archive_directories": six_dirs,
        "raw_inputs_named_directories": sorted(raw_input_dirs),
        "h180_data_named_directories": sorted(h180_data_dirs),
        "file_contents_read": False,
        "zip_contents_opened": False,
        "file_hashes_computed": False,
        "market_rows_parsed": False,
        "outcome_evaluation_performed": False,
        "return_or_pnl_computation_performed": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
        "orders_submitted": False,
        "errors": errors[:100],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Locate H180 raw outer archives without opening them")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    payload = run(Path(args.project_root))
    receipt = Path(args.receipt)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0 if payload["status"] == "FOUND_SIX_RAW_OUTER_ARCHIVES_COLOCATED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
