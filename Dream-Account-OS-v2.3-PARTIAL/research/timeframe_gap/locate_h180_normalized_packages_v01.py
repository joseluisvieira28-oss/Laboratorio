from __future__ import annotations

"""Filename-only locator for the six H180 normalized ZIP packages.

This helper never opens ZIP contents or parses market data. It recursively searches
candidate filesystem roots and prints exactly one verified directory path to stdout
when all six expected package filenames coexist there. Diagnostics go to stderr.
"""

import argparse
import os
import sys
from pathlib import Path

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
EXPECTED = tuple(f"H180-0001_NORMALIZED_{symbol}.zip" for symbol in SYMBOLS)
REFERENCE = EXPECTED[0]


def has_all_packages(directory: Path) -> bool:
    return directory.is_dir() and all((directory / name).is_file() for name in EXPECTED)


def candidate_roots(project_root: Path, explicit: list[str]) -> list[Path]:
    roots: list[Path] = []
    for raw in explicit:
        if raw:
            roots.append(Path(raw).expanduser())
    roots.extend([
        project_root / "research" / "local_data",
        Path.home() / "Documents" / "Codex",
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.home() / "Downloads",
        Path.home() / "OneDrive",
    ])
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            key = os.path.normcase(os.path.abspath(str(root)))
        except OSError:
            continue
        if key not in seen:
            seen.add(key)
            out.append(root)
    return out


def locate(project_root: Path, explicit: list[str]) -> Path | None:
    for root in candidate_roots(project_root, explicit):
        if not root.exists():
            continue
        if has_all_packages(root):
            return root.resolve()
        try:
            for ref in root.rglob(REFERENCE):
                parent = ref.parent
                if has_all_packages(parent):
                    return parent.resolve()
        except (OSError, PermissionError):
            continue
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Locate the verified six-package H180 normalized directory")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--candidate", action="append", default=[])
    args = parser.parse_args()
    found = locate(Path(args.project_root), args.candidate)
    if found is None:
        print("NO_VERIFIED_H180_DIRECTORY", file=sys.stderr)
        return 2
    print(str(found))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
