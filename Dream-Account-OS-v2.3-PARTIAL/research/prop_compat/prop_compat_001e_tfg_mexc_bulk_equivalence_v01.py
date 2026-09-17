from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
BASE = "https://www.mexc.com"
LISTING = BASE + "/file-svc/history/download"
SYMBOLS_V2 = BASE + "/api/platform/spot/market-v2/web/symbolsV2"
PORTAL = BASE + "/market-data-download"
INTERVAL = "Min15"
MONTH = "2024-12-01"
EXPECTED_ROWS = 2976
OUT = Path(__file__).resolve().parents[2] / "research" / "local_data" / "prop_compat_001e_bulk_gate"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": PORTAL,
    "User-Agent": "PROP-COMPAT-001E TFG MEXC bulk source-equivalence research/1.0",
}
FIELDS = ("open_time", "open", "high", "low", "close", "volume", "amount", "close_time")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise RuntimeError(f"INVALID_DECIMAL:{value}") from exc


def request_bytes(url: str, *, retries: int = 3) -> tuple[bytes, dict[str, str]]:
    last: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                if int(getattr(resp, "status", 200)) != 200:
                    raise RuntimeError(f"HTTP_{getattr(resp, 'status', None)}:{url}")
                return resp.read(), {str(k).lower(): str(v) for k, v in resp.headers.items()}
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(1.0 + attempt)
    raise RuntimeError(f"FETCH_FAILED:{url}:{type(last).__name__}:{last}")


def request_json(url: str) -> Any:
    raw, _ = request_bytes(url)
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise RuntimeError(f"JSON_DECODE:{url}:{raw[:160]!r}") from exc


def listing(path: str) -> list[Any]:
    url = LISTING + "?" + urllib.parse.urlencode({"filePath": path})
    payload = request_json(url)
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        raise RuntimeError(f"LISTING_SCHEMA:{path}:{type(data).__name__}")
    return data


def normalize_text(x: Any) -> str:
    return "".join(ch for ch in str(x).upper() if ch.isalnum())


def discover_ids(payload: Any) -> dict[str, str]:
    """Recover current MEXC symbol IDs without assuming one brittle JSON nesting shape.

    The website metadata groups symbols by quote currency. Entries are known to carry
    opaque `id` and base-currency `vn`; this walker also accepts explicit symbol/name
    fields as a fail-safe. Only the six frozen symbols may be returned.
    """
    targets = set(SYMBOLS)
    found: dict[str, set[str]] = {s: set() for s in SYMBOLS}

    def walk(node: Any, parent_key: str | None = None) -> None:
        if isinstance(node, dict):
            ident = node.get("id")
            if isinstance(ident, str) and len(ident) >= 8:
                explicit_values = []
                for key in ("symbol", "s", "sn", "symbolName", "displayName"):
                    if key in node and isinstance(node[key], (str, int, float)):
                        explicit_values.append(normalize_text(node[key]))
                base = node.get("vn")
                if base is not None and parent_key:
                    explicit_values.append(normalize_text(base) + normalize_text(parent_key))
                for text in explicit_values:
                    if text in targets:
                        found[text].add(ident)
            for key, value in node.items():
                walk(value, str(key))
        elif isinstance(node, list):
            for value in node:
                walk(value, parent_key)

    walk(payload)
    resolved: dict[str, str] = {}
    for symbol, ids in found.items():
        if len(ids) != 1:
            raise RuntimeError(f"SYMBOL_ID_RESOLUTION:{symbol}:ids={sorted(ids)}")
        resolved[symbol] = next(iter(ids))
    return resolved


def pair_prefix(symbol: str) -> str:
    if not symbol.endswith("USDT"):
        raise RuntimeError(f"UNSUPPORTED_SYMBOL:{symbol}")
    return f"{symbol[:-4]}_USDT"


def resolve_bulk_file(symbol: str, symbol_id: str) -> tuple[str, str]:
    expected = f"{pair_prefix(symbol)}-{INTERVAL}-{MONTH}.csv"
    path = f"SPOT2/kline/{symbol_id}/monthly/{INTERVAL}/"
    rows = listing(path)
    hits: list[tuple[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        fn = item.get("fileName")
        url = item.get("maskedUrl")
        if fn == expected and isinstance(url, str) and url.startswith("http"):
            hits.append((fn, url))
    if len(hits) != 1:
        sample = [item.get("fileName") for item in rows if isinstance(item, dict)][:8]
        raise RuntimeError(f"BULK_FILE_RESOLUTION:{symbol}:hits={len(hits)}:sample={sample}")
    return hits[0]


def locate_parent_csv(root: Path, symbol: str) -> Path:
    name = f"{pair_prefix(symbol)}-{INTERVAL}-{MONTH}.csv"
    hits = sorted(root.rglob(name))
    if len(hits) != 1:
        raise RuntimeError(f"PARENT_FILE_RESOLUTION:{symbol}:hits={len(hits)}")
    return hits[0]


def load_csv_bytes(raw: bytes, label: str) -> dict[int, tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, int]]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise RuntimeError(f"HEADER_MISMATCH:{label}:{reader.fieldnames}")
    out: dict[int, tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, int]] = {}
    for row in reader:
        t = int(row["open_time"])
        if t in out:
            raise RuntimeError(f"DUPLICATE:{label}:{t}")
        out[t] = (
            dec(row["open"]), dec(row["high"]), dec(row["low"]), dec(row["close"]),
            dec(row["volume"]), dec(row["amount"]), int(row["close_time"]),
        )
    return out


