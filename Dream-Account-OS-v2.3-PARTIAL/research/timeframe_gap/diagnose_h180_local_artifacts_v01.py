from __future__ import annotations

"""Filename-only local artifact diagnostic for TFG-VWAP-15M-001.

This helper does NOT open ZIP files, decompress market data, parse candles, inspect
prices, form signals, calculate returns/PnL, or access 2024/2025/2026 market rows.
It only walks filesystem directory entries and reports paths/names/sizes for H180
artifacts that may contain the already-audited normalized Discovery source.
"""

import argparse
import json
import os
from pathlib import Path

LAB_ID = "TFG-VWAP-15M-001"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
EXPECTED = {symbol: f"H180-0001_NORMALIZED_{symbol}.zip" for symbol in SYMBOLS}
AMENDMENT_PACKAGE = "H180-0001_RUN03C_AMENDMENT01_PACKAGE.zip"


def default_roots(project_root: Path) -> list[Path]:
    home = Path.home()
    candidates = [
        project_root / "research" / "local_data",
        home / "Documents" / "Codex",
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "OneDrive",
    ]
    roots: list[Path] = []
    seen: set[str] = set()
    for root in candidates:
        try:
            key = os.path.normcase(os.path.abspath(str(root)))
        except OSError:
            continue
        if key in seen:
            continue
        seen.add(key)
        roots.append(root)
    return roots


def classify_name(name: str) -> bool:
    lower = name.lower()
    if name in EXPECTED.values() or name == AMENDMENT_PACKAGE:
        return True
    if lower.endswith(".zip") and "h180" in lower and ("normal" in lower or "run03" in lower or "amend" in lower):
        return True
    if lower.endswith(".csv.zst") and "normalized" in lower:
        return True
    return False


def scan(project_root: Path) -> dict:
    exact: dict[str, list[dict]] = {symbol: [] for symbol in SYMBOLS}
    amendment: list[dict] = []
    other_candidates: list[dict] = []
    scanned_roots: list[str] = []
    errors: list[str] = []

    expected_by_name = {name: symbol for symbol, name in EXPECTED.items()}
    seen_paths: set[str] = set()

    for root in default_roots(project_root):
        if not root.exists():
            continue
        scanned_roots.append(str(root))
        try:
            for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
                # Skip obvious high-noise/cache folders without losing user/project data.
                dirnames[:] = [d for d in dirnames if d.lower() not in {".git", "node_modules", "__pycache__", ".venv", "venv", "appdata"}]
                base = Path(dirpath)
                for name in filenames:
                    if not classify_name(name):
                        continue
                    path = base / name
                    try:
                        resolved = str(path.resolve())
                        size = path.stat().st_size
                    except (OSError, PermissionError) as exc:
                        errors.append(f"STAT_ERROR:{path}:{type(exc).__name__}")
                        continue
                    key = os.path.normcase(resolved)
                    if key in seen_paths:
                        continue
                    seen_paths.add(key)
                    row = {"name": name, "path": resolved, "parent": str(path.parent.resolve()), "size_bytes": int(size)}
                    if name in expected_by_name:
                        exact[expected_by_name[name]].append(row)
                    elif name == AMENDMENT_PACKAGE:
                        amendment.append(row)
                    else:
                        other_candidates.append(row)
        except (OSError, PermissionError) as exc:
            errors.append(f"WALK_ERROR:{root}:{type(exc).__name__}")

    common_dirs: dict[str, list[str]] = {}
    for symbol, rows in exact.items():
        for row in rows:
            common_dirs.setdefault(row["parent"], []).append(symbol)
    verified_six_dirs = [
        {"directory": directory, "symbols": sorted(symbols)}
        for directory, symbols in common_dirs.items()
        if set(symbols) == set(SYMBOLS)
    ]

    exact_found_count = sum(len(rows) for rows in exact.values())
    symbols_found = [symbol for symbol, rows in exact.items() if rows]
    missing_symbols = [symbol for symbol, rows in exact.items() if not rows]

    status = "FOUND_VERIFIED_SIX_PACKAGE_DIRECTORY" if verified_six_dirs else (
        "FOUND_EXPECTED_PACKAGES_BUT_NOT_COLOCATED" if exact_found_count else "NO_EXPECTED_NORMALIZED_PACKAGES_FOUND"
    )

    return {
        "status": status,
        "lab_id": LAB_ID,
        "scanned_roots": scanned_roots,
        "expected_exact_packages": EXPECTED,
        "exact_matches": exact,
        "symbols_with_at_least_one_exact_package": symbols_found,
        "symbols_missing_exact_package": missing_symbols,
        "exact_match_count": exact_found_count,
        "verified_six_package_directories": verified_six_dirs,
        "amendment_package_matches": amendment,
        "other_h180_normalized_or_run03_candidates": other_candidates[:200],
        "other_candidate_count": len(other_candidates),
        "filesystem_entry_names_read": True,
        "file_contents_read": False,
        "zip_members_opened": False,
        "market_rows_parsed": False,
        "outcome_evaluation_performed": False,
        "return_or_pnl_computation_performed": False,
        "internal_oos_2024_market_data_opened": False,
        "protected_2025_market_data_opened": False,
        "locked_2026_market_data_opened": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
        "orders_submitted": False,
        "errors": errors[:100],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Filename-only H180 local artifact diagnostic")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    payload = scan(Path(args.project_root))
    receipt = Path(args.receipt)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0 if payload["status"] == "FOUND_VERIFIED_SIX_PACKAGE_DIRECTORY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
