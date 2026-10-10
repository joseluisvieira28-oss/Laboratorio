#!/usr/bin/env python3
"""HYPE-BUYBACK-FLOW-001 — preregistered 0-dollar GET-only historical-source transport census.
No HYPE price or outcome access, no credential use, no paid/unknown methods."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from urllib import error, request

AF = "0x" + "fe" * 20
assert len(AF) == 42
LIMIT = 1572864
OUT = Path("research/hype_buyback_flow_001/receipts/free_90d_v03")
OUT.mkdir(parents=True, exist_ok=True)
TARGETS = [
    ("hypedexer_export_public_landing", "https://trade-export.hypedexer.com/"),
    ("hypedexer_public_openapi", "https://api.hypedexer.com/openapi.json"),
    ("hypedexer_public_spot_fills_no_key", "https://api.hypedexer.com/fills/spot/user/" + AF),
    ("asxn_public_buyback_daily_proxy", "https://api-data.asxn.xyz/api/data/hl-buybacks"),
]

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

OPENER = request.build_opener(NoRedirect)

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def describe_json(name, obj):
    out={}
    if name == "hypedexer_public_openapi" and isinstance(obj, dict):
        paths=obj.get("paths", {})
        route=paths.get("/fills/spot/user/{user_address}", {})
        out={
            "openapi_version":obj.get("openapi"),
            "route_documented":isinstance(route, dict) and bool(route),
            "route_methods":list(route.keys()) if isinstance(route, dict) else [],
            "route_security_described": route.get("get",{}).get("security") if isinstance(route,dict) else None,
            "global_security_described":bool(obj.get("security")),
            "route_query_parameters":[p.get("name") for p in route.get("get",{}).get("parameters",[]) if isinstance(p,dict)] if isinstance(route,dict) else [],
            "auth_scheme_names":list(obj.get("components",{}).get("securitySchemes",{}).keys()),
        }
    elif name == "asxn_public_buyback_daily_proxy":
        if isinstance(obj, list):
            out={"response_type":"list", "row_count":len(obj), "first_record_field_names":sorted(obj[0].keys()) if obj and isinstance(obj[0],dict) else []}
            dates=[str(x.get("date"))[:10] for x in obj if isinstance(x, dict) and isinstance(x.get("date"),str)]
            out["first_date"]=min(dates) if dates else None
            out["last_date"]=max(dates) if dates else None
            out["rows_with_trade_id"]=sum(any(k in x for k in ("tid","trade_id","hash","tx_hash")) for x in obj if isinstance(x,dict))
            out["daily_aggregate_NOT_causal_fill_archive"]=True
        else:
            out={"response_type":type(obj).__name__,"is_exact_fill_archive":False}
    elif name=="hypedexer_public_spot_fills_no_key":
        if isinstance(obj,dict):
            out={"response_type":"dict","field_names":sorted(obj.keys())[:20]}
        elif isinstance(obj,list):
            out={"response_type":"list","returned_rows":len(obj)}
        else:
            out={"response_type":type(obj).__name__}
        out["not_validated_90d_corpus"]=True
    return out

def main():
    summary={
        "candidate_id":"HYPE-BUYBACK-FLOW-001", "phase":"SOURCE_ONLY",
        "trading_authority":"NONE", "price_outcomes_read":0,
        "orders":0,"account_private_reads":0,"api_key_used":False,
        "paid_data":0,"s3_requests":0,
        "run_id":os.environ.get("GITHUB_RUN_ID","LOCAL"),
        "source_commit":os.environ.get("GITHUB_SHA","UNSET"),
        "status":"SOURCE_BLOCKED_90D_PENDING_EVIDENCE",
        "probe_started_utc":utcnow(), "results":[]
    }
    for name,url in TARGETS:
        rec={"candidate":name,"url":url,
             "request_method":"GET","authorization":"NONE",
             "started_utc":utcnow()}
        tic=time.monotonic()
        try:
            req=request.Request(url,headers={"User-Agent":"CryptoLab-HYPE-SourceOnly/0.3","Accept":"application/json,text/html,*/*"})
            with OPENER.open(req,timeout=16) as response:
                payload=response.read(LIMIT+1)
                rec["status_code"]=response.status
                rec["content_type"]=response.headers.get("Content-Type","")
            rec["bytes_returned"]=len(payload)
            rec["truncated"]=len(payload)>LIMIT
            rec["sha256_raw"]=hashlib.sha256(payload).hexdigest()
            if not rec["truncated"]:
                (OUT/(name+".response")).write_bytes(payload)
                if "json" in rec["content_type"].lower() or payload.startswith((b"[",b"{")):
                    try: rec["schema_diagnostic"]=describe_json(name,json.loads(payload))
                    except (ValueError,UnicodeDecodeError,TypeError): rec["json_valid"]=False
                if name=="hypedexer_export_public_landing":
                    s=payload.decode("utf-8","replace").lower()
                    rec["advertised_export_form"]=("export" in s and "wallet" in s) or "no limits" in s
                    rec["html_has_login_text"]="login" in s or "log in" in s
                    rec["client_script_assets_present"]="<script" in s
            else: rec["reason"]="RESPONSE_GT_1_5_MIB_NO_FULL_SCHEMA_CLAIM"
        except error.HTTPError as exc:
            ebody=exc.read(1024)
            rec.update({"status_code":exc.code,"error_sha256":hashlib.sha256(ebody).hexdigest(),
                       "error_short":ebody.decode("utf-8","replace")[:150]})
            if exc.code in (401,403):rec["source_access"]="AUTH_REQUIRED_OR_DENIED"
        except (error.URLError, TimeoutError, OSError, ValueError) as exc:
            rec["transport_error_type"]=type(exc).__name__
            rec["source_access"]="UNVERIFIED"
        rec["elapsed_ms"]=round((time.monotonic()-tic)*1000,2)
        rec["finished_utc"]=utcnow()
        summary["results"].append(rec)
    summary["probe_finished_utc"]=utcnow()
    (OUT/"SOURCE_90D_DISCOVERY_V03_RECEIPT.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
