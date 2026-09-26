from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "local_data" / "cross_venue_diamond_replication_002_source_probe"
OUT.mkdir(parents=True, exist_ok=True)

BYBIT_SYMBOL = "AVAXUSDT"
OKX_INST = "AVAX-USDT-SWAP"
ANCHORS = [
    "2024-09-01T00:00:00Z",
    "2025-01-01T00:00:00Z",
    "2025-04-01T00:00:00Z",
    "2025-07-01T00:00:00Z",
    "2025-10-01T00:00:00Z",
    "2025-12-31T00:00:00Z",
]
UA = "CROSS-VENUE-DIAMOND-REPLICATION-002 source-only probe/1.0"

def ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)

def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def get_json(base: str, params: dict, retries: int = 3):
    url = base + "?" + urllib.parse.urlencode(params)
    last = None
    for k in range(retries):
        try:
            time.sleep(0.15)
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                if r.status != 200:
                    raise RuntimeError(f"HTTP_{r.status}")
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            if k + 1 < retries:
                time.sleep(1.0 * (2 ** k))
    raise RuntimeError(f"GET_FAILED:{base}:{params}:{last}")


def get_bybit_json(path: str, params: dict):
    last = None
    for host in ("https://api.bybit.com", "https://api.bytick.com"):
        try:
            return get_json(host + path, params)
        except Exception as e:
            last = e
    raise RuntimeError(f"BYBIT_OFFICIAL_HOSTS_FAILED:{path}:{params}:{last}")

def summary(times):
    x = sorted(set(int(t) for t in times))
    return {"count": len(x), "min_ts": x[0] if x else None, "max_ts": x[-1] if x else None, "timestamps_sha256": sha(x)}

def near(times, target, tolerance):
    return any(abs(int(t) - target) <= tolerance for t in times)

def bybit():
    out = {"instrument": {}, "price_1m": {}, "funding": {}, "errors": []}
    try:
        j = get_bybit_json("/v5/market/instruments-info", {"category": "linear", "symbol": BYBIT_SYMBOL})
        rows = ((j.get("result") or {}).get("list") or [])
        out["instrument"] = {"present": j.get("retCode") == 0 and any(r.get("symbol") == BYBIT_SYMBOL for r in rows), "count": len(rows)}
    except Exception as e:
        out["instrument"] = {"present": False, "error": str(e)}
        out["errors"].append(f"INSTRUMENT:{e}")

    for a in ANCHORS:
        t = ms(a)
        try:
            j = get_bybit_json("/v5/market/kline", {
                "category": "linear", "symbol": BYBIT_SYMBOL, "interval": "1",
                "start": t - 10 * 60_000, "end": t + 10 * 60_000, "limit": 50
            })
            if j.get("retCode") != 0:
                raise RuntimeError(f"BYBIT_RET:{j.get('retCode')}:{j.get('retMsg')}")
            rows = ((j.get("result") or {}).get("list") or [])
            times = [int(r[0]) for r in rows]
            out["price_1m"][a] = {**summary(times), "anchor_present": near(times, t, 60_000)}
        except Exception as e:
            out["price_1m"][a] = {"anchor_present": False, "error": str(e)}
            out["errors"].append(f"PRICE:{a}:{e}")

        try:
            j = get_bybit_json("/v5/market/funding/history", {
                "category": "linear", "symbol": BYBIT_SYMBOL,
                "startTime": t - 3 * 86400_000, "endTime": t + 3 * 86400_000, "limit": 200
            })
            if j.get("retCode") != 0:
                raise RuntimeError(f"BYBIT_RET:{j.get('retCode')}:{j.get('retMsg')}")
            rows = ((j.get("result") or {}).get("list") or [])
            times = [int(r["fundingRateTimestamp"]) for r in rows if r.get("fundingRateTimestamp")]
            out["funding"][a] = {**summary(times), "near_anchor": near(times, t, 3 * 86400_000)}
        except Exception as e:
            out["funding"][a] = {"near_anchor": False, "error": str(e)}
            out["errors"].append(f"FUNDING:{a}:{e}")

    out["coverage_pass"] = (
        bool(out["instrument"].get("present"))
        and not out["errors"]
        and all(v.get("anchor_present") for v in out["price_1m"].values())
        and all(v.get("near_anchor") for v in out["funding"].values())
    )
    return out

