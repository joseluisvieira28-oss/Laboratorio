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
FIFTEEN_MS = 900_000
OVERLAP_START = 1732982400000  # 2024-11-30T16:00:00Z; exact first row of MEXC Dec local-month file
OVERLAP_END = 1735660800000    # 2024-12-31T16:00:00Z exclusive; exact end of Dec local-month file
EXPECTED_ROWS = (OVERLAP_END - OVERLAP_START) // FIFTEEN_MS  # 2976
API = "https://api.mexc.com/api/v3/klines"
UA = "PROP-COMPAT-001E TFG source equivalence research/1.0"
OUT = Path(__file__).resolve().parents[2] / "research" / "local_data" / "prop_compat_001e_source_gate"


def prefix(symbol: str) -> str:
    return f"{symbol[:-4]}_USDT"


def locate_parent_csv(root: Path, symbol: str) -> Path:
    name = f"{prefix(symbol)}-Min15-2024-12-01.csv"
    hits = sorted(root.rglob(name))
    if len(hits) != 1:
        raise RuntimeError(f"PARENT_FILE_RESOLUTION:{symbol}:hits={len(hits)}")
    return hits[0]


def dec(x: Any) -> Decimal:
    try:
        return Decimal(str(x))
    except InvalidOperation as e:
        raise RuntimeError(f"INVALID_DECIMAL:{x}") from e


def load_parent(path: Path) -> dict[int, tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, int]]:
    out: dict[int, tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, int]] = {}
    with path.open("r", encoding="utf-8", newline="") as h:
        r = csv.DictReader(h)
        expected = ("open_time", "open", "high", "low", "close", "volume", "amount", "close_time")
        if tuple(r.fieldnames or ()) != expected:
            raise RuntimeError(f"PARENT_HEADER_MISMATCH:{path.name}:{r.fieldnames}")
        for row in r:
            t = int(row["open_time"])
            if not (OVERLAP_START <= t < OVERLAP_END):
                continue
            if t in out:
                raise RuntimeError(f"PARENT_DUPLICATE:{path.name}:{t}")
            out[t] = (
                dec(row["open"]), dec(row["high"]), dec(row["low"]), dec(row["close"]),
                dec(row["volume"]), dec(row["amount"]), int(row["close_time"]),
            )
    return out


def get_json(params: dict[str, Any]) -> Any:
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP_{resp.status}")
        raw = resp.read()
    return json.loads(raw)


def fetch_api(symbol: str, start_ms: int, end_ms: int) -> dict[int, tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, int]]:
    out: dict[int, tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, int]] = {}
    cursor = start_ms
    calls = 0
    while cursor < end_ms:
        batch_end = min(end_ms - 1, cursor + (999 * FIFTEEN_MS))
        data = get_json({
            "symbol": symbol,
            "interval": "15m",
            "startTime": cursor,
            "endTime": batch_end,
            "limit": 1000,
        })
        calls += 1
        if not isinstance(data, list) or not data:
            raise RuntimeError(f"API_EMPTY:{symbol}:{cursor}:{batch_end}")
        batch_times: list[int] = []
        for x in data:
            if not isinstance(x, list) or len(x) < 8:
                raise RuntimeError(f"API_SCHEMA:{symbol}:{type(x).__name__}:{x!r}")
            t = int(x[0])
            if not (cursor <= t <= batch_end):
                raise RuntimeError(f"API_OUTSIDE_REQUEST_WINDOW:{symbol}:{t}:{cursor}:{batch_end}")
            if t % FIFTEEN_MS:
                raise RuntimeError(f"API_ALIGNMENT:{symbol}:{t}")
            if t in out:
                raise RuntimeError(f"API_DUPLICATE:{symbol}:{t}")
            out[t] = (dec(x[1]), dec(x[2]), dec(x[3]), dec(x[4]), dec(x[5]), dec(x[7]), int(x[6]))
            batch_times.append(t)
        batch_times.sort()
        expected_first = cursor
        expected_last = cursor + (len(batch_times) - 1) * FIFTEEN_MS
        if batch_times[0] != expected_first or batch_times[-1] != expected_last:
            raise RuntimeError(
                f"API_NONCONTIGUOUS_BATCH:{symbol}:first={batch_times[0]}:expected_first={expected_first}:"
                f"last={batch_times[-1]}:expected_last={expected_last}:n={len(batch_times)}"
            )
        if any(b - a != FIFTEEN_MS for a, b in zip(batch_times, batch_times[1:])):
            raise RuntimeError(f"API_INTERNAL_GAP:{symbol}:{cursor}:{batch_end}")
        cursor = batch_times[-1] + FIFTEEN_MS
        time.sleep(0.06)
        if calls > 10:
            raise RuntimeError(f"API_PAGINATION_RUNAWAY:{symbol}")
    return out


