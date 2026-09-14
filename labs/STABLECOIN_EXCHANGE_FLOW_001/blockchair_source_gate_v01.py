#!/usr/bin/env python3
"""Outcome-blind Blockchair feasibility gate for the frozen Binance USDT basket.

No BTC market data, returns, PnL, 2025, or 2026 data are requested.
"""
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
# Binance publication snapshot was already public at block ~15.935m. This probe begins after it.
START_BLOCK = 15935900
# Verified 2024-12-31 00:59 UTC block; deliberately stops inside 2024 and cannot touch 2025.
END_BLOCK = 21519027
OUT = Path("artifacts/stablecoin_exchange_flow_blockchair_gate_v01")
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
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-SEF-research-only/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            txt = raw.decode("utf-8", errors="replace")
            try:
                payload = json.loads(txt)
            except Exception:
                payload = None
            return {
                "url": url,
                "status": r.status,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "json": payload,
                "text_prefix": txt[:1000],
            }
    except urllib.error.HTTPError as e:
        raw = e.read()
        return {
            "url": url,
            "status": e.code,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "json": None,
            "text_prefix": raw.decode("utf-8", errors="replace")[:1000],
        }
    except Exception as e:
        return {"url": url, "status": None, "error": f"{type(e).__name__}:{e}"}


def endpoint(direction: str) -> str:
    if direction not in {"recipient", "sender"}:
        raise ValueError(direction)
    q = f"token_address({USDT}),{direction}({PROBE_ADDRESS}),block_id({START_BLOCK}..{END_BLOCK})"
    params = urllib.parse.urlencode({"q": q, "limit": "5", "s": "block_id(asc)"})
    return "https://api.blockchair.com/ethereum/erc-20/transactions?" + params


def rows(probe: dict) -> list:
    p = probe.get("json")
    if isinstance(p, dict) and isinstance(p.get("data"), list):
        return p["data"]
    return []


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not AUTHORITY.exists():
        raise SystemExit("FROZEN_REMEDIATION_AUTHORITY_MISSING")

    probes = {
        "inbound": fetch(endpoint("recipient")),
        "outbound": fetch(endpoint("sender")),
    }
    statuses = [p.get("status") for p in probes.values()]
    counts = {k: len(rows(v)) for k, v in probes.items()}

    if any(s in (401, 402, 403, 429, 430, 434, 435, 436, 437) for s in statuses):
        classification = "SOURCE_AUTH_BLOCKED"
        reason = "Blockchair protected query is rate/auth/plan blocked without additional access"
    elif all(s == 200 for s in statuses) and sum(counts.values()) > 0:
        classification = "SOURCE_FEASIBILITY_PASS"
        reason = "protected-period ERC-20 USDT rows are queryable for the frozen public Binance basket"
    elif all(s == 200 for s in statuses):
        classification = "DATA_FAILURE"
        reason = "queries executed but returned no matching protected-period USDT rows for probe address"
    else:
        classification = "TECHNICAL_FAILURE_PREOUTCOME"
        reason = f"unexpected Blockchair statuses: {statuses}"

    receipt = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "classification": classification,
        "reason": reason,
        "git_head": git_head(),
        "authority_sha256": sha256_file(AUTHORITY),
        "source": "Blockchair Ethereum ERC-20 transactions",
        "token": USDT,
        "probe_address": PROBE_ADDRESS,
        "start_block": START_BLOCK,
        "end_block": END_BLOCK,
        "matched_rows": counts,
        "access_2025": False,
        "access_2026": False,
        "btc_market_data_accessed": False,
        "returns_computed": False,
        "pnl_computed": False,
        "probes": probes,
    }
    (OUT / "SOURCE_GATE_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
