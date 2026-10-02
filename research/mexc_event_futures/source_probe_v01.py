#!/usr/bin/env python3
import json, os, sys, time
from datetime import datetime, timezone
import requests

BASE = "https://contract.mexc.com"
SYMBOLS = {
    "BTCUSDT": "BTC_USDT",
    "ETHUSDT": "ETH_USDT",
    "NVDAUSDT": "NVIDIA_USDT",
    "MUUSDT": "MUSTOCK_USDT",
    "SPCXUSDT": "SPCXSTOCK_USDT",
}
INTERVALS = ["Min1", "Min5", "Min15", "Min60", "Hour4", "Day1"]

def get_json(path, params=None, timeout=20):
    url = BASE + path
    r = requests.get(url, params=params, timeout=timeout)
    return {"url": r.url, "status_code": r.status_code, "json": r.json() if r.content else None}

def ok_payload(resp):
    j = resp.get("json")
    return resp.get("status_code") == 200 and isinstance(j, dict) and j.get("success") is True

def main():
    now = datetime.now(timezone.utc)
    end = int(now.timestamp())
    start = end - 3 * 24 * 3600
    out = {
        "lab": "MEXC_EVENT_FUTURES_V0.1",
        "generated_at_utc": now.isoformat(),
        "purpose": "source-availability only; no strategy outcome interpretation",
        "symbols": {},
    }

    for display, symbol in SYMBOLS.items():
        row = {"display": display, "proxy_symbol": symbol, "intervals": {}}
        try:
            detail = get_json("/api/v1/contract/detail", {"symbol": symbol})
            row["detail"] = {
                "ok": ok_payload(detail),
                "status_code": detail["status_code"],
                "url": detail["url"],
            }
        except Exception as e:
            row["detail"] = {"ok": False, "error": repr(e)}

        try:
            idx = get_json(f"/api/v1/contract/index_price/{symbol}")
            row["index_price"] = {
                "ok": ok_payload(idx),
                "status_code": idx["status_code"],
                "url": idx["url"],
                "timestamp": ((idx.get("json") or {}).get("data") or {}).get("timestamp"),
            }
        except Exception as e:
            row["index_price"] = {"ok": False, "error": repr(e)}

        for interval in INTERVALS:
            try:
                kl = get_json(
                    f"/api/v1/contract/kline/index_price/{symbol}",
                    {"interval": interval, "start": start, "end": end},
                )
                data = ((kl.get("json") or {}).get("data") or {})
                times = data.get("time") or []
                closes = data.get("close") or []
                row["intervals"][interval] = {
                    "ok": ok_payload(kl) and len(times) > 0 and len(times) == len(closes),
                    "status_code": kl["status_code"],
                    "rows": len(times),
                    "first_time": times[0] if times else None,
                    "last_time": times[-1] if times else None,
                    "url": kl["url"],
                }
            except Exception as e:
                row["intervals"][interval] = {"ok": False, "error": repr(e)}
            time.sleep(0.12)
        out["symbols"][display] = row

    all_checks = []
    for row in out["symbols"].values():
        all_checks.append(bool(row.get("detail", {}).get("ok")))
        all_checks.append(bool(row.get("index_price", {}).get("ok")))
        all_checks.extend(bool(v.get("ok")) for v in row.get("intervals", {}).values())

    out["source_gate"] = "PASS" if all(all_checks) else ("PARTIAL_PASS" if any(all_checks) else "BLOCKED")
    out["exact_event_futures_backtest"] = "BLOCKED"
    out["exact_blockers"] = [
        "No official Event Futures API trading support.",
        "No authoritative historical payout-at-entry endpoint identified.",
        "No proof yet that standard-futures index-price history is identical to Event Futures entry/settlement index.",
        "No authoritative historical Event Futures contract timestamp/rounding ledger identified.",
    ]

    os.makedirs("artifacts/mexc_event_futures", exist_ok=True)
    path = "artifacts/mexc_event_futures/source_probe_v01.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print(json.dumps(out, indent=2, sort_keys=True))
    print(f"WROTE {path}")

if __name__ == "__main__":
    main()
