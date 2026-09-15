import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "PRE_SOURCE_PROTOCOL_V01.json"
OUTDIR = HERE / "source_evidence"
OUT = OUTDIR / "PLS_SOURCE_DATA_GATE_V01.json"

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
DV = "https://data.binance.vision"
FUT_ROOT = "data/futures/um/monthly/klines/"
SPOT_ROOT = "data/spot/monthly/klines/"
BOUNDARY_MONTH = "2022-12"
YEARS = (2023, 2024)
ALLOWED_YEAR_STRINGS = {"2022", "2023", "2024"}
UA = {"User-Agent": "Mozilla/5.0 PLS-BINANCE-USDTM-LAUNCH-001-SOURCE-GATE/1.0"}

GUARDS = {
    "mode": "SOURCE_DATA_GATE_ONLY",
    "market_price_values_parsed": False,
    "ohlc_parsed": False,
    "returns_computed": False,
    "range_computed": False,
    "pnl_computed": False,
    "funding_opened": False,
    "open_interest_opened": False,
    "taker_flow_opened": False,
    "current_exchange_info_opened": False,
    "binance_cms_opened": False,
    "year_2025_archive_requested": False,
    "year_2026_archive_requested": False,
    "year_2025_metadata_serialized": False,
    "year_2026_metadata_serialized": False,
    "live_trading": False,
    "exchange_mutation": False,
    "orders": False,
    "alerts_or_webhooks": False,
}


class SourceAccessBlocked(RuntimeError):
    pass


class DataIntegrityFailure(RuntimeError):
    pass


def localname(tag):
    return tag.rsplit("}", 1)[-1]


def get(url, attempts=4, allow_404=False):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=35) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if allow_404 and e.code == 404:
                return None
            last = e
        except Exception as e:
            last = e
        time.sleep(0.35 * (2 ** i))
    raise last


def parse_s3_xml(raw):
    try:
        return ET.fromstring(raw)
    except Exception as e:
        raise SourceAccessBlocked(f"S3_XML_PARSE:{type(e).__name__}") from e


def s3_root_symbols():
    symbols = []
    marker = None
    page_count = 0
    while True:
        params = {"prefix": FUT_ROOT, "delimiter": "/", "max-keys": "1000"}
        if marker:
            params["marker"] = marker
        raw = get(S3 + "?" + urllib.parse.urlencode(params))
        root = parse_s3_xml(raw)
        page_count += 1
        # At this hierarchy level only symbol CommonPrefixes are authorized.
        # Any object Contents would carry mutable object metadata and fails closed.
        if any(localname(x.tag) == "Contents" for x in root.iter()):
            raise SourceAccessBlocked("ROOT_LISTING_RETURNED_OBJECT_CONTENTS")
        prefixes = []
        for cp in root.iter():
            if localname(cp.tag) != "CommonPrefixes":
                continue
            p = next((c.text for c in cp if localname(c.tag) == "Prefix"), None)
            if p:
                prefixes.append(p)
        for p in prefixes:
            if not p.startswith(FUT_ROOT) or not p.endswith("/"):
                raise SourceAccessBlocked("MALFORMED_ROOT_COMMON_PREFIX")
            sym = p[len(FUT_ROOT):-1]
            if re.fullmatch(r"[A-Z0-9]{2,40}USDT", sym):
                symbols.append(sym)
        truncated = next((x.text for x in root.iter() if localname(x.tag) == "IsTruncated"), "false") == "true"
        if not truncated:
            break
        nm = next((x.text for x in root.iter() if localname(x.tag) == "NextMarker" and x.text), None)
        if not nm:
            if not prefixes:
                raise SourceAccessBlocked("TRUNCATED_WITHOUT_NEXT_MARKER")
            nm = prefixes[-1]
        marker = nm
        if page_count > 20:
            raise SourceAccessBlocked("ROOT_LISTING_EXCESSIVE_PAGINATION")
    return sorted(set(symbols)), page_count


