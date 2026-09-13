"""Cross-Venue Funding/Basis V0.4.4 — Hyperliquid asset_ctx provenance.

Outcome-blind provenance only. The script may internally read funding/premium and
mark/oracle fields solely to identify source semantics and settlement-reference
availability. It never emits raw economic values and never computes cross-venue
spreads, carry, basis return, PnL, APR/APY, Sharpe or signals.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import io
import json
import math
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 40

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
AMENDMENT_ID = "CROSS_VENUE_FUNDING_BASIS_HL_ASSET_CTX_PROVENANCE_V044"
EXPECTED_HEADER = [
    "time", "coin", "funding", "open_interest", "prev_day_px", "day_ntl_vlm",
    "premium", "oracle_px", "mark_px", "mid_px", "impact_bid_px", "impact_ask_px",
]
TARGET_ASSETS = ("BTC", "ETH")
SEMANTIC_PANEL = ("BTC", "ETH", "ARB", "AVAX", "SOL", "MATIC", "LINK", "ATOM")
INTEREST_8H = Decimal("0.0001")
CANDIDATE_CLAMPS = (Decimal("0.0003"), Decimal("0.0005"))
CANDIDATE_DIVISORS = (1, 8)
TOL = Decimal("1e-12")
CANDIDATE_START = date(2023, 9, 1)
CANDIDATE_END = date(2025, 12, 31)

SCALE_START = datetime(2023, 9, 1, tzinfo=timezone.utc)
SCALE_END = datetime(2023, 9, 7, 23, 59, 59, tzinfo=timezone.utc)
EARLY_START = datetime(2023, 12, 1, tzinfo=timezone.utc)
EARLY_END = datetime(2023, 12, 11, 22, 59, 59, tzinfo=timezone.utc)
LATE_START = datetime(2023, 12, 11, 23, 0, 0, tzinfo=timezone.utc)
LATE_END = datetime(2023, 12, 22, 23, 59, 59, tzinfo=timezone.utc)

carry_computed = False
basis_return_computed = False
pnl_computed = False
signals_computed = False
cross_venue_rate_comparison_computed = False
raw_economic_values_output = False


class ProvenanceFailure(RuntimeError):
    pass


def _dec(x: Any) -> Decimal | None:
    try:
        d = Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return d if d.is_finite() else None


def _positive(x: Any) -> bool:
    d = _dec(x)
    return d is not None and d > 0


def _clamp(x: Decimal, c: Decimal) -> Decimal:
    return min(max(x, -c), c)


def _expected(premium: Decimal, clamp_bound: Decimal, divisor: int) -> Decimal:
    return (premium + _clamp(INTEREST_8H - premium, clamp_bound)) / Decimal(divisor)


def _parse_ts(text: str) -> datetime:
    # Official archive observed format is second-resolution ISO Z. Be strict.
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _candidate_key(c: Decimal, divisor: int) -> str:
    return f"clamp_{c}_divisor_{divisor}"


def _blank_semantic() -> dict[str, Any]:
    candidates = {
        _candidate_key(c, d): {"finite_rows": 0, "matches": 0}
        for c in CANDIDATE_CLAMPS for d in CANDIDATE_DIVISORS
    }
    return {
        "scale_candidates": candidates,
        "early": {"discriminating_rows": 0, "old_clamp_matches": 0, "new_clamp_matches": 0, "neither_matches": 0},
        "late": {"discriminating_rows": 0, "old_clamp_matches": 0, "new_clamp_matches": 0, "neither_matches": 0},
        "panel_rows_by_asset": {asset: 0 for asset in SEMANTIC_PANEL},
        "premium_invalid_due_to_impact_book": 0,
        "finite_semantic_rows": 0,
    }


def _update_semantic(sem: dict[str, Any], row: dict[str, str], dt: datetime) -> None:
    coin = row["coin"]
    if coin not in SEMANTIC_PANEL:
        return
    in_scale = SCALE_START <= dt <= SCALE_END
    in_early = EARLY_START <= dt <= EARLY_END
    in_late = LATE_START <= dt <= LATE_END
    if not (in_scale or in_early or in_late):
        return
    sem["panel_rows_by_asset"][coin] += 1
    if not (_positive(row["impact_bid_px"]) and _positive(row["impact_ask_px"])):
        sem["premium_invalid_due_to_impact_book"] += 1
        return
    p = _dec(row["premium"])
    f = _dec(row["funding"])
    if p is None or f is None:
        return
    sem["finite_semantic_rows"] += 1

    if in_scale:
        for c in CANDIDATE_CLAMPS:
            for d in CANDIDATE_DIVISORS:
                bucket = sem["scale_candidates"][_candidate_key(c, d)]
                bucket["finite_rows"] += 1
                if abs(f - _expected(p, c, d)) <= TOL:
                    bucket["matches"] += 1

    if in_early or in_late:
        old_c, new_c = CANDIDATE_CLAMPS
        e_old = _expected(p, old_c, 8)
        e_new = _expected(p, new_c, 8)
        if abs(e_old - e_new) <= TOL:
            return
        bucket = sem["early" if in_early else "late"]
        bucket["discriminating_rows"] += 1
        old_match = abs(f - e_old) <= TOL
        new_match = abs(f - e_new) <= TOL
        if old_match:
            bucket["old_clamp_matches"] += 1
        if new_match:
            bucket["new_clamp_matches"] += 1
        if not old_match and not new_match:
            bucket["neither_matches"] += 1


def inspect_day(raw_path: Path, expected_date: date) -> dict[str, Any]:
    try:
        import lz4.frame  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime preflight
        raise ProvenanceFailure("lz4 package is required") from exc

    raw_sha = _sha256(raw_path)
    raw_bytes = raw_path.stat().st_size
    target = {
        asset: {
            "rows": 0,
            "minute_buckets": set(),
            "exact_top_hours": Counter(),
            "settlement_ready_top_hours": Counter(),
            "off_grid_rows": 0,
        }
        for asset in TARGET_ASSETS
    }
    exact_pairs: Counter[tuple[str, str]] = Counter()
    rows_total = 0
    wrong_date_rows = 0
    semantic = _blank_semantic()

    with lz4.frame.open(str(raw_path), mode="rb") as compressed:
        text = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
        reader = csv.DictReader(text)
        header = reader.fieldnames or []
        if header != EXPECTED_HEADER:
            return {
                "schema_version": "0.1", "lab_id": LAB_ID, "amendment_id": AMENDMENT_ID,
                "date": expected_date.isoformat(), "status": "FAIL_SCHEMA_MISMATCH",
                "schema_match": False, "raw_bytes": raw_bytes, "raw_sha256": raw_sha,
                "economic_values_output": False,
            }
        for row in reader:
            if None in row:
                raise ProvenanceFailure("Malformed CSV row")
            dt = _parse_ts(row["time"])
            coin = row["coin"]
            rows_total += 1
            if dt.date() != expected_date:
                wrong_date_rows += 1
            exact_pairs[(row["time"], coin)] += 1
            _update_semantic(semantic, row, dt)

            if coin not in TARGET_ASSETS:
                continue
            s = target[coin]
            s["rows"] += 1
            minute = dt.replace(second=0, microsecond=0)
            s["minute_buckets"].add(minute)
            if dt.second != 0 or dt.microsecond != 0:
                s["off_grid_rows"] += 1
            if dt.minute == 0 and dt.second == 0 and dt.microsecond == 0:
                s["exact_top_hours"][dt] += 1
                if _positive(row["mark_px"]) and _positive(row["oracle_px"]):
                    s["settlement_ready_top_hours"][dt] += 1

    duplicate_exact_pairs = sum(1 for n in exact_pairs.values() if n > 1)
    asset_out: dict[str, Any] = {}
    structural_global_ok = wrong_date_rows == 0 and duplicate_exact_pairs == 0
    for asset in TARGET_ASSETS:
        s = target[asset]
        exact_unique = sum(1 for n in s["exact_top_hours"].values() if n == 1)
        ready_unique = sum(
            1 for dt, n in s["settlement_ready_top_hours"].items()
            if n == 1 and s["exact_top_hours"].get(dt, 0) == 1
        )
        full = (
            structural_global_ok
            and len(s["minute_buckets"]) == 1440
            and exact_unique == 24
            and ready_unique == 24
        )
        asset_out[asset] = {
            "rows": s["rows"],
            "distinct_minute_buckets": len(s["minute_buckets"]),
            "off_grid_rows": s["off_grid_rows"],
            "exact_top_of_hour_unique_slots": exact_unique,
            "settlement_ready_unique_hours": ready_unique,
            "full_day": full,
        }

    return {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "amendment_id": AMENDMENT_ID,
        "date": expected_date.isoformat(),
        "source_key": f"asset_ctxs/{expected_date.strftime('%Y%m%d')}.csv.lz4",
        "status": "DAY_PROVENANCE_INSPECTED",
        "schema_match": True,
        "raw_bytes": raw_bytes,
        "raw_sha256": raw_sha,
        "rows_total": rows_total,
        "wrong_date_rows": wrong_date_rows,
        "duplicate_exact_time_coin_pairs": duplicate_exact_pairs,
        "target_assets": asset_out,
        "semantic_counts": semantic,
        "economic_values_output": False,
        "carry_computed": False,
        "basis_return_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "cross_venue_rate_comparison_computed": False,
    }


def seed_prior_20240901() -> dict[str, Any]:
    # Recovered from the previously authorized blind schema/timestamp probe.
    # It is sufficient to fail the full-day rule; mark/oracle values were not viewed.
    assets = {
        a: {
            "rows": 1018,
            "distinct_minute_buckets": 1018,
            "off_grid_rows": 1,
            "exact_top_of_hour_unique_slots": 17,
            "settlement_ready_unique_hours": None,
            "full_day": False,
        }
        for a in TARGET_ASSETS
    }
    return {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "amendment_id": AMENDMENT_ID,
        "date": "2024-09-01",
        "source_key": "asset_ctxs/20240901.csv.lz4",
        "status": "SEEDED_PRIOR_AUTHORIZED_PROVENANCE_PARTIAL_DAY",
        "schema_match": True,
        "raw_bytes": 5329628,
        "raw_sha256": "84be15acb2a7a02cb9a346c9c37c6f790153b517710ec4f010e9cb8e413ae948",
        "prior_probe_receipt_sha256": "12e73987aff73896f1945fabb408d755e2d1e74fdd65e372982b5267f3778784",
        "wrong_date_rows": 0,
        "duplicate_exact_time_coin_pairs": 0,
        "target_assets": assets,
        "semantic_counts": _blank_semantic(),
        "economic_values_output": False,
        "economic_fields_reinspected": False,
        "carry_computed": False,
        "basis_return_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "cross_venue_rate_comparison_computed": False,
    }


def missing_day(day: date, reason: str) -> dict[str, Any]:
    return {
        "schema_version": "0.1", "lab_id": LAB_ID, "amendment_id": AMENDMENT_ID,
        "date": day.isoformat(), "source_key": f"asset_ctxs/{day.strftime('%Y%m%d')}.csv.lz4",
        "status": "SOURCE_DAY_UNAVAILABLE_FAIL_CLOSED", "reason": reason,
        "schema_match": None,
        "target_assets": {a: {"full_day": False} for a in TARGET_ASSETS},
        "semantic_counts": _blank_semantic(), "economic_values_output": False,
    }


def _load_receipts(directory: Path) -> list[dict[str, Any]]:
    out = []
    for p in sorted(directory.glob("*.json")):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if r.get("amendment_id") == AMENDMENT_ID and r.get("date"):
            out.append(r)
    return out


def _ratio(n: int, d: int) -> float:
    return 0.0 if d == 0 else n / d


def aggregate_semantics(receipts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    scale = {
        _candidate_key(c, d): {"finite_rows": 0, "matches": 0}
        for c in CANDIDATE_CLAMPS for d in CANDIDATE_DIVISORS
    }
    early = {"discriminating_rows": 0, "old_clamp_matches": 0, "new_clamp_matches": 0, "neither_matches": 0}
    late = dict(early)
    panel_rows = {a: 0 for a in SEMANTIC_PANEL}
    invalid = 0
    source_days = 0
    schema_fail_days = 0

    for r in receipts:
        d = date.fromisoformat(r["date"])
        if not ((date(2023, 9, 1) <= d <= date(2023, 9, 7)) or (date(2023, 12, 1) <= d <= date(2023, 12, 22))):
            continue
        source_days += 1
        if r.get("schema_match") is not True:
            schema_fail_days += 1
        sem = r.get("semantic_counts", {})
        for k in scale:
            b = sem.get("scale_candidates", {}).get(k, {})
            scale[k]["finite_rows"] += int(b.get("finite_rows", 0))
            scale[k]["matches"] += int(b.get("matches", 0))
        for name, target in (("early", early), ("late", late)):
            b = sem.get(name, {})
            for k in target:
                target[k] += int(b.get(k, 0))
        for a in panel_rows:
            panel_rows[a] += int(sem.get("panel_rows_by_asset", {}).get(a, 0))
        invalid += int(sem.get("premium_invalid_due_to_impact_book", 0))

    for b in scale.values():
        b["match_ratio"] = _ratio(b["matches"], b["finite_rows"])
    best_div8 = max(v["match_ratio"] for k, v in scale.items() if k.endswith("divisor_8"))
    best_div1 = max(v["match_ratio"] for k, v in scale.items() if k.endswith("divisor_1"))
    scale_pass = best_div8 >= 0.95 and best_div8 >= best_div1 + 0.50
    early_ratio = _ratio(early["old_clamp_matches"], early["discriminating_rows"])
    late_ratio = _ratio(late["new_clamp_matches"], late["discriminating_rows"])
    clamp_pass = (
        early["discriminating_rows"] >= 10 and late["discriminating_rows"] >= 10
        and early_ratio >= 0.75 and late_ratio >= 0.75
        and early["old_clamp_matches"] > early["new_clamp_matches"]
        and late["new_clamp_matches"] > late["old_clamp_matches"]
    )
    all_panel_present = all(n > 0 for n in panel_rows.values())
    expected_source_days = 29
    semantic_pass = (
        source_days == expected_source_days
        and schema_fail_days == 0
        and all_panel_present
        and scale_pass
        and clamp_pass
    )
    return {
        "schema_version": "0.1", "lab_id": LAB_ID, "amendment_id": AMENDMENT_ID,
        "stage": "A_SEMANTIC_IDENTIFICATION", "status": "PASS" if semantic_pass else "FAIL_CLOSED",
        "source_days_seen": source_days, "source_days_expected": expected_source_days,
        "schema_fail_days": schema_fail_days, "fixed_panel_rows": panel_rows,
        "premium_invalid_due_to_impact_book": invalid,
        "scale_candidates": scale, "best_divisor_8_match_ratio": best_div8,
        "best_divisor_1_match_ratio": best_div1, "hourly_scale_pass": scale_pass,
        "early_clamp": early, "late_clamp": late,
        "early_correct_match_ratio": early_ratio, "late_correct_match_ratio": late_ratio,
        "clamp_transition_pass": clamp_pass, "semantic_probe_pass": semantic_pass,
        "discovery_authorized": False, "economic_values_output": False,
        "carry_computed": False, "basis_return_computed": False, "pnl_computed": False,
    }


def _daterange(start: date, end: date) -> Iterable[date]:
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def aggregate_coverage(receipts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    by_date = {r["date"]: r for r in receipts if r.get("date")}
    months: dict[str, Any] = {}
    for d in _daterange(CANDIDATE_START, CANDIDATE_END):
        key = d.strftime("%Y-%m")
        m = months.setdefault(key, {"expected_days": calendar.monthrange(d.year, d.month)[1], "seen_days": 0, "failed_days": [], "BTC_full_days": 0, "ETH_full_days": 0})
        r = by_date.get(d.isoformat())
        if r is None:
            m["failed_days"].append({"date": d.isoformat(), "reason": "RECEIPT_MISSING"})
            continue
        m["seen_days"] += 1
        for a in TARGET_ASSETS:
            if r.get("target_assets", {}).get(a, {}).get("full_day") is True:
                m[f"{a}_full_days"] += 1
        if not all(r.get("target_assets", {}).get(a, {}).get("full_day") is True for a in TARGET_ASSETS):
            m["failed_days"].append({"date": d.isoformat(), "reason": r.get("status", "DAY_NOT_FULL")})

    common = []
    for key, m in months.items():
        n = m["expected_days"]
        m["common_full_month"] = (
            m["seen_days"] == n and m["BTC_full_days"] == n and m["ETH_full_days"] == n and not m["failed_days"]
        )
        m["failed_day_count"] = len(m["failed_days"])
        # Keep output compact: dates/reasons are provenance, but cap list only after counting.
        if m["failed_day_count"] > 10:
            m["failed_days_first_10"] = m["failed_days"][:10]
            del m["failed_days"]
        if m["common_full_month"]:
            common.append(key)

    return {
        "schema_version": "0.1", "lab_id": LAB_ID, "amendment_id": AMENDMENT_ID,
        "stage": "B_CALENDAR_COVERAGE", "status": "PASS_COMMON_MONTHS_EXIST" if common else "FAIL_CLOSED_ZERO_COMMON_MONTHS",
        "candidate_start": CANDIDATE_START.isoformat(), "candidate_end": CANDIDATE_END.isoformat(),
        "common_complete_month_count": len(common), "common_complete_months": common,
        "months": months, "2026_accessed": False, "economic_values_output": False,
        "carry_computed": False, "basis_return_computed": False, "pnl_computed": False,
        "discovery_authorized": False,
    }


def _write(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect-day")
    p.add_argument("--file", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("seed-prior-20240901")
    p.add_argument("--out", required=True)

    p = sub.add_parser("missing-day")
    p.add_argument("--date", required=True)
    p.add_argument("--reason", default="AWS_GET_FAILED")
    p.add_argument("--out", required=True)

    p = sub.add_parser("aggregate-semantics")
    p.add_argument("--receipt-dir", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("aggregate-coverage")
    p.add_argument("--receipt-dir", required=True)
    p.add_argument("--out", required=True)

    args = parser.parse_args()
    if args.cmd == "inspect-day":
        d = date.fromisoformat(args.date)
        if d.year == 2026 or d < CANDIDATE_START or d > CANDIDATE_END:
            raise SystemExit("FAIL-CLOSED: date outside frozen 2023-09-01..2025-12-31 range")
        obj = inspect_day(Path(args.file), d)
        _write(Path(args.out), obj)
        print(json.dumps({"date": obj["date"], "status": obj["status"], "schema_match": obj.get("schema_match"), "BTC_full_day": obj.get("target_assets", {}).get("BTC", {}).get("full_day"), "ETH_full_day": obj.get("target_assets", {}).get("ETH", {}).get("full_day"), "economic_values_output": False}, sort_keys=True))
        return 0 if obj.get("schema_match") is True else 2
    if args.cmd == "seed-prior-20240901":
        obj = seed_prior_20240901(); _write(Path(args.out), obj)
        print(json.dumps({"date": obj["date"], "status": obj["status"], "raw_sha256": obj["raw_sha256"]}, sort_keys=True)); return 0
    if args.cmd == "missing-day":
        d = date.fromisoformat(args.date)
        obj = missing_day(d, args.reason); _write(Path(args.out), obj)
        print(json.dumps({"date": obj["date"], "status": obj["status"]}, sort_keys=True)); return 0
    if args.cmd == "aggregate-semantics":
        obj = aggregate_semantics(_load_receipts(Path(args.receipt_dir))); _write(Path(args.out), obj)
        print(json.dumps({"status": obj["status"], "semantic_probe_pass": obj["semantic_probe_pass"], "best_divisor_8_match_ratio": obj["best_divisor_8_match_ratio"], "best_divisor_1_match_ratio": obj["best_divisor_1_match_ratio"], "early_discriminating_rows": obj["early_clamp"]["discriminating_rows"], "late_discriminating_rows": obj["late_clamp"]["discriminating_rows"], "economic_values_output": False}, sort_keys=True))
        return 0 if obj["semantic_probe_pass"] else 2
    if args.cmd == "aggregate-coverage":
        obj = aggregate_coverage(_load_receipts(Path(args.receipt_dir))); _write(Path(args.out), obj)
        print(json.dumps({"status": obj["status"], "common_complete_month_count": obj["common_complete_month_count"], "common_complete_months": obj["common_complete_months"], "economic_values_output": False}, sort_keys=True))
        return 0 if obj["common_complete_month_count"] > 0 else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
