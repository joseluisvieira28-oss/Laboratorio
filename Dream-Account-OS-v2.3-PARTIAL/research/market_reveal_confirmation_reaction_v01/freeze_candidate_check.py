"""Build and verify the current MRCR implementation manifest in-memory.

This is a reproducibility check only. It does not freeze or authorize science.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from freeze_manifest import (
    build_implementation_manifest,
    verify_implementation_manifest,
)


HERE = Path(__file__).resolve().parent
DREAM_ROOT = HERE.parents[1]
FILESET = HERE / "IMPLEMENTATION_FREEZE_FILESET_V01.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--head-sha", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec = json.loads(FILESET.read_text(encoding="utf-8"))
    relative_paths = spec.get("files")
    if not isinstance(relative_paths, list) or not relative_paths:
        raise ValueError("freeze fileset is empty")

    manifest = build_implementation_manifest(
        root=DREAM_ROOT,
        relative_paths=relative_paths,
        implementation_head_sha=args.head_sha,
    )
    if not verify_implementation_manifest(
        root=DREAM_ROOT,
        manifest=manifest,
    ):
        raise RuntimeError("implementation manifest failed immediate verification")

    print(json.dumps({
        "check": "MRCR_IMPLEMENTATION_FREEZE_CANDIDATE_V01",
        "file_count": len(manifest["files"]),
        "implementation_head_sha": args.head_sha,
        "manifest_sha256": manifest["manifest_sha256"],
        "persisted_as_scientific_freeze": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