def bounded_keys(prefix):
    # Prefix must itself bind the request to boundary 2022-12 or research years.
    if not (BOUNDARY_MONTH in prefix or "-2023-" in prefix or "-2024-" in prefix):
        raise RuntimeError("UNBOUNDED_S3_PREFIX_ATTEMPT")
    params = {"prefix": prefix, "max-keys": "1000"}
    raw = get(S3 + "?" + urllib.parse.urlencode(params))
    root = parse_s3_xml(raw)
    keys = []
    for c in root.iter():
        if localname(c.tag) != "Contents":
            continue
        k = next((x.text for x in c if localname(x.tag) == "Key"), None)
        if not k:
            continue
        if "-2025-" in k or "-2026-" in k:
            raise SourceAccessBlocked("PROTECTED_PERIOD_KEY_RETURNED_BY_BOUNDED_PREFIX")
        keys.append(k)
    return keys


def futures_months(symbol):
    boundary_prefix = f"{FUT_ROOT}{symbol}/1m/{symbol}-1m-{BOUNDARY_MONTH}"
    boundary = bounded_keys(boundary_prefix)
    if any(k.endswith(".zip") for k in boundary):
        return "BOUNDARY_PRESENT", []
    months = []
    for y in YEARS:
        prefix = f"{FUT_ROOT}{symbol}/1m/{symbol}-1m-{y}-"
        for k in bounded_keys(prefix):
            m = re.fullmatch(re.escape(f"{FUT_ROOT}{symbol}/1m/{symbol}-1m-") + r"(20\d\d-\d\d)\.zip", k)
            if m and m.group(1)[:4] in {"2023", "2024"}:
                months.append(m.group(1))
    return "WINDOW", sorted(set(months))


def parse_checksum(raw, expected_name):
    if raw is None:
        return None
    parts = raw.decode("utf-8", "replace").strip().split()
    if not parts:
        raise DataIntegrityFailure(f"EMPTY_CHECKSUM:{expected_name}")
    dg = parts[0].lower()
    if len(dg) != 64 or any(c not in "0123456789abcdef" for c in dg):
        raise DataIntegrityFailure(f"MALFORMED_CHECKSUM:{expected_name}")
    if len(parts) >= 2 and parts[-1].lstrip("*") != expected_name:
        raise DataIntegrityFailure(f"CHECKSUM_FILENAME_MISMATCH:{expected_name}")
    return dg


def path_for(market, symbol, ym):
    year = ym[:4]
    if year not in ALLOWED_YEAR_STRINGS:
        if year == "2025":
            GUARDS["year_2025_archive_requested"] = True
        if year == "2026":
            GUARDS["year_2026_archive_requested"] = True
        raise RuntimeError("PROTECTED_OR_UNAUTHORIZED_YEAR_PATH_ATTEMPT")
    root = FUT_ROOT if market == "futures_um" else SPOT_ROOT
    return f"{root}{symbol}/1m/{symbol}-1m-{ym}.zip"


def checksum_only(market, symbol, ym):
    path = path_for(market, symbol, ym)
    raw = get(f"{DV}/{path}.CHECKSUM", allow_404=True)
    if raw is None:
        return None
    return parse_checksum(raw, path.rsplit("/", 1)[-1])


def verified_zip(market, symbol, ym):
    path = path_for(market, symbol, ym)
    name = path.rsplit("/", 1)[-1]
    cb = get(f"{DV}/{path}.CHECKSUM", allow_404=True)
    if cb is None:
        return None
    official = parse_checksum(cb, name)
    zb = get(f"{DV}/{path}")
    computed = hashlib.sha256(zb).hexdigest().lower()
    if computed != official:
        raise DataIntegrityFailure(f"SHA256_MISMATCH:{market}:{symbol}:{ym}")
    return {"bytes": zb, "sha256": computed, "path": path}


