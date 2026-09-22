from __future__ import annotations

import hashlib
import json
from math import isfinite
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

HOSTS = (
    "https://fapi.binance.com",
    "https://fapi1.binance.com",
    "https://fapi2.binance.com",
    "https://fapi3.binance.com",
    "https://fapi4.binance.com",
)
PATH = "/fapi/v1/fundingRate"
SYMBOL = "AVAXUSDT"
START_MS = 1789948800000
END_MS = 1790035199000
LIMIT = 1000


def _validate_payload(data: Any) -> tuple[bool, int | None]:
    if not isinstance(data, list) or not data:
        return False, len(data) if isinstance(data, list) else None
    for row in data:
        if not isinstance(row, dict):
            return False, len(data)
        if any(k not in row for k in ("symbol", "fundingTime", "fundingRate", "markPrice")):
            return False, len(data)
        if row["symbol"] != SYMBOL:
            return False, len(data)
        try:
            ft = int(row["fundingTime"])
            rate = float(row["fundingRate"])
            mark_price = float(row["markPrice"])
        except (TypeError, ValueError):
            return False, len(data)
        if (
            not START_MS <= ft <= END_MS
            or not isfinite(rate)
            or not isfinite(mark_price)
            or mark_price <= 0
        ):
            return False, len(data)
    return True, len(data)


def probe_host(host: str, *, timeout: int = 12) -> dict[str, Any]:
    if host not in HOSTS:
        raise ValueError("host outside frozen CED1D probe set")
    query = urllib.parse.urlencode(
        {
            "symbol": SYMBOL,
            "startTime": START_MS,
            "endTime": END_MS,
            "limit": LIMIT,
        }
    )
    url = f"{host}{PATH}?{query}"
    rec: dict[str, Any] = {"host": host, "endpoint": PATH}
    try:
        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": "crypto-edge-radar/0.9 ced1d-render-source-probe",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            rec["http_status"] = int(response.status)
        rec["body_sha256"] = hashlib.sha256(body).hexdigest()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            rec["schema_pass"] = False
            rec["row_count"] = None
            rec["error_class"] = "JSONDecodeError"
            return rec
        schema_pass, row_count = _validate_payload(data)
        rec["schema_pass"] = bool(rec["http_status"] == 200 and schema_pass)
        rec["row_count"] = row_count
        return rec
    except urllib.error.HTTPError as exc:
        rec["http_status"] = int(exc.code)
        rec["schema_pass"] = False
        rec["row_count"] = None
        rec["error_class"] = "HTTPError"
        try:
            body = exc.read()
            rec["body_sha256"] = hashlib.sha256(body).hexdigest()
        except Exception:
            pass
        return rec
    except Exception as exc:
        rec["schema_pass"] = False
        rec["row_count"] = None
        rec["error_class"] = type(exc).__name__
        return rec


def ced1d_render_source_probe(*, timeout: int = 12) -> dict[str, Any]:
    results = [probe_host(host, timeout=timeout) for host in HOSTS]
    winners = [x["host"] for x in results if x.get("schema_pass") is True]
    return {
        "probe_id": "CED1D-0031-RENDER-SOURCE-PROBE-V0.2",
        "required_fields": ["symbol", "fundingTime", "fundingRate", "markPrice"],
        "classification": (
            "OFFICIAL_ENDPOINT_EXACT_SCHEMA_PASS"
            if winners
            else "OFFICIAL_ENDPOINT_EXACT_SCHEMA_BLOCKED"
        ),
        "accessible_exact_schema_hosts": winners,
        "results": results,
        "used_as_forward_evidence": False,
        "collector_adoption_authorized": False,
        "returns_computed": False,
        "pnl_computed": False,
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }
