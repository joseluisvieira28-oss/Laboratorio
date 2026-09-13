from __future__ import annotations

"""Fail-closed validation runner for MVE-CPI-FAMILY-01.

Preparation is inert: protected market data cannot be accessed unless a separate
active authorization receipt exists and matches the frozen scope exactly.
No exchange actions exist in this module.
"""

import csv
from copy import deepcopy
from datetime import date, datetime, time as dt_time, timezone
from decimal import Decimal, getcontext
from hashlib import sha256
from io import BytesIO, TextIOWrapper
import json
from math import isfinite
from pathlib import Path
import re
import statistics
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile
from zoneinfo import ZoneInfo

getcontext().prec = 50

ROOT = Path(__file__).parent
HISTORICAL_FREEZE_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_PRE_DISCOVERY_SIGNAL_STATISTICAL_FREEZE_V0.1.json"
HISTORICAL_CLOSEOUT_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_DISCOVERY_FINAL_CLOSEOUT_RECEIPT_V0.1.json"
MVE_FREEZE_PATH = ROOT / "MVE_CPI_FAMILY_01_PROSPECTIVE_FREEZE_V01.json"
ACTIVE_AUTH_PATH = ROOT / "MVE_CPI_FAMILY_01_DATA_ACCESS_AUTHORIZATION_V01.json"

HYPOTHESIS_ID = "MVE-CPI-FAMILY-01"
EXPECTED_HISTORICAL_FREEZE_FINGERPRINT = "945924528dde46a7e596ac77cec32e8deeff62adb42859f7e52abf63b6d5a37f"
EXPECTED_HISTORICAL_CLOSEOUT_FINGERPRINT = "2d94b1bbccf4f994bdc10a73449e6ce3580df53e38f52343ab0633ae8db571d0"
BASE_URL = "https://data.binance.vision/data/spot/daily/klines"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
TIMEFRAME = "1m"
TIMEFRAME_MS = 60_000
EXPECTED_FIELDS = 12
EXPECTED_HEADER = (
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume", "ignore",
)
CHECKSUM_RE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?([^\s]+)\s*$")
NY = ZoneInfo("America/New_York")
ENTRY_LOCAL = dt_time(8, 31)
EXIT_LOCAL = dt_time(8, 45)
FIXED_COST_BPS = Decimal("10")
DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_TIMEOUT_SECONDS = 60


def canonical_hash(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def load_hashed(path: Path, expected: str, label: str) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("fingerprint") != expected:
        raise PermissionError(f"{label} supplied fingerprint drift")
    unsigned = deepcopy(obj)
    unsigned.pop("fingerprint", None)
    if canonical_hash(unsigned) != expected:
        raise PermissionError(f"{label} canonical fingerprint drift")
    return obj


def load_active_authorization(path: Path = ACTIVE_AUTH_PATH) -> dict[str, Any]:
    if not path.exists():
        raise PermissionError("MVE CPI protected-data authorization is absent")
    auth = json.loads(path.read_text(encoding="utf-8"))
    if auth.get("document_type") != "MVE_CPI_FAMILY_01_DATA_ACCESS_AUTHORIZATION_V01":
        raise PermissionError("unexpected authorization document type")
    if auth.get("status") != "VALIDATION_2025_01_THROUGH_2025_08_AUTHORIZED_RESEARCH_ONLY":
        raise PermissionError("protected-data authorization is not active")
    if auth.get("authorization_active") is not True or auth.get("hypothesis_id") != HYPOTHESIS_ID:
        raise PermissionError("authorization identity/status drift")
    return auth


def validate_authority_chain(auth_path: Path = ACTIVE_AUTH_PATH) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    historical = load_hashed(HISTORICAL_FREEZE_PATH, EXPECTED_HISTORICAL_FREEZE_FINGERPRINT, "historical V0.3A freeze")
    closeout = load_hashed(HISTORICAL_CLOSEOUT_PATH, EXPECTED_HISTORICAL_CLOSEOUT_FINGERPRINT, "historical V0.3A closeout")
    mve = json.loads(MVE_FREEZE_PATH.read_text(encoding="utf-8"))
    auth = load_active_authorization(auth_path)

    if closeout.get("decision") != "NO_EDGE_STOP":
        raise PermissionError("historical parent verdict drift")
    gov = closeout["governance_closeout"]
    if gov["validation_2025_01_through_2025_08_accessed"] is not False or gov["holdout_2026_accessed"] is not False:
        raise PermissionError("protected cohort no longer untouched under historical closeout")

    if mve.get("status") != "FROZEN_PRE_AUTHORIZATION" or mve.get("hypothesis_id") != HYPOTHESIS_ID:
        raise PermissionError("MVE freeze drift")
    if mve["market_scope"] != {
        "source": "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY", "market_type": "SPOT", "timeframe": "1m",
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "entry": "OPEN_OF_08:31_AMERICA_NEW_YORK_1M_CANDLE",
        "exit": "OPEN_OF_08:45_AMERICA_NEW_YORK_1M_CANDLE",
        "fixed_round_trip_cost_bps": 10,
    }:
        raise PermissionError("MVE market scope drift")
    if mve["governance"]["data_access_authorized"] is not False:
        raise PermissionError("freeze itself must never authorize market access")

    validation = historical["cohorts"]["validation"]
    event_ids = validation["event_ids"]
    if validation["event_count"] != 8 or validation["period"] != "2025-01-01_THROUGH_2025-08-31":
        raise PermissionError("historical validation cohort drift")
    counts = historical["validation_signal_counts"]
    if (counts["directional_events"], counts["cooler"], counts["hotter"], counts["neutral"]) != (7, 6, 1, 1):
        raise PermissionError("historical validation signal counts drift")
    contract = historical["validation_contract_if_later_authorized"]
    if contract["both_assets_required"] is not True or contract["directional_event_count"] != 7:
        raise PermissionError("historical validation contract drift")
    if contract["per_asset_criteria"] != {
        "mean_aligned_net_bps_gt": "0",
        "median_aligned_gross_bps_gt": "0",
        "minimum_positive_aligned_gross_events": "5_OF_7",
    }:
        raise PermissionError("historical validation criteria drift")

    if auth.get("freeze_file_sha256") != file_sha256(MVE_FREEZE_PATH):
        raise PermissionError("authorization is not bound to current MVE freeze bytes")
    if auth.get("historical_pre_discovery_fingerprint") != EXPECTED_HISTORICAL_FREEZE_FINGERPRINT:
        raise PermissionError("authorization historical authority drift")
    scope = auth.get("authorized_scope", {})
    if scope.get("event_ids") != event_ids or scope.get("symbols") != list(SYMBOLS):
        raise PermissionError("authorization event/symbol scope drift")
    if scope.get("market_type") != "SPOT" or scope.get("timeframe") != TIMEFRAME:
        raise PermissionError("authorization market scope drift")
    if scope.get("fixed_round_trip_cost_bps") != 10:
        raise PermissionError("authorization cost drift")
    if auth.get("still_locked", {}).get("2025_09_through_2025_12") is not True:
        raise PermissionError("later 2025 unexpectedly unlocked")
    if auth.get("still_locked", {}).get("2026_and_later") is not True:
        raise PermissionError("2026 unexpectedly unlocked")
    if auth.get("still_locked", {}).get("exchange_mutation") is not True or auth.get("still_locked", {}).get("live_trading") is not True:
        raise PermissionError("trading capability unexpectedly unlocked")
    return historical, closeout, mve, auth


def event_day(event_id: str, allowed_event_ids: list[str]) -> str:
    if event_id not in allowed_event_ids or not event_id.startswith("US_CPI_2025-"):
        raise PermissionError("event outside exact authorized validation cohort")
    parsed = date.fromisoformat(event_id[7:])
    if parsed.year != 2025 or parsed.month > 8:
        raise PermissionError("date outside authorized Jan-Aug 2025 cohort")
    return parsed.isoformat()


def event_times_utc_ms(day: str) -> tuple[int, int]:
    parsed = date.fromisoformat(day)
    if parsed.year != 2025 or parsed.month > 8:
        raise PermissionError("timestamp construction outside authorized validation cohort")
    entry = datetime.combine(parsed, ENTRY_LOCAL, tzinfo=NY).astimezone(timezone.utc)
    exit_ = datetime.combine(parsed, EXIT_LOCAL, tzinfo=NY).astimezone(timezone.utc)
    if int((exit_ - entry).total_seconds()) != 14 * 60:
        raise RuntimeError("frozen interval drift")
    return int(entry.timestamp() * 1000), int(exit_.timestamp() * 1000)


def normalize_binance_timestamp_ms(raw: int) -> int:
    if raw >= 1_000_000_000_000_000:
        if raw % 1000 != 0:
            raise RuntimeError("microsecond timestamp not millisecond-aligned")
        raw //= 1000
    if raw < 1_000_000_000_000 or raw >= 10_000_000_000_000:
        raise RuntimeError("unexpected timestamp magnitude")
    return raw


def daily_object(symbol: str, event_id: str, allowed_event_ids: list[str]) -> dict[str, str]:
    if symbol not in SYMBOLS:
        raise PermissionError("alternate symbol blocked")
    day = event_day(event_id, allowed_event_ids)
    filename = f"{symbol}-{TIMEFRAME}-{day}.zip"
    url = f"{BASE_URL}/{symbol}/{TIMEFRAME}/{filename}"
    return {"symbol": symbol, "event_id": event_id, "day": day, "filename": filename,
            "archive_url": url, "checksum_url": url + ".CHECKSUM"}


def _download(url: str) -> bytes:
    if not url.startswith(BASE_URL + "/"):
        raise PermissionError("network destination outside official Binance Vision")
    last: Exception | None = None
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            req = Request(url, headers={"User-Agent": "DreamAccountOS-MVE-CPI-Validation/1.0"})
            with urlopen(req, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                if getattr(response, "status", 200) != 200:
                    raise RuntimeError(f"unexpected HTTP status {getattr(response, 'status', None)}")
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last = exc
            if attempt < DOWNLOAD_ATTEMPTS:
                time.sleep(float(attempt))
    raise RuntimeError(f"download failed after {DOWNLOAD_ATTEMPTS} attempts: {url}: {last}")


def _parse_checksum(text: str, filename: str) -> str:
    match = CHECKSUM_RE.fullmatch(text.strip())
    if match is None or match.group(2) != filename:
        raise ValueError("invalid official Binance CHECKSUM")
    return match.group(1).lower()


def _is_header(row: list[str]) -> bool:
    return tuple(c.strip().lower().replace(" ", "_") for c in row) == EXPECTED_HEADER


def adapt_daily_archive(*, obj: dict[str, str], archive_bytes: bytes, checksum_text: str) -> dict[str, Any]:
    digest = sha256(archive_bytes).hexdigest()
    if digest != _parse_checksum(checksum_text, obj["filename"]):
        raise RuntimeError(f"CHECKSUM_MISMATCH:{obj['symbol']}:{obj['day']}")
    try:
        zf = ZipFile(BytesIO(archive_bytes))
    except BadZipFile as exc:
        raise RuntimeError("INVALID_ZIP") from exc
    expected_member = obj["filename"][:-4] + ".csv"
    infos = zf.infolist()
    if len(infos) != 1 or infos[0].filename != expected_member or infos[0].is_dir() or infos[0].flag_bits & 1:
        raise RuntimeError("UNEXPECTED_ZIP_MEMBER")

    entry_ms, exit_ms = event_times_utc_ms(obj["day"])
    targets = {entry_ms: "entry", exit_ms: "exit"}
    extracted: dict[str, Decimal] = {}
    seen: set[int] = set()
    previous: int | None = None
    row_count = gap_count = missing_count = 0
    day_start = int(datetime.strptime(obj["day"], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
    day_end = day_start + 86_400_000

    with zf.open(infos[0], "r") as binary:
        reader = csv.reader(TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
        first = False
        for row in reader:
            if not row or all(not c.strip() for c in row):
                continue
            if not first and _is_header(row):
                first = True
                continue
            first = True
            if len(row) != EXPECTED_FIELDS:
                raise RuntimeError("MALFORMED_FIELD_COUNT")
            try:
                raw_open_time = int(row[0])
                open_time = normalize_binance_timestamp_ms(raw_open_time)
                op, hi, lo, cl, vol = map(Decimal, row[1:6])
                int(row[6]); Decimal(row[7]); int(row[8]); Decimal(row[9]); Decimal(row[10]); Decimal(row[11])
            except Exception as exc:
                raise RuntimeError("MALFORMED_NUMERIC_FIELD") from exc
            if open_time in seen:
                raise RuntimeError("DUPLICATE_OPEN_TIME")
            seen.add(open_time)
            if previous is not None:
                delta = open_time - previous
                if delta <= 0 or delta % TIMEFRAME_MS != 0:
                    raise RuntimeError("IRREGULAR_OPEN_TIME_ORDER_OR_SPACING")
                if delta > TIMEFRAME_MS:
                    gap_count += 1
                    missing_count += delta // TIMEFRAME_MS - 1
            previous = open_time
            if open_time % TIMEFRAME_MS != 0 or not day_start <= open_time < day_end:
                raise RuntimeError("OPEN_TIME_ALIGNMENT_OR_DAY_BOUNDARY")
            if min(op, hi, lo, cl) <= 0 or vol < 0 or hi < max(op, cl) or lo > min(op, cl) or hi < lo:
                raise RuntimeError("OHLCV_INTEGRITY")
            if not all(isfinite(float(v)) for v in (op, hi, lo, cl, vol)):
                raise RuntimeError("NON_FINITE_VALUE")
            row_count += 1
            label = targets.get(open_time)
            if label:
                if label in extracted:
                    raise RuntimeError("DUPLICATE_REQUIRED_TIMESTAMP")
                extracted[label] = op

    if row_count == 0 or set(extracted) != {"entry", "exit"}:
        raise RuntimeError("MISSING_REQUIRED_EVENT_TIMESTAMP")
    return {
        "event_id": obj["event_id"], "symbol": obj["symbol"], "day": obj["day"],
        "archive_filename": obj["filename"], "archive_sha256": digest, "checksum_verified": True,
        "row_count": row_count, "gap_count": gap_count, "missing_candle_count": missing_count,
        "entry_open_time_utc_ms": entry_ms, "exit_open_time_utc_ms": exit_ms,
        "entry_open": str(extracted["entry"]), "exit_open": str(extracted["exit"]),
    }


def gross_return_bps(entry: Decimal, exit_: Decimal) -> Decimal:
    if entry <= 0 or exit_ <= 0:
        raise ValueError("prices must be positive")
    return Decimal("10000") * (exit_ / entry - Decimal("1"))


def evaluate_asset(aligned_gross: list[Decimal]) -> dict[str, Any]:
    if len(aligned_gross) != 7:
        raise ValueError("validation requires exactly seven directional events")
    mean_gross = sum(aligned_gross, Decimal("0")) / Decimal(7)
    mean_net = mean_gross - FIXED_COST_BPS
    median_gross = statistics.median(aligned_gross)
    positive_count = sum(x > 0 for x in aligned_gross)
    loo = [(sum(aligned_gross, Decimal("0")) - aligned_gross[i]) / Decimal(6) - FIXED_COST_BPS for i in range(7)]
    total_abs = sum((abs(x) for x in aligned_gross), Decimal("0"))
    abs_sorted = sorted((abs(x) for x in aligned_gross), reverse=True)
    diagnostics = {
        "leave_one_out_mean_aligned_net_bps": loo,
        "minimum_leave_one_out_mean_aligned_net_bps": min(loo),
        "largest_abs_event_share_of_total_abs": None if total_abs == 0 else abs_sorted[0] / total_abs,
        "top3_abs_event_share_of_total_abs": None if total_abs == 0 else sum(abs_sorted[:3], Decimal("0")) / total_abs,
    }
    criteria = {
        "mean_aligned_net_bps_gt_0": mean_net > 0,
        "median_aligned_gross_bps_gt_0": median_gross > 0,
        "positive_aligned_gross_events_gte_5_of_7": positive_count >= 5,
    }
    return {
        "mean_aligned_gross_bps": mean_gross, "mean_aligned_net_bps": mean_net,
        "median_aligned_gross_bps": median_gross, "positive_aligned_gross_event_count": positive_count,
        "criteria": criteria, "pass": all(criteria.values()), "diagnostics": diagnostics,
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def write_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(body), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_validation(output_dir: Path) -> dict[str, Any]:
    historical, closeout, mve, auth = validate_authority_chain()
    event_ids = list(auth["authorized_scope"]["event_ids"])
    labels = historical["surprise_signal"]["frozen_event_labels"]
    neutral_ids = set(historical["validation_signal_counts"]["neutral_event_ids"])

    source_rows: list[dict[str, Any]] = []
    prices: dict[tuple[str, str], tuple[Decimal, Decimal]] = {}
    for event_id in event_ids:
        for symbol in SYMBOLS:
            obj = daily_object(symbol, event_id, event_ids)
            checksum = _download(obj["checksum_url"]).decode("utf-8-sig")
            archive = _download(obj["archive_url"])
            row = adapt_daily_archive(obj=obj, archive_bytes=archive, checksum_text=checksum)
            source_rows.append(row)
            prices[(event_id, symbol)] = (Decimal(row["entry_open"]), Decimal(row["exit_open"]))
    if len(source_rows) != 16 or len(prices) != 16:
        raise RuntimeError("validation event-symbol cardinality drift")

    directional: dict[str, list[Decimal]] = {s: [] for s in SYMBOLS}
    event_rows: list[dict[str, Any]] = []
    for event_id in event_ids:
        frozen = labels[event_id]
        sign = int(frozen["shock_sign"])
        neutral = event_id in neutral_ids
        if neutral != (frozen["label"] == "NEUTRAL" and sign == 0):
            raise RuntimeError("neutral identity drift")
        row: dict[str, Any] = {"event_id": event_id, "label": frozen["label"], "shock_sign": sign, "assets": {}}
        for symbol in SYMBOLS:
            entry, exit_ = prices[(event_id, symbol)]
            gross = gross_return_bps(entry, exit_)
            aligned_gross = None if neutral else Decimal(-sign) * gross
            aligned_net = None if neutral else aligned_gross - FIXED_COST_BPS
            row["assets"][symbol] = {"entry_open": entry, "exit_open": exit_, "gross_return_bps": gross,
                                      "aligned_gross_bps": aligned_gross, "aligned_net_bps": aligned_net}
            if not neutral:
                directional[symbol].append(aligned_gross)
        event_rows.append(row)

    evaluations = {s: evaluate_asset(directional[s]) for s in SYMBOLS}
    family_pass = all(evaluations[s]["pass"] for s in SYMBOLS)
    classification = "MVE_1_OOS_POSITIVE" if family_pass else "MVE_CLOSED_NO_EDGE"
    result = {
        "document_type": "MVE_CPI_FAMILY_01_VALIDATION_CLOSEOUT_V01",
        "version": "0.1", "hypothesis_id": HYPOTHESIS_ID,
        "classification": classification, "family_pass": family_pass,
        "market_scope": mve["market_scope"], "event_ids": event_ids,
        "source_integrity": {"archive_count": len(source_rows), "archives": source_rows},
        "events": event_rows, "assets": evaluations,
        "governance": {
            "historical_parent_verdict": closeout["decision"],
            "2025_09_through_2025_12_accessed": False,
            "2026_accessed": False,
            "exchange_mutation": False,
            "live_trading": False,
            "post_pass_route": "SHADOW_OR_PAPER_DESIGN_ONLY",
        },
    }
    result["fingerprint"] = canonical_hash(_jsonable(result))
    write_json(output_dir / "MVE_CPI_FAMILY_01_VALIDATION_CLOSEOUT_V01.json", result)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    # validate_authority_chain is called before any network action.
    run_validation(args.output_dir)
