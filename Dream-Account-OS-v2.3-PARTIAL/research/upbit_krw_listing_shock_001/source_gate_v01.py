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
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTO = HERE / "FROZEN_PROTOCOL_V01.json"
OUTDIR = HERE / "source_evidence"
OUT = OUTDIR / "UKLS_SOURCE_GATE_V01.json"
UPBIT_LIST = "https://api-manager.upbit.com/api/v1/announcements"
DV = "https://data.binance.vision"
START = datetime(2023, 1, 1, tzinfo=timezone.utc)
END = datetime(2025, 1, 1, tzinfo=timezone.utc)
UA = {
    "User-Agent": "Mozilla/5.0 UKLS-UPBIT-KRW-BINANCE-SPOT-001/1.0",
    "Accept": "application/json",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.5",
    "Origin": "https://upbit.com",
    "Referer": "https://upbit.com/",
}

GUARDS = {
    "mode": "SOURCE_DATA_GATE_ONLY",
    "upbit_2025_2026_titles_serialized": False,
    "binance_2025_market_data_requested": False,
    "binance_2026_market_data_requested": False,
    "market_price_values_parsed": False,
    "ohlcv_parsed": False,
    "returns_computed": False,
    "pnl_computed": False,
    "live_trading": False,
    "exchange_mutation": False,
    "orders": False,
}

class SourceBlocked(RuntimeError):
    pass

class DataFailure(RuntimeError):
    pass


def get(url, attempts=6, allow_404=False):
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


def parse_iso(x):
    if not isinstance(x, str) or not x.strip():
        raise DataFailure("MISSING_LISTED_AT")
    s = x.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except Exception as e:
        raise DataFailure(f"BAD_LISTED_AT:{x}") from e
    if dt.tzinfo is None:
        raise DataFailure(f"NAIVE_LISTED_AT:{x}")
    return dt.astimezone(timezone.utc)


def title_is_listing(title):
    return isinstance(title, str) and ("신규 거래지원 안내" in title or "신규 거래 지원 안내" in title)


def clean_market_tokens(group):
    x = group.replace("마켓", " ")
    return {p.strip().upper() for p in re.split(r"[,/\s]+", x) if p.strip()}


def parse_title(title):
    """Frozen deterministic title parser. Returns per-token market associations or [] on ambiguity."""
    if not title_is_listing(title):
        return []

    out = []
    # Pattern A: NAME(SYMBOL)(KRW, BTC, USDT 마켓), potentially repeated in one title.
    paired = list(re.finditer(r"([^,()]{1,100}?)\(([A-Z0-9]{2,20})\)\(([^)]*마켓[^)]*)\)", title))
    if paired:
        for m in paired:
            sym = m.group(2).strip().upper()
            markets = clean_market_tokens(m.group(3))
            out.append({"symbol": sym, "markets": sorted(markets), "parse_mode": "PAIRED_SEGMENT"})
        return out

    # Pattern B: exactly one NAME(SYMBOL) and one separate market-list parenthesis.
    syms = list(re.finditer(r"([^,()]{1,100}?)\(([A-Z0-9]{2,20})\)", title))
    market_groups = [g for g in re.findall(r"\(([^)]*마켓[^)]*)\)", title)]
    if len(syms) == 1 and len(market_groups) == 1:
        sym = syms[0].group(2).strip().upper()
        markets = clean_market_tokens(market_groups[0])
        return [{"symbol": sym, "markets": sorted(markets), "parse_mode": "SINGLE_SYMBOL_TRAILING_MARKETS"}]
    return []


def month_floor(dt):
    return f"{dt.year:04d}-{dt.month:02d}"


def previous_month(ym):
    y, m = map(int, ym.split("-"))
    if m == 1:
        return f"{y-1:04d}-12"
    return f"{y:04d}-{m-1:02d}"


def archive_path(symbol, ym):
    year = int(ym[:4])
    if year == 2025:
        GUARDS["binance_2025_market_data_requested"] = True
        raise RuntimeError("PROTECTED_2025_BINANCE_PATH_ATTEMPT")
    if year == 2026:
        GUARDS["binance_2026_market_data_requested"] = True
        raise RuntimeError("PROTECTED_2026_BINANCE_PATH_ATTEMPT")
    pair = symbol + "USDT"
    return f"data/spot/monthly/klines/{pair}/1m/{pair}-1m-{ym}.zip"


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


def verified_archive_first_ts(symbol, ym, allow_missing=False):
    path = archive_path(symbol, ym)
    name = path.rsplit("/", 1)[-1]
    raw_checksum = get(f"{DV}/{path}.CHECKSUM", allow_404=allow_missing)
    if raw_checksum is None:
        return None
    official = parse_checksum(raw_checksum, name)
    zb = get(f"{DV}/{path}")
    actual = hashlib.sha256(zb).hexdigest().lower()
    if actual != official:
        raise DataFailure(f"SHA256_MISMATCH:{symbol}:{ym}")
    first_ts = None
    with zipfile.ZipFile(io.BytesIO(zb)) as zz:
        names = [n for n in zz.namelist() if not n.endswith("/")]
        if len(names) != 1:
            raise DataFailure(f"ZIP_MEMBER_COUNT:{symbol}:{ym}:{len(names)}")
        with zz.open(names[0]) as f:
            wrapper = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace", newline="")
            for row in csv.reader(wrapper):
                if not row:
                    continue
                first = str(row[0]).strip()
                if first.lower() in {"open_time", "opentime"}:
                    continue
                if not re.fullmatch(r"\d{10,18}", first):
                    raise DataFailure(f"FIRST_FIELD_NOT_TIMESTAMP:{symbol}:{ym}")
                n = int(first)
                sec = n / 1_000_000 if n > 10**14 else n / 1000 if n > 10**11 else n
                first_ts = datetime.fromtimestamp(sec, tz=timezone.utc)
                break
    if first_ts is None:
        raise DataFailure(f"NO_DATA_ROW:{symbol}:{ym}")
    return {"path": path, "sha256": actual, "first_open_time_utc": first_ts.isoformat().replace("+00:00", "Z")}


def prove_binance_preexistence(event):
    sym = event["symbol"]
    if any(sym.startswith(x) for x in ("1000", "10000", "1000000")):
        return {"qualified": False, "reason": "EXCLUDED_MULTIPLIER_PREFIX"}
    event_dt = datetime.fromisoformat(event["announcement_utc"].replace("Z", "+00:00"))
    ym = month_floor(event_dt)
    event_arc = verified_archive_first_ts(sym, ym, allow_missing=True)
    if event_arc is None:
        return {"qualified": False, "reason": "NO_BINANCE_EXACT_SPOT_EVENT_MONTH_ARCHIVE"}
    threshold = event_dt - timedelta(hours=24)
    event_first = datetime.fromisoformat(event_arc["first_open_time_utc"].replace("Z", "+00:00"))
    proof = {"event_month": event_arc, "minimum_preexistence_hours": 24}
    if event_first <= threshold:
        proof["proof_mode"] = "EVENT_MONTH_FIRST_OPEN"
        proof["qualified"] = True
        return proof
    prev = previous_month(ym)
    prev_arc = verified_archive_first_ts(sym, prev, allow_missing=True)
    if prev_arc is None:
        proof["qualified"] = False
        proof["reason"] = "BINANCE_SPOT_NOT_PROVEN_24H_PREEXISTING"
        return proof
    prev_first = datetime.fromisoformat(prev_arc["first_open_time_utc"].replace("Z", "+00:00"))
    proof["previous_month"] = prev_arc
    if prev_first <= threshold:
        proof["proof_mode"] = "PREVIOUS_MONTH_FIRST_OPEN"
        proof["qualified"] = True
    else:
        proof["qualified"] = False
        proof["reason"] = "BINANCE_SPOT_NOT_PROVEN_24H_PREEXISTING"
    return proof


def enumerate_upbit():
    candidates = []
    parser_rejects = []
    page_receipts = []
    page = 1
    total_pages = None
    reached_window = False
    in_window_notice_count = 0
    listing_title_count = 0
    while page <= 400:
        q = urllib.parse.urlencode({"os": "web", "page": page, "per_page": 30, "category": "trade"})
        url = UPBIT_LIST + "?" + q
        raw = get(url)
        page_receipts.append({"page": page, "sha256": hashlib.sha256(raw).hexdigest()})
        try:
            doc = json.loads(raw)
        except Exception as e:
            raise DataFailure(f"UPBIT_JSON_PAGE_{page}:{e}")
        data = doc.get("data") if isinstance(doc, dict) else None
        if not isinstance(data, dict) or not isinstance(data.get("notices"), list):
            raise DataFailure(f"UPBIT_SCHEMA_PAGE_{page}")
        if total_pages is None:
            try:
                total_pages = int(data.get("total_pages"))
            except Exception:
                total_pages = None
        notices = data["notices"]
        if not notices:
            break
        page_dates = []
        for n in notices:
            if not isinstance(n, dict):
                continue
            try:
                dt = parse_iso(n.get("listed_at"))
            except DataFailure:
                continue
            page_dates.append(dt)
            if dt >= END:
                # Required pagination metadata is traversed but recent titles are not serialized.
                continue
            if dt < START:
                continue
            reached_window = True
            in_window_notice_count += 1
            title = n.get("title")
            if not title_is_listing(title):
                continue
            listing_title_count += 1
            parsed = parse_title(title)
            if not parsed:
                parser_rejects.append({
                    "notice_id": n.get("id"),
                    "announcement_utc": dt.isoformat().replace("+00:00", "Z"),
                    "title": title,
                    "reason": "FROZEN_TITLE_PARSER_AMBIGUOUS_OR_UNPARSED",
                })
                continue
            for item in parsed:
                sym = item["symbol"]
                if not re.fullmatch(r"[A-Z0-9]{2,20}", sym):
                    continue
                if "KRW" not in set(item["markets"]):
                    continue
                candidates.append({
                    "notice_id": n.get("id"),
                    "official_url": f"https://upbit.com/service_center/notice?id={n.get('id')}",
                    "title": title,
                    "announcement_utc": dt.isoformat().replace("+00:00", "Z"),
                    "symbol": sym,
                    "markets": item["markets"],
                    "parse_mode": item["parse_mode"],
                })
        if page_dates and min(page_dates) < START and reached_window:
            break
        if total_pages is not None and page >= total_pages:
            break
        page += 1
    # Chronologically first qualifying KRW-support notice per exact symbol.
    candidates.sort(key=lambda x: (x["announcement_utc"], str(x["notice_id"])))
    first = {}
    duplicate_count = 0
    for e in candidates:
        if e["symbol"] in first:
            duplicate_count += 1
            continue
        first[e["symbol"]] = e
    return list(first.values()), parser_rejects, {
        "pages_traversed": len(page_receipts),
        "page_receipts": page_receipts,
        "total_pages_reported": total_pages,
        "in_window_trade_notices": in_window_notice_count,
        "listing_titles_in_window": listing_title_count,
        "raw_krw_token_events_before_symbol_dedupe": len(candidates),
        "duplicate_symbol_events_removed": duplicate_count,
    }


