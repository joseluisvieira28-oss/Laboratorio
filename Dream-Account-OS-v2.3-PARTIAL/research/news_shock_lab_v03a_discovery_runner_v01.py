from __future__ import annotations

"""Frozen Discovery runner for NEWS_SHOCK_LAB_V03A_CPI_SURPRISE.

Executes only the separately authorized 2022-2024 Discovery computation using
official Binance Vision Spot daily 1m archives. It verifies official SHA-256
CHECKSUM files, extracts only the frozen 08:31 and 08:45 America/New_York
candle OPEN values, and evaluates the already-frozen exact fixed-count
permutation test. It never accesses 2025/2026 market data and never authorizes
trading, exchange mutation, tuning, alternate windows, or alternate assets.
"""

import csv
from copy import deepcopy
from datetime import date, datetime, time as dt_time, timezone
from decimal import Decimal, getcontext
from hashlib import sha256
from itertools import combinations
from io import BytesIO, TextIOWrapper
import json
from math import comb, isfinite, sqrt
from pathlib import Path
import re
import statistics
import sys
import time
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile
from zoneinfo import ZoneInfo

getcontext().prec = 50

ROOT = Path(__file__).parent
PRE_DISCOVERY_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_PRE_DISCOVERY_SIGNAL_STATISTICAL_FREEZE_V0.1.json"
FINAL_PROVENANCE_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_FINAL_CONSENSUS_PROVENANCE_FREEZE_V0.1.json"
AUTHORIZATION_PATH = ROOT / "NEWS_SHOCK_LAB_V03A_DISCOVERY_DATA_ACCESS_AUTHORIZATION_V0.1.json"

EXPECTED_PRE_DISCOVERY_FINGERPRINT = "945924528dde46a7e596ac77cec32e8deeff62adb42859f7e52abf63b6d5a37f"
EXPECTED_FINAL_PROVENANCE_FINGERPRINT = "dbf8e972076fe98e90a6ed45dac5a091a557e2e24f6391ee790b6de2af49c0e4"
EXPECTED_AUTHORIZATION_FINGERPRINT = "c9ead499648c5951245df1f9db13c8838edca1b9bf25ebeacbfa796fe2ad162e"
EXPECTED_PRE_DISCOVERY_GATE_RECEIPT_FINGERPRINT = "70e96e2721b19f5980b46f9fb48581a7898ccd345f0603079198ddadbd187fa5"
EXPECTED_PRE_DISCOVERY_GATE_ARTIFACT_DIGEST = "sha256:c0f17bd24f1fd8e644cc824ee3c7ca749c4dc579a8392fd28040e6c4ed5a0a0b"

LAB_ID = "NEWS_SHOCK_LAB_V03A_CPI_SURPRISE"
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
NEW_YORK = ZoneInfo("America/New_York")
ENTRY_LOCAL = dt_time(8, 31)
EXIT_LOCAL = dt_time(8, 45)
FIXED_COST_BPS = Decimal("10")
ALPHA = Decimal("0.05")
HOTTER_COUNT = 11
COOLER_COUNT = 10
DIRECTIONAL_COUNT = 21
EXPECTED_PERMUTATIONS = 352_716
DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_TIMEOUT_SECONDS = 60


def canonical_hash(obj: object) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def load_hashed(path: Path, expected: str, label: str) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("fingerprint") != expected:
        raise PermissionError(f"{label} supplied fingerprint drift: {raw.get('fingerprint')}")
    unsigned = deepcopy(raw)
    unsigned.pop("fingerprint", None)
    actual = canonical_hash(unsigned)
    if actual != expected:
        raise PermissionError(f"{label} canonical fingerprint drift: {actual}")
    return raw


