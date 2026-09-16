import calendar
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
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTO = HERE / "FROZEN_PROTOCOL_V01.json"
OUTDIR = HERE / "source_evidence"
OUT = OUTDIR / "QBC_SOURCE_GATE_V01.json"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
DV = "https://data.binance.vision"
FUT_ROOT = "data/futures/um/monthly/klines/"
SPOT_ROOT = "data/spot/monthly/klines/"
UA = {"User-Agent": "Mozilla/5.0 QBC-BINANCE-USDM-7D-001-SOURCE-GATE/1.0"}
ALLOWED_YEARS = {2021, 2022, 2023, 2024}

GUARDS = {
    "mode": "SOURCE_DATA_GATE_ONLY",
    "market_price_values_parsed": False,
    "ohlcv_parsed": False,
    "basis_computed": False,
    "returns_computed": False,
    "pnl_computed": False,
    "year_2025_market_data_requested": False,
    "year_2026_market_data_requested": False,
    "live_trading": False,
    "exchange_mutation": False,
    "orders": False,
}

class SourceBlocked(RuntimeError):
    pass

class DataFailure(RuntimeError):
    pass


def get(url, attempts=5, allow_404=False):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if allow_404 and e.code == 404:
                return None
            last = e
            if e.code not in (429, 500, 502, 503, 504):
                break
        except Exception as e:
            last = e
        time.sleep(min(8.0, 0.5 * (2 ** i)))
    raise SourceBlocked(f"GET_FAILED:{url}:{type(last).__name__}:{last}")


def lname(tag):
    return tag.rsplit("}", 1)[-1]


def parse_xml(raw):
    try:
        return ET.fromstring(raw)
    except Exception as e:
        raise DataFailure(f"S3_XML_PARSE:{type(e).__name__}:{e}") from e


def enumerate_symbol_prefixes():
    out = []
    marker = None
    pages = 0
    while True:
        params = {"prefix": FUT_ROOT, "delimiter": "/", "max-keys": "1000"}
        if marker:
            params["marker"] = marker
        raw = get(S3 + "?" + urllib.parse.urlencode(params))
        root = parse_xml(raw)
        pages += 1
        prefixes = []
        for cp in root.iter():
            if lname(cp.tag) != "CommonPrefixes":
                continue
            p = next((c.text for c in cp if lname(c.tag) == "Prefix"), None)
            if p:
                prefixes.append(p)
        for p in prefixes:
            if p.startswith(FUT_ROOT) and p.endswith("/"):
                out.append(p[len(FUT_ROOT):-1])
        trunc = next((x.text for x in root.iter() if lname(x.tag) == "IsTruncated"), "false") == "true"
        if not trunc:
            break
        nxt = next((x.text for x in root.iter() if lname(x.tag) == "NextMarker" and x.text), None)
        if not nxt:
            if not prefixes:
                raise DataFailure("S3_TRUNCATED_WITHOUT_MARKER")
            nxt = prefixes[-1]
        marker = nxt
        if pages > 20:
            raise DataFailure("S3_EXCESSIVE_PAGINATION")
    return sorted(set(out)), pages


def last_friday(year, month):
    last_day = calendar.monthrange(year, month)[1]
    d = datetime(year, month, last_day, tzinfo=timezone.utc)
    while d.weekday() != calendar.FRIDAY:
        d -= timedelta(days=1)
    return d.date()


def parse_contract(symbol):
    m = re.fullmatch(r"(BTC|ETH)USDT_((?:21|22|23|24)\d{4})", symbol)
    if not m:
        return None
    asset, suffix = m.groups()
    yy = int(suffix[0:2])
    mm = int(suffix[2:4])
    dd = int(suffix[4:6])
    year = 2000 + yy
    if year not in ALLOWED_YEARS or mm not in (3, 6, 9, 12):
        return None
    try:
        dt = datetime(year, mm, dd, 8, 0, tzinfo=timezone.utc)
    except ValueError:
        return None
    if dt.weekday() != calendar.FRIDAY:
        return None
    if dt.date() != last_friday(year, mm):
        return None
    return asset, dt


def parse_checksum(raw, expected_name):
    parts = raw.decode("utf-8", "replace").strip().split()
    if not parts:
        raise DataFailure(f"EMPTY_CHECKSUM:{expected_name}")
    dg = parts[0].lower()
    if len(dg) != 64 or any(c not in "0123456789abcdef" for c in dg):
        raise DataFailure(f"BAD_CHECKSUM:{expected_name}")
    if len(parts) >= 2 and parts[-1].lstrip("*") != expected_name:
        raise DataFailure(f"CHECKSUM_FILENAME_MISMATCH:{expected_name}")
    return dg


