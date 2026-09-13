#!/usr/bin/env python3
"""
OPTIONS-SPOTPERP-001 V0.1 — SOURCE AUDIT ONLY.

Research-only. No trading outcomes, forward returns, PnL, or holdout access.
Fetches Deribit historical BTC option trades only for the frozen Discovery source window
and audits whether the free public history route can support the frozen trade-IV skew MVE.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

UTC = dt.timezone.utc
LAB_ID = "OPTIONS-SPOTPERP-001"
VERSION = "V0.1"
PROTOCOL_SHA256 = "138cee737d75d27b43d9f377fc9a77e823e8fb2015f360b300cdc4a16cf67cfa"

HOST = "history.deribit.com"
PATH = "/api/v2/public/get_last_trades_by_currency_and_time"
START = dt.datetime(2021, 4, 1, tzinfo=UTC)
END_EXCLUSIVE = dt.datetime(2025, 1, 1, tzinfo=UTC)
HOLDOUT_START_MS = int(END_EXCLUSIVE.timestamp() * 1000)
COUNT = 1000
MIN_WINDOW_MS = 1000
MAX_RETRIES = 4
USER_AGENT = f"{LAB_ID}/{VERSION} source-audit-only"

MIN_DTE_DAYS = 30.0
MAX_DTE_DAYS = 120.0
CALL_MONEYNESS_MIN = 1.05
CALL_MONEYNESS_MAX = 1.20
PUT_MONEYNESS_MIN = 0.80
PUT_MONEYNESS_MAX = 0.95
MIN_DISTINCT_INSTRUMENTS_PER_SIDE = 5
MIN_VALID_DAYS = 500


class ExecutionEnvironmentBlocked(RuntimeError):
    """DNS/transport/timeout failure. Not a scientific source verdict."""


class AuditAccumulator:
    """Incremental source-audit state; never computes skew, returns, or PnL."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        if self.db_path.exists():
            self.db_path.unlink()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute(
            "CREATE TABLE trade_ids (id TEXT PRIMARY KEY) WITHOUT ROWID"
        )
        self.total_trades = 0
        self.unique_trade_ids = 0
        self.duplicate_ids = 0
        self.timestamp_violations = 0
        self.parse_failures = 0
        self.missing_iv = 0
        self.missing_index = 0
        self.eligible_trade_count = 0
        self.calls_by_day: dict[str, set[str]] = defaultdict(set)
        self.puts_by_day: dict[str, set[str]] = defaultdict(set)

    def consume(self, trades: list[dict[str, Any]]) -> None:
        trade_ids = [
            str(row.get("trade_id", ""))
            for row in trades
            if str(row.get("trade_id", ""))
        ]
        if trade_ids:
            before = self.conn.total_changes
            self.conn.executemany(
                "INSERT OR IGNORE INTO trade_ids(id) VALUES (?)",
                ((trade_id,) for trade_id in trade_ids),
            )
            inserted = self.conn.total_changes - before
            self.unique_trade_ids += inserted
            self.duplicate_ids += len(trade_ids) - inserted
            self.conn.commit()

        for row in trades:
            self.total_trades += 1

            try:
                ts_ms = int(row["timestamp"])
            except Exception:
                self.timestamp_violations += 1
                continue

            if ts_ms < int(START.timestamp() * 1000) or ts_ms >= HOLDOUT_START_MS:
                self.timestamp_violations += 1
                continue

            name = str(row.get("instrument_name", ""))
            try:
                expiry, strike, opt_type = parse_instrument(name)
            except Exception:
                self.parse_failures += 1
                continue

            try:
                iv = float(row["iv"])
                if not math.isfinite(iv) or iv <= 0:
                    raise ValueError
            except Exception:
                self.missing_iv += 1
                continue

            try:
                index_price = float(row["index_price"])
                if not math.isfinite(index_price) or index_price <= 0:
                    raise ValueError
            except Exception:
                self.missing_index += 1
                continue

            trade_time = dt.datetime.fromtimestamp(ts_ms / 1000, tz=UTC)
            dte = (expiry - trade_time).total_seconds() / 86400.0
            if dte < MIN_DTE_DAYS or dte > MAX_DTE_DAYS:
                continue

            m = strike / index_price
            day_key = trade_time.date().isoformat()
            if opt_type == "C" and CALL_MONEYNESS_MIN <= m <= CALL_MONEYNESS_MAX:
                self.calls_by_day[day_key].add(name)
                self.eligible_trade_count += 1
            elif opt_type == "P" and PUT_MONEYNESS_MIN <= m <= PUT_MONEYNESS_MAX:
                self.puts_by_day[day_key].add(name)
                self.eligible_trade_count += 1

    def close(self) -> None:
        try:
            self.conn.close()
        finally:
            for suffix in ("", "-wal", "-shm"):
                p = Path(str(self.db_path) + suffix)
                if p.exists():
                    p.unlink()

    def finalize(self) -> dict[str, Any]:
        all_days: list[str] = []
        d = START.date()
        while d < END_EXCLUSIVE.date():
            all_days.append(d.isoformat())
            d += dt.timedelta(days=1)

        valid_days = [
            day_key for day_key in all_days
            if len(self.calls_by_day.get(day_key, set()))
            >= MIN_DISTINCT_INSTRUMENTS_PER_SIDE
            and len(self.puts_by_day.get(day_key, set()))
            >= MIN_DISTINCT_INSTRUMENTS_PER_SIDE
        ]

        call_counts = [
            len(self.calls_by_day.get(day_key, set())) for day_key in all_days
        ]
        put_counts = [
            len(self.puts_by_day.get(day_key, set())) for day_key in all_days
        ]

        return {
            "total_trades": self.total_trades,
            "unique_trade_ids": self.unique_trade_ids,
            "duplicate_trade_ids": self.duplicate_ids,
            "timestamp_violations": self.timestamp_violations,
            "instrument_parse_failures": self.parse_failures,
            "missing_or_invalid_iv_after_parse": self.missing_iv,
            "missing_or_invalid_index_price_after_parse": self.missing_index,
            "eligible_trade_count": self.eligible_trade_count,
            "calendar_days": len(all_days),
            "valid_signal_coverage_days": len(valid_days),
            "min_required_valid_days": MIN_VALID_DAYS,
            "call_distinct_instrument_count_min":
                min(call_counts) if call_counts else 0,
            "call_distinct_instrument_count_median":
                sorted(call_counts)[len(call_counts) // 2] if call_counts else 0,
            "put_distinct_instrument_count_min":
                min(put_counts) if put_counts else 0,
            "put_distinct_instrument_count_median":
                sorted(put_counts)[len(put_counts) // 2] if put_counts else 0,
            "valid_days_preview_first_10": valid_days[:10],
            "skew_values_computed": False,
            "forward_returns_computed": False,
            "pnl_computed": False,
        }


def iso_ms(ts_ms: int) -> str:
    return dt.datetime.fromtimestamp(ts_ms / 1000, tz=UTC).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def request_json(url: str) -> tuple[bytes, dict[str, Any]]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last: Exception | None = None
    last_environment_error = False

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                status = getattr(resp, "status", 200)
                if status != 200:
                    raise RuntimeError(f"HTTP {status}")
                body = resp.read()
            if not body:
                raise RuntimeError("empty response")
            obj = json.loads(body.decode("utf-8"))
            if not isinstance(obj, dict):
                raise RuntimeError("response is not a JSON object")
            if "error" in obj and obj["error"]:
                raise RuntimeError(f"Deribit error: {obj['error']}")
            return body, obj
        except urllib.error.HTTPError as exc:
            # Remote source answered; treat persistent HTTP failures as a source gate issue.
            last = exc
            last_environment_error = False
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            last_environment_error = True
        except (RuntimeError, json.JSONDecodeError) as exc:
            last = exc
            last_environment_error = False

        if attempt < MAX_RETRIES:
            delay = 1.5 * attempt
            if isinstance(last, urllib.error.HTTPError) and last.code == 429:
                try:
                    retry_after = float(last.headers.get("Retry-After", "0"))
                    delay = max(delay, retry_after)
                except Exception:
                    pass
            time.sleep(delay)

    if last_environment_error:
        raise ExecutionEnvironmentBlocked(
            f"network/transport request failed after {MAX_RETRIES} attempts: {last}"
        )
    raise RuntimeError(f"source request failed after {MAX_RETRIES} attempts: {last}")


def build_url(start_ms: int, end_ms: int) -> str:
    if start_ms >= HOLDOUT_START_MS or end_ms >= HOLDOUT_START_MS:
        raise RuntimeError("FAIL-CLOSED: attempted 2025+ Deribit request")
    q = urllib.parse.urlencode({
        "currency": "BTC",
        "kind": "option",
        "include_old": "true",
        "start_timestamp": str(start_ms),
        "end_timestamp": str(end_ms),
        "count": str(COUNT),
        "sorting": "asc",
    })
    return f"https://{HOST}{PATH}?{q}"


def parse_instrument(name: str) -> tuple[dt.datetime, float, str]:
    # Canonical Deribit BTC option format: BTC-25JUN21-50000-C.
    # The source audit uses the encoded expiry date only for broad 30–120 DTE
    # eligibility. It does not price options or compute outcomes.
    parts = name.split("-")
    if len(parts) != 4 or parts[0] != "BTC" or parts[3] not in {"C", "P"}:
        raise ValueError(f"unexpected instrument name: {name}")
    expiry = dt.datetime.strptime(parts[1].upper(), "%d%b%y").replace(tzinfo=UTC)
    strike = float(parts[2])
    if not math.isfinite(strike) or strike <= 0:
        raise ValueError(f"invalid strike: {name}")
    return expiry, strike, parts[3]


def write_gz(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb", compresslevel=6) as f:
        f.write(body)


def fetch_complete_window(
    start_ms: int,
    end_ms: int,
    raw_dir: Path,
    page_counter: list[int],
    manifest_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if start_ms > end_ms:
        return []

    url = build_url(start_ms, end_ms)
    body, obj = request_json(url)
    result = obj.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("response missing result object")
    trades = result.get("trades")
    has_more = bool(result.get("has_more"))
    if not isinstance(trades, list):
        raise RuntimeError("response missing trades list")

    if has_more:
        width = end_ms - start_ms
        if width <= MIN_WINDOW_MS:
            raise RuntimeError(
                f"FAIL-CLOSED: >{COUNT} trades in unsplittable window "
                f"{iso_ms(start_ms)}..{iso_ms(end_ms)}"
            )
        mid = start_ms + width // 2
        left = fetch_complete_window(
            start_ms, mid, raw_dir, page_counter, manifest_entries
        )
        right = fetch_complete_window(
            mid + 1, end_ms, raw_dir, page_counter, manifest_entries
        )
        return left + right

    page_counter[0] += 1
    page_name = f"response_{page_counter[0]:06d}.json.gz"
    page_path = raw_dir / page_name
    write_gz(page_path, body)
    manifest_entries.append({
        "page": page_name,
        "url": url,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "count": len(trades),
        "sha256": sha256_file(page_path),
        "bytes_gzip": page_path.stat().st_size,
    })
    return [t for t in trades if isinstance(t, dict)]


def daily_windows() -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    day = START
    while day < END_EXCLUSIVE:
        nxt = min(day + dt.timedelta(days=1), END_EXCLUSIVE)
        start_ms = int(day.timestamp() * 1000)
        end_ms = int(nxt.timestamp() * 1000) - 1
        windows.append((start_ms, end_ms))
        day = nxt
    return windows


def write_outputs(
    root: Path,
    manifest_entries: list[dict[str, Any]],
    probe_mode: bool,
    requested_windows: int,
    completed_windows: int,
    state: AuditAccumulator,
    status: str,
    fetch_complete: bool,
    detail: str | None = None,
) -> tuple[Path, Path]:
    audit = state.finalize()

    manifest = {
        "lab_id": LAB_ID,
        "version": VERSION,
        "protocol_sha256": PROTOCOL_SHA256,
        "stage": "SOURCE_AUDIT_ONLY",
        "status": status,
        "probe_mode": probe_mode,
        "requested_period": {
            "start": START.isoformat(),
            "end_exclusive": END_EXCLUSIVE.isoformat(),
        },
        "requested_top_level_windows": requested_windows,
        "completed_top_level_windows": completed_windows,
        "source_fetch_complete": fetch_complete,
        "holdout_accessed": False,
        "locked_2026_accessed": False,
        "raw_pages": manifest_entries,
    }
    if detail:
        manifest["detail"] = detail

    manifest_path = root / "source_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    checks = {
        "source_fetch_complete": fetch_complete,
        "not_probe_mode": not probe_mode,
        "protocol_hash_bound": manifest["protocol_sha256"] == PROTOCOL_SHA256,
        "no_duplicate_trade_ids": audit["duplicate_trade_ids"] == 0,
        "no_timestamp_violations": audit["timestamp_violations"] == 0,
        "valid_day_coverage_ge_500":
            audit["valid_signal_coverage_days"] >= MIN_VALID_DAYS,
        "no_holdout_access": manifest["holdout_accessed"] is False,
        "no_2026_access": manifest["locked_2026_accessed"] is False,
    }

    report = {
        "lab_id": LAB_ID,
        "version": VERSION,
        "stage": "SOURCE_AUDIT_ONLY",
        "status": status,
        "checks": checks,
        "audit": audit,
        "detail": detail,
        "outcome_metrics_computed": False,
        "holdout_accessed": False,
        "locked_2026_accessed": False,
    }
    report_path = root / "source_audit_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest_path, report_path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="source_audit_data")
    p.add_argument(
        "--probe-days",
        type=int,
        default=0,
        help="If >0, fetch only the first N frozen days for connectivity/schema probing. "
             "Probe mode can never PASS the full source gate.",
    )
    args = p.parse_args()

    root = Path(args.output).resolve()
    raw_dir = root / "raw"
    root.mkdir(parents=True, exist_ok=True)

    windows = daily_windows()
    probe_mode = args.probe_days > 0
    if probe_mode:
        windows = windows[: args.probe_days]

    manifest_entries: list[dict[str, Any]] = []
    page_counter = [0]
    state = AuditAccumulator(root / "source_audit_work.sqlite")
    completed_windows = 0

    print(f"{LAB_ID} {VERSION} — SOURCE AUDIT ONLY")
    print("NO outcomes | NO forward returns | NO PnL | NO 2025/2026")
    print("Incremental audit mode: raw responses are hashed; trades are not retained in RAM.")

    try:
        for i, (start_ms, end_ms) in enumerate(windows, start=1):
            print(f"[{i}/{len(windows)}] {iso_ms(start_ms)}")
            rows = fetch_complete_window(
                start_ms, end_ms, raw_dir, page_counter, manifest_entries
            )
            state.consume(rows)
            completed_windows += 1
    except ExecutionEnvironmentBlocked as exc:
        _, report_path = write_outputs(
            root=root,
            manifest_entries=manifest_entries,
            probe_mode=probe_mode,
            requested_windows=len(windows),
            completed_windows=completed_windows,
            state=state,
            status="EXECUTION_ENVIRONMENT_BLOCKED",
            fetch_complete=False,
            detail=str(exc),
        )
        print(f"EXECUTION_ENVIRONMENT_BLOCKED: {report_path}")
        print("This is NOT a scientific SOURCE_AUDIT_BLOCKED verdict.")
        state.close()
        return 12
    except Exception as exc:
        _, report_path = write_outputs(
            root=root,
            manifest_entries=manifest_entries,
            probe_mode=probe_mode,
            requested_windows=len(windows),
            completed_windows=completed_windows,
            state=state,
            status="SOURCE_AUDIT_BLOCKED",
            fetch_complete=False,
            detail=str(exc),
        )
        print(f"SOURCE_AUDIT_BLOCKED: {report_path}")
        state.close()
        return 2

    audit = state.finalize()
    checks = {
        "source_fetch_complete": True,
        "not_probe_mode": not probe_mode,
        "protocol_hash_bound": True,
        "no_duplicate_trade_ids": audit["duplicate_trade_ids"] == 0,
        "no_timestamp_violations": audit["timestamp_violations"] == 0,
        "valid_day_coverage_ge_500":
            audit["valid_signal_coverage_days"] >= MIN_VALID_DAYS,
        "no_holdout_access": True,
        "no_2026_access": True,
    }

    if probe_mode:
        status = "PROBE_ONLY_NO_DECISION"
        return_code = 4
    elif all(checks.values()):
        status = "SOURCE_AUDIT_PASS"
        return_code = 0
    else:
        status = "SOURCE_AUDIT_BLOCKED"
        return_code = 2

    _, report_path = write_outputs(
        root=root,
        manifest_entries=manifest_entries,
        probe_mode=probe_mode,
        requested_windows=len(windows),
        completed_windows=completed_windows,
        state=state,
        status=status,
        fetch_complete=True,
        detail=None,
    )

    print(f"{status}: {report_path}")
    state.close()
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
