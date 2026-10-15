#!/usr/bin/env python3
"""Source-only schema probe for Kalshi event live data.

No reference prices, market odds, outcomes, or economics are persisted.
"""

from __future__ import annotations
import datetime as dt
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE = "https://api.elections.kalshi.com/trade-api/v2"
UA = "CryptoLab-POB-KalshiLiveData/0.1 research-only"
OUT = Path("artifacts/prediction_oracle_basis/kalshi_live_data")


def now():
    return dt.datetime.now(dt.timezone.utc)


def iso(x):
    return x.astimezone(dt.timezone.utc).isoformat()


def parse_iso(v):
    if not v:
        return None
    try:
        x = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        if x.tzinfo is None:
            x = x.replace(tzinfo=dt.timezone.utc)
        return x.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def request(url):
    started = now()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            status = int(resp.status)
            ctype = resp.headers.get("content-type", "")
    except urllib.error.HTTPError as exc:
        raw = exc.read() if exc.fp else b""
        status = int(exc.code)
        ctype = exc.headers.get("content-type", "") if exc.headers else ""
    finished = now()
    obj = None
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception:
        pass
    return {
        "url": url,
        "status": status,
        "content_type": ctype,
        "bytes": len(raw),
        "raw_sha256": sha(raw),
        "started_at_utc": iso(started),
        "finished_at_utc": iso(finished),
        "obj": obj,
        "raw_text_lower": raw.decode("utf-8", errors="ignore").lower(),
    }


def choose_event():
    url = BASE + "/markets?" + urllib.parse.urlencode({
        "series_ticker": "KXBTCD",
        "status": "open",
        "limit": 1000,
    })
    r = request(url)
    if r["status"] != 200 or not isinstance(r["obj"], dict):
        raise RuntimeError("public KXBTCD enumeration failed")
    t0 = now()
    candidates = []
    for m in r["obj"].get("markets", []):
        if not isinstance(m, dict):
            continue
        close = parse_iso(m.get("close_time") or m.get("latest_expiration_time"))
        event = str(m.get("event_ticker") or "")
        if close and close > t0 and event:
            candidates.append((close, event))
    if not candidates:
        raise RuntimeError("no future open KXBTCD event")
    earliest = min(x[0] for x in candidates)
    events = sorted({event for close, event in candidates if close == earliest})
    return events[0], iso(earliest), {
        "enumeration_status": r["status"],
        "enumeration_raw_sha256": r["raw_sha256"],
        "future_candidate_count": len(candidates),
    }


def schema_walk(x: Any, prefix="$", paths=None, arrays=None):
    if paths is None:
        paths = []
    if arrays is None:
        arrays = {}
    if isinstance(x, dict):
        for k, v in x.items():
            p = f"{prefix}.{k}"
            paths.append(p)
            schema_walk(v, p, paths, arrays)
    elif isinstance(x, list):
        arrays[prefix] = len(x)
        for v in x[:1]:
            schema_walk(v, prefix + "[]", paths, arrays)
    return paths, arrays


def provenance_labels(x: Any, prefix="$", out=None):
    if out is None:
        out = []
    wanted = ("type", "source", "symbol", "ticker", "index", "benchmark", "provider", "unit", "name")
    if isinstance(x, dict):
        for k, v in x.items():
            p = f"{prefix}.{k}"
            kl = str(k).lower()
            if any(w in kl for w in wanted) and isinstance(v, str):
                vl = v.lower()
                # prevent accidental persistence of numeric price-like values
                if not any(ch.isdigit() for ch in v) or any(s in vl for s in ("brti", "benchmark", "btc", "usd", "crypto")):
                    out.append({"path": p, "value": v[:240]})
            provenance_labels(v, p, out)
    elif isinstance(x, list):
        for v in x[:3]:
            provenance_labels(v, prefix + "[]", out)
    return out[:100]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    event, close_utc, enum_meta = choose_event()
    url = BASE + "/live_data/events/" + urllib.parse.quote(event)
    r = request(url)
    obj = r["obj"]
    paths, arrays = schema_walk(obj) if obj is not None else ([], {})
    labels = provenance_labels(obj) if obj is not None else []
    raw_lower = r["raw_text_lower"]

    explicit_brti = "brti" in raw_lower
    explicit_cf = "cf benchmarks" in raw_lower or "cfbenchmarks" in raw_lower
    explicit_btc = "btc" in raw_lower or "bitcoin" in raw_lower

    if r["status"] in (401, 403):
        cls = "KALSHI_EVENT_LIVE_DATA_AUTH_REQUIRED"
    elif 200 <= r["status"] < 300 and obj is not None and (explicit_brti or explicit_cf):
        cls = "KALSHI_EVENT_LIVE_DATA_BRTI_PUBLIC_PASS"
    elif 200 <= r["status"] < 300 and obj is not None:
        cls = "KALSHI_EVENT_LIVE_DATA_PUBLIC_REFERENCE_UNPROVEN"
    else:
        cls = "KALSHI_EVENT_LIVE_DATA_TECHNICAL_FAILURE"

    receipt = {
        "schema": "POB_HOURLY_KALSHI_LIVE_DATA_SOURCE_PROBE_V0.1",
        "generated_at_utc": iso(now()),
        "authority": "POB_HOURLY_KALSHI_LIVE_DATA_AUTHORITY_V0.1.md",
        "target": {
            "event_ticker": event,
            "event_close_utc": close_utc,
            **enum_meta,
        },
        "request": {
            "url": r["url"],
            "status": r["status"],
            "content_type": r["content_type"],
            "bytes": r["bytes"],
            "raw_sha256": r["raw_sha256"],
            "started_at_utc": r["started_at_utc"],
            "finished_at_utc": r["finished_at_utc"],
        },
        "schema_observation": {
            "top_level_keys": sorted(obj.keys()) if isinstance(obj, dict) else [],
            "key_paths": sorted(set(paths)),
            "array_lengths": arrays,
            "provenance_labels": labels,
            "contains_brti_label": explicit_brti,
            "contains_cf_benchmarks_label": explicit_cf,
            "contains_btc_label": explicit_btc,
            "numeric_reference_values_persisted": False,
        },
        "adjudication": {
            "classification": cls,
            "economic_outputs_computed": False,
            "matured_outcomes_read": False,
            "market_quotes_compared": False,
            "orders": False,
            "authenticated_trading_endpoints": False,
        },
    }
    receipt["receipt_sha256"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    (OUT / "source_probe_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(receipt["adjudication"], indent=2, sort_keys=True))
    print(json.dumps(receipt["schema_observation"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