def validate_authority_chain() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    final = load_hashed(FINAL_PROVENANCE_PATH, EXPECTED_FINAL_PROVENANCE_FINGERPRINT, "final provenance")
    pre = load_hashed(PRE_DISCOVERY_PATH, EXPECTED_PRE_DISCOVERY_FINGERPRINT, "pre-discovery freeze")
    auth = load_hashed(AUTHORIZATION_PATH, EXPECTED_AUTHORIZATION_FINGERPRINT, "Discovery authorization")

    if final.get("status") != "FINAL_PROVENANCE_FROZEN_PRE_MARKET_OUTCOME":
        raise PermissionError("final provenance status drift")
    if (final["corpus"]["events_total"], final["corpus"]["complete_a"], final["corpus"]["incomplete"], final["corpus"]["complete_b"]) != (44, 35, 9, 0):
        raise PermissionError("final provenance corpus count drift")
    if pre["lab_id"] != LAB_ID or auth["lab_id"] != LAB_ID:
        raise PermissionError("lab identity drift")
    if pre["status"] != "FROZEN_PENDING_FAIL_CLOSED_GATE_NO_MARKET_OUTCOMES_ACCESSED":
        raise PermissionError("pre-discovery freeze status drift")
    if auth["status"] != "DISCOVERY_2022_2024_MARKET_DATA_ACCESS_AUTHORIZED_RESEARCH_ONLY":
        raise PermissionError("Discovery market-data access is not authorized")

    chain = auth["authority_chain"]
    if chain["final_provenance_freeze_fingerprint"] != EXPECTED_FINAL_PROVENANCE_FINGERPRINT:
        raise PermissionError("authorization final-provenance authority drift")
    if chain["pre_discovery_freeze_fingerprint"] != EXPECTED_PRE_DISCOVERY_FINGERPRINT:
        raise PermissionError("authorization pre-discovery authority drift")
    if chain["pre_discovery_gate_receipt_fingerprint"] != EXPECTED_PRE_DISCOVERY_GATE_RECEIPT_FINGERPRINT:
        raise PermissionError("authorization gate-receipt authority drift")
    if chain["pre_discovery_gate_artifact_digest"] != EXPECTED_PRE_DISCOVERY_GATE_ARTIFACT_DIGEST:
        raise PermissionError("authorization gate-artifact authority drift")

    discovery = pre["cohorts"]["discovery"]
    scope = auth["authorized_scope"]
    if discovery["event_count"] != 27 or len(discovery["event_ids"]) != 27:
        raise PermissionError("Discovery cohort cardinality drift")
    if scope["discovery_event_ids"] != discovery["event_ids"] or scope["event_count"] != 27:
        raise PermissionError("authorized Discovery cohort identity drift")
    if any(not event_id.startswith(("US_CPI_2022-", "US_CPI_2023-", "US_CPI_2024-")) for event_id in discovery["event_ids"]):
        raise PermissionError("protected year leaked into Discovery cohort")
    if scope["source"] != "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY" or scope["market_type"] != "SPOT":
        raise PermissionError("authorized market source/type drift")
    if scope["symbols"] != list(SYMBOLS) or scope["timeframe"] != TIMEFRAME:
        raise PermissionError("authorized symbols/timeframe drift")
    if scope["checksum_required"] is not True or scope["no_interpolation"] is not True or scope["no_synthetic_candles"] is not True:
        raise PermissionError("authorized data-integrity contract weakened")
    if scope["analysis_extraction_policy"] != "Only the frozen 08:31 and 08:45 America/New_York 1m candle OPEN values may be used for the primary outcome computation; no alternate market windows may be evaluated.":
        raise PermissionError("analysis extraction policy drift")

    computation = auth["authorized_computation"]
    if computation["may_compute_discovery_crypto_returns"] is not True:
        raise PermissionError("Discovery return computation not authorized")
    if computation["may_compute_only_frozen_primary_test_and_secondary_diagnostics"] is not True:
        raise PermissionError("frozen-test-only authority missing")
    if computation["may_tune_after_results"] is not False:
        raise PermissionError("post-result tuning unexpectedly authorized")
    if computation["fixed_cost_bps"] != "10" or computation["permutations"] != EXPECTED_PERMUTATIONS:
        raise PermissionError("authorized cost/permutation drift")
    if computation["primary_assets"] != list(SYMBOLS):
        raise PermissionError("authorized primary assets drift")

    for key in (
        "2025_01_through_2025_08_validation_market_data", "2025_09_through_2025_12_mexc",
        "2026_all_market_data", "alternate_assets", "alternate_entry_exit_times",
        "alternate_horizons", "alternate_signal_weights", "exchange_mutation", "live_trading",
        "main_merge", "outlier_deletion_or_winsorization", "render_deploy",
        "signal_magnitude_thresholds", "subperiod_or_regime_search",
    ):
        if auth["still_locked"].get(key) is not True:
            raise PermissionError(f"protected capability unexpectedly unlocked: {key}")

    timing = pre["event_timing_contract"]
    if timing["primary_entry"] != "OPEN_OF_08:31_AMERICA_NEW_YORK_1M_CANDLE" or timing["primary_exit"] != "OPEN_OF_08:45_AMERICA_NEW_YORK_1M_CANDLE":
        raise PermissionError("frozen primary timing drift")
    if pre["return_and_cost_contract"]["fixed_round_trip_cost_bps"] != "10":
        raise PermissionError("frozen cost drift")
    primary = pre["primary_discovery_test"]
    if primary["test"] != "EXACT_FIXED_COUNT_LABEL_PERMUTATION" or primary["rng"] != "NONE":
        raise PermissionError("primary exact-test contract drift")
    if primary["preserve_label_counts"] != {"COOLER": COOLER_COUNT, "HOTTER": HOTTER_COUNT}:
        raise PermissionError("fixed label-count contract drift")
    if primary["unique_assignment_count"] != EXPECTED_PERMUTATIONS or primary["directional_event_count"] != DIRECTIONAL_COUNT:
        raise PermissionError("primary exact-test cardinality drift")
    if primary["statistic"] != "MEAN_ALIGNED_GROSS_BPS" or primary["alternative"] != "GREATER_THAN_ZERO":
        raise PermissionError("primary statistic/alternative drift")
    if Decimal(primary["alpha"]) != ALPHA:
        raise PermissionError("alpha drift")
    counts = pre["discovery_signal_counts"]
    if (counts["directional_events"], counts["hotter"], counts["cooler"], counts["neutral"], counts["exact_label_permutation_count"]) != (21, 11, 10, 6, EXPECTED_PERMUTATIONS):
        raise PermissionError("frozen Discovery signal counts drift")
    if comb(DIRECTIONAL_COUNT, HOTTER_COUNT) != EXPECTED_PERMUTATIONS:
        raise RuntimeError("combination cardinality contradicts frozen contract")
    return final, pre, auth


