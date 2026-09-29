from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "local_data" / "cross_venue_diamond_replication_001_source_probe_v02"
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
BYBIT_HOSTS = ["https://api.bybit.com", "https://api.bytick.com"]
OKX = "https://www.okx.com"
UA = "CROSS-VENUE-DIAMOND-REPLICATION-001 source-remediation-v02/1.0"
OKX_MIN_INTERVAL_S = 0.30
_last_okx_request = 0.0

# Outcome-blind semantic candidates only; payload archives are never downloaded here.
MODULE_CANDIDATES = [
    "__SOURCE_ENUM_PROBE__",
    "candlestick",
    "candlesticks",
    "candle",
    "kline",
    "fundingRate",
    "funding-rate",
    "funding_rate",
    "funding",
]


def ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


def sha256_json(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def request_json(base: str, params: dict, retries: int = 4, okx: bool = False):
    global _last_okx_request
    if okx:
        elapsed = time.monotonic() - _last_okx_request
        if elapsed < OKX_MIN_INTERVAL_S:
            time.sleep(OKX_MIN_INTERVAL_S - elapsed)
    url = base + "?" + urllib.parse.urlencode(params)
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read()
                if okx:
                    _last_okx_request = time.monotonic()
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if okx:
                _last_okx_request = time.monotonic()
            last = f"HTTP_{e.code}"
            if e.code == 429 and k + 1 < retries:
                time.sleep(1.5 * (k + 1))
                continue
            raise RuntimeError(last)
        except Exception as e:
            if okx:
                _last_okx_request = time.monotonic()
            last = repr(e)
            if k + 1 < retries:
                time.sleep(0.5 * (k + 1))
                continue
            raise RuntimeError(last)
    raise RuntimeError(str(last))


def summary(times: list[int]) -> dict:
    t = sorted(set(times))
    return {
        "count": len(t),
        "min_ts": t[0] if t else None,
        "max_ts": t[-1] if t else None,
        "timestamps_sha256": sha256_json(t),
    }


def contains_anchor(times: list[int], anchor_ms: int) -> bool:
    return anchor_ms in set(times)


def bybit_transport_probe() -> dict:
    result = {"hosts": {}, "classification": None}
    probe_t = ms("2024-01-01T00:00:00Z")
    for host in BYBIT_HOSTS:
        entry = {"host": host}
        try:
            j = request_json(
                host + "/v5/market/kline",
                {
                    "category": "linear",
                    "symbol": "BTCUSDT",
                    "interval": "360",
                    "start": probe_t - 6 * 3600_000,
                    "end": probe_t + 6 * 3600_000,
                    "limit": 10,
                },
                retries=2,
                okx=False,
            )
            entry["retCode"] = j.get("retCode")
            entry["retMsg"] = j.get("retMsg")
            rows = ((j.get("result") or {}).get("list") or [])
            entry["timestamp_count"] = len(rows)
            entry["transport_ok"] = j.get("retCode") == 0 and bool(rows)
        except Exception as e:
            entry["error"] = str(e)
            entry["transport_ok"] = False
        result["hosts"][host] = entry

    if any(v.get("transport_ok") for v in result["hosts"].values()):
        result["classification"] = "BYBIT_TRANSPORT_AVAILABLE"
    elif all(v.get("error") == "HTTP_403" for v in result["hosts"].values()):
        result["classification"] = "BYBIT_SOURCE_BLOCKED_ENVIRONMENT"
    else:
        result["classification"] = "BYBIT_SOURCE_TRANSPORT_UNRESOLVED"
    return result


def okx_candle_probe() -> dict:
    venue = {"symbols": [], "rate_limit_policy_s": OKX_MIN_INTERVAL_S}
    for symbol in SYMBOLS:
        inst = OKX_MAP[symbol]
        item = {"symbol": symbol, "instId": inst, "price_6h": {}, "price_1m": {}, "errors": []}
        for a in ANCHORS:
            t = ms(a)
            for bar, key, after_delta, lim in [
                ("6Hutc", "price_6h", 24 * 3600_000, 20),
                ("1m", "price_1m", 60 * 60_000, 100),
            ]:
                try:
                    j = request_json(
                        OKX + "/api/v5/market/history-candles",
                        {"instId": inst, "bar": bar, "after": t + after_delta, "limit": lim},
                        okx=True,
                    )
                    if j.get("code") != "0":
                        raise RuntimeError(f"OKX_CODE_{j.get('code')}:{j.get('msg')}")
                    times = [int(x[0]) for x in (j.get("data") or [])]
                    item[key][a] = {**summary(times), "anchor_present": contains_anchor(times, t)}
                except Exception as e:
                    item[key][a] = {"anchor_present": False, "error": str(e)}
                    item["errors"].append(f"{bar}:{a}:{e}")
        item["candles_pass"] = (
            not item["errors"]
            and all(v.get("anchor_present") for v in item["price_6h"].values())
            and all(v.get("anchor_present") for v in item["price_1m"].values())
        )
        venue["symbols"].append(item)
    venue["candles_venue_pass"] = all(x["candles_pass"] for x in venue["symbols"])
    return venue


def archive_metadata_shape(data):
    # Keep provider metadata only. Never follow/download file URLs.
    out = []
    for row in data if isinstance(data, list) else []:
        if isinstance(row, dict):
            clean = {}
            for k, v in row.items():
                lk = k.lower()
                if any(tok in lk for tok in ["url", "href", "file", "name", "inst", "begin", "end", "date", "module", "type", "ts"]):
                    clean[k] = v
            out.append(clean)
        else:
            out.append({"type": type(row).__name__})
    return out


def okx_archive_module_discovery() -> dict:
    begin = ms("2024-01-01T00:00:00Z")
    end = ms("2024-02-01T00:00:00Z")
    out = {"probes": [], "accepted_candidates": []}
    for module in MODULE_CANDIDATES:
        rec = {"module": module}
        try:
            j = request_json(
                OKX + "/api/v5/public/market-data-history",
                {
                    "module": module,
                    "instType": "SWAP",
                    "dateAggrType": "1M",
                    "begin": begin,
                    "end": end,
                    "instIdList": "BTC-USDT-SWAP",
                },
                okx=True,
            )
            rec["code"] = j.get("code")
            rec["msg"] = j.get("msg")
            rec["data_count"] = len(j.get("data") or []) if isinstance(j.get("data"), list) else None
            rec["metadata"] = archive_metadata_shape(j.get("data") or [])
            if j.get("code") == "0":
                out["accepted_candidates"].append(module)
        except Exception as e:
            rec["transport_error"] = str(e)
        out["probes"].append(rec)
    return out


def classify_archive_modules(discovery: dict) -> dict:
    # Classification from provider-returned metadata/accepted semantic name only.
    found = {"candlestick_module": None, "funding_module": None}
    for rec in discovery["probes"]:
        if rec.get("code") != "0":
            continue
        text = json.dumps(rec, sort_keys=True).lower()
        m = rec["module"]
        if found["funding_module"] is None and ("fund" in m.lower() or "fund" in text):
            found["funding_module"] = m
        if found["candlestick_module"] is None and any(x in m.lower() for x in ["candle", "kline"]):
            found["candlestick_module"] = m
    return found


def okx_funding_archive_coverage(module: str | None) -> dict:
    out = {"module": module, "symbols": []}
    if not module:
        out["coverage_pass"] = False
        out["classification"] = "OKX_FUNDING_ARCHIVE_MODULE_UNRESOLVED"
        return out

    windows = [
        ("2023-01", "2023-01-01T00:00:00Z", "2023-02-01T00:00:00Z"),
        ("2024-12", "2024-12-01T00:00:00Z", "2025-01-01T00:00:00Z"),
    ]
    for symbol in SYMBOLS:
        inst = OKX_MAP[symbol]
        s = {"symbol": symbol, "instId": inst, "windows": {}, "pass": True}
        for label, b, e in windows:
            try:
                j = request_json(
                    OKX + "/api/v5/public/market-data-history",
                    {
                        "module": module,
                        "instType": "SWAP",
                        "dateAggrType": "1M",
                        "begin": ms(b),
                        "end": ms(e),
                        "instIdList": inst,
                    },
                    okx=True,
                )
                data = j.get("data") or []
                meta = archive_metadata_shape(data)
                ok = j.get("code") == "0" and len(data) > 0
                s["windows"][label] = {
                    "code": j.get("code"),
                    "msg": j.get("msg"),
                    "data_count": len(data) if isinstance(data, list) else None,
                    "metadata": meta,
                    "archive_metadata_present": ok,
                }
                s["pass"] = s["pass"] and ok
            except Exception as ex:
                s["windows"][label] = {"archive_metadata_present": False, "error": str(ex)}
                s["pass"] = False
        out["symbols"].append(s)
    out["coverage_pass"] = all(x["pass"] for x in out["symbols"])
    out["classification"] = "OKX_FUNDING_ARCHIVE_METADATA_PASS" if out["coverage_pass"] else "OKX_FUNDING_ARCHIVE_METADATA_BLOCKED"
    return out


def main() -> int:
    receipt = {
        "lab_id": "CROSS-VENUE-DIAMOND-REPLICATION-001",
        "candidate": "HTF-DONCHIAN-DH-02-HO1-6H",
        "stage": "SOURCE_TRANSPORT_REMEDIATION_V02",
        "outcome_blind": True,
        "signal_calculation_performed": False,
        "return_calculation_performed": False,
        "pnl_calculation_performed": False,
        "archive_payload_opened": False,
        "years_allowed": [2023, 2024],
        "years_forbidden": [2025, 2026],
    }

    receipt["bybit"] = bybit_transport_probe()
    receipt["okx_candles"] = okx_candle_probe()
    discovery = okx_archive_module_discovery()
    receipt["okx_archive_module_discovery"] = discovery
    modules = classify_archive_modules(discovery)
    receipt["okx_archive_binding_candidates"] = modules
    receipt["okx_funding_archive_coverage"] = okx_funding_archive_coverage(modules["funding_module"])

    receipt["okx_exact_source_ready"] = (
        receipt["okx_candles"]["candles_venue_pass"]
        and receipt["okx_funding_archive_coverage"]["coverage_pass"]
    )
    receipt["bybit_exact_source_ready"] = receipt["bybit"]["classification"] == "BYBIT_TRANSPORT_AVAILABLE"
    receipt["classification"] = (
        "OKX_SOURCE_READY_BYBIT_ENVIRONMENT_BLOCKED"
        if receipt["okx_exact_source_ready"] and receipt["bybit"]["classification"] == "BYBIT_SOURCE_BLOCKED_ENVIRONMENT"
        else "SOURCE_REMEDIATION_PARTIAL_OR_BLOCKED"
    )
    receipt["fingerprint"] = sha256_json(receipt)

    p = OUT / "CROSS_VENUE_DIAMOND_REPLICATION_001_SOURCE_REMEDIATION_RECEIPT_V0.2.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(json.dumps({
        "classification": receipt["classification"],
        "bybit": receipt["bybit"]["classification"],
        "okx_candles_pass": receipt["okx_candles"]["candles_venue_pass"],
        "okx_funding_archive": receipt["okx_funding_archive_coverage"]["classification"],
        "okx_module_candidates": receipt["okx_archive_binding_candidates"],
        "fingerprint": receipt["fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
