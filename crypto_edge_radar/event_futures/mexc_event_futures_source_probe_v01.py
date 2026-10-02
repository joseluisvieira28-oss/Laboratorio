from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

API_BASE = "https://api.mexc.com"
PAGE_BASES = (
    "https://www.mexc.com/futures/event-futures/{pair}",
    "https://www.mexc.com/futures/prediction-futures/{pair}",
)

DISPLAY_ASSETS: dict[str, tuple[str, ...]] = {
    "BTCUSDT": ("BTC_USDT",),
    "ETHUSDT": ("ETH_USDT",),
    "NVDAUSDT": ("NVDA_USDT", "NVIDIA_USDT"),
    "MUUSDT": ("MU_USDT", "MUSTOCK_USDT"),
    "SPCXUSDT": ("SPCX_USDT", "SPCXSTOCK_USDT"),
}

PAGE_PAIRS: dict[str, tuple[str, ...]] = {
    "BTCUSDT": ("BTC_USDT",),
    "ETHUSDT": ("ETH_USDT",),
    "NVDAUSDT": ("NVDA_USDT", "NVIDIA_USDT"),
    "MUUSDT": ("MU_USDT", "MUSTOCK_USDT"),
    "SPCXUSDT": ("SPCX_USDT", "SPCXSTOCK_USDT"),
}

INTERVAL = "Min1"


class ProbeError(RuntimeError):
    pass


def http_get(url: str, timeout: int = 30, retries: int = 3) -> tuple[int, bytes, str]:
    last: Exception | None = None
    headers = {
        "User-Agent": "crypto-edge-radar/mexc-event-futures-source-probe-v01",
        "Accept": "application/json,text/html,*/*",
    }
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return int(r.status), r.read(), str(r.headers.get("content-type", ""))
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(1.0 + attempt)
    raise ProbeError(f"HTTP_GET_FAILED:{type(last).__name__}:{last}")


def parse_kline_payload(payload: Any, start_s: int, end_s: int) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "PAYLOAD_NOT_OBJECT"}
    if payload.get("success") is not True:
        return {
            "ok": False,
            "reason": "API_SUCCESS_FALSE",
            "code": payload.get("code"),
            "message": payload.get("message"),
        }
    data = payload.get("data")
    if not isinstance(data, dict):
        return {"ok": False, "reason": "DATA_NOT_OBJECT"}

    required = ("time", "open", "close", "high", "low")
    if any(not isinstance(data.get(k), list) for k in required):
        return {"ok": False, "reason": "REQUIRED_ARRAY_MISSING"}

    n = len(data["time"])
    if n == 0:
        return {"ok": False, "reason": "EMPTY"}

    if any(len(data[k]) != n for k in required):
        return {"ok": False, "reason": "ARRAY_LENGTH_MISMATCH", "rows": n}

    times: list[int] = []
    bad_numeric = 0
    for i in range(n):
        try:
            ts = int(data["time"][i])
            vals = [float(data[k][i]) for k in ("open", "close", "high", "low")]
        except Exception:
            return {"ok": False, "reason": "PARSE_FAILURE", "rows": n}
        times.append(ts)
        if not all(math.isfinite(v) and v > 0 for v in vals):
            bad_numeric += 1

    monotonic = all(times[i] <= times[i + 1] for i in range(len(times) - 1))
    duplicate_timestamps = len(times) - len(set(times))
    outside = sum(1 for x in times if x < start_s - 120 or x > end_s + 120)

    return {
        "ok": bool(monotonic and bad_numeric == 0 and outside == 0),
        "rows": n,
        "first_timestamp": min(times),
        "last_timestamp": max(times),
        "monotonic": monotonic,
        "duplicate_timestamps": duplicate_timestamps,
        "outside_requested_window": outside,
        "invalid_ohlc_rows": bad_numeric,
        "raw_prices_reported": False,
    }


