#!/usr/bin/env python3
"""Outcome-blind daily aggregation feasibility gate for Binance public USDT basket."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

LAB_ID = "STABLECOIN-EXCHANGE-FLOW-001"
MVE_ID = "SEF-BINANCE-PUBLIC-USDT-ETH-1D-001"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
PROBE_ADDRESS = "0x28c6c06298d514db089934071355e5743bf21d60"
START_TIME = "2022-11-11 00:00:00"
END_TIME = "2024-12-31 23:59:59"
OUT = Path("artifacts/stablecoin_exchange_flow_aggregation_gate_v01")
AUTHORITY = Path("labs/STABLECOIN_EXCHANGE_FLOW_001/SOURCE_REMEDIATION_001_BINANCE_PUBLIC_BASKET.md")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return os.environ.get("GITHUB_SHA")


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-SEF-aggregation-probe/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            txt = raw.decode("utf-8", errors="replace")
            try:
                payload = json.loads(txt)
            except Exception:
                payload = None
            return {"url": url, "status": r.status, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "json": payload, "text_prefix": txt[:1000]}
    except urllib.error.HTTPError as e:
        raw = e.read()
        return {"url": url, "status": e.code, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "json": None, "text_prefix": raw.decode("utf-8", errors="replace")[:1000]}
    except Exception as e:
        return {"url": url, "status": None, "error": f"{type(e).__name__}:{e}"}


def endpoint(direction: str) -> str:
    q = f"token_address({USDT}),{direction}({PROBE_ADDRESS}),time({START_TIME}..{END_TIME})"
    params = urllib.parse.urlencode({"q": q, "a": "date,sum(value),count()", "limit": "1000", "s": "date(asc)"})
    return "https://api.blockchair.com/ethereum/erc-20/transactions?" + params


def data_rows(p: dict) -> list:
    j = p.get("json")
    return j.get("data", []) if isinstance(j, dict) and isinstance(j.get("data"), list) else []


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not AUTHORITY.exists():
        raise SystemExit("AUTHORITY_MISSING")
    probes = {"inbound": fetch(endpoint("recipient")), "outbound": fetch(endpoint("sender"))}
    counts = {k: len(data_rows(v)) for k, v in probes.items()}
    statuses = [v.get("status") for v in probes.values()]

    if all(s == 200 for s in statuses) and all(n > 0 for n in counts.values()):
        classification = "DAILY_AGGREGATION_PASS"
        reason = "Blockchair can return protected daily USDT sums for both directions"
    elif any(s in (401, 402, 403, 429, 430, 434, 435, 436, 437) for s in statuses):
        classification = "SOURCE_AUTH_BLOCKED"
        reason = "daily aggregation requires unavailable rate/auth/plan access"
    else:
        classification = "DATA_FAILURE"
        reason = f"daily aggregation unusable statuses={statuses} rows={counts}"

    receipt = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "classification": classification,
        "reason": reason,
        "git_head": git_head(),
        "authority_sha256": sha256_file(AUTHORITY),
        "start_time": START_TIME,
        "end_time": END_TIME,
        "probe_address": PROBE_ADDRESS,
        "daily_rows": counts,
        "access_2025": False,
        "access_2026": False,
        "btc_market_data_accessed": False,
        "returns_computed": False,
        "pnl_computed": False,
        "probes": probes,
    }
    (OUT / "AGGREGATION_GATE_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