def compare(symbol: str, parent_raw: bytes, current_raw: bytes, url: str, symbol_id: str) -> dict[str, Any]:
    parent = load_csv_bytes(parent_raw, f"parent:{symbol}")
    current = load_csv_bytes(current_raw, f"current:{symbol}")
    p_ts = sorted(parent)
    c_ts = sorted(current)
    missing = sorted(set(parent) - set(current))
    extra = sorted(set(current) - set(parent))
    mismatches: list[dict[str, Any]] = []
    labels = FIELDS[1:]
    for t in sorted(set(parent) & set(current)):
        p = parent[t]
        c = current[t]
        bad = [labels[i] for i, (a, b) in enumerate(zip(p, c)) if a != b]
        if bad:
            mismatches.append({
                "open_time": t,
                "fields": bad,
                "parent": [str(v) for v in p],
                "current": [str(v) for v in c],
            })
            if len(mismatches) >= 10:
                break
    semantic_equal = (
        len(parent) == EXPECTED_ROWS
        and len(current) == EXPECTED_ROWS
        and p_ts == c_ts
        and not missing and not extra and not mismatches
    )
    return {
        "symbol": symbol,
        "symbol_id": symbol_id,
        "file_name": f"{pair_prefix(symbol)}-{INTERVAL}-{MONTH}.csv",
        "masked_url": url,
        "parent_rows": len(parent),
        "current_rows": len(current),
        "expected_rows": EXPECTED_ROWS,
        "parent_sha256": sha256_bytes(parent_raw),
        "current_sha256": sha256_bytes(current_raw),
        "byte_sha256_equal": sha256_bytes(parent_raw) == sha256_bytes(current_raw),
        "first_parent_open_time": p_ts[0] if p_ts else None,
        "last_parent_open_time": p_ts[-1] if p_ts else None,
        "first_current_open_time": c_ts[0] if c_ts else None,
        "last_current_open_time": c_ts[-1] if c_ts else None,
        "missing_current_count": len(missing),
        "extra_current_count": len(extra),
        "value_mismatch_sample_count": len(mismatches),
        "value_mismatch_sample": mismatches,
        "exact_all_8_fields_equal": semantic_equal,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: bulk_equivalence PARENT_ARTIFACT_DIR")
    parent_root = Path(argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    ids: dict[str, str] = {}
    try:
        ids = discover_ids(request_json(SYMBOLS_V2))
    except Exception as exc:
        errors.append({"symbol": "__SYMBOL_METADATA__", "error": f"{type(exc).__name__}:{exc}"})

    if not errors:
        for symbol in SYMBOLS:
            try:
                parent_path = locate_parent_csv(parent_root, symbol)
                parent_raw = parent_path.read_bytes()
                _, url = resolve_bulk_file(symbol, ids[symbol])
                current_raw, headers = request_bytes(url)
                ctype = headers.get("content-type", "")
                if "html" in ctype.lower() or current_raw.lstrip().lower().startswith(b"<!doctype html"):
                    raise RuntimeError(f"NON_CSV_PAYLOAD:{symbol}:content_type={ctype}")
                results.append(compare(symbol, parent_raw, current_raw, url, ids[symbol]))
            except Exception as exc:
                errors.append({"symbol": symbol, "error": f"{type(exc).__name__}:{exc}"})

    passed = (not errors) and len(results) == len(SYMBOLS) and all(r["exact_all_8_fields_equal"] for r in results)
    status = "MEXC_BULK_SOURCE_EQUIVALENCE_PASS" if passed else "MEXC_BULK_SOURCE_EQUIVALENCE_FAIL_CLOSED"
    receipt = {
        "document_id": "PROP_COMPAT_001E_TFG_MEXC_BULK_EQUIVALENCE_V0.1",
        "campaign_id": "PROP-COMPAT-001E",
        "status": status,
        "setup_id": "TFG-DONCHIAN-1D-001",
        "authority_freeze": "PROP_COMPAT_001E_MEXC_BULK_REACQUISITION_FREEZE_V0.1",
        "source_candidate": "OFFICIAL_MEXC_SPOT_HISTORICAL_MARKET_DATA_BULK",
        "portal": PORTAL,
        "listing_endpoint": LISTING,
        "symbol_metadata_endpoint": SYMBOLS_V2,
        "parent_artifact_id": 10419067320,
        "comparison_year": 2024,
        "comparison_month": 12,
        "interval": INTERVAL,
        "comparison_fields": list(FIELDS),
        "symbol_ids": ids,
        "results": results,
        "errors": errors,
        "outcome_evaluation_performed": False,
        "access_2025_performed": False,
        "access_2026_performed": False,
        "governance": {
            "research_only": True,
            "fail_closed": True,
            "alternate_venue_substitution": False,
            "setup_rules_changed": False,
            "live_trading": False,
            "orders": False,
            "exchange_authentication": False,
        },
    }
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    receipt["fingerprint"] = hashlib.sha256(canonical).hexdigest()
    out = OUT / "PROP_COMPAT_001E_TFG_MEXC_BULK_EQUIVALENCE_V0.1.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "resolved_symbol_ids": ids,
        "passed_symbols": [r["symbol"] for r in results if r["exact_all_8_fields_equal"]],
        "byte_equal_symbols": [r["symbol"] for r in results if r["byte_sha256_equal"]],
        "failed_symbols": [r["symbol"] for r in results if not r["exact_all_8_fields_equal"]],
        "errors": errors,
        "fingerprint": receipt["fingerprint"],
    }, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv))
