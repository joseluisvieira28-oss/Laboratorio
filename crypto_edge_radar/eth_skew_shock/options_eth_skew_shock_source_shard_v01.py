#!/usr/bin/env python3
"""Frozen monthly ETH daily-skew builder for OPTIONS-ETH-SKEW-SHOCK-001 V0.1.

Source-side only. Computes daily ETH call-minus-put IV skew, but never touches
price outcomes, forward returns, PnL, 2024 promotion data, or 2026 data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

UTC = dt.timezone.utc
HOST = "history.deribit.com"
PATH = "/api/v2/public/get_last_trades_by_currency_and_time"
COUNT = 1000
MAX_RETRIES = 5
MIN_WINDOW_MS = 1000

MIN_DTE, MAX_DTE = 30, 120
CALL_MIN, CALL_MAX = 1.05, 1.20
PUT_MIN, PUT_MAX = 0.80, 0.95
MIN_SIDE = 5

ALLOWED_YEARS = {2021, 2022, 2023, 2025}


class TransportBlocked(RuntimeError):
    pass


def month_bounds(month: str) -> tuple[dt.datetime, dt.datetime]:
    y, m = map(int, month.split("-"))
    if y not in ALLOWED_YEARS:
        raise RuntimeError(f"year {y} is not authorized for this candidate source runner")
    a = dt.datetime(y, m, 1, tzinfo=UTC)
    b = dt.datetime(y + 1, 1, 1, tzinfo=UTC) if m == 12 else dt.datetime(y, m + 1, 1, tzinfo=UTC)
    if b > dt.datetime(2026, 1, 1, tzinfo=UTC):
        raise RuntimeError("2026 access blocked")
    return a, b


def parse_instrument(name: str) -> tuple[dt.date, float, str]:
    p = name.split("-")
    if len(p) != 4 or p[0] != "ETH" or p[3] not in {"C", "P"}:
        raise ValueError(name)
    expiry = dt.datetime.strptime(p[1].upper(), "%d%b%y").date()
    strike = float(p[2])
    if not math.isfinite(strike) or strike <= 0:
        raise ValueError(name)
    return expiry, strike, p[3]


def request_json(url: str) -> tuple[bytes, dict[str, Any]]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CryptoLab-ETH-Skew-Shock-Source/0.1"},
    )
    last: Exception | None = None
    transport = False
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = resp.read()
            obj = json.loads(body.decode("utf-8"))
            if not isinstance(obj, dict) or obj.get("error"):
                raise RuntimeError(
                    f"Deribit response error: {obj.get('error') if isinstance(obj, dict) else 'non-object'}"
                )
            return body, obj
        except urllib.error.HTTPError as exc:
            last = exc
            transport = False
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            transport = True
        except (json.JSONDecodeError, RuntimeError) as exc:
            last = exc
            transport = False
        if attempt < MAX_RETRIES:
            time.sleep(min(8.0, 1.5 * attempt))
    if transport:
        raise TransportBlocked(str(last))
    raise RuntimeError(str(last))


def build_url(start_ms: int, end_ms: int) -> str:
    q = urllib.parse.urlencode(
        {
            "currency": "ETH",
            "kind": "option",
            "include_old": "true",
            "start_timestamp": start_ms,
            "end_timestamp": end_ms,
            "count": COUNT,
            "sorting": "asc",
        }
    )
    return f"https://{HOST}{PATH}?{q}"


def fetch_complete(
    start_ms: int,
    end_ms: int,
    page_manifest: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    body, obj = request_json(build_url(start_ms, end_ms))
    result = obj.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("missing result")
    rows = result.get("trades")
    if not isinstance(rows, list):
        raise RuntimeError("missing trades")
    if result.get("has_more"):
        width = end_ms - start_ms
        if width <= MIN_WINDOW_MS:
            raise RuntimeError("unsplittable full source window")
        mid = start_ms + width // 2
        return fetch_complete(start_ms, mid, page_manifest) + fetch_complete(mid + 1, end_ms, page_manifest)
    page_manifest.append(
        {
            "start_ms": start_ms,
            "end_ms": end_ms,
            "count": len(rows),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
    )
    return [r for r in rows if isinstance(r, dict)]


def day_windows(a: dt.datetime, b: dt.datetime):
    cur = a
    while cur < b:
        nxt = min(cur + dt.timedelta(days=1), b)
        yield int(cur.timestamp() * 1000), int(nxt.timestamp() * 1000) - 1
        cur = nxt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    a, b = month_bounds(args.month)
    start_ms = int(a.timestamp() * 1000)
    end_ms_exclusive = int(b.timestamp() * 1000)

    inst_ivs: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    inst_side: dict[str, str] = {}
    page_manifest: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    totals: dict[str, int] = defaultdict(int)
    transport_error = None
    source_error = None

    try:
        for wa, wb in day_windows(a, b):
            for row in fetch_complete(wa, wb, page_manifest):
                totals["source_rows"] += 1
                name = str(row.get("instrument_name") or "")
                if not name.startswith("ETH-"):
                    totals["non_target_rows_filtered"] += 1
                    continue

                totals["target_rows"] += 1
                trade_id = str(row.get("trade_id") or "")
                if not trade_id:
                    totals["missing_structural"] += 1
                elif trade_id in seen_ids:
                    totals["duplicate_trade_ids"] += 1
                else:
                    seen_ids.add(trade_id)

                try:
                    ts = int(row["timestamp"])
                except Exception:
                    totals["missing_structural"] += 1
                    continue
                if ts < start_ms or ts >= end_ms_exclusive:
                    totals["timestamp_violations"] += 1
                    continue

                t = dt.datetime.fromtimestamp(ts / 1000, tz=UTC)
                try:
                    expiry, strike, side = parse_instrument(name)
                except Exception:
                    totals["parse_failures"] += 1
                    continue

                try:
                    iv = float(row.get("iv"))
                    if not math.isfinite(iv) or iv <= 0:
                        raise ValueError
                except Exception:
                    totals["invalid_iv"] += 1
                    continue

                try:
                    index = float(row.get("index_price"))
                    if not math.isfinite(index) or index <= 0:
                        raise ValueError
                except Exception:
                    totals["invalid_index"] += 1
                    continue

                dte = (expiry - t.date()).days
                if not (MIN_DTE <= dte <= MAX_DTE):
                    totals["dte_rejected"] += 1
                    continue

                moneyness = strike / index
                eligible = (
                    side == "C" and CALL_MIN <= moneyness <= CALL_MAX
                ) or (
                    side == "P" and PUT_MIN <= moneyness <= PUT_MAX
                )
                if not eligible:
                    totals["moneyness_rejected"] += 1
                    continue

                day = t.date().isoformat()
                inst_ivs[day][name].append(iv)
                inst_side[name] = side
                totals["eligible_rows"] += 1

    except TransportBlocked as exc:
        transport_error = f"{type(exc).__name__}:{exc}"
    except Exception as exc:
        source_error = f"{type(exc).__name__}:{exc}"

    daily = []
    cur = a.date()
    while cur < b.date():
        calls: list[float] = []
        puts: list[float] = []
        for name, vals in inst_ivs.get(cur.isoformat(), {}).items():
            med = float(statistics.median(vals))
            if inst_side[name] == "C":
                calls.append(med)
            else:
                puts.append(med)
        valid = len(calls) >= MIN_SIDE and len(puts) >= MIN_SIDE
        daily.append(
            {
                "date": cur.isoformat(),
                "distinct_calls": len(calls),
                "distinct_puts": len(puts),
                "valid": valid,
                "call_iv": float(statistics.median(calls)) if valid else None,
                "put_iv": float(statistics.median(puts)) if valid else None,
                "skew": float(statistics.median(calls) - statistics.median(puts)) if valid else None,
            }
        )
        cur += dt.timedelta(days=1)

    complete = transport_error is None and source_error is None
    structural_ok = (
        totals["missing_structural"] == 0
        and totals["duplicate_trade_ids"] == 0
        and totals["timestamp_violations"] == 0
        and totals["parse_failures"] == 0
    )
    status = "PASS" if complete and structural_ok else ("BLOCKED_TRANSPORT" if transport_error else "FAIL_DATA")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    receipt = {
        "candidate_id": "OPTIONS-ETH-SKEW-SHOCK-001-V0.1",
        "asset": "ETH",
        "month": args.month,
        "status": status,
        "source_complete": complete,
        "structural_ok": structural_ok,
        "unique_trade_ids": len(seen_ids),
        **dict(totals),
        "valid_daily_skew_days": sum(1 for r in daily if r["valid"]),
        "transport_error": transport_error,
        "source_error": source_error,
        "daily_skew_computed": True,
        "skew_shock_computed": False,
        "forward_returns_computed": False,
        "pnl_computed": False,
        "outcome_source_contacted": False,
        "calendar_2024_accessed": False,
        "year_2026_accessed": False,
    }

    stem = f"eth_{args.month}"
    (out / f"{stem}_daily_skew.json").write_text(
        json.dumps({"month": args.month, "daily": daily}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / f"{stem}_source_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / f"{stem}_page_hash_manifest.json").write_text(
        json.dumps({"month": args.month, "pages": page_manifest}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with gzip.open(out / f"{stem}_trade_ids.txt.gz", "wt", encoding="utf-8") as fh:
        for tid in sorted(seen_ids):
            fh.write(tid + "\n")

    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if status == "PASS" else (12 if status == "BLOCKED_TRANSPORT" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