def compare(symbol: str, parent: dict[int, tuple], api: dict[int, tuple]) -> dict[str, Any]:
    parent_ts = sorted(parent)
    api_ts = sorted(api)
    missing_api = sorted(set(parent) - set(api))
    extra_api = sorted(set(api) - set(parent))
    mismatches: list[dict[str, Any]] = []
    fields = ("open", "high", "low", "close", "volume", "amount", "close_time")
    for t in sorted(set(parent) & set(api)):
        p = parent[t]
        a = api[t]
        bad = [fields[i] for i, (pv, av) in enumerate(zip(p, a)) if pv != av]
        if bad:
            mismatches.append({
                "open_time": t,
                "fields": bad,
                "parent": [str(v) for v in p],
                "api": [str(v) for v in a],
            })
            if len(mismatches) >= 10:
                break
    all_equal = (
        len(parent) == EXPECTED_ROWS
        and len(api) == EXPECTED_ROWS
        and not missing_api and not extra_api and not mismatches
        and parent_ts == api_ts
    )
    return {
        "symbol": symbol,
        "parent_rows": len(parent),
        "api_rows": len(api),
        "expected_rows": EXPECTED_ROWS,
        "first_parent_open_time": parent_ts[0] if parent_ts else None,
        "last_parent_open_time": parent_ts[-1] if parent_ts else None,
        "first_api_open_time": api_ts[0] if api_ts else None,
        "last_api_open_time": api_ts[-1] if api_ts else None,
        "missing_api_count": len(missing_api),
        "extra_api_count": len(extra_api),
        "value_mismatch_sample_count": len(mismatches),
        "value_mismatch_sample": mismatches,
        "exact_all_8_fields_equal": all_equal,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: source_equivalence PARENT_ARTIFACT_DIR")
    parent_root = Path(argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for symbol in SYMBOLS:
        try:
            p = load_parent(locate_parent_csv(parent_root, symbol))
            a = fetch_api(symbol, OVERLAP_START, OVERLAP_END)
            results.append(compare(symbol, p, a))
        except Exception as e:
            errors.append({"symbol": symbol, "error": f"{type(e).__name__}:{e}"})
    passed = (not errors) and len(results) == len(SYMBOLS) and all(r["exact_all_8_fields_equal"] for r in results)
    status = "SOURCE_EQUIVALENCE_PASS" if passed else "SOURCE_EQUIVALENCE_FAIL_CLOSED"
    receipt = {
        "document_id": "PROP_COMPAT_001E_TFG_MEXC15_SOURCE_EQUIVALENCE_V0.1",
        "campaign_id": "PROP-COMPAT-001E",
        "status": status,
        "setup_id": "TFG-DONCHIAN-1D-001",
        "authority_freeze": "PROP_COMPAT_001E_TFG_EXACT_RECOVERY_FREEZE_V0.1",
        "source_candidate": "OFFICIAL_MEXC_SPOT_PUBLIC_API_V3_KLINES_15M",
        "parent_artifact_id": 10419067320,
        "comparison_window": {
            "start_open_time_ms_inclusive": OVERLAP_START,
            "end_open_time_ms_exclusive": OVERLAP_END,
            "bars_per_symbol": EXPECTED_ROWS,
            "note": "exact raw MEXC local-month December 2024 parent file window"
        },
        "comparison_fields": ["open_time", "open", "high", "low", "close", "volume", "amount", "close_time"],
        "results": results,
        "errors": errors,
        "outcome_evaluation_performed": False,
        "access_2025_performed": False,
        "access_2026_performed": False,
        "governance": {
            "fail_closed": True,
            "alternate_venue_substitution": False,
            "setup_rules_changed": False,
            "live_trading": False,
            "orders": False,
            "exchange_authentication": False,
        },
    }
    raw = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    receipt["fingerprint"] = hashlib.sha256(raw).hexdigest()
    p = OUT / "PROP_COMPAT_001E_TFG_MEXC15_SOURCE_EQUIVALENCE_V0.1.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(json.dumps({
        "status": status,
        "passed_symbols": [r["symbol"] for r in results if r["exact_all_8_fields_equal"]],
        "failed_symbols": [r["symbol"] for r in results if not r["exact_all_8_fields_equal"]],
        "errors": errors,
        "fingerprint": receipt["fingerprint"],
    }, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv))