def verified_archive_timestamp_bounds(path):
    name = path.rsplit("/", 1)[-1]
    raw_checksum = get(f"{DV}/{path}.CHECKSUM", allow_404=True)
    if raw_checksum is None:
        return None
    official = parse_checksum(raw_checksum, name)
    zb = get(f"{DV}/{path}")
    actual = hashlib.sha256(zb).hexdigest().lower()
    if actual != official:
        raise DataFailure(f"SHA256_MISMATCH:{path}")
    first = None
    last = None
    rows = 0
    with zipfile.ZipFile(io.BytesIO(zb)) as zz:
        bad = zz.testzip()
        if bad is not None:
            raise DataFailure(f"ZIP_CRC_FAILURE:{path}:{bad}")
        names = [n for n in zz.namelist() if not n.endswith("/")]
        if len(names) != 1:
            raise DataFailure(f"ZIP_MEMBER_COUNT:{path}:{len(names)}")
        with zz.open(names[0]) as f:
            wrapper = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace", newline="")
            for row in csv.reader(wrapper):
                if not row:
                    continue
                v = str(row[0]).strip()
                if v.lower() in {"open_time", "opentime"}:
                    continue
                if not re.fullmatch(r"\d{10,18}", v):
                    raise DataFailure(f"FIRST_FIELD_NOT_TIMESTAMP:{path}")
                n = int(v)
                sec = n / 1_000_000 if n > 10**14 else n / 1000 if n > 10**11 else n
                dt = datetime.fromtimestamp(sec, tz=timezone.utc)
                if first is None:
                    first = dt
                last = dt
                rows += 1
    if first is None or last is None:
        raise DataFailure(f"NO_TIMESTAMP_ROWS:{path}")
    return {
        "path": path,
        "sha256": actual,
        "rows": rows,
        "first_open_time_utc": first.isoformat().replace("+00:00", "Z"),
        "last_open_time_utc": last.isoformat().replace("+00:00", "Z"),
    }


def route_paths(asset, contract, expiry):
    year = expiry.year
    if year == 2025:
        GUARDS["year_2025_market_data_requested"] = True
        raise RuntimeError("PROTECTED_2025_PATH_ATTEMPT")
    if year == 2026:
        GUARDS["year_2026_market_data_requested"] = True
        raise RuntimeError("PROTECTED_2026_PATH_ATTEMPT")
    if year not in ALLOWED_YEARS:
        raise RuntimeError("UNAUTHORIZED_YEAR_PATH_ATTEMPT")
    ym = expiry.strftime("%Y-%m")
    fut = f"{FUT_ROOT}{contract}/1m/{contract}-1m-{ym}.zip"
    pair = asset + "USDT"
    spot = f"{SPOT_ROOT}{pair}/1m/{pair}-1m-{ym}.zip"
    return fut, spot


def dt_parse(x):
    return datetime.fromisoformat(x.replace("Z", "+00:00"))