def ts_from_first_csv_field(zip_bytes):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        bad = z.testzip()
        if bad is not None:
            raise DataIntegrityFailure(f"ZIP_CRC_FAILURE:{bad}")
        names = [n for n in z.namelist() if not n.endswith("/")]
        if len(names) != 1:
            raise DataIntegrityFailure("ZIP_MEMBER_COUNT_NOT_ONE")
        with z.open(names[0]) as f:
            wrapper = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace", newline="")
            for row in csv.reader(wrapper):
                if not row:
                    continue
                first = str(row[0]).strip()
                if first.lower() in {"open_time", "opentime"}:
                    continue
                if not re.fullmatch(r"\d{10,18}", first):
                    raise DataIntegrityFailure("FIRST_CSV_FIELD_NOT_TIMESTAMP")
                x = int(first)
                if x > 10**14:
                    sec = x / 1_000_000.0
                elif x > 10**11:
                    sec = x / 1_000.0
                else:
                    sec = float(x)
                return datetime.fromtimestamp(sec, tz=timezone.utc)
    raise DataIntegrityFailure("NO_DATA_ROW_IN_ARCHIVE")


def previous_month(ym):
    y, m = map(int, ym.split("-"))
    if m == 1:
        return f"{y-1:04d}-12"
    return f"{y:04d}-{m-1:02d}"


def classify_symbol(symbol):
    try:
        state, months = futures_months(symbol)
        if state == "BOUNDARY_PRESENT":
            return {"kind": "boundary_old"}
        if not months:
            return {"kind": "no_window"}
        first_month = months[0]
        fut = verified_zip("futures_um", symbol, first_month)
        if fut is None:
            return {"kind": "technical", "symbol": symbol, "reason": "LISTED_FUTURES_ZIP_CHECKSUM_MISSING"}
        fut_ts = ts_from_first_csv_field(fut["bytes"])
        if fut_ts.year not in YEARS:
            return {"kind": "technical", "symbol": symbol, "reason": "FIRST_FUTURES_TIMESTAMP_OUTSIDE_WINDOW"}

        prev = previous_month(first_month)
        spot_prev_sha = checksum_only("spot", symbol, prev)
        spot_proof = None
        if spot_prev_sha:
            spot_proof = {
                "mode": "PREVIOUS_MONTH_CHECKSUM",
                "month": prev,
                "official_sha256": spot_prev_sha,
                "strictly_before_futures_event": True,
            }
        else:
            spot = verified_zip("spot", symbol, first_month)
            if spot is None:
                return {
                    "kind": "in_window_reject",
                    "symbol": symbol,
                    "futures_first_month": first_month,
                    "futures_first_open_time_utc": fut_ts.isoformat().replace("+00:00", "Z"),
                    "reason": "NO_EXACT_SAME_SYMBOL_SPOT_ROUTE_AT_LAUNCH_MONTH",
                }
            spot_ts = ts_from_first_csv_field(spot["bytes"])
            if not spot_ts < fut_ts:
                return {
                    "kind": "in_window_reject",
                    "symbol": symbol,
                    "futures_first_month": first_month,
                    "futures_first_open_time_utc": fut_ts.isoformat().replace("+00:00", "Z"),
                    "spot_first_open_time_utc": spot_ts.isoformat().replace("+00:00", "Z"),
                    "reason": "SPOT_NOT_STRICTLY_PREEXISTING_FUTURES_EVENT",
                }
            spot_proof = {
                "mode": "SAME_MONTH_FIRST_OPEN_TIME",
                "month": first_month,
                "spot_first_open_time_utc": spot_ts.isoformat().replace("+00:00", "Z"),
                "spot_zip_sha256": spot["sha256"],
                "strictly_before_futures_event": True,
            }

        return {
            "kind": "qualified",
            "symbol": symbol,
            "event_timestamp_utc": fut_ts.isoformat().replace("+00:00", "Z"),
            "futures_first_month": first_month,
            "futures_zip_path": fut["path"],
            "futures_zip_sha256": fut["sha256"],
            "spot_preexistence_proof": spot_proof,
        }
    except SourceAccessBlocked as e:
        return {"kind": "source_blocked", "reason": str(e)}
    except DataIntegrityFailure as e:
        return {"kind": "technical", "symbol": symbol, "reason": str(e)}
    except Exception as e:
        return {"kind": "technical", "symbol": symbol, "reason": f"{type(e).__name__}:{e}"}


def write_receipt(doc):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(doc["receipt"], indent=2, sort_keys=True))