def probe_api_symbol(symbol: str, start_s: int, end_s: int) -> dict[str, Any]:
    q = urllib.parse.urlencode(
        {"interval": INTERVAL, "start": str(start_s), "end": str(end_s)}
    )
    out: dict[str, Any] = {"symbol": symbol, "interval": INTERVAL}

    for kind, path in (
        ("index", f"/api/v1/contract/kline/index_price/{symbol}"),
        ("contract", f"/api/v1/contract/kline/{symbol}"),
    ):
        url = API_BASE + path + "?" + q
        try:
            status, body, content_type = http_get(url)
            parsed = json.loads(body.decode("utf-8", errors="strict"))
            verdict = parse_kline_payload(parsed, start_s, end_s)
            out[kind] = {
                "http_status": status,
                "content_type": content_type,
                **verdict,
            }
        except Exception as exc:
            out[kind] = {
                "ok": False,
                "reason": f"{type(exc).__name__}:{exc}",
            }
    return out


def probe_page(display: str) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for pair in PAGE_PAIRS[display]:
        for template in PAGE_BASES:
            url = template.format(pair=pair)
            try:
                status, body, content_type = http_get(url)
                html = body.decode("utf-8", errors="replace")
                low = html.lower()
                attempts.append(
                    {
                        "pair": pair,
                        "url_family": "event-futures"
                        if "/event-futures/" in url
                        else "prediction-futures",
                        "http_status": status,
                        "content_type": content_type,
                        "bytes": len(body),
                        "has_up_payout_label": "up payout" in low,
                        "has_down_payout_label": "down payout" in low,
                        "has_index_label": "index" in low,
                        "script_tag_count": low.count("<script"),
                        "payout_value_extracted": False,
                    }
                )
            except Exception as exc:
                attempts.append(
                    {
                        "pair": pair,
                        "url_family": "event-futures"
                        if "/event-futures/" in url
                        else "prediction-futures",
                        "ok": False,
                        "reason": f"{type(exc).__name__}:{exc}",
                    }
                )
    return {"display": display, "attempts": attempts}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=3)
    ap.add_argument(
        "--output",
        default="mexc_event_futures_source_probe_receipt_v01.json",
    )
    args = ap.parse_args()

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = now - timedelta(hours=max(1, args.hours))
    start_s = int(start.timestamp())
    end_s = int(now.timestamp())

    assets: list[dict[str, Any]] = []
    for display, aliases in DISPLAY_ASSETS.items():
        alias_results = [probe_api_symbol(sym, start_s, end_s) for sym in aliases]
        valid = [
            x["symbol"]
            for x in alias_results
            if x.get("index", {}).get("ok") is True
        ]
        assets.append(
            {
                "display_pair": display,
                "candidate_aliases": list(aliases),
                "valid_index_aliases": valid,
                "source_status": "INDEX_SOURCE_PASS" if valid else "INDEX_SOURCE_BLOCKED",
                "aliases": alias_results,
                "event_page": probe_page(display),
            }
        )

    all_index = all(x["valid_index_aliases"] for x in assets)

    receipt = {
        "probe_id": "MEXC_EVENT_FUTURES_MULTI_ASSET_SOURCE_PROBE_V0.1",
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "probe_window": {
            "start_utc": start.isoformat().replace("+00:00", "Z"),
            "end_utc": now.isoformat().replace("+00:00", "Z"),
            "interval": INTERVAL,
        },
        "assets": assets,
        "product_mechanics_source": "OFFICIAL_MEXC_HELP",
        "event_futures_api_trading_supported_by_official_docs": False,
        "historical_event_payout_route": "NOT_PROVEN",
        "historical_product_pnl_authorized": False,
        "directional_bulk_outcomes_opened": False,
        "account_or_private_endpoint_used": False,
        "orders_created": False,
        "raw_prices_reported": False,
        "gate_status": (
            "SOURCE_GATE_PASS_DIRECTIONAL_ONLY"
            if all_index
            else "SOURCE_GATE_PARTIAL_OR_BLOCKED"
        ),
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if all_index else 3


if __name__ == "__main__":
    raise SystemExit(main())