def event_day(event_id: str) -> str:
    if not event_id.startswith("US_CPI_"):
        raise ValueError("unexpected event id")
    parsed = date.fromisoformat(event_id[len("US_CPI_"):])
    if parsed.year not in (2022, 2023, 2024):
        raise PermissionError("attempted protected-year market-data access")
    return parsed.isoformat()


def event_times_utc_ms(day: str) -> tuple[int, int]:
    parsed = date.fromisoformat(day)
    if parsed.year not in (2022, 2023, 2024):
        raise PermissionError("protected-year timestamp construction blocked")
    entry_utc = datetime.combine(parsed, ENTRY_LOCAL, tzinfo=NEW_YORK).astimezone(timezone.utc)
    exit_utc = datetime.combine(parsed, EXIT_LOCAL, tzinfo=NEW_YORK).astimezone(timezone.utc)
    if (exit_utc - entry_utc).total_seconds() != 14 * 60:
        raise RuntimeError("frozen open-to-open interval drift")
    return int(entry_utc.timestamp() * 1000), int(exit_utc.timestamp() * 1000)


def daily_object(symbol: str, day: str) -> dict[str, str]:
    if symbol not in SYMBOLS:
        raise PermissionError("alternate symbol blocked")
    if date.fromisoformat(day).year not in (2022, 2023, 2024):
        raise PermissionError("protected-year archive construction blocked")
    filename = f"{symbol}-{TIMEFRAME}-{day}.zip"
    archive_url = f"{BASE_URL}/{symbol}/{TIMEFRAME}/{filename}"
    return {"symbol": symbol, "day": day, "filename": filename, "archive_url": archive_url, "checksum_url": archive_url + ".CHECKSUM"}


def _download(url: str) -> bytes:
    if not url.startswith(BASE_URL + "/"):
        raise PermissionError("network destination outside official Binance Vision archive")
    last_error: Exception | None = None
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            req = Request(url, headers={"User-Agent": "DreamAccountOS-NewsShock-V03A-Research/1.0"})
            with urlopen(req, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                if getattr(response, "status", 200) != 200:
                    raise RuntimeError(f"unexpected HTTP status {getattr(response, 'status', None)}")
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < DOWNLOAD_ATTEMPTS:
                time.sleep(float(attempt))
    raise RuntimeError(f"download failed after {DOWNLOAD_ATTEMPTS} attempts: {url}: {last_error}")


def _parse_checksum(text: str, filename: str) -> str:
    match = CHECKSUM_RE.fullmatch(text.strip())
    if match is None or match.group(2) != filename:
        raise ValueError("invalid official Binance CHECKSUM")
    return match.group(1).lower()


def _is_header(row: list[str]) -> bool:
    return tuple(cell.strip().lower().replace(" ", "_") for cell in row) == EXPECTED_HEADER


def _utc_day_bounds_ms(day: str) -> tuple[int, int]:
    start = int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
    return start, start + 86_400_000


def adapt_authorized_daily_archive(*, symbol: str, day: str, archive_bytes: bytes, checksum_text: str) -> dict[str, Any]:
    obj = daily_object(symbol, day)
    expected_digest = _parse_checksum(checksum_text, obj["filename"])
    actual_digest = sha256(archive_bytes).hexdigest()
    if actual_digest != expected_digest:
        raise RuntimeError(f"CHECKSUM_MISMATCH:{symbol}:{day}")
    expected_member = obj["filename"][:-4] + ".csv"
    try:
        zf = ZipFile(BytesIO(archive_bytes))
    except BadZipFile as exc:
        raise RuntimeError(f"INVALID_ZIP:{symbol}:{day}") from exc
    infos = zf.infolist()
    if len(infos) != 1 or infos[0].filename != expected_member or infos[0].is_dir() or infos[0].flag_bits & 0x1:
        raise RuntimeError(f"UNEXPECTED_ZIP_MEMBER:{symbol}:{day}")

    start_ms, end_ms = _utc_day_bounds_ms(day)
    entry_ms, exit_ms = event_times_utc_ms(day)
    targets = {entry_ms: "entry", exit_ms: "exit"}
    extracted: dict[str, Decimal] = {}
    row_count = gap_count = missing_count = 0
    previous: int | None = None
    seen: set[int] = set()

    with zf.open(infos[0], "r") as binary:
        reader = csv.reader(TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
        first = False
        for row in reader:
            if not row or all(not cell.strip() for cell in row):
                continue
            if not first and _is_header(row):
                first = True
                continue
            first = True
            if len(row) != EXPECTED_FIELDS:
                raise RuntimeError(f"MALFORMED_FIELD_COUNT:{symbol}:{day}")
            try:
                open_time = int(row[0]); open_price = Decimal(row[1]); high = Decimal(row[2]); low = Decimal(row[3]); close = Decimal(row[4]); volume = Decimal(row[5]); close_time = int(row[6])
                Decimal(row[7]); int(row[8]); Decimal(row[9]); Decimal(row[10]); Decimal(row[11])
            except Exception as exc:
                raise RuntimeError(f"MALFORMED_NUMERIC_FIELD:{symbol}:{day}") from exc
            if open_time >= 1_000_000_000_000_000 or close_time >= 1_000_000_000_000_000:
                raise RuntimeError(f"UNEXPECTED_MICROSECOND_TIMESTAMP_IN_DISCOVERY:{symbol}:{day}")
            if open_time in seen:
                raise RuntimeError(f"DUPLICATE_OPEN_TIME:{symbol}:{day}")
            seen.add(open_time)
            if previous is not None:
                delta = open_time - previous
                if open_time <= previous or delta % TIMEFRAME_MS != 0:
                    raise RuntimeError(f"IRREGULAR_OPEN_TIME_ORDER_OR_SPACING:{symbol}:{day}")
                if delta > TIMEFRAME_MS:
                    gap_count += 1; missing_count += delta // TIMEFRAME_MS - 1
            previous = open_time
            if open_time % TIMEFRAME_MS != 0 or not start_ms <= open_time < end_ms:
                raise RuntimeError(f"OPEN_TIME_ALIGNMENT_OR_DAY_BOUNDARY:{symbol}:{day}")
            if close_time <= open_time or close_time > open_time + TIMEFRAME_MS - 1:
                raise RuntimeError(f"CLOSE_TIME_BOUNDARY:{symbol}:{day}")
            if min(open_price, high, low, close) <= 0 or volume < 0 or high < max(open_price, close) or low > min(open_price, close) or high < low:
                raise RuntimeError(f"OHLCV_INTEGRITY:{symbol}:{day}")
            if not all(isfinite(float(v)) for v in (open_price, high, low, close, volume)):
                raise RuntimeError(f"NON_FINITE_VALUE:{symbol}:{day}")
            row_count += 1
            label = targets.get(open_time)
            if label is not None:
                if label in extracted:
                    raise RuntimeError(f"DUPLICATE_REQUIRED_TIMESTAMP:{symbol}:{day}:{label}")
                extracted[label] = open_price

    if row_count == 0:
        raise RuntimeError(f"EMPTY_ARCHIVE:{symbol}:{day}")
    if set(extracted) != {"entry", "exit"}:
        raise RuntimeError(f"MISSING_REQUIRED_EVENT_TIMESTAMP:{symbol}:{day}:{sorted({'entry','exit'} - set(extracted))}")
    return {
        "symbol": symbol, "day": day, "archive_filename": obj["filename"], "archive_url": obj["archive_url"],
        "checksum_url": obj["checksum_url"], "archive_sha256": actual_digest, "checksum_verified": True,
        "row_count": row_count, "gap_count": gap_count, "missing_candle_count": missing_count,
        "entry_open_time_utc_ms": entry_ms, "exit_open_time_utc_ms": exit_ms,
        "entry_open": str(extracted["entry"]), "exit_open": str(extracted["exit"]),
    }


def acquire_authorized_event_symbol(symbol: str, event_id: str) -> dict[str, Any]:
    day = event_day(event_id)
    obj = daily_object(symbol, day)
    checksum_text = _download(obj["checksum_url"]).decode("utf-8-sig")
    result = adapt_authorized_daily_archive(symbol=symbol, day=day, archive_bytes=_download(obj["archive_url"]), checksum_text=checksum_text)
    result["event_id"] = event_id
    return result


def gross_return_bps(entry: Decimal, exit_: Decimal) -> Decimal:
    if entry <= 0 or exit_ <= 0:
        raise ValueError("prices must be positive")
    return Decimal("10000") * (exit_ / entry - Decimal("1"))


def exact_fixed_count_p_value(gross_returns: list[Decimal], observed_signs: list[int], *, hotter_count: int = HOTTER_COUNT, expected_permutations: int | None = EXPECTED_PERMUTATIONS) -> dict[str, Any]:
    n = len(gross_returns)
    if len(observed_signs) != n or any(s not in (-1, 1) for s in observed_signs):
        raise ValueError("directional input drift")
    if sum(s == 1 for s in observed_signs) != hotter_count or sum(s == -1 for s in observed_signs) != n - hotter_count:
        raise ValueError("observed fixed label counts drift")
    assignment_count = comb(n, hotter_count)
    if expected_permutations is not None and assignment_count != expected_permutations:
        raise ValueError("exact permutation cardinality drift")
    observed_aligned = [Decimal(-s) * r for s, r in zip(observed_signs, gross_returns)]
    observed_stat = sum(observed_aligned, Decimal("0")) / Decimal(n)
    total = sum(gross_returns, Decimal("0"))
    extreme = enumerated = 0
    for hot_indices in combinations(range(n), hotter_count):
        hot_sum = sum((gross_returns[i] for i in hot_indices), Decimal("0"))
        if (total - Decimal("2") * hot_sum) / Decimal(n) >= observed_stat:
            extreme += 1
        enumerated += 1
    if enumerated != assignment_count:
        raise RuntimeError("exact enumeration count drift")
    return {"observed_mean_aligned_gross_bps": observed_stat, "extreme_assignment_count": extreme, "assignment_count": enumerated, "p_value": Decimal(extreme) / Decimal(enumerated), "observed_aligned_gross_bps": observed_aligned}


def evaluate_asset(gross_returns: list[Decimal], observed_signs: list[int]) -> dict[str, Any]:
    exact = exact_fixed_count_p_value(gross_returns, observed_signs)
    aligned = exact["observed_aligned_gross_bps"]
    n = len(aligned); aligned_sum = sum(aligned, Decimal("0"))
    mean_gross = exact["observed_mean_aligned_gross_bps"]
    mean_net = mean_gross - FIXED_COST_BPS
    median_gross = statistics.median(aligned)
    loo = [(aligned_sum - aligned[i]) / Decimal(n - 1) - FIXED_COST_BPS for i in range(n)]
    criteria = {
        "exact_one_sided_p_lte_0_05": exact["p_value"] <= ALPHA,
        "mean_aligned_net_bps_gt_0": mean_net > 0,
        "median_aligned_gross_bps_gt_0": median_gross > 0,
        "every_leave_one_out_mean_aligned_net_bps_gt_0": all(v > 0 for v in loo),
    }
    return {
        "directional_event_count": n, "mean_aligned_gross_bps": mean_gross, "mean_aligned_net_bps": mean_net,
        "median_aligned_gross_bps": median_gross, "hit_rate_aligned_gross_gt_zero": Decimal(sum(v > 0 for v in aligned)) / Decimal(n),
        "exact_one_sided_p_value": exact["p_value"], "exact_extreme_assignment_count": exact["extreme_assignment_count"],
        "exact_assignment_count": exact["assignment_count"], "leave_one_out_mean_aligned_net_bps": loo,
        "minimum_leave_one_out_mean_aligned_net_bps": min(loo), "criteria": criteria,
        "pass": all(criteria.values()), "aligned_gross_bps": aligned,
    }


def pearson_descriptive(xs: list[Decimal], ys: list[Decimal]) -> float | None:
    xf = [float(v) for v in xs]; yf = [float(v) for v in ys]
    mx = sum(xf) / len(xf); my = sum(yf) / len(yf)
    dx = [v - mx for v in xf]; dy = [v - my for v in yf]
    denom = sqrt(sum(v*v for v in dx) * sum(v*v for v in dy))
    return None if denom == 0 else sum(a*b for a,b in zip(dx,dy)) / denom


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal): return format(value, "f")
    if isinstance(value, dict): return {k: _jsonable(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [_jsonable(v) for v in value]
    return value


def _with_fingerprint(body: dict[str, Any]) -> dict[str, Any]:
    result = _jsonable(body); result["fingerprint"] = canonical_hash(result); return result


def write_json(path: Path, body: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(body), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_discovery(output_dir: Path) -> dict[str, Any]:
    _, pre, auth = validate_authority_chain()
    output_dir.mkdir(parents=True, exist_ok=True)
    event_ids = list(auth["authorized_scope"]["discovery_event_ids"])
    labels = pre["surprise_signal"]["frozen_event_labels"]
    neutral_ids = set(pre["discovery_signal_counts"]["neutral_event_ids"])

    source_rows: list[dict[str, Any]] = []
    prices: dict[tuple[str,str], tuple[Decimal,Decimal]] = {}
    for index, event_id in enumerate(event_ids, 1):
        for symbol in SYMBOLS:
            result = acquire_authorized_event_symbol(symbol, event_id)
            source_rows.append(result)
            prices[(event_id, symbol)] = (Decimal(result["entry_open"]), Decimal(result["exit_open"]))
        print(f"NEWS V03A Discovery data {index:02d}/{len(event_ids)} {event_id}", flush=True)
    if len(source_rows) != 54 or len(prices) != 54:
        raise RuntimeError("authorized event-symbol cardinality drift")

    source_manifest = _with_fingerprint({
        "document_type": "NEWS_SHOCK_LAB_V03A_DISCOVERY_SOURCE_MANIFEST_V0.1", "version": "0.1", "lab_id": LAB_ID,
        "status": "DISCOVERY_SOURCE_DATA_INTEGRITY_PASS", "source": "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY", "market_type": "SPOT",
        "timeframe": TIMEFRAME, "symbols": list(SYMBOLS), "event_count": 27, "archive_count": 54,
        "pre_discovery_freeze_fingerprint": EXPECTED_PRE_DISCOVERY_FINGERPRINT,
        "discovery_authorization_fingerprint": EXPECTED_AUTHORIZATION_FINGERPRINT,
        "protected_data_access": {"validation_2025_accessed": False, "mexc_2025_09_through_2025_12_accessed": False, "holdout_2026_accessed": False},
        "archives": source_rows,
    })
    write_json(output_dir / "discovery_source_manifest.json", source_manifest)

    event_rows = []; directional_ids = []; directional_signs = []
    gross_by_symbol: dict[str,list[Decimal]] = {s: [] for s in SYMBOLS}
    for event_id in event_ids:
        label = labels[event_id]["label"]; sign = int(labels[event_id]["shock_sign"]); neutral = event_id in neutral_ids
        if neutral != (sign == 0 and label == "NEUTRAL"):
            raise RuntimeError(f"neutral identity/sign drift: {event_id}")
        row: dict[str,Any] = {"event_id": event_id, "label": label, "shock_sign": sign, "composite_surprise_pp": labels[event_id]["composite_surprise_pp"], "assets": {}}
        if not neutral:
            directional_ids.append(event_id); directional_signs.append(sign)
        for symbol in SYMBOLS:
            entry, exit_ = prices[(event_id, symbol)]; gross = gross_return_bps(entry, exit_)
            aligned_gross = None if neutral else Decimal(-sign) * gross
            aligned_net = None if neutral else aligned_gross - FIXED_COST_BPS
            row["assets"][symbol] = {"entry_open": entry, "exit_open": exit_, "gross_return_bps": gross, "aligned_gross_bps": aligned_gross, "aligned_net_bps": aligned_net}
            if not neutral: gross_by_symbol[symbol].append(gross)
        event_rows.append(row)
    if len(directional_ids) != DIRECTIONAL_COUNT or sum(s == 1 for s in directional_signs) != HOTTER_COUNT or sum(s == -1 for s in directional_signs) != COOLER_COUNT:
        raise RuntimeError("directional event/label count drift")

    event_doc = _with_fingerprint({
        "document_type": "NEWS_SHOCK_LAB_V03A_DISCOVERY_EVENT_RETURNS_V0.1", "version": "0.1", "lab_id": LAB_ID,
        "status": "DISCOVERY_RETURNS_COMPUTED_FROZEN_WINDOW_ONLY", "event_count": 27, "directional_event_count": 21,
        "neutral_event_count": 6, "timing": "08:31_TO_08:45_AMERICA_NEW_YORK_OPEN_TO_OPEN",
        "fixed_round_trip_cost_bps": FIXED_COST_BPS, "neutral_events_excluded_from_directional_test": True, "events": event_rows,
    })
    write_json(output_dir / "discovery_event_returns.json", event_doc)

    evaluations = {s: evaluate_asset(gross_by_symbol[s], directional_signs) for s in SYMBOLS}
    if not evaluations["BTCUSDT"]["pass"]:
        decision = "NO_EDGE_STOP"
    elif not evaluations["ETHUSDT"]["pass"]:
        decision = "NO_ROBUST_CROSS_ASSET_EDGE_STOP"
    else:
        decision = "DISCOVERY_SURVIVES_ELIGIBLE_FOR_SEPARATE_2025_VALIDATION_AUTHORIZATION"

    btc_aligned = evaluations["BTCUSDT"]["aligned_gross_bps"]; eth_aligned = evaluations["ETHUSDT"]["aligned_gross_bps"]
    diagnostics = {"directional_event_ids": directional_ids, "btc_eth_cross_event_comparison": {
        "pearson_correlation_aligned_gross": pearson_descriptive(btc_aligned, eth_aligned),
        "same_sign_count": sum((b>0 and e>0) or (b<0 and e<0) or (b==0 and e==0) for b,e in zip(btc_aligned,eth_aligned)),
        "directional_event_count": DIRECTIONAL_COUNT,
    }}
    summary = {}
    for symbol, evaluation in evaluations.items():
        item = dict(evaluation); item.pop("aligned_gross_bps"); summary[symbol] = item

    result_doc = _with_fingerprint({
        "document_type": "NEWS_SHOCK_LAB_V03A_DISCOVERY_RESULTS_V0.1", "version": "0.1", "lab_id": LAB_ID,
        "status": "DISCOVERY_FROZEN_TEST_COMPLETE", "decision": decision,
        "pre_discovery_freeze_fingerprint": EXPECTED_PRE_DISCOVERY_FINGERPRINT,
        "discovery_authorization_fingerprint": EXPECTED_AUTHORIZATION_FINGERPRINT,
        "source_manifest_fingerprint": source_manifest["fingerprint"], "event_returns_fingerprint": event_doc["fingerprint"],
        "primary_test": {"test": "EXACT_FIXED_COUNT_LABEL_PERMUTATION", "alternative": "GREATER_THAN_ZERO", "statistic": "MEAN_ALIGNED_GROSS_BPS", "hotter_count": 11, "cooler_count": 10, "unique_assignment_count": EXPECTED_PERMUTATIONS, "alpha": ALPHA, "fixed_round_trip_cost_bps": FIXED_COST_BPS},
        "assets": summary, "secondary_diagnostics": diagnostics,
        "governance": {"tuning_after_results_performed": False, "alternate_windows_evaluated": False, "alternate_assets_evaluated": False,
            "magnitude_thresholds_evaluated": False, "subperiod_or_regime_search_performed": False, "outliers_deleted_or_winsorized": False,
            "validation_2025_accessed": False, "mexc_2025_09_through_2025_12_accessed": False, "holdout_2026_accessed": False,
            "live_trading_authorized": False, "exchange_mutation_authorized": False},
    })
    write_json(output_dir / "discovery_results.json", result_doc)

    survives = decision.startswith("DISCOVERY_SURVIVES")
    closeout = _with_fingerprint({
        "document_type": "NEWS_SHOCK_LAB_V03A_DISCOVERY_CLOSEOUT_V0.1", "version": "0.1", "lab_id": LAB_ID,
        "status": "DISCOVERY_COMPLETE_SURVIVES_AWAIT_SEPARATE_VALIDATION_AUTHORIZATION" if survives else "DISCOVERY_COMPLETE_HYPOTHESIS_CLOSED_NO_VALIDATION_ACCESS",
        "decision": decision, "discovery_results_fingerprint": result_doc["fingerprint"], "source_manifest_fingerprint": source_manifest["fingerprint"],
        "event_returns_fingerprint": event_doc["fingerprint"], "validation_2025_market_data_access_authorized": False,
        "mexc_2025_09_through_2025_12_access_authorized": False, "holdout_2026_access_authorized": False,
        "live_trading_authorized": False, "exchange_mutation_authorized": False,
        "next_gate": "SEPARATE_2025_VALIDATION_DATA_ACCESS_AUTHORIZATION_REQUIRED" if survives else "STOP_NO_EDGE_NO_2025_VALIDATION_ACCESS",
        "no_rescue": True,
    })
    write_json(output_dir / "discovery_closeout.json", closeout)
    print(json.dumps(_jsonable({"status": closeout["status"], "decision": decision, "source_manifest_fingerprint": source_manifest["fingerprint"],
        "event_returns_fingerprint": event_doc["fingerprint"], "results_fingerprint": result_doc["fingerprint"], "closeout_fingerprint": closeout["fingerprint"],
        "BTCUSDT": summary["BTCUSDT"], "ETHUSDT": summary["ETHUSDT"],
        "protected_data": {"validation_2025_accessed": False, "mexc_2025_09_through_2025_12_accessed": False, "holdout_2026_accessed": False}}, indent=2, sort_keys=True))
    return closeout


def write_failure_receipt(output_dir: Path, exc: Exception) -> None:
    body = _with_fingerprint({"document_type": "NEWS_SHOCK_LAB_V03A_DISCOVERY_FAILURE_RECEIPT_V0.1", "version": "0.1", "lab_id": LAB_ID,
        "status": "DATA_INADEQUATE_OR_AUTHORITY_FAILURE_STOP_BEFORE_INFERENCE", "error_type": type(exc).__name__, "error": str(exc),
        "pre_discovery_freeze_fingerprint": EXPECTED_PRE_DISCOVERY_FINGERPRINT, "discovery_authorization_fingerprint": EXPECTED_AUTHORIZATION_FINGERPRINT,
        "validation_2025_accessed": False, "mexc_2025_09_through_2025_12_accessed": False, "holdout_2026_accessed": False,
        "live_trading_authorized": False, "exchange_mutation_authorized": False, "inference_authorized_after_failure": False})
    write_json(output_dir / "discovery_failure_receipt.json", body)


def main(argv: Iterable[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: python -m research.news_shock_lab_v03a_discovery_runner_v01 OUTPUT_DIR", file=sys.stderr); return 2
    output_dir = Path(args[0])
    try:
        run_discovery(output_dir)
    except Exception as exc:
        output_dir.mkdir(parents=True, exist_ok=True); write_failure_receipt(output_dir, exc)
        print(f"NEWS V03A DISCOVERY FAIL-CLOSED: {type(exc).__name__}: {exc}", file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
