import calendar
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROVIDER_MANIFEST = HERE / "source_probe_output_v03" / "TUE_PROVIDER_PIT_MANIFEST_2023_2024_V01.json"
IDENTITY_MAP = HERE / "TOKEN_IDENTITY_MAP_V01.json"
OUT = HERE / "source_probe_output_v04" / "TUE_PROVIDER_BINANCE_ROUTE_GATE_V01.json"

MIN_EVENTS = 40
MIN_TOKENS = 15
MIN_YEARS = 2
BASE = "https://data.binance.vision/data/spot/monthly/klines"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_events(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict) and isinstance(obj.get("events"), list):
        return obj["events"]
    raise RuntimeError("provider manifest does not expose an events list")


def event_files(event):
    value = event.get("source_files")
    if isinstance(value, list):
        return [str(x) for x in value]
    value = event.get("source_file") or event.get("file")
    return [str(value)] if value else []


def event_time(event):
    raw = event.get("scheduled_at_utc") or event.get("scheduled_unlock_timestamp_utc")
    if raw:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone(timezone.utc)
    ts = event.get("timestamp")
    if ts is not None:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    raise RuntimeError("event has no exact timestamp")


def months_covering(start_dt, end_dt):
    if end_dt < start_dt:
        return []
    y, m = start_dt.year, start_dt.month
    out = []
    while (y, m) <= (end_dt.year, end_dt.month):
        out.append((y, m))
        m += 1
        if m == 13:
            y += 1
            m = 1
    return out


def checksum_url(symbol, year, month):
    pair = f"{symbol}USDT"
    ym = f"{year:04d}-{month:02d}"
    return f"{BASE}/{pair}/1d/{pair}-1d-{ym}.zip.CHECKSUM"


def fetch_checksum_metadata(url):
    # CHECKSUM contains only archive integrity metadata; no kline values are opened.
    req = urllib.request.Request(url, headers={"User-Agent": "TOKEN-UNLOCK-EVENT-001-source-gate/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read(512).decode("utf-8", errors="replace").strip()
            status = getattr(resp, "status", 200)
            if status != 200:
                return False, status, None
            parts = body.split()
            digest = parts[0] if parts else ""
            if len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
                return False, status, body[:120]
            return True, status, digest.lower()
    except urllib.error.HTTPError as exc:
        return False, exc.code, None
    except Exception as exc:
        return False, f"ERROR:{type(exc).__name__}", None


def canonical_input_fingerprint(events, identity):
    payload = json.dumps({"events": events, "identity": identity}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main():
    provider_obj = load_json(PROVIDER_MANIFEST)
    events = parse_events(provider_obj)
    identity = load_json(IDENTITY_MAP)
    assert identity["status"] == "FROZEN_PRE_ROUTE_CHECK"
    mapping = identity["provider_adapter_to_symbol"]

    route_cache = {}
    qualified = []
    excluded = []
    route_queries = []

    for idx, event in enumerate(events):
        files = event_files(event)
        if len(files) != 1:
            excluded.append({"index": idx, "reason": "AMBIGUOUS_SOURCE_FILE_IDENTITY", "source_files": files})
            continue
        source_file = files[0]
        symbol = mapping.get(source_file)
        if not symbol:
            excluded.append({"index": idx, "reason": "UNMAPPED_SOURCE_FILE", "source_file": source_file})
            continue

        dt = event_time(event)
        if dt.year not in (2023, 2024):
            raise RuntimeError("date firewall breach")

        known_lead = float(event.get("known_lead_days", -1))
        if known_lead < 30:
            excluded.append({"index": idx, "reason": "KNOWN_AHEAD_LT_30D", "symbol": symbol, "scheduled_at_utc": dt.isoformat()})
            continue

        amount = float(event.get("scheduled_unlock_tokens", event.get("amount", 0)))
        if amount <= 0:
            excluded.append({"index": idx, "reason": "NON_POSITIVE_UNLOCK_AMOUNT", "symbol": symbol, "scheduled_at_utc": dt.isoformat()})
            continue

        # Frozen fail-closed identity quarantine discovered before route results.
        if source_file == "liquity.ts" and str(event.get("known_at_utc", "")).startswith("2023-"):
            excluded.append({"index": idx, "reason": "LIQUITY_2023_LUSD_LQTY_IDENTITY_CONFLICT", "symbol": symbol, "scheduled_at_utc": dt.isoformat()})
            continue

        window_start = (dt - timedelta(days=30)).date()
        window_end = (dt - timedelta(days=1)).date()
        needed = months_covering(
            datetime.combine(window_start, datetime.min.time(), tzinfo=timezone.utc),
            datetime.combine(window_end, datetime.min.time(), tzinfo=timezone.utc),
        )
        month_results = []
        route_ok = True
        for year, month in needed:
            if year >= 2025:
                raise RuntimeError("protected-period route breach")
            key = (symbol, year, month)
            if key not in route_cache:
                url = checksum_url(symbol, year, month)
                ok, status, digest = fetch_checksum_metadata(url)
                route_cache[key] = {"ok": ok, "status": status, "checksum_sha256": digest, "url": url}
                route_queries.append({"symbol": symbol, "year": year, "month": month, **route_cache[key]})
            month_results.append(route_cache[key])
            route_ok = route_ok and route_cache[key]["ok"]

        if not route_ok:
            excluded.append({
                "index": idx,
                "reason": "BINANCE_30D_PRE_EVENT_ARCHIVE_ROUTE_INCOMPLETE",
                "symbol": symbol,
                "source_file": source_file,
                "scheduled_at_utc": dt.isoformat(),
                "required_months": [f"{y:04d}-{m:02d}" for y, m in needed],
                "route_statuses": [x["status"] for x in month_results],
            })
            continue

        qualified.append({
            "symbol": symbol,
            "source_file": source_file,
            "scheduled_at_utc": dt.isoformat().replace("+00:00", "Z"),
            "scheduled_unlock_tokens": amount,
            "known_at_utc": event.get("known_at_utc"),
            "known_lead_days": known_lead,
            "source_commit": event.get("source_commit"),
            "source_repo": event.get("source_repo"),
            "sources": event.get("sources", []),
            "pit_status": event.get("pit_status"),
            "binance_pair": f"{symbol}USDT",
            "pre_event_30d_route_months": [f"{y:04d}-{m:02d}" for y, m in needed],
            "market_prices_accessed": False,
            "returns_computed": False,
            "pnl_computed": False,
        })

    symbols = sorted({x["symbol"] for x in qualified})
    years = sorted({datetime.fromisoformat(x["scheduled_at_utc"].replace("Z", "+00:00")).year for x in qualified})
    counts = {s: sum(1 for x in qualified if x["symbol"] == s) for s in symbols}
    pass_counts = len(qualified) >= MIN_EVENTS and len(symbols) >= MIN_TOKENS and len(years) >= MIN_YEARS
    classification = "SOURCE_DATA_FEASIBLE" if pass_counts else "SOURCE_DATA_INADEQUATE"

    receipt = {
        "lab_id": "TOKEN-UNLOCK-EVENT-001",
        "mve_id": "TUE-CLIFF-ADV30-001",
        "mode": "SOURCE_GATE_ONLY_PROVIDER_ROUTE_V01",
        "classification": classification,
        "provider_input_event_count": len(events),
        "qualified_event_count": len(qualified),
        "required_event_count": MIN_EVENTS,
        "qualified_distinct_tokens": len(symbols),
        "required_distinct_tokens": MIN_TOKENS,
        "qualified_tokens": symbols,
        "events_per_token": counts,
        "qualified_years": years,
        "required_calendar_years": MIN_YEARS,
        "excluded_event_count": len(excluded),
        "route_query_count": len(route_queries),
        "input_fingerprint_sha256": canonical_input_fingerprint(events, identity),
        "guards": {
            "binance_checksum_metadata_only": True,
            "kline_zip_downloaded": False,
            "market_price_values_opened": False,
            "returns_computed": False,
            "pnl_computed": False,
            "profit_factor_computed": False,
            "year_2025_opened": False,
            "year_2026_opened": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
        "next_action": (
            "If SOURCE_DATA_FEASIBLE, freeze execution semantics/costs/promotion gates prospectively before any market outcome access. "
            "If SOURCE_DATA_INADEQUATE, do not reduce thresholds; additional PIT sources may be qualified under a separate source-only remediation."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"receipt": receipt, "qualified_events": qualified, "excluded_events": excluded, "route_queries": route_queries}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print("NO KLINE ZIP / NO PRICE VALUES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
