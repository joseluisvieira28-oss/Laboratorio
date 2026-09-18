from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "local_data" / "cross_venue_diamond_replication_001_source_probe"
OUT.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]
OKX_MAP = {s: s.replace("USDT", "-USDT-SWAP") for s in SYMBOLS}
ANCHORS = [
    "2023-01-01T00:00:00Z",
    "2023-07-01T00:00:00Z",
    "2024-01-01T00:00:00Z",
    "2024-07-01T00:00:00Z",
    "2024-12-31T00:00:00Z",
]
UA = "CROSS-VENUE-DIAMOND-REPLICATION-001 source-only probe/1.0"


def ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


def sha256_json(obj) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(b).hexdigest()


def get_json(base: str, params: dict, retries: int = 5):
    url = base + "?" + urllib.parse.urlencode(params)
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                if r.status != 200:
                    raise RuntimeError(f"HTTP_{r.status}")
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            if k + 1 < retries:
                time.sleep(min(8, 2 ** k))
    raise RuntimeError(f"GET_FAILED:{base}:{params}:{last}")


def summarize_times(times: list[int]) -> dict:
    times = sorted(set(times))
    return {
        "count": len(times),
        "min_ts": times[0] if times else None,
        "max_ts": times[-1] if times else None,
        "timestamps_sha256": sha256_json(times),
    }


def exact_or_near(times: list[int], anchor: int, tolerance_ms: int) -> bool:
    return any(abs(t - anchor) <= tolerance_ms for t in times)


def probe_bybit_symbol(symbol: str) -> dict:
    result = {"symbol": symbol, "price_6h": {}, "price_1m": {}, "funding": {}, "errors": []}
    for a in ANCHORS:
        t = ms(a)
        try:
            j = get_json(
                "https://api.bybit.com/v5/market/kline",
                {
                    "category": "linear",
                    "symbol": symbol,
                    "interval": "360",
                    "start": t - 12 * 3600_000,
                    "end": t + 24 * 3600_000,
                    "limit": 20,
                },
            )
            if j.get("retCode") != 0:
                raise RuntimeError(f"BYBIT_RET:{j.get('retCode')}:{j.get('retMsg')}")
            rows = ((j.get("result") or {}).get("list") or [])
            times = [int(x[0]) for x in rows]
            result["price_6h"][a] = {
                **summarize_times(times),
                "anchor_present": exact_or_near(times, t, 1_000),
            }
        except Exception as e:
            result["price_6h"][a] = {"error": str(e), "anchor_present": False}
            result["errors"].append(f"6H:{a}:{e}")

        try:
            j = get_json(
                "https://api.bybit.com/v5/market/kline",
                {
                    "category": "linear",
                    "symbol": symbol,
                    "interval": "1",
                    "start": t - 10 * 60_000,
                    "end": t + 10 * 60_000,
                    "limit": 50,
                },
            )
            if j.get("retCode") != 0:
                raise RuntimeError(f"BYBIT_RET:{j.get('retCode')}:{j.get('retMsg')}")
            rows = ((j.get("result") or {}).get("list") or [])
            times = [int(x[0]) for x in rows]
            result["price_1m"][a] = {
                **summarize_times(times),
                "anchor_present": exact_or_near(times, t, 1_000),
            }
        except Exception as e:
            result["price_1m"][a] = {"error": str(e), "anchor_present": False}
            result["errors"].append(f"1M:{a}:{e}")

    for a in (ANCHORS[0], ANCHORS[-1]):
        t = ms(a)
        try:
            j = get_json(
                "https://api.bybit.com/v5/market/funding/history",
                {
                    "category": "linear",
                    "symbol": symbol,
                    "startTime": t - 3 * 86400_000,
                    "endTime": t + 3 * 86400_000,
                    "limit": 200,
                },
            )
            if j.get("retCode") != 0:
                raise RuntimeError(f"BYBIT_RET:{j.get('retCode')}:{j.get('retMsg')}")
            rows = ((j.get("result") or {}).get("list") or [])
            times = [int(x["fundingRateTimestamp"]) for x in rows if x.get("fundingRateTimestamp")]
            result["funding"][a] = {
                **summarize_times(times),
                "near_anchor": exact_or_near(times, t, 3 * 86400_000),
            }
        except Exception as e:
            result["funding"][a] = {"error": str(e), "near_anchor": False}
            result["errors"].append(f"FUNDING:{a}:{e}")

    result["coverage_pass"] = (
        not result["errors"]
        and all(v.get("anchor_present") for v in result["price_6h"].values())
        and all(v.get("anchor_present") for v in result["price_1m"].values())
        and all(v.get("near_anchor") for v in result["funding"].values())
    )
    return result


