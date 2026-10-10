"""CED1D-0031 PUBLIC SOURCE-ONLY gate; never interpret trading outcomes.

No secrets, authentication, exchange commands, performance tuning, or source
replacement. Check only Binance Vision exact immutable daily archive filenames
and checksum siblings; a HEAD result is availability, not verified file content.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
import json
import sys

ARCHIVE_ROOT = "https://data.binance.vision/data/futures/um/daily/bookDepth/AVAXUSDT"
FIRST = date(2026, 10, 4)
LAST = date(2026, 10, 9)


def url_for(day: date) -> str:
    if not FIRST <= day <= LAST:
        raise ValueError("day not in frozen 2026-10-04..09 source-probe window")
    return f"{ARCHIVE_ROOT}/AVAXUSDT-bookDepth-{day.isoformat()}.zip"


def check(url: str, method: str, timeout: float = 12) -> dict:
    if urlsplit(url).hostname != "data.binance.vision" or not url.startswith(ARCHIVE_ROOT + "/"):
        raise ValueError("hostname/path not approved")
    request = Request(url, method=method, headers={"User-Agent": "CryptoLab-CED1D-sourcegate/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            final_url = response.geturl()
            if urlsplit(final_url).hostname != "data.binance.vision":
                return {"state": "SOURCE_REDIRECT_UNVERIFIED", "http_status": int(response.status)}
            if method == "GET":
                snippet = response.read(1024)
                # A readable checksum sibling is NOT proof the archive is valid.
                checksum_shape = len(snippet.strip().split()) >= 2 and len(snippet) < 512
                return {"state": "PRESENT_UNVALIDATED" if checksum_shape else "INVALID_CHECKSUM_SHAPE",
                        "http_status": int(response.status)}
            return {"state": "HEAD_OK_NOT_CONTENT_VALIDATED", "http_status": int(response.status)}
    except HTTPError as exc:
        return {"state": "NOT_PUBLISHED" if exc.code == 404 else "ACCESS_OR_TRANSPORT_BLOCKED",
                "http_status": int(exc.code)}
    except (URLError, TimeoutError, OSError):
        return {"state": "TRANSPORT_UNVERIFIED", "http_status": None}


def one(day: date) -> dict:
    url = url_for(day)
    return {"day": day.isoformat(), "archive": check(url, "HEAD"),
            "checksum": check(url + ".CHECKSUM", "GET"),
            "archive_url": url}


def probe() -> dict:
    days = [FIRST + timedelta(days=i) for i in range((LAST-FIRST).days+1)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = sorted(pool.map(one, days), key=lambda x:x["day"])
    return {
        "schema": "CED1D_0031_PUBLIC_SOURCE_COVERAGE_V0.1",
        "authority": "SOURCE_ONLY_NO_OUTCOMES_OPENED",
        "provider": "BINANCE_VISION_PUBLIC",
        "symbol": "AVAXUSDT",
        "results": results,
        "all_archive_heads_present": all(x["archive"]["state"]=="HEAD_OK_NOT_CONTENT_VALIDATED" for x in results),
        "source_hashes_verified": False,
        "scientific_rules_changed": False,
        "orders_created": False,
        "authenticated_exchange_api_used": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
        "forward_promotion_authorized": False,
    }


if __name__ == "__main__":
    output = probe()
    print(json.dumps(output, sort_keys=True, indent=2))
    with open("/tmp/ced1d-source-coverage.json","w",encoding="utf-8") as f:
        json.dump(output,f,sort_keys=True,indent=2)
