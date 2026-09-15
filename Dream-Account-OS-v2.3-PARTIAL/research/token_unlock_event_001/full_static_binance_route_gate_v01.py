import calendar
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "source_probe_output_v07" / "TUE_FULL_STATIC_IDENTITY_MANIFEST_V01.json"
OUT = HERE / "source_probe_output_v08" / "TUE_FULL_STATIC_BINANCE_ROUTE_GATE_V01.json"

MIN_EVENTS = 40
MIN_TOKENS = 15
MIN_YEARS = 2
BASE = "https://data.binance.vision/data/spot/monthly/klines"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


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
    req = urllib.request.Request(url, headers={"User-Agent": "TOKEN-UNLOCK-EVENT-001-full-static-source-gate/1.0"})
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


def main():
    obj = load_json(MANIFEST)
    receipt_in = obj["receipt"]
    if receipt_in["classification"] != "PASS_IDENTITY_PREFREEZE":
        raise RuntimeError("identity manifest did not pass pre-route gate")
    events = obj["events"]

    route_cache = {}
    qualified = []
    excluded = []
    route_queries = []

    for idx, event in enumerate(events):
        symbol = str(event["symbol"])
        dt = datetime.fromisoformat(str(event["scheduled_at_utc"]).replace("Z", "+00:00")).astimezone(timezone.utc)
        if dt.year not in (2023, 2024):
            raise RuntimeError("date firewall breach")
        known_lead = float(event.get("known_lead_days", -1))
        if known_lead < 30:
            raise RuntimeError("identity manifest contains <30d event")
        if float(event.get("scheduled_unlock_tokens", 0)) <= 0:
            raise RuntimeError("identity manifest contains non-positive amount")

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
                "source_file": event.get("file"),
                "scheduled_at_utc": dt.isoformat(),
                "required_months": [f"{y:04d}-{m:02d}" for y, m in needed],
                "route_statuses": [x["status"] for x in month_results],
            })
            continue

        qualified.append({
            **event,
            "binance_pair": f"{symbol}USDT",
            "pre_event_30d_route_months": [f"{y:04d}-{m:02d}" for y, m in needed],
            "market_prices_accessed": False,
            "returns_computed": False,
            "pnl_computed": False,
        })

    symbols = sorted({x["symbol"] for x in qualified})
    years = sorted({int(str(x["scheduled_at_utc"])[0:4]) for x in qualified})
    counts = {s: sum(1 for x in qualified if x["symbol"] == s) for s in symbols}
    pass_counts = len(qualified) >= MIN_EVENTS and len(symbols) >= MIN_TOKENS and len(years) >= MIN_YEARS
    classification = "SOURCE_DATA_FEASIBLE" if pass_counts else "SOURCE_DATA_INADEQUATE"

    receipt = {
        "lab_id": "TOKEN-UNLOCK-EVENT-001",
        "mve_id": "TUE-CLIFF-ADV30-001",
        "mode": "SOURCE_GATE_ONLY_FULL_STATIC_BINANCE_ROUTE_V01",
        "classification": classification,
        "identity_manifest_event_count": len(events),
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
        "identity_manifest_fingerprint_sha256": receipt_in["manifest_fingerprint_sha256"],
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
            "exchange_mutation": False
        },
        "next_action": (
            "If SOURCE_DATA_FEASIBLE, freeze execution semantics, costs and promotion gates prospectively before any market outcome access. "
            "If SOURCE_DATA_INADEQUATE, do not reduce thresholds or cherry-pick tokens."
        )
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"receipt": receipt, "qualified_events": qualified, "excluded_events": excluded, "route_queries": route_queries}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print("CHECKSUM METADATA ONLY / NO KLINE ZIP / NO PRICE VALUES / NO RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