def main():
    p = json.loads(PROTO.read_text(encoding="utf-8"))
    assert p["status"] == "FROZEN_PRE_SOURCE_OUTCOME_BLIND"
    mins = p["source_gate"]
    try:
        symbols, pages = enumerate_symbol_prefixes()
    except SourceBlocked as e:
        receipt = {"classification": "SOURCE_ACCESS_BLOCKED", "reason": str(e), "guards": GUARDS}
        write({"lab_id": p["lab_id"], "mve_id": p["mve_id"], "receipt": receipt, "qualified_routes": []})
        return
    except Exception as e:
        receipt = {"classification": "DATA_FAILURE", "reason": f"{type(e).__name__}:{e}", "guards": GUARDS}
        write({"lab_id": p["lab_id"], "mve_id": p["mve_id"], "receipt": receipt, "qualified_routes": []})
        return

    candidates = []
    for s in symbols:
        parsed = parse_contract(s)
        if parsed:
            asset, expiry = parsed
            candidates.append((s, asset, expiry))
    candidates.sort(key=lambda x: (x[2], x[1]))

    qualified = []
    rejected = []
    technical = []
    spot_cache = {}
    for contract, asset, expiry in candidates:
        snapshot = expiry - timedelta(days=7, minutes=1)
        entry = expiry - timedelta(days=7)
        forced_exit = expiry - timedelta(minutes=15)
        try:
            fut_path, spot_path = route_paths(asset, contract, expiry)
            fut = verified_archive_timestamp_bounds(fut_path)
            if fut is None:
                rejected.append({"contract": contract, "reason": "FUTURES_ARCHIVE_MISSING"})
                continue
            if spot_path not in spot_cache:
                spot_cache[spot_path] = verified_archive_timestamp_bounds(spot_path)
            spot = spot_cache[spot_path]
            if spot is None:
                rejected.append({"contract": contract, "reason": "SPOT_ARCHIVE_MISSING"})
                continue
            f0, f1 = dt_parse(fut["first_open_time_utc"]), dt_parse(fut["last_open_time_utc"])
            s0, s1 = dt_parse(spot["first_open_time_utc"]), dt_parse(spot["last_open_time_utc"])
            if not (f0 <= snapshot and f1 >= forced_exit):
                rejected.append({"contract": contract, "reason": "FUTURES_ARCHIVE_DOES_NOT_COVER_FROZEN_TIMES"})
                continue
            if not (s0 <= snapshot and s1 >= forced_exit):
                rejected.append({"contract": contract, "reason": "SPOT_ARCHIVE_DOES_NOT_COVER_FROZEN_TIMES"})
                continue
            qualified.append({
                "contract": contract,
                "asset": asset,
                "expiry_utc": expiry.isoformat().replace("+00:00", "Z"),
                "snapshot_utc": snapshot.isoformat().replace("+00:00", "Z"),
                "entry_utc": entry.isoformat().replace("+00:00", "Z"),
                "forced_exit_utc": forced_exit.isoformat().replace("+00:00", "Z"),
                "futures_archive": fut,
                "spot_archive": spot,
            })
        except SourceBlocked as e:
            technical.append({"contract": contract, "reason": f"SOURCE_BLOCKED:{e}"})
        except Exception as e:
            technical.append({"contract": contract, "reason": f"{type(e).__name__}:{e}"})

    yc = Counter(x["expiry_utc"][:4] for x in qualified)
    ac = Counter(x["asset"] for x in qualified)
    if technical:
        classification = "TECHNICAL_FAILURE"
        reason = f"{len(technical)} contract routes technically unresolved"
    elif (
        len(qualified) >= int(mins["qualified_contract_routes_min"]) and
        ac.get("BTC", 0) >= int(mins["qualified_btc_routes_min"]) and
        ac.get("ETH", 0) >= int(mins["qualified_eth_routes_min"]) and
        yc.get("2021", 0) >= int(mins["qualified_routes_2021_min"]) and
        yc.get("2022", 0) >= int(mins["qualified_routes_2022_min"]) and
        yc.get("2023", 0) >= int(mins["qualified_routes_2023_min"]) and
        yc.get("2024", 0) >= int(mins["qualified_routes_2024_min"])
    ):
        classification = "SOURCE_DATA_PASS"
        reason = "all frozen source minimums passed"
    else:
        classification = "INSUFFICIENT_SOURCE_SAMPLE"
        reason = "one or more frozen source minimums failed"

    receipt = {
        "classification": classification,
        "reason": reason,
        "root_symbol_prefixes_seen": len(symbols),
        "root_pages": pages,
        "candidate_quarterly_contracts_2021_2024": len(candidates),
        "qualified_contract_routes": len(qualified),
        "qualified_asset_counts": dict(sorted(ac.items())),
        "qualified_year_counts": dict(sorted(yc.items())),
        "rejected_count": len(rejected),
        "technical_count": len(technical),
        "source_minimums": {
            "qualified_contract_routes_min": mins["qualified_contract_routes_min"],
            "qualified_btc_routes_min": mins["qualified_btc_routes_min"],
            "qualified_eth_routes_min": mins["qualified_eth_routes_min"],
            "qualified_routes_2021_min": mins["qualified_routes_2021_min"],
            "qualified_routes_2022_min": mins["qualified_routes_2022_min"],
            "qualified_routes_2023_min": mins["qualified_routes_2023_min"],
            "qualified_routes_2024_min": mins["qualified_routes_2024_min"],
        },
        "guards": GUARDS,
        "next_action": "Open 2021-2023 Discovery price fields only if SOURCE_DATA_PASS. Keep 2024 prices locked until Discovery survives; keep 2025/2026 locked."
    }
    write({
        "lab_id": p["lab_id"],
        "mve_id": p["mve_id"],
        "receipt": receipt,
        "qualified_routes": qualified,
        "rejected": rejected,
        "technical": technical,
    })


def write(doc):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(doc["receipt"], indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