def main():
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if protocol["status"] != "FROZEN_PRE_SOURCE_OUTCOME_BLIND":
        raise RuntimeError("PRE_SOURCE_PROTOCOL_NOT_FROZEN")
    mins = protocol["source_minimums"]

    try:
        symbols, root_pages = s3_root_symbols()
    except Exception as e:
        classification = "SOURCE_ACCESS_BLOCKED"
        doc = {
            "lab_id": protocol["lab_id"],
            "mve_id": protocol["mve_id"],
            "receipt": {
                "classification": classification,
                "reason": f"{type(e).__name__}:{e}",
                "source_minimums": mins,
                "guards": GUARDS,
                "next_action": "Close exact source route unless a purely technical transport defect is proven; do not weaken minimums or open outcomes.",
            },
            "qualified_events": [],
            "in_window_rejections": [],
        }
        write_receipt(doc)
        return

    counters = {
        "root_symbol_prefixes_exact_usdt": len(symbols),
        "boundary_old_count": 0,
        "no_window_archive_count": 0,
        "in_window_candidate_count": 0,
    }
    qualified = []
    rejected = []
    technical = []
    source_blocks = []

    with ThreadPoolExecutor(max_workers=24) as ex:
        futs = {ex.submit(classify_symbol, s): s for s in symbols}
        for f in as_completed(futs):
            r = f.result()
            k = r.get("kind")
            if k == "boundary_old":
                counters["boundary_old_count"] += 1
            elif k == "no_window":
                counters["no_window_archive_count"] += 1
            elif k == "qualified":
                counters["in_window_candidate_count"] += 1
                qualified.append(r)
            elif k == "in_window_reject":
                counters["in_window_candidate_count"] += 1
                rejected.append(r)
            elif k == "technical":
                technical.append(r)
            elif k == "source_blocked":
                source_blocks.append(r)
            else:
                technical.append({"kind": "technical", "reason": "UNKNOWN_WORKER_CLASSIFICATION"})

    qualified.sort(key=lambda x: (x["event_timestamp_utc"], x["symbol"]))
    rejected.sort(key=lambda x: (x.get("futures_first_open_time_utc", ""), x.get("symbol", "")))
    year_counts = {"2023": 0, "2024": 0}
    for e in qualified:
        y = e["event_timestamp_utc"][:4]
        if y in year_counts:
            year_counts[y] += 1
    distinct = len({e["symbol"] for e in qualified})

    if source_blocks:
        classification = "SOURCE_ACCESS_BLOCKED"
    elif technical:
        classification = "TECHNICAL_OR_DATA_FAILURE"
    else:
        pass_all = (
            len(qualified) >= int(mins["qualified_launch_events"])
            and distinct >= int(mins["distinct_exact_symbols"])
            and year_counts["2023"] >= int(mins["qualified_events_2023"])
            and year_counts["2024"] >= int(mins["qualified_events_2024"])
            and not GUARDS["year_2025_archive_requested"]
            and not GUARDS["year_2026_archive_requested"]
        )
        classification = "SOURCE_DATA_PASS" if pass_all else "INSUFFICIENT_SOURCE_SAMPLE"

    receipt = {
        "classification": classification,
        "root_listing_pages": root_pages,
        "source_minimums": mins,
        "population_counts": counters,
        "qualified_launch_events": len(qualified),
        "qualified_distinct_exact_symbols": distinct,
        "qualified_year_counts": year_counts,
        "in_window_rejected_count": len(rejected),
        "technical_failure_count": len(technical),
        "source_block_count": len(source_blocks),
        "guards": GUARDS,
        "next_action": (
            "STOP before outcomes. Freeze FINAL_PRE_DISCOVERY_PROTOCOL prospectively before opening any price outcome."
            if classification == "SOURCE_DATA_PASS"
            else "Preserve exact blocked/insufficient classification. Do not lower minimums, alias symbols, or open outcomes."
        ),
    }
    doc = {
        "lab_id": protocol["lab_id"],
        "mve_id": protocol["mve_id"],
        "mode": "SOURCE_DATA_GATE_ONLY",
        "receipt": receipt,
        "qualified_events": qualified,
        "in_window_rejections": rejected,
        "technical_failures": technical[:100],
        "source_blocks": source_blocks[:100],
    }
    write_receipt(doc)


if __name__ == "__main__":
    main()