def okx():
    out = {"instrument": {}, "price_1m": {}, "funding": {}, "errors": []}
    try:
        j = get_json("https://www.okx.com/api/v5/public/instruments", {"instType": "SWAP", "instId": OKX_INST})
        rows = j.get("data") or []
        out["instrument"] = {"present": j.get("code") == "0" and any(r.get("instId") == OKX_INST for r in rows), "count": len(rows)}
    except Exception as e:
        out["instrument"] = {"present": False, "error": str(e)}
        out["errors"].append(f"INSTRUMENT:{e}")

    for a in ANCHORS:
        t = ms(a)
        try:
            j = get_json("https://www.okx.com/api/v5/market/history-candles", {
                "instId": OKX_INST, "bar": "1m", "after": t + 60 * 60_000, "limit": 100
            })
            if j.get("code") != "0":
                raise RuntimeError(f"OKX_CODE:{j.get('code')}:{j.get('msg')}")
            times = [int(r[0]) for r in (j.get("data") or [])]
            out["price_1m"][a] = {**summary(times), "anchor_present": near(times, t, 60_000)}
        except Exception as e:
            out["price_1m"][a] = {"anchor_present": False, "error": str(e)}
            out["errors"].append(f"PRICE:{a}:{e}")

        try:
            j = get_json("https://www.okx.com/api/v5/public/funding-rate-history", {
                "instId": OKX_INST, "after": t + 3 * 86400_000, "limit": 30
            })
            if j.get("code") != "0":
                raise RuntimeError(f"OKX_CODE:{j.get('code')}:{j.get('msg')}")
            times = [int(r["fundingTime"]) for r in (j.get("data") or []) if r.get("fundingTime")]
            out["funding"][a] = {**summary(times), "near_anchor": near(times, t, 3 * 86400_000)}
        except Exception as e:
            out["funding"][a] = {"near_anchor": False, "error": str(e)}
            out["errors"].append(f"FUNDING:{a}:{e}")

    out["coverage_pass"] = (
        bool(out["instrument"].get("present"))
        and not out["errors"]
        and all(v.get("anchor_present") for v in out["price_1m"].values())
        and all(v.get("near_anchor") for v in out["funding"].values())
    )
    return out

def main():
    receipt = {
        "lab_id": "CROSS-VENUE-DIAMOND-REPLICATION-002",
        "candidate": "CED1D-0031-AVAX20-CONTINUATION-H1",
        "stage": "SOURCE_COVERAGE_GATE",
        "outcome_blind": True,
        "signal_calculation_performed": False,
        "return_calculation_performed": False,
        "pnl_calculation_performed": False,
        "2026_plus_accessed": False,
        "anchors": ANCHORS,
        "transport_remediation": {"serialized_requests": True, "bybit_official_host_fallback": ["api.bybit.com", "api.bytick.com"], "okx_shared_ip_throttle_seconds": 0.15},
        "venues": {
            "BYBIT_LINEAR_USDT": bybit(),
            "OKX_USDT_SWAP": okx(),
        },
    }
    passed = [k for k, v in receipt["venues"].items() if v["coverage_pass"]]
    receipt["replication_authorized_venues"] = passed
    receipt["status"] = "SOURCE_DATA_PASS_BOTH_VENUES" if len(passed) == 2 else ("SOURCE_DATA_PARTIAL_PASS" if len(passed) == 1 else "SOURCE_DATA_BLOCKED")
    receipt["source_fingerprint"] = sha(receipt)
    p = OUT / "CROSS_VENUE_DIAMOND_REPLICATION_002_SOURCE_COVERAGE_RECEIPT_V0.1.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "replication_authorized_venues": passed, "source_fingerprint": receipt["source_fingerprint"]}, sort_keys=True))

if __name__ == "__main__":
    main()