def okx_times(resp: dict) -> list[int]:
    if resp.get("code") != "0":
        raise RuntimeError(f"OKX_CODE:{resp.get('code')}:{resp.get('msg')}")
    return [int(x[0]) for x in (resp.get("data") or [])]


def probe_okx_symbol(symbol: str) -> dict:
    inst = OKX_MAP[symbol]
    result = {"symbol": symbol, "instId": inst, "price_6h": {}, "price_1m": {}, "funding": {}, "errors": []}
    for a in ANCHORS:
        t = ms(a)
        try:
            j = get_json(
                "https://www.okx.com/api/v5/market/history-candles",
                {"instId": inst, "bar": "6Hutc", "after": t + 24 * 3600_000, "limit": 20},
            )
            times = okx_times(j)
            result["price_6h"][a] = {
                **summarize_times(times),
                "anchor_present": exact_or_near(times, t, 1_000),
            }
        except Exception as e:
            result["price_6h"][a] = {"error": str(e), "anchor_present": False}
            result["errors"].append(f"6H:{a}:{e}")

        try:
            j = get_json(
                "https://www.okx.com/api/v5/market/history-candles",
                {"instId": inst, "bar": "1m", "after": t + 60 * 60_000, "limit": 100},
            )
            times = okx_times(j)
            result["price_1m"][a] = {
                **summarize_times(times),
                "anchor_present": exact_or_near(times, t, 1_000),
            }
        except Exception as e:
            result["price_1m"][a] = {"error": str(e), "anchor_present": False}
            result["errors"].append(f"1M:{a}:{e}")

    for a in (ANCHORS[0], ANCHORS[-1]):
        t = ms(a)
        try:
            j = get_json(
                "https://www.okx.com/api/v5/public/funding-rate-history",
                {"instId": inst, "after": t + 3 * 86400_000, "limit": 30},
            )
            if j.get("code") != "0":
                raise RuntimeError(f"OKX_CODE:{j.get('code')}:{j.get('msg')}")
            rows = j.get("data") or []
            times = [int(x["fundingTime"]) for x in rows if x.get("fundingTime")]
            result["funding"][a] = {
                **summarize_times(times),
                "near_anchor": exact_or_near(times, t, 3 * 86400_000),
            }
        except Exception as e:
            result["funding"][a] = {"error": str(e), "near_anchor": False}
            result["errors"].append(f"FUNDING:{a}:{e}")

    result["coverage_pass"] = (
        not result["errors"]
        and all(v.get("anchor_present") for v in result["price_6h"].values())
        and all(v.get("anchor_present") for v in result["price_1m"].values())
        and all(v.get("near_anchor") for v in result["funding"].values())
    )
    return result


def main() -> int:
    receipt = {
        "lab_id": "CROSS-VENUE-DIAMOND-REPLICATION-001",
        "candidate": "HTF-DONCHIAN-DH-02-HO1-6H",
        "stage": "SOURCE_COVERAGE_GATE",
        "status": "RUNNING",
        "outcome_blind": True,
        "signal_calculation_performed": False,
        "return_calculation_performed": False,
        "pnl_calculation_performed": False,
        "years_allowed": [2023, 2024],
        "years_forbidden": [2025, 2026],
        "anchors": ANCHORS,
        "symbols": SYMBOLS,
        "venues": {},
    }

    bybit = [probe_bybit_symbol(s) for s in SYMBOLS]
    okx = [probe_okx_symbol(s) for s in SYMBOLS]
    receipt["venues"]["BYBIT_LINEAR_USDT"] = {
        "symbols": bybit,
        "venue_pass": all(x["coverage_pass"] for x in bybit),
    }
    receipt["venues"]["OKX_USDT_SWAP"] = {
        "symbols": okx,
        "venue_pass": all(x["coverage_pass"] for x in okx),
    }

    pass_count = sum(int(v["venue_pass"]) for v in receipt["venues"].values())
    receipt["status"] = "SOURCE_DATA_PASS_BOTH_VENUES" if pass_count == 2 else (
        "SOURCE_DATA_PARTIAL_PASS" if pass_count == 1 else "SOURCE_DATA_BLOCKED"
    )
    receipt["replication_authorized_venues"] = [
        k for k, v in receipt["venues"].items() if v["venue_pass"]
    ]
    receipt["source_fingerprint"] = sha256_json(receipt)

    out = OUT / "CROSS_VENUE_DIAMOND_REPLICATION_001_SOURCE_COVERAGE_RECEIPT_V0.1.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(json.dumps({
        "status": receipt["status"],
        "replication_authorized_venues": receipt["replication_authorized_venues"],
        "source_fingerprint": receipt["source_fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
