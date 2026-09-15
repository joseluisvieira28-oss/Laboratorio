from __future__ import annotations

"""Static fail-closed gate for the TFG VWAP provenance-only checker.

This gate never opens market data. It inspects Python source text/AST only and
ensures the provenance preflight cannot quietly grow network, subprocess,
deserialization/decompression, outcome, or trading capabilities.
"""

import argparse
import ast
import hashlib
import json
from pathlib import Path

ALLOWED_IMPORT_ROOTS = {
    "__future__", "argparse", "hashlib", "json", "zipfile", "pathlib", "typing"
}
FORBIDDEN_IMPORT_ROOTS = {
    "requests", "httpx", "aiohttp", "urllib", "socket", "websocket", "websockets",
    "subprocess", "multiprocessing", "asyncio", "ftplib", "paramiko", "ccxt",
    "zstandard", "gzip", "bz2", "lzma", "pickle", "joblib", "pandas", "numpy",
}
FORBIDDEN_CALL_NAMES = {
    "system", "popen", "run", "call", "check_call", "check_output", "urlopen",
    "request", "post", "put", "patch", "delete", "send", "sendall",
    "decompress", "read_csv", "read_parquet",
}
FORBIDDEN_SOURCE_PATTERNS = (
    "exchange.create_order", "create_order(", "submit_order(", "place_order(",
    "requests.", "httpx.", "aiohttp.", "ccxt.", "subprocess.", "socket.",
    "zstandard.", "zstd.", "pd.read_", "pandas.read_", "np.", "numpy.",
)
REQUIRED_LITERALS = (
    'OUTCOME_COMPUTATION_AUTHORIZED = False',
    'WORKFLOW_TRIGGER_AUTHORIZED = False',
    'PASS_DISCOVERY_SOURCE_IDENTITY_ONLY',
    'BLOCKED_PROVENANCE',
    'validation_2024_member_content_opened',
    'protected_2025_member_content_opened',
    'holdout_2026_member_content_opened',
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imported = set()
    forbidden_imports = []
    suspicious_calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                imported.add(root)
                if root in FORBIDDEN_IMPORT_ROOTS or root not in ALLOWED_IMPORT_ROOTS:
                    forbidden_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            imported.add(root)
            if root in FORBIDDEN_IMPORT_ROOTS or root not in ALLOWED_IMPORT_ROOTS:
                forbidden_imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            fn = node.func
            name = None
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            if name in FORBIDDEN_CALL_NAMES:
                suspicious_calls.append(name)

    forbidden_patterns = [p for p in FORBIDDEN_SOURCE_PATTERNS if p in source]
    missing_literals = [literal for literal in REQUIRED_LITERALS if literal not in source]

    if forbidden_imports or suspicious_calls or forbidden_patterns or missing_literals:
        raise RuntimeError(json.dumps({
            "forbidden_imports": sorted(set(forbidden_imports)),
            "suspicious_calls": sorted(set(suspicious_calls)),
            "forbidden_patterns": forbidden_patterns,
            "missing_required_literals": missing_literals,
        }, sort_keys=True))

    return {
        "status": "PASS_STATIC_PROVENANCE_ONLY_GATE",
        "target": path.name,
        "sha256": sha256_file(path),
        "imports": sorted(imported),
        "network_capability_found": False,
        "subprocess_capability_found": False,
        "decompression_capability_found": False,
        "market_parser_capability_found": False,
        "trading_capability_found": False,
        "outcome_authority_literal": False,
        "workflow_authority_literal": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path)
    ap.add_argument("--receipt", type=Path)
    args = ap.parse_args()
    try:
        result = scan(args.target)
        rc = 0
    except Exception as exc:
        result = {"status": "BLOCKED_STATIC_GATE", "reason": str(exc)}
        rc = 2
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
