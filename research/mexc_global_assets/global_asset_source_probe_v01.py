#!/usr/bin/env python3
"""
MEXC Global Asset Lab V0.1 — public/no-auth source probe.

Research only.
- No API keys.
- No private endpoints.
- No account reads.
- No orders or exchange mutation.
- Preserves raw response bytes + SHA-256.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://api.mexc.com"
ASSETS = {
    "NAS100": "NAS100_USDT",
    "SP500": "SPX500_USDT",
    "NVIDIA": "NVIDIA_USDT",
    "GOLD": "XAU_USDT",
}
OUT = Path("artifacts/mexc_global_assets/source_gate_v01")
UA = "CryptoLab-ResearchOnly-MEXC-GlobalAssets/0.1"
INTERVAL = "Min5"
LOOKBACK_DAYS = 14
STEP = 300

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def get_raw(path: str, params=None, retries=4):
    url = BASE + path
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30, headers={"User-Agent": UA})
            raw = r.content
            meta = {
                "url": r.url,
                "status_code": r.status_code,
                "captured_at_utc": utcnow(),
                "sha256": sha256_bytes(raw),
                "bytes": len(raw),
            }
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}: {raw[:300]!r}")
            j = r.json()
            if not isinstance(j, dict) or j.get("success") is not True:
                raise RuntimeError(f"non-success payload: {j}")
            return raw, j, meta
        except Exception as e:
            last = e
            time.sleep(0.8 * (i + 1))
    raise last

def write_raw(name: str, raw: bytes, meta: dict):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    p.write_bytes(raw)
    (OUT / f"{name}.meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")

def parse_kline(j):
    d = j.get("data") or {}
    rows = []
    for t, o, c, h, l in zip(
        d.get("time") or [],
        d.get("open") or [],
        d.get("close") or [],
        d.get("high") or [],
        d.get("low") or [],
    ):
        try:
            rows.append({
                "bucket_start": int(t),
                "observable_at": int(t) + STEP,
                "open": float(o),
                "close": float(c),
                "high": float(h),
                "low": float(l),
            })
        except Exception:
            continue
    return rows

def main():
    if any(k for k in os.environ if k.upper() in {"MEXC_API_KEY", "MEXC_SECRET_KEY", "API_KEY", "SECRET_KEY"}):
        print("FAIL_CLOSED: credential-like environment variable detected", file=sys.stderr)
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    start = now - LOOKBACK_DAYS * 86400
    report = {
        "lab": "MEXC_GLOBAL_ASSET_SOURCE_GATE_V0_1",
        "captured_at_utc": utcnow(),
        "base_url": BASE,
        "auth_used": False,
        "private_endpoints_used": False,
        "account_reads": False,
        "orders": False,
        "exchange_mutation": False,
        "interval": INTERVAL,
        "lookback_days": LOOKBACK_DAYS,
        "assets": {},
    }

    all_structure = True
    for asset, symbol in ASSETS.items():
        rec = {"symbol": symbol}
        try:
            raw, j, meta = get_raw("/api/v1/contract/detail", {"symbol": symbol})
            write_raw(f"{asset}_detail.json", raw, meta)
            data = j.get("data")
            if isinstance(data, list):
                match = next((x for x in data if x.get("symbol") == symbol), None)
            elif isinstance(data, dict):
                match = data if data.get("symbol") == symbol else None
            else:
                match = None
            if not match:
                raise RuntimeError("contract detail missing exact symbol")
            rec["detail"] = {
                "sha256": meta["sha256"],
                "apiAllowed": match.get("apiAllowed"),
                "futureType": match.get("futureType"),
                "contractSize": match.get("contractSize"),
                "minLeverage": match.get("minLeverage"),
                "maxLeverage": match.get("maxLeverage"),
            }

            raw_c, jc, mc = get_raw(
                f"/api/v1/contract/kline/{symbol}",
                {"interval": INTERVAL, "start": start, "end": now},
            )
            write_raw(f"{asset}_contract_kline.json", raw_c, mc)
            raw_i, ji, mi = get_raw(
                f"/api/v1/contract/kline/index_price/{symbol}",
                {"interval": INTERVAL, "start": start, "end": now},
            )
            write_raw(f"{asset}_index_kline.json", raw_i, mi)

            crows = parse_kline(jc)
            irows = parse_kline(ji)
            cm = {r["observable_at"]: r["close"] for r in crows}
            im = {r["observable_at"]: r["close"] for r in irows}
            overlap = sorted(set(cm) & set(im))
            if not overlap:
                raise RuntimeError("zero timestamp-overlap between contract and index klines")

            latest = overlap[-1]
            age_sec = now - latest
            rec["market_data"] = {
                "contract_rows": len(crows),
                "index_rows": len(irows),
                "overlap_rows": len(overlap),
                "first_overlap_utc": datetime.fromtimestamp(overlap[0], tz=timezone.utc).isoformat(),
                "last_overlap_utc": datetime.fromtimestamp(latest, tz=timezone.utc).isoformat(),
                "last_overlap_age_sec": age_sec,
                "contract_raw_sha256": mc["sha256"],
                "index_raw_sha256": mi["sha256"],
                "timestamp_alignment": "PASS",
                "freshness_note": "age may be large during documented market-close periods",
            }
            rec["status"] = "STRUCTURE_PASS"
        except Exception as e:
            rec["status"] = "SOURCE_FAIL"
            rec["error"] = repr(e)
            all_structure = False
        report["assets"][asset] = rec

    report["source_structure_pass"] = all_structure
    report["verdict"] = "MEXC_MARKET_SOURCE_PASS" if all_structure else "SOURCE_BLOCKED"
    report["outcomes_opened"] = 0
    report["crossvenue_realtime_reference"] = "NOT_ACTIVATED"
    report["live_trading_authorized"] = False

    rp = OUT / "GLOBAL_ASSET_SOURCE_GATE_RECEIPT_V01.json"
    rp.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "verdict": report["verdict"],
        "assets": {k: v["status"] for k, v in report["assets"].items()},
        "receipt": str(rp),
        "outcomes_opened": 0,
    }, indent=2, sort_keys=True))
    return 0 if all_structure else 3

if __name__ == "__main__":
    raise SystemExit(main())
