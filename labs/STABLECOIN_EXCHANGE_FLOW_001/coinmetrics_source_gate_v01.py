#!/usr/bin/env python3
"""Outcome-blind source/provenance gate for STABLECOIN-EXCHANGE-FLOW-001.

No BTC price, return, PnL, 2025, or 2026 data is requested or computed.
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
MVE_ID = "SEF-USDT-EXFLOW-1D-001"
START = "2021-01-01"
END = "2024-12-31"
METRICS = "FlowInExNtv,FlowOutExNtv"
OUT = Path("artifacts/stablecoin_exchange_flow_source_gate_v01")
PROTOCOL = Path("labs/STABLECOIN_EXCHANGE_FLOW_001/PRE_SOURCE_PROTOCOL_V0.1.md")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return os.environ.get("GITHUB_SHA")


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-STABLECOIN-EXCHANGE-FLOW-001/0.1 research-only"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            text = raw.decode("utf-8", errors="replace")
            payload = None
            try:
                payload = json.loads(text)
            except Exception:
                pass
            return {"url": url, "status": r.status, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "json": payload, "text_prefix": text[:500]}
    except urllib.error.HTTPError as e:
        raw = e.read()
        return {"url": url, "status": e.code, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "json": None, "text_prefix": raw.decode("utf-8", errors="replace")[:500]}
    except Exception as e:
        return {"url": url, "status": None, "error": f"{type(e).__name__}:{e}"}


def ts_url(host: str) -> str:
    q = urllib.parse.urlencode({
        "assets": "usdt",
        "metrics": METRICS,
        "frequency": "1d",
        "start_time": START,
        "end_time": END,
        "page_size": "10",
        "paging_from": "start",
    })
    return f"{host}/v4/timeseries/asset-metrics?{q}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not PROTOCOL.exists():
        raise SystemExit("FROZEN_PROTOCOL_MISSING")

    probes = {
        "community_timeseries": get(ts_url("https://community-api.coinmetrics.io")),
        "pro_timeseries_no_key": get(ts_url("https://api.coinmetrics.io")),
        "community_reference_metrics": get("https://community-api.coinmetrics.io/v4/reference-data/asset-metrics?metrics=FlowInExNtv,FlowOutExNtv&page_size=20"),
    }

    # Source access classification comes before any market outcome access.
    statuses = [probes[k].get("status") for k in ("community_timeseries", "pro_timeseries_no_key")]
    community = probes["community_timeseries"]
    rows = []
    if community.get("status") == 200 and isinstance(community.get("json"), dict):
        rows = community["json"].get("data") or []

    if all(s in (401, 403) for s in statuses if s is not None) and not rows:
        classification = "SOURCE_AUTH_BLOCKED"
        access_reason = "protected historical exchange-flow metrics require authorization"
    elif community.get("status") != 200 or not rows:
        classification = "DATA_FAILURE"
        access_reason = "community route did not return usable protected historical rows"
    else:
        # Even numeric access is not enough for this lab: current reconstructed exchange
        # address histories can be revised when new addresses are discovered. No provider
        # point-in-time snapshot/version evidence is established by this gate.
        classification = "SOURCE_PIT_BLOCKED"
        access_reason = "numeric history accessible but point-in-time exchange-address observability not established"

    receipt = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "classification": classification,
        "reason": access_reason,
        "git_head": git_head(),
        "protocol_sha256": sha256_file(PROTOCOL),
        "source_asset": "usdt",
        "source_metrics": ["FlowInExNtv", "FlowOutExNtv"],
        "protected_start": START,
        "protected_end": END,
        "access_2025": False,
        "access_2026": False,
        "btc_market_data_accessed": False,
        "returns_computed": False,
        "pnl_computed": False,
        "point_in_time_provenance_defended": False,
        "probes": probes,
    }
    (OUT / "SOURCE_GATE_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
