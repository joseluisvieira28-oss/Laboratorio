from __future__ import annotations

import hashlib
import json
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

PROGRAMS = {
    "kamino_lend": "KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
    "marginfi_v2": "MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
    "drift_v2": "dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH",
    "save_solend": "So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
}
FROM_UTC = 1734220800
TO_UTC = 1734307199
BASE = "https://api.solana.fm/v0/accounts/{program}/transactions"


def _one(name: str, program: str, timeout: int) -> dict[str, Any]:
    query = urllib.parse.urlencode(
        {"utcFrom": FROM_UTC, "utcTo": TO_UTC, "limit": 5, "page": 1}
    )
    url = BASE.format(program=program) + "?" + query
    rec: dict[str, Any] = {
        "protocol": name,
        "program_id": program,
        "window_utc": ["2024-12-15T00:00:00Z", "2024-12-15T23:59:59Z"],
    }
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DLS-RENDER-SOURCE-PROBE/0.2", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read()
            rec["http_status"] = int(response.status)
        rec["body_sha256"] = hashlib.sha256(body).hexdigest()
        data = json.loads(body)
        rec["parseable_json"] = True
        rec["json_type"] = type(data).__name__
        if isinstance(data, list):
            rec["row_count"] = len(data)
        elif isinstance(data, dict):
            rec["top_level_keys"] = sorted(data)
            for key in ("result", "data", "transactions"):
                if isinstance(data.get(key), list):
                    rec["row_count"] = len(data[key])
                    rec["row_container"] = key
                    break
        rec["transport_schema_pass"] = rec["http_status"] == 200
    except urllib.error.HTTPError as exc:
        rec["http_status"] = int(exc.code)
        rec["error"] = "HTTPError"
        try:
            body = exc.read()
            rec["error_body_sha256"] = hashlib.sha256(body).hexdigest()
        except Exception:
            pass
        rec["transport_schema_pass"] = False
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}:{exc}"
        rec["transport_schema_pass"] = False
    return rec


def dls_solanafm_render_source_probe(*, timeout: int = 15) -> dict[str, Any]:
    rows = [_one(name, program, timeout) for name, program in PROGRAMS.items()]
    passed = [x["protocol"] for x in rows if x.get("transport_schema_pass")]
    classification = (
        "TIME_BOUNDED_INDEXED_ROUTE_ACCESSIBLE"
        if len(passed) == len(rows)
        else "PARTIAL_INDEXED_ROUTE_ACCESS"
        if passed
        else "INDEXED_ROUTE_ACCESS_BLOCKED"
    )
    return {
        "lab_id": "DEFI-LIQUIDATION-SHOCK-001",
        "probe_version": "V0.2_RENDER",
        "classification": classification,
        "accessible_protocols": passed,
        "results": rows,
        "source_data_pass": False,
        "prices": False,
        "returns": False,
        "pnl": False,
        "direction": False,
        "market_response": False,
        "first_success_boundary_adjudicated": False,
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "wallets_used": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }
