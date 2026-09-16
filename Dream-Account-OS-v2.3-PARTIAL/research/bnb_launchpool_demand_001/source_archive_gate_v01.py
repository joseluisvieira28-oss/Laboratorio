import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECON = HERE / "BNB_LAUNCHPOOL_DEMAND_001_SOURCE_RECON_V0.1.json"
AMENDMENT = HERE / "BNB_LAUNCHPOOL_DEMAND_001_SOURCE_TRANSPORT_AMENDMENT_V0.1.json"
OUTDIR = HERE / "source_archive_v01"
RAW = OUTDIR / "raw"
RECEIPT = OUTDIR / "BNB_LAUNCHPOOL_DEMAND_001_SOURCE_ARCHIVE_RECEIPT_V0.1.json"

ROUTE = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode={}"
UA = {
    "User-Agent": "Mozilla/5.0 BNB-LAUNCHPOOL-DEMAND-001-SOURCE-GATE/1.0",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

GUARDS = {
    "market_price_fields_opened": False,
    "bnb_price_opened": False,
    "btc_price_opened": False,
    "returns_computed": False,
    "pnl_computed": False,
    "catalog_or_list_endpoint_opened": False,
    "search_endpoint_opened": False,
    "current_launchpool_page_opened": False,
    "current_exchange_info_opened": False,
    "year_2025_source_page_requested": False,
    "year_2026_source_page_requested": False,
    "live_trading": False,
    "exchange_mutation": False,
    "orders": False,
    "alerts_or_webhooks": False,
    "merge_to_main": False,
}


def utc_iso(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_ts(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        x = float(v)
        if x > 1e14:
            x /= 1_000_000.0
        elif x > 1e11:
            x /= 1_000.0
        try:
            return utc_iso(datetime.fromtimestamp(x, tz=timezone.utc))
        except Exception:
            return None
    s = str(v).strip()
    if not s:
        return None
    if re.fullmatch(r"\d{10,18}", s):
        return parse_ts(int(s))
    z = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(z)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return utc_iso(dt)
    except Exception:
        return None


def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            yield p, v
            yield from walk(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            p = f"{path}[{i}]"
            yield p, v
            yield from walk(v, p)


def flatten_text(obj):
    chunks = []
    for _, v in walk(obj):
        if isinstance(v, str):
            chunks.append(v)
    s = "\n".join(chunks)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"\s+", " ", s).strip()


def find_publication_ts(obj):
    priority = [
        "releasedate", "release_time", "releasetime", "publishdate", "publish_date",
        "publishtime", "publish_time", "publishedat", "published_at", "publicationdate",
    ]
    found = []
    for p, v in walk(obj):
        key = p.rsplit(".", 1)[-1].lower()
        key = key.split("[")[0]
        if key in priority:
            ts = parse_ts(v)
            if ts:
                found.append((priority.index(key), p, ts))
    if not found:
        return None, None
    found.sort(key=lambda x: (x[0], x[1]))
    return found[0][2], found[0][1]


def extract_code(url):
    m = re.search(r"/detail/([0-9a-fA-F]{32})", url)
    if not m:
        raise ValueError(f"MALFORMED_OFFICIAL_URL:{url}")
    return m.group(1).lower()


def ordinal(n):
    if 10 <= (n % 100) <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def get_bytes(url, attempts=4):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=35) as r:
                body = r.read()
                final_url = r.geturl()
                status = getattr(r, "status", 200)
                ctype = r.headers.get("Content-Type", "")
                return status, final_url, ctype, body
        except Exception as e:
            last = e
            time.sleep(0.5 * (2 ** i))
    raise last


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    recon = json.loads(RECON.read_text(encoding="utf-8"))
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    events = recon["events"]

    assert amendment["status"] == "FROZEN_BEFORE_TRANSPORT_EXECUTION_AND_BEFORE_ANY_MARKET_OUTCOME"
    assert amendment["transport"]["pagination_allowed"] is False
    assert amendment["transport"]["catalog_or_list_endpoint_allowed"] is False
    assert amendment["transport"]["protected_period_metadata_traversal_allowed"] is False
    assert len(events) == 33
    assert [e["n"] for e in events] == list(range(31, 64))

    codes = [extract_code(e["url"]) for e in events]
    assert len(codes) == len(set(codes)) == 33

    rows = []
    transport_failures = 0
    integrity_failures = 0
    clean = 0

    for e, code in zip(events, codes):
        n = int(e["n"])
        symbol = str(e["symbol"]).upper()
        expected_ts = str(e["published"])
        url = ROUTE.format(code)
        row = {
            "n": n,
            "symbol": symbol,
            "article_code": code,
            "official_support_url": e["url"],
            "transport_url": url,
            "expected_published_utc": expected_ts,
            "status": "PENDING",
        }
        try:
            status, final_url, ctype, body = get_bytes(url)
            row.update({
                "http_status": status,
                "final_url": final_url,
                "content_type": ctype,
                "response_bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            })
            raw_path = RAW / f"{n:02d}_{symbol}_{code}.json"
            raw_path.write_bytes(body)
            row["raw_file"] = str(raw_path.relative_to(OUTDIR))

            if status != 200 or not body:
                row["status"] = "TRANSPORT_FAILURE"
                transport_failures += 1
                rows.append(row)
                continue

            try:
                obj = json.loads(body.decode("utf-8"))
            except Exception as ex:
                row["status"] = "NON_JSON_RESPONSE"
                row["error"] = type(ex).__name__
                transport_failures += 1
                rows.append(row)
                continue

            text = flatten_text(obj)
            text_l = text.lower()
            pub_ts, pub_path = find_publication_ts(obj)
            article_code_present = code in text_l
            launchpool_present = "launchpool" in text_l
            bnb_present = re.search(r"\bbnb\b", text_l) is not None
            staking_language_present = any(x in text_l for x in ("stake", "staking", "lock", "locking", "farm", "farming"))
            symbol_present = re.search(rf"(?<![A-Z0-9]){re.escape(symbol)}(?![A-Z0-9])", text, flags=re.I) is not None
            project_number_present = (f"#{n}" in text_l) or (ordinal(n).lower() in text_l)
            timestamp_match = pub_ts == expected_ts

            row.update({
                "recovered_published_utc": pub_ts,
                "publication_field_path": pub_path,
                "timestamp_match": timestamp_match,
                "article_code_present": article_code_present,
                "launchpool_present": launchpool_present,
                "bnb_present": bnb_present,
                "staking_or_locking_language_present": staking_language_present,
                "symbol_present": symbol_present,
                "project_number_present": project_number_present,
            })

            required = [
                timestamp_match,
                article_code_present,
                launchpool_present,
                bnb_present,
                staking_language_present,
                symbol_present,
                project_number_present,
            ]
            if all(required):
                row["status"] = "CLEAN"
                clean += 1
            else:
                row["status"] = "DATA_INTEGRITY_FAILURE"
                integrity_failures += 1
        except urllib.error.HTTPError as ex:
            row.update({"status": "TRANSPORT_FAILURE", "error": f"HTTP_{ex.code}"})
            transport_failures += 1
        except Exception as ex:
            row.update({"status": "TRANSPORT_FAILURE", "error": f"{type(ex).__name__}:{ex}"})
            transport_failures += 1
        rows.append(row)

    manifest_basis = "\n".join(
        f"{r['n']}|{r['symbol']}|{r.get('sha256','')}|{r['status']}" for r in rows
    ).encode("utf-8")
    manifest_sha = hashlib.sha256(manifest_basis).hexdigest()

    if transport_failures:
        classification = "SOURCE_ACCESS_BLOCKED"
    elif integrity_failures:
        classification = "DATA_INTEGRITY_FAILURE"
    elif clean < 25:
        classification = "INSUFFICIENT_SOURCE_SAMPLE"
    elif clean == 33:
        classification = "SOURCE_DATA_PASS"
    else:
        classification = "INSUFFICIENT_SOURCE_SAMPLE"

    receipt = {
        "lab_id": "BNB-LAUNCHPOOL-DEMAND-001",
        "source_gate_id": "BLP-BNB-OFFICIAL-ANNOUNCEMENTS-001",
        "transport_amendment": "BLP-SOURCE-TRANSPORT-AMENDMENT-V0.1",
        "classification": classification,
        "expected_events": 33,
        "clean_events": clean,
        "transport_failures": transport_failures,
        "integrity_failures": integrity_failures,
        "ordered_manifest_sha256": manifest_sha,
        "events": rows,
        "guards": GUARDS,
        "market_outcomes_opened": False,
        "access_2025": False,
        "access_2026": False,
        "promotion_to_market_discovery_authorized": classification == "SOURCE_DATA_PASS",
        "note": "SOURCE_DATA_PASS, if reached, authorizes only creation of a separate prospective mechanism-discovery freeze. It does not itself authorize BNB/BTC market outcome access.",
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ["classification", "clean_events", "transport_failures", "integrity_failures", "ordered_manifest_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
