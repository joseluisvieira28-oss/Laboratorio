from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

SOURCE_REF = "origin/tfg-donchian-1d-oos-2025-v01"
SOURCE_PATH = "Dream-Account-OS-v2.3-PARTIAL/research/timeframe_gap/TFG_DONCHIAN_1D_001_2025_OOS_BULK15M_SOURCE_AMENDMENT_V0.1D.json"
EXPECTED_BLOB = "1973a9906171fab536d12f63324ef31548b2d001"
OUT = Path(__file__).resolve().parents[2] / "research" / "local_data" / "prop_compat_001e"


def git_bytes(ref: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{ref}:{path}"])


def blob_sha(ref: str, path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"{ref}:{path}"], text=True).strip()


def walk(x: Any, path: tuple[str, ...] = ()):
    if isinstance(x, dict):
        yield path, x
        for k, v in x.items():
            yield from walk(v, path + (str(k),))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from walk(v, path + (str(i),))


def string_values(x: Any) -> list[str]:
    out: list[str] = []
    if isinstance(x, dict):
        for v in x.values():
            if isinstance(v, str):
                out.append(v)
    return out


def compact_record(path: tuple[str, ...], d: dict[str, Any]) -> dict[str, Any] | None:
    vals = string_values(d)
    interesting = any(
        ("download.mexc.com" in s)
        or ("translate.google" in s)
        or ("translate.goog" in s)
        or s.lower().endswith(".zip")
        for s in vals
    )
    keys = {str(k).lower() for k in d}
    if not interesting and not ({"sha256", "url"} <= keys or {"sha256", "source_url"} <= keys):
        return None
    keep: dict[str, Any] = {"json_path": "/".join(path)}
    for k, v in d.items():
        lk = str(k).lower()
        if isinstance(v, (str, int, float, bool)) and (
            lk in {
                "file", "filename", "name", "zip", "zip_name", "url", "source_url",
                "original_url", "proxy_url", "download_url", "sha256", "digest",
                "content_length", "size", "bytes", "symbol", "month", "market",
                "interval", "rows", "first_open_time_ms", "last_open_time_ms"
            }
            or (isinstance(v, str) and ("mexc" in v.lower() or "translate" in v.lower() or v.lower().endswith(".zip")))
        ):
            keep[str(k)] = v
    return keep if len(keep) > 1 else None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    observed_blob = blob_sha(SOURCE_REF, SOURCE_PATH)
    if observed_blob != EXPECTED_BLOB:
        raise SystemExit(f"AMENDMENT_BLOB_MISMATCH:{observed_blob}")
    raw = git_bytes(SOURCE_REF, SOURCE_PATH)
    doc = json.loads(raw)

    recs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path, d in walk(doc):
        rec = compact_record(path, d)
        if rec is None:
            continue
        key = json.dumps(rec, sort_keys=True, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            recs.append(rec)

    top = {}
    for k, v in doc.items():
        top[k] = {
            "type": type(v).__name__,
            "count": len(v) if isinstance(v, (list, dict)) else None,
            "value": v if isinstance(v, (str, int, float, bool)) and len(str(v)) < 300 else None,
        }

    zip_names = sorted({
        str(v)
        for r in recs for k, v in r.items()
        if isinstance(v, str) and v.lower().endswith(".zip")
    })
    urls = sorted({
        str(v)
        for r in recs for k, v in r.items()
        if isinstance(v, str) and v.startswith(("http://", "https://"))
    })
    sha256s = sorted({
        str(v).lower()
        for r in recs for k, v in r.items()
        if "sha256" in k.lower() and isinstance(v, str) and len(v.replace("sha256:", "")) == 64
    })

    receipt = {
        "document_id": "PROP_COMPAT_001E_TFG_AMENDMENT_COMPACT_MANIFEST_V0.1",
        "status": "AMENDMENT_EXTRACTED_FROM_FROZEN_BLOB",
        "source_ref": SOURCE_REF,
        "source_path": SOURCE_PATH,
        "source_blob_sha": observed_blob,
        "source_bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "top_level_schema": top,
        "interesting_record_count": len(recs),
        "zip_name_count": len(zip_names),
        "url_count": len(urls),
        "sha256_identity_count": len(sha256s),
        "zip_names": zip_names,
        "urls": urls,
        "records": recs,
        "governance": {
            "source_only": True,
            "outcome_replay": False,
            "2026_access": False,
            "setup_change": False,
            "live_trading": False,
        },
    }
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    receipt["fingerprint"] = hashlib.sha256(canonical).hexdigest()
    p = OUT / "PROP_COMPAT_001E_TFG_AMENDMENT_COMPACT_MANIFEST_V0.1.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(json.dumps({
        "status": receipt["status"],
        "record_count": len(recs),
        "zip_name_count": len(zip_names),
        "url_count": len(urls),
        "sha256_identity_count": len(sha256s),
        "fingerprint": receipt["fingerprint"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
