#!/usr/bin/env python3
"""Outcome-blind Deribit historical source census for ETH/SOL/XRP option hooks."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

UTC = dt.timezone.utc
HOST = "history.deribit.com"
PATH = "/api/v2/public/get_last_trades_by_currency_and_time"
COUNT = 1000
MAX_RETRIES = 5
MIN_WINDOW_MS = 1000

ROUTE_CURRENCY = {"ETH": "ETH", "SOL": "USDC", "XRP": "USDC"}
TARGET_PREFIX = {"ETH": "ETH-", "SOL": "SOL_USDC-", "XRP": "XRP_USDC-"}

WINDOWS = {
    "ETH": (
        dt.datetime(2024, 1, 1, tzinfo=UTC),
        dt.datetime(2025, 1, 1, tzinfo=UTC),
    ),
    "SOL": (
        dt.datetime(2024, 3, 1, tzinfo=UTC),
        dt.datetime(2025, 1, 1, tzinfo=UTC),
    ),
    "XRP": (
        dt.datetime(2024, 3, 1, tzinfo=UTC),
        dt.datetime(2025, 1, 1, tzinfo=UTC),
    ),
}


class TransportBlocked(RuntimeError):
    pass


def request_json(url: str) -> tuple[bytes, dict[str, Any]]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CryptoLab-Options-MultiAsset-SourceGate/0.1"},
    )
    last: Exception | None = None
    transport = False
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = resp.read()
            obj = json.loads(body.decode("utf-8"))
            if not isinstance(obj, dict) or obj.get("error"):
                raise RuntimeError(f"Deribit response error: {obj.get('error') if isinstance(obj, dict) else 'non-object'}")
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


def build_url(asset: str, start_ms: int, end_ms: int) -> str:
    if asset not in WINDOWS:
        raise ValueError("unsupported asset")
    end_exclusive = WINDOWS[asset][1]
    if start_ms >= int(end_exclusive.timestamp() * 1000):
        raise RuntimeError("2025+ request blocked")
    q = urllib.parse.urlencode(
        {
            "currency": ROUTE_CURRENCY[asset],
            "kind": "option",
            "include_old": "true",
            "start_timestamp": start_ms,
            "end_timestamp": end_ms,
            "count": COUNT,
            "sorting": "asc",
        }
    )
    return f"https://{HOST}{PATH}?{q}"


def parse_instrument(asset: str, name: str) -> tuple[dt.datetime, float, str]:
    parts = name.split("-")
    if len(parts) != 4 or parts[3] not in {"C", "P"}:
        raise ValueError(name)
    prefix = parts[0]
    if prefix not in {asset, f"{asset}_USDC"}:
        raise ValueError(name)
    expiry = dt.datetime.strptime(parts[1].upper(), "%d%b%y").replace(tzinfo=UTC)
    strike = float(parts[2])
    if not math.isfinite(strike) or strike <= 0:
        raise ValueError(name)
    return expiry, strike, parts[3]


def day_windows(start: dt.datetime, end: dt.datetime):
    cur = start
    while cur < end:
        nxt = min(cur + dt.timedelta(days=1), end)
        yield int(cur.timestamp() * 1000), int(nxt.timestamp() * 1000) - 1
        cur = nxt


def fetch_complete(
    *,
    asset: str,
    start_ms: int,
    end_ms: int,
    manifest: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    url = build_url(asset, start_ms, end_ms)
    body, obj = request_json(url)
    result = obj.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("missing result")
    rows = result.get("trades")
    if not isinstance(rows, list):
        raise RuntimeError("missing trades")
    if result.get("has_more"):
        width = end_ms - start_ms
        if width <= MIN_WINDOW_MS:
            raise RuntimeError("unsplittable full window")
        mid = start_ms + width // 2
        return fetch_complete(asset=asset, start_ms=start_ms, end_ms=mid, manifest=manifest) + fetch_complete(
            asset=asset, start_ms=mid + 1, end_ms=end_ms, manifest=manifest
        )
    manifest.append(
        {
            "start_ms": start_ms,
            "end_ms": end_ms,
            "count": len(rows),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
    )
    return [x for x in rows if isinstance(x, dict)]


def first_full_month(first_ts_ms: int) -> str:
    first = dt.datetime.fromtimestamp(first_ts_ms / 1000, tz=UTC)
    if first.day == 1 and first.hour == 0 and first.minute == 0 and first.second == 0:
        return first.strftime("%Y-%m")
    if first.month == 12:
        nxt = dt.datetime(first.year + 1, 1, 1, tzinfo=UTC)
    else:
        nxt = dt.datetime(first.year, first.month + 1, 1, tzinfo=UTC)
    return nxt.strftime("%Y-%m")


def expected_months(first_full: str) -> list[str]:
    y, m = map(int, first_full.split("-"))
    cur = dt.date(y, m, 1)
    end = dt.date(2025, 1, 1)
    out = []
    while cur < end:
        out.append(cur.strftime("%Y-%m"))
        cur = dt.date(cur.year + (cur.month == 12), 1 if cur.month == 12 else cur.month + 1, 1)
    return out


def run(asset: str, out_dir: Path) -> tuple[dict[str, Any], int]:
    start, end = WINDOWS[asset]
    start_ms_bound = int(start.timestamp() * 1000)
    end_ms_bound = int(end.timestamp() * 1000)
    manifest: list[dict[str, Any]] = []
    seen: set[str] = set()
    months = Counter()
    instruments_by_month: dict[str, set[str]] = {}
    totals = Counter()
    first_ts = None
    last_ts = None
    transport_error = None
    source_error = None

    try:
        for a, b in day_windows(start, end):
            rows = fetch_complete(asset=asset, start_ms=a, end_ms=b, manifest=manifest)
            for row in rows:
                totals["source_rows"] += 1
                name = str(row.get("instrument_name") or "")
                if not name:
                    totals["unroutable_source_rows"] += 1
                    continue
                if not name.startswith(TARGET_PREFIX[asset]):
                    totals["non_target_rows_filtered"] += 1
                    continue

                totals["rows"] += 1
                trade_id = str(row.get("trade_id") or "")
                if not trade_id:
                    totals["missing_structural"] += 1
                elif trade_id in seen:
                    totals["duplicates"] += 1
                else:
                    seen.add(trade_id)

                try:
                    ts = int(row["timestamp"])
                except Exception:
                    totals["missing_structural"] += 1
                    continue
                if ts < start_ms_bound or ts >= end_ms_bound:
                    totals["timestamp_violations"] += 1
                    continue

                try:
                    parse_instrument(asset, name)
                except Exception:
                    totals["instrument_parse_failures"] += 1

                month = dt.datetime.fromtimestamp(ts / 1000, tz=UTC).strftime("%Y-%m")
                months[month] += 1
                instruments_by_month.setdefault(month, set()).add(name)
                first_ts = ts if first_ts is None else min(first_ts, ts)
                last_ts = ts if last_ts is None else max(last_ts, ts)

                try:
                    iv = float(row.get("iv"))
                    if not math.isfinite(iv) or iv <= 0:
                        raise ValueError
                except Exception:
                    totals["invalid_iv"] += 1
                try:
                    idx = float(row.get("index_price"))
                    if not math.isfinite(idx) or idx <= 0:
                        raise ValueError
                except Exception:
                    totals["invalid_index_price"] += 1
    except TransportBlocked as exc:
        transport_error = f"{type(exc).__name__}:{exc}"
    except Exception as exc:
        source_error = f"{type(exc).__name__}:{exc}"

    first_full = first_full_month(first_ts) if first_ts is not None else None
    required_months = expected_months(first_full) if first_full else []
    empty_required = [m for m in required_months if months.get(m, 0) == 0]

    fetch_complete_ok = transport_error is None and source_error is None
    pass_data = (
        fetch_complete_ok
        and totals["rows"] > 0
        and totals["timestamp_violations"] == 0
        and totals["instrument_parse_failures"] == 0
        and totals["missing_structural"] == 0
        and not empty_required
    )
    if transport_error:
        verdict = "SOURCE_GATE_BLOCKED_TRANSPORT"
        rc = 12
    elif pass_data:
        verdict = "SOURCE_GATE_PASS"
        rc = 0
    else:
        verdict = "SOURCE_GATE_FAIL_DATA"
        rc = 2

    report = {
        "gate_id": f"OPTIONS_{asset}_001_SOURCE_GATE_V0.1",
        "asset": asset,
        "verdict": verdict,
        "requested_start_utc": start.isoformat(),
        "requested_end_exclusive_utc": end.isoformat(),
        "source_fetch_complete": fetch_complete_ok,
        "first_observed_trade_utc": None if first_ts is None else dt.datetime.fromtimestamp(first_ts / 1000, tz=UTC).isoformat(),
        "last_observed_trade_utc": None if last_ts is None else dt.datetime.fromtimestamp(last_ts / 1000, tz=UTC).isoformat(),
        "first_full_listed_month": first_full,
        "source_rows": totals["source_rows"],
        "non_target_rows_filtered": totals["non_target_rows_filtered"],
        "unroutable_source_rows": totals["unroutable_source_rows"],
        "request_currency": ROUTE_CURRENCY[asset],
        "target_instrument_prefix": TARGET_PREFIX[asset],
        "rows": totals["rows"],
        "unique_trade_ids": len(seen),
        "duplicate_trade_ids": totals["duplicates"],
        "timestamp_violations": totals["timestamp_violations"],
        "missing_structural_fields": totals["missing_structural"],
        "instrument_parse_failures": totals["instrument_parse_failures"],
        "invalid_iv_rows": totals["invalid_iv"],
        "invalid_index_price_rows": totals["invalid_index_price"],
        "month_row_counts": dict(sorted(months.items())),
        "month_distinct_instrument_counts": {
            k: len(v) for k, v in sorted(instruments_by_month.items())
        },
        "empty_required_months": empty_required,
        "transport_error": transport_error,
        "source_error": source_error,
        "skew_computed": False,
        "signal_computed": False,
        "forward_return_computed": False,
        "pnl_computed": False,
        "outcome_source_contacted": False,
        "year_2025_option_rows_requested": False,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{asset.lower()}_source_gate_receipt.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / f"{asset.lower()}_page_hash_manifest.json").write_text(
        json.dumps(
            {
                "asset": asset,
                "source": f"https://{HOST}{PATH}",
                "page_count": len(manifest),
                "pages": manifest,
                "outcome_metrics_computed": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return report, rc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", required=True, choices=sorted(WINDOWS))
    ap.add_argument("--out-dir", default="multiasset_source_gate_receipts")
    args = ap.parse_args()
    report, rc = run(args.asset, Path(args.out_dir))
    print(json.dumps({
        "asset": args.asset,
        "verdict": report["verdict"],
        "rows": report["rows"],
        "first_observed_trade_utc": report["first_observed_trade_utc"],
        "last_observed_trade_utc": report["last_observed_trade_utc"],
        "empty_required_months": report["empty_required_months"],
        "invalid_iv_rows": report["invalid_iv_rows"],
        "invalid_index_price_rows": report["invalid_index_price_rows"],
        "source_error": report["source_error"],
        "transport_error": report["transport_error"],
        "request_currency": report["request_currency"],
        "non_target_rows_filtered": report["non_target_rows_filtered"],
    }, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
