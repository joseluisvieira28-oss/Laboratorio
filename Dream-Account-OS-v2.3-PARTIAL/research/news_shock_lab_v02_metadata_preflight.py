from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
from io import TextIOWrapper
import json
from pathlib import Path
import zipfile
from zoneinfo import ZoneInfo

from research.news_shock_lab_v01_cpi_nfp_runner import load_manifest

FREEZE_PATH = Path(__file__).with_name(
    "NEWS_SHOCK_LAB_V02_CPI_NFP_ROBUST_CONTROLS_FREEZE.json"
)
EXPECTED_FREEZE_FINGERPRINT = (
    "92370dcfb389e2f3cae1c434bfb77dabe254c5514741bfd731fca6ecf3e23796"
)
EXPECTED_MANIFEST_FINGERPRINT = (
    "baececa93f922a71d328373c94109652c911deae6ae03e76ea4e23d3f8d90560"
)
SYMBOLS = ("BTCUSDT", "ETHUSDT")
CONTROL_LAGS = (7, 14, 21, 28, 35, 42, 49, 56)
MIN_VALID_CONTROLS = 4
ONE_MIN_MS = 60_000
NY = ZoneInfo("America/New_York")
EARLIEST_CONTROL_DATE = date(2020, 11, 1)


def canonical_hash(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def load_freeze() -> dict:
    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    if supplied != EXPECTED_FREEZE_FINGERPRINT or canonical_hash(unsigned) != supplied:
        raise PermissionError("V0.2 freeze fingerprint mismatch")
    if raw.get("status") != "FROZEN_DIAGNOSTIC_ONLY_PENDING_METADATA_PREFLIGHT":
        raise PermissionError("V0.2 freeze status mismatch")
    if raw["event_contract"]["schedule_manifest_fingerprint"] != EXPECTED_MANIFEST_FINGERPRINT:
        raise PermissionError("V0.2 manifest binding mismatch")
    cc = raw["control_contract"]
    if tuple(cc["candidate_lags_days"]) != CONTROL_LAGS:
        raise PermissionError("V0.2 control lag drift")
    if int(cc["minimum_valid_controls"]) != MIN_VALID_CONTROLS:
        raise PermissionError("V0.2 minimum-control drift")
    if cc["no_interpolation"] is not True or cc["no_synthetic_candles"] is not True:
        raise PermissionError("V0.2 synthetic-data guard drift")
    mp = raw["metadata_preflight"]
    if mp["inspect_only_timestamps_and_file_integrity_not_prices_returns_volume_trade_count_or_flow"] is not True:
        raise PermissionError("V0.2 metadata-only guard drift")
    for key, value in raw["governance"].items():
        if value is not False:
            raise PermissionError(f"V0.2 governance drift: {key}")
    return raw


def norm_ts(value: int) -> int:
    return value // 1000 if abs(value) >= 100_000_000_000_000 else value


def parse_checksum(text: str, filename: str) -> str:
    parts = text.strip().split()
    if len(parts) < 2:
        raise ValueError("invalid checksum")
    digest = parts[0].lower()
    fname = parts[-1].lstrip("*")
    if fname != filename or len(digest) != 64:
        raise ValueError("checksum filename/format mismatch")
    return digest


def read_timestamp_set(root: Path, symbol: str, day: str) -> set[int]:
    filename = f"{symbol}-1m-{day}.zip"
    zip_path = root / symbol / filename
    checksum_path = root / symbol / (filename + ".CHECKSUM")
    raw = zip_path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    expected = parse_checksum(checksum_path.read_text(encoding="utf-8"), filename)
    if actual != expected:
        raise ValueError(f"checksum mismatch {symbol} {day}")
    member = filename[:-4] + ".csv"
    timestamps: set[int] = set()
    with zipfile.ZipFile(zip_path) as zf:
        if zf.namelist() != [member]:
            raise ValueError(f"zip member mismatch {symbol} {day}")
        with zf.open(member) as binary:
            reader = csv.reader(TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
            for row in reader:
                if not row or not row[0].strip().lstrip("-").isdigit():
                    continue
                ts = norm_ts(int(row[0]))
                if ts % ONE_MIN_MS != 0:
                    raise ValueError(f"timestamp alignment {symbol} {day}")
                if ts in timestamps:
                    raise ValueError(f"duplicate timestamp {symbol} {day}")
                timestamps.add(ts)
    return timestamps


def event_ts_ms(event_date: str) -> int:
    d = date.fromisoformat(event_date)
    local = datetime(d.year, d.month, d.day, 8, 30, tzinfo=NY)
    return int(local.astimezone(timezone.utc).timestamp() * 1000)


def control_ts_ms(control_date: date) -> int:
    local = datetime(control_date.year, control_date.month, control_date.day, 8, 30, tzinfo=NY)
    return int(local.astimezone(timezone.utc).timestamp() * 1000)


def candidate_control_dates(event_date: str, event_dates: set[str]) -> tuple[date, ...]:
    d = date.fromisoformat(event_date)
    candidates: list[date] = []
    for lag in CONTROL_LAGS:
        c = d - timedelta(days=lag)
        if c < EARLIEST_CONTROL_DATE:
            raise RuntimeError(f"control before frozen floor: {c.isoformat()}")
        if c.isoformat() in event_dates:
            continue
        candidates.append(c)
    return tuple(candidates)


def required_days(manifest: dict) -> tuple[str, ...]:
    event_dates = {e["event_date"] for e in manifest["events"]}
    days = set(event_dates)
    for event in manifest["events"]:
        for c in candidate_control_dates(event["event_date"], event_dates):
            days.add(c.isoformat())
    if any(day.startswith("2026-") for day in days):
        raise RuntimeError("2026 required-day guard violation")
    return tuple(sorted(days))


def required_timestamps(ts: int) -> set[int]:
    # Pre-event metrics use fixed endpoints; post-event flow/volume requires every
    # minute from release through +119, while +120 is the return endpoint.
    req = {ts - 60 * ONE_MIN_MS, ts - 15 * ONE_MIN_MS, ts - 5 * ONE_MIN_MS}
    req.update(ts + i * ONE_MIN_MS for i in range(0, 121))
    return req


def coverage_reason(timestamps: set[int], ts: int) -> str | None:
    missing = sorted(required_timestamps(ts) - timestamps)
    if not missing:
        return None
    offsets = [int((m - ts) // ONE_MIN_MS) for m in missing[:20]]
    return f"missing_required_minutes_offsets={offsets};missing_count={len(missing)}"


def run(raw_root: Path, manifest_path: Path, output_path: Path) -> dict:
    freeze = load_freeze()
    manifest = load_manifest(manifest_path)
    if manifest.get("fingerprint") != EXPECTED_MANIFEST_FINGERPRINT:
        raise PermissionError("unexpected manifest fingerprint")

    days = required_days(manifest)
    event_dates = {e["event_date"] for e in manifest["events"]}
    timestamp_cache: dict[str, dict[str, set[int]]] = {s: {} for s in SYMBOLS}

    for symbol in SYMBOLS:
        for day in days:
            timestamp_cache[symbol][day] = read_timestamp_set(raw_root, symbol, day)

    event_failures: list[dict] = []
    control_adequacy_failures: list[dict] = []
    per_event_symbol: list[dict] = []

    for symbol in SYMBOLS:
        for event in manifest["events"]:
            event_date = event["event_date"]
            ets = event_ts_ms(event_date)
            event_reason = coverage_reason(timestamp_cache[symbol][event_date], ets)
            if event_reason is not None:
                event_failures.append(
                    {
                        "symbol": symbol,
                        "event_type": event["event_type"],
                        "event_date": event_date,
                        "reason": event_reason,
                    }
                )

            valid_controls: list[str] = []
            invalid_controls: list[dict] = []
            for c in candidate_control_dates(event_date, event_dates):
                day = c.isoformat()
                reason = coverage_reason(timestamp_cache[symbol][day], control_ts_ms(c))
                if reason is None:
                    valid_controls.append(day)
                else:
                    invalid_controls.append({"control_date": day, "reason": reason})

            if len(valid_controls) < MIN_VALID_CONTROLS:
                control_adequacy_failures.append(
                    {
                        "symbol": symbol,
                        "event_type": event["event_type"],
                        "event_date": event_date,
                        "valid_control_count": len(valid_controls),
                        "invalid_controls": invalid_controls,
                    }
                )

            per_event_symbol.append(
                {
                    "symbol": symbol,
                    "event_type": event["event_type"],
                    "event_date": event_date,
                    "event_timestamp_complete": event_reason is None,
                    "candidate_control_count_after_event_date_exclusions": len(
                        candidate_control_dates(event_date, event_dates)
                    ),
                    "valid_control_count": len(valid_controls),
                    "valid_controls": valid_controls,
                    "invalid_controls": invalid_controls,
                }
            )

    status = (
        "PASS_METADATA_PREFLIGHT"
        if not event_failures and not control_adequacy_failures
        else "DATA_INADEQUATE_STOP"
    )
    valid_counts = [row["valid_control_count"] for row in per_event_symbol]
    body = {
        "document_type": "NEWS_SHOCK_LAB_V02_METADATA_PREFLIGHT_RECEIPT",
        "version": "0.2",
        "status": status,
        "freeze_fingerprint": EXPECTED_FREEZE_FINGERPRINT,
        "schedule_manifest_fingerprint": manifest["fingerprint"],
        "market_days_checked": len(days),
        "symbols": list(SYMBOLS),
        "event_count": manifest["event_count_total"],
        "event_symbol_cases": len(per_event_symbol),
        "event_timestamp_failure_count": len(event_failures),
        "control_adequacy_failure_count": len(control_adequacy_failures),
        "minimum_valid_control_count_observed": min(valid_counts),
        "maximum_valid_control_count_observed": max(valid_counts),
        "event_failures": event_failures,
        "control_adequacy_failures": control_adequacy_failures,
        "per_event_symbol": per_event_symbol,
        "inspection_boundary": {
            "timestamps_inspected": True,
            "checksums_inspected": True,
            "prices_inspected": False,
            "returns_computed": False,
            "volume_inspected": False,
            "trade_count_inspected": False,
            "taker_flow_inspected": False,
            "outcomes_evaluated": False,
        },
        "guards": {
            "holdout_2026_accessed": False,
            "mexc_2025_09_through_2025_12_accessed": False,
            "live_trading": False,
            "exchange_mutation": False,
            "main_merge": False,
            "render_deploy": False,
        },
        "frozen_control_contract": freeze["control_contract"],
    }
    body["fingerprint"] = canonical_hash(body)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return body


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        raise SystemExit("usage: v02_preflight <raw_root> <manifest.json> <receipt.json>")
    receipt = run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "fingerprint": receipt["fingerprint"],
                "market_days_checked": receipt["market_days_checked"],
                "event_symbol_cases": receipt["event_symbol_cases"],
                "event_timestamp_failure_count": receipt["event_timestamp_failure_count"],
                "control_adequacy_failure_count": receipt["control_adequacy_failure_count"],
                "minimum_valid_control_count_observed": receipt[
                    "minimum_valid_control_count_observed"
                ],
                "maximum_valid_control_count_observed": receipt[
                    "maximum_valid_control_count_observed"
                ],
                "inspection_boundary": receipt["inspection_boundary"],
                "guards": receipt["guards"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    raise SystemExit(0 if receipt["status"] == "PASS_METADATA_PREFLIGHT" else 3)
