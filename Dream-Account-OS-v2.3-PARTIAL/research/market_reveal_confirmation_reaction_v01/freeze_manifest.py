"""Deterministic implementation fingerprint builder for future MRCR freezes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def manifest_sha256(manifest_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(manifest_without_hash)).hexdigest()


def build_implementation_manifest(
    *,
    root: Path,
    relative_paths: Sequence[str],
    implementation_head_sha: str,
) -> dict[str, Any]:
    if not implementation_head_sha or len(implementation_head_sha) < 7:
        raise ValueError("implementation_head_sha is required")
    normalized = sorted(set(relative_paths))
    if not normalized:
        raise ValueError("relative_paths cannot be empty")

    files = []
    for rel in normalized:
        path = root / rel
        if not path.is_file():
            raise FileNotFoundError(str(path))
        files.append({
            "path": rel.replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        })

    preimage = {
        "document_type": "MRCR_IMPLEMENTATION_MANIFEST_V01",
        "implementation_head_sha": implementation_head_sha,
        "files": files,
    }
    out = dict(preimage)
    out["manifest_sha256"] = manifest_sha256(preimage)
    return out


def verify_implementation_manifest(*, root: Path, manifest: dict[str, Any]) -> bool:
    claimed = manifest.get("manifest_sha256")
    if not isinstance(claimed, str):
        return False

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        return False

    rebuilt_rows = []
    for row in files:
        rel = row.get("path")
        if not isinstance(rel, str):
            return False
        path = root / rel
        if not path.is_file():
            return False
        rebuilt_rows.append({
            "path": rel,
            "bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        })

    preimage = {
        "document_type": manifest.get("document_type"),
        "implementation_head_sha": manifest.get("implementation_head_sha"),
        "files": rebuilt_rows,
    }
    return (
        rebuilt_rows == files
        and manifest_sha256(preimage) == claimed
    )


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value.lower())
    )


def validate_implementation_manifest_structure(
    manifest: dict[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    blockers: list[str] = []

    if manifest.get("document_type") != "MRCR_IMPLEMENTATION_MANIFEST_V01":
        blockers.append("DOCUMENT_TYPE_MISMATCH")

    head = manifest.get("implementation_head_sha")
    if (
        not isinstance(head, str)
        or len(head) != 40
        or not all(ch in "0123456789abcdef" for ch in head.lower())
    ):
        blockers.append("IMPLEMENTATION_HEAD_SHA_INVALID")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        blockers.append("FILES_MISSING")
        files = []

    seen_paths: set[str] = set()
    normalized_rows = []
    for index, row in enumerate(files):
        if not isinstance(row, dict):
            blockers.append(f"FILE_{index}_INVALID")
            continue
        path = row.get("path")
        size = row.get("bytes")
        sha = row.get("sha256")
        if not isinstance(path, str) or not path:
            blockers.append(f"FILE_{index}_PATH_INVALID")
        elif path in seen_paths:
            blockers.append("DUPLICATE_FILE_PATH")
        else:
            seen_paths.add(path)
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            blockers.append(f"FILE_{index}_BYTES_INVALID")
        if not _is_sha256(sha):
            blockers.append(f"FILE_{index}_SHA256_INVALID")
        if (
            isinstance(path, str)
            and path
            and isinstance(size, int)
            and not isinstance(size, bool)
            and size >= 0
            and _is_sha256(sha)
        ):
            normalized_rows.append({
                "path": path,
                "bytes": size,
                "sha256": sha,
            })

    claimed = manifest.get("manifest_sha256")
    if not _is_sha256(claimed):
        blockers.append("MANIFEST_SHA256_INVALID_OR_MISSING")
    elif len(normalized_rows) == len(files):
        preimage = {
            "document_type": manifest.get("document_type"),
            "implementation_head_sha": head,
            "files": normalized_rows,
        }
        if manifest_sha256(preimage) != claimed:
            blockers.append("MANIFEST_SHA256_MISMATCH")

    return len(blockers) == 0, tuple(sorted(set(blockers)))
