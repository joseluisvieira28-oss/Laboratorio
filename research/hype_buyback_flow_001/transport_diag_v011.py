#!/usr/bin/env python3
"""One-shot predeclared transport diagnostic, public sources ONLY; never evaluates returns."""
import datetime as dt
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://api.hyperliquid.xyz/info"
AF = "0xfefefefefefefefefefefefefefefefefefefe"
OUT = Path("research/hype_buyback_flow_001/receipts/transport_v011")
OUT.mkdir(parents=True, exist_ok=True)
now_ms = int(time.time() * 1000)
requests = [
    ("A_af_time_minimal", {"type": "userFillsByTime", "user": AF, "startTime": now_ms-3_600_000}),
    ("B_af_userFills", {"type": "userFills", "user": AF}),
    ("C_recent_hype_market", {"type": "recentTrades", "coin": "@107"}),
]
result = {
    "candidate": "HYPE-BUYBACK-FLOW-001",
    "phase": "SOURCE_ONLY", "status": "SOURCE_BLOCKED",
    "trading_authority": "NONE", "outcome_reads": 0, "requests": [],
    "run_id": os.getenv("GITHUB_RUN_ID", "LOCAL"),
    "commit": os.getenv("GITHUB_SHA", "UNSET"),
}

for name, payload in requests:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    t0 = time.monotonic()
    meta = {"route": name, "request_sha256": hashlib.sha256(body).hexdigest(), "started_at_utc": started}
    try:
        req = urllib.request.Request(URL, data=body, headers={
            "Content-Type": "application/json", "User-Agent": "CryptoLab-HYPE-SourceOnlyTransport/0.1.1"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read(8_000_001)
            meta["http_status"] = r.status
        if len(raw) > 8_000_000:
            raise RuntimeError("MAX_RESPONSE_BYTES_EXCEEDED")
        (OUT / (name + ".json")).write_bytes(raw)
        meta["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        decoded = json.loads(raw)
        meta["json_array"] = isinstance(decoded, list)
        meta["count"] = len(decoded) if isinstance(decoded, list) else None
        if name == "C_recent_hype_market" and isinstance(decoded, list):
            buyers = []
            with_user = 0
            for trade in decoded:
                if not isinstance(trade, dict):
                    continue
                users = trade.get("users")
                if isinstance(users, list) and len(users) == 2 and all(isinstance(x, str) for x in users):
                    with_user += 1
                    if users[0].lower() == AF:
                        buyers.append((trade.get("time"), trade.get("coin"), trade.get("tid")))
            meta["trades_with_buyer_seller_addresses"] = with_user
            meta["public_trades_buyer_exactly_AF"] = len(buyers)
            meta["AF_purchases_are_a_complete_source"] = False
    except urllib.error.HTTPError as e:
        raw = e.read(1200)
        meta["http_status"] = e.code
        meta["public_error"] = raw.decode("utf-8", errors="replace")[:300]
        meta["error_sha256"] = hashlib.sha256(raw).hexdigest()
    except Exception as e:
        meta["probe_error_type"] = type(e).__name__
    meta["latency_ms"] = round((time.monotonic()-t0)*1000, 2)
    meta["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    result["requests"].append(meta)
result["checked_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
(OUT / "TRANSPORT_RECEIPT_V011.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
