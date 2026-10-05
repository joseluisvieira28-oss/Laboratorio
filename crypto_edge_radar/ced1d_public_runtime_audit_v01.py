#!/usr/bin/env python3
"""Read-only audit of the canonical public Crypto Edge Radar CED1D runtime."""
from __future__ import annotations
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE="https://crypto-edge-radar-v05-canary.onrender.com"
OUT=Path("artifacts/ced1d/public_runtime_audit_v01")
UA="CryptoLab-CED1D-PublicRuntimeAudit/0.1"

def sha(b): return hashlib.sha256(b).hexdigest()

def get(path):
    r=requests.get(BASE+path,headers={"User-Agent":UA,"Accept":"application/json"},timeout=60)
    r.raise_for_status()
    return r, r.json()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sr,state=get("/api/state")
    dr,diamond=get("/api/diamond")
    ced=state.get("ced1d_render_shadow") or {}
    board=(diamond.get("candidates") or {}).get("CED1D-0031") or diamond.get("CED1D-0031") or {}
    metrics=ced.get("metrics") or {}
    receipt={
      "audit_id":"CED1D-0031-PUBLIC-RUNTIME-AUDIT-V0.1",
      "checked_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "public_service":BASE,
      "state_http":sr.status_code,
      "state_sha256":sha(sr.content),
      "diamond_http":dr.status_code,
      "diamond_sha256":sha(dr.content),
      "health":state.get("health"),
      "ced1d_render_shadow":ced,
      "ced1d_diamond_board":board,
      "summary":{
        "runtime_status":ced.get("status"),
        "resolved_trade_events":metrics.get("resolved_trade_events"),
        "complete_utc_signal_weeks":metrics.get("complete_utc_signal_weeks"),
        "routing":metrics.get("routing"),
        "latest_mature_signal_day":ced.get("through_signal_day") or ced.get("latest_mature_signal_day"),
        "metrics_preserved_from_through_signal_day":ced.get("metrics_preserved_from_through_signal_day"),
        "bookdepth_snapshot_coverage":metrics.get("bookdepth_snapshot_coverage"),
        "bookdepth_capacity_coverage":metrics.get("bookdepth_capacity_coverage"),
        "execution_complete_pairs":metrics.get("execution_complete_pairs"),
        "execution_mean_base_bps":metrics.get("execution_mean_base_bps"),
        "reference_base_mean_bps":metrics.get("reference_base_mean_bps"),
        "reference_base_pf":metrics.get("reference_base_pf"),
        "reference_stress_mean_bps":metrics.get("reference_stress_mean_bps"),
        "verdict_allowed_now":board.get("verdict_allowed_now"),
        "board_state":board.get("state") or board.get("classification"),
      },
      "authenticated_exchange_api_used":False,
      "account_reads":False,
      "orders_created":False,
      "wallet_used":False,
      "exchange_mutation_performed":False,
      "live_trading_authorized":False
    }
    (OUT/"CED1D_0031_PUBLIC_RUNTIME_AUDIT_V01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print("CED1D_SUMMARY")
    print(json.dumps(receipt["summary"],indent=2,sort_keys=True))
    print("DIAMOND_BOARD")
    print(json.dumps(diamond,indent=2,sort_keys=True))
if __name__=="__main__":
    main()
