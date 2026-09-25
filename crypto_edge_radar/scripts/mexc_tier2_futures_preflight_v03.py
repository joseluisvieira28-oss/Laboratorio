from __future__ import annotations

import argparse,hashlib,json,os
from pathlib import Path
from typing import Any

from radar.market import MEXCFuturesPublicFeed
from radar.mexc_auth_readonly import MEXCCredentials,MEXCFuturesAuthenticatedReadOnlyClient
from radar.mexc_authenticated_preflight import run_authenticated_preflight

def _current_equity(client:MEXCFuturesAuthenticatedReadOnlyClient)->float:
    rows=client.assets()
    row=next((r for r in rows if str(r.get("currency","")).upper()=="USDT"),None)
    if row is None: raise RuntimeError("USDT_ASSET_MISSING")
    value=float(row.get("equity",0) or 0)
    if value<=0: raise RuntimeError("FUTURES_EQUITY_NOT_POSITIVE")
    return value

def run(*,binding_sha256:str)->dict[str,Any]:
    creds=MEXCCredentials.from_env()
    actual_hash=hashlib.sha256(creds.api_key.encode()).hexdigest()
    if not binding_sha256 or actual_hash.lower()!=binding_sha256.lower():
        return {
            "preflight_id":"MEXC_TIER2_FUTURES_PREFLIGHT_V0.3","status":"FAIL_CLOSED","pass":False,
            "blockers":["LOCAL_API_KEY_BINDING_MISMATCH"],"security":{"exchange_mutation_performed":False,"order_created":False}
        }
    client=MEXCFuturesAuthenticatedReadOnlyClient(creds)
    equity=_current_equity(client)
    out=run_authenticated_preflight(private_client=client,public_feed=MEXCFuturesPublicFeed(timeout=10),expected_equity_usdt=equity,expected_equity_tolerance_usdt=0.01)
    out["preflight_id"]="MEXC_TIER2_FUTURES_PREFLIGHT_V0.3"
    out["automation_identity_binding"]={
        "mode":"LOCAL_DPAPI_API_KEY_SHA256_BINDING",
        "api_key_sha256_match":True,
        "manual_equity_prompt_required":False,
        "equity_binding_role":"same-session sanity read only"
    }
    # The legacy ETF 0.1% diagnostic remains historical context only and does not
    # control Tier-2 V0.3 eligibility.
    out["tier2_policy"]={
        "policy_id":"TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24",
        "max_notional_usdt":10.0,
        "old_etf_0_1pct_candidate_feasibility_controls_v03":False
    }
    return out

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--binding-file",default=str(Path.home()/".crypto_edge_radar"/"mexc_account_binding.json"))
    ap.add_argument("--out",default="mexc_tier2_futures_preflight_receipt.json")
    args=ap.parse_args()
    try:
        binding=json.loads(Path(args.binding_file).read_text(encoding="utf-8"))
        expected=str(binding["api_key_sha256"])
        result=run(binding_sha256=expected)
    except Exception as exc:
        result={"preflight_id":"MEXC_TIER2_FUTURES_PREFLIGHT_V0.3","status":"FAIL_CLOSED","pass":False,"blockers":["TIER2_FUTURES_PREFLIGHT_RUNTIME_EXCEPTION"],"error":f"{type(exc).__name__}:{exc}","security":{"exchange_mutation_performed":False,"order_created":False}}
    Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":result.get("status"),"pass":result.get("pass"),"blockers":result.get("blockers",[]),"out":str(Path(args.out).resolve())},indent=2))
    return 0 if result.get("pass") is True else 2

if __name__=="__main__": raise SystemExit(main())