def write(doc):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(doc["receipt"], indent=2, sort_keys=True, ensure_ascii=False))


def main():
    p = json.loads(PROTO.read_text(encoding="utf-8"))
    assert p["status"] == "FROZEN_PRE_SOURCE_OUTCOME_BLIND"
    mins = p["source_gate"]
    try:
        events, parser_rejects, enumeration = enumerate_upbit()
    except SourceBlocked as e:
        write({"lab_id": p["lab_id"], "mve_id": p["mve_id"], "receipt": {
            "classification": "SOURCE_ACCESS_BLOCKED", "reason": str(e), "guards": GUARDS,
            "next_action": "Close source route unless a transport-only defect is proven; do not open outcomes."},
            "qualified_events": [], "parser_rejects": []})
        return
    except Exception as e:
        write({"lab_id": p["lab_id"], "mve_id": p["mve_id"], "receipt": {
            "classification": "DATA_FAILURE", "reason": f"{type(e).__name__}:{e}", "guards": GUARDS,
            "next_action": "Fail closed; no market outcomes."},
            "qualified_events": [], "parser_rejects": []})
        return

    qualified = []
    route_rejects = []
    technical = []
    for e in events:
        try:
            proof = prove_binance_preexistence(e)
            if proof.get("qualified"):
                x = dict(e)
                x["binance_preexistence"] = proof
                qualified.append(x)
            else:
                route_rejects.append({"notice_id": e["notice_id"], "symbol": e["symbol"], "announcement_utc": e["announcement_utc"], "reason": proof.get("reason")})
        except SourceBlocked as ex:
            technical.append({"notice_id": e["notice_id"], "symbol": e["symbol"], "reason": f"SOURCE_BLOCKED:{ex}"})
        except Exception as ex:
            technical.append({"notice_id": e["notice_id"], "symbol": e["symbol"], "reason": f"{type(ex).__name__}:{ex}"})

    yc = Counter(x["announcement_utc"][:4] for x in qualified)
    if technical:
        classification = "TECHNICAL_FAILURE"
        reason = f"{len(technical)} route checks ended technically unresolved"
    elif (len(qualified) >= int(mins["qualified_events_min"]) and
          len({x["symbol"] for x in qualified}) >= int(mins["distinct_symbols_min"]) and
          yc.get("2023", 0) >= int(mins["events_2023_min"]) and
          yc.get("2024", 0) >= int(mins["events_2024_min"])):
        classification = "SOURCE_DATA_PASS"
        reason = "all frozen source minimums passed"
    else:
        classification = "INSUFFICIENT_SOURCE_SAMPLE"
        reason = "one or more frozen source minimums failed"

    receipt = {
        "classification": classification,
        "reason": reason,
        "qualified_events": len(qualified),
        "qualified_distinct_symbols": len({x["symbol"] for x in qualified}),
        "qualified_year_counts": dict(sorted(yc.items())),
        "upbit_first_krw_events_before_binance_route": len(events),
        "parser_reject_count": len(parser_rejects),
        "route_reject_count": len(route_rejects),
        "technical_count": len(technical),
        "source_minimums": {
            "qualified_events_min": mins["qualified_events_min"],
            "distinct_symbols_min": mins["distinct_symbols_min"],
            "events_2023_min": mins["events_2023_min"],
            "events_2024_min": mins["events_2024_min"],
        },
        "enumeration": enumeration,
        "guards": GUARDS,
        "next_action": "Open frozen Discovery prices only if SOURCE_DATA_PASS; otherwise close/fail-closed without threshold or parser rescue.",
    }
    write({
        "lab_id": p["lab_id"],
        "mve_id": p["mve_id"],
        "receipt": receipt,
        "qualified_events": qualified,
        "parser_rejects": parser_rejects,
        "route_rejects": route_rejects,
        "technical": technical,
    })

if __name__ == "__main__":
    main()
