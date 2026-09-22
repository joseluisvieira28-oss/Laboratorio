#!/usr/bin/env python3
import hashlib, json, subprocess, urllib.parse
from pathlib import Path

URL="https://data.api.drift.trade/playground/json"
MAX_BYTES=25*1024*1024
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_DATA_API_SCHEMA_TRANSPORT_REMEDIATION_RECEIPT_V0.2.json")
TMP=Path("drift_openapi_schema_v02.json")

base={
  "schema_version":"0.2",
  "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "schema_url":URL,
  "event_rows":False,
  "liquidation_rows":False,
  "prices":False,
  "funding_values":False,
  "returns":False,
  "pnl":False,
  "direction":False,
  "protected_market_outcomes_2025_2026":False,
  "credentials":False,
  "account_creation":False,
  "paid_source":False,
  "live_trading":False,
  "orders":False,
  "wallets":False,
  "exchange_mutation":False,
  "merge_main":False,
  "discovered_routes_called":False
}

def attempt(ipv4):
    if TMP.exists():
        TMP.unlink()
    cmd=["curl","-sS","-L","--proto","=https","--proto-redir","=https",
         "--connect-timeout","20","--max-time","60",
         "--max-filesize",str(MAX_BYTES),
         "-H","Accept: application/json",
         "-A","crypto-lab-dls-source-schema/0.2",
         "-o",str(TMP),
         "-w","%{http_code}\n%{url_effective}\n%{size_download}\n"]
    if ipv4:
        cmd.insert(1,"-4")
    cmd.append(URL)
    p=subprocess.run(cmd,capture_output=True,text=True)
    lines=(p.stdout or "").splitlines()
    status=int(lines[0]) if len(lines)>=1 and lines[0].isdigit() else None
    effective=lines[1] if len(lines)>=2 else None
    size=None
    if len(lines)>=3:
        try: size=float(lines[2])
        except: pass
    return {
      "transport":"curl_ipv4" if ipv4 else "curl_default_stack",
      "returncode":p.returncode,
      "http_status":status,
      "effective_url":effective,
      "size_download":size,
      "stderr_type":"present" if (p.stderr or "").strip() else "none",
      "file_exists":TMP.exists()
    }

receipt=dict(base)
attempts=[]
chosen=None
for ipv4 in (True,False):
    a=attempt(ipv4)
    attempts.append(a)
    if a["returncode"]==0 and a["http_status"]==200 and a["file_exists"]:
        host=(urllib.parse.urlparse(a["effective_url"] or "").hostname or "").lower()
        a["effective_host"]=host
        if host=="drift.trade" or host.endswith(".drift.trade"):
            chosen=a
            break
        receipt.update(classification="DRIFT_DATA_API_SCHEMA_FAIL_CLOSED",
                       reason="redirect_outside_drift_trade",
                       attempts=attempts)
        OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(receipt,indent=2,sort_keys=True))
        raise SystemExit(0)

if chosen is None:
    receipt.update(classification="DRIFT_DATA_API_SCHEMA_TRANSPORT_BLOCKED",attempts=attempts)
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    raise SystemExit(0)

raw=TMP.read_bytes()
if len(raw)>MAX_BYTES:
    receipt.update(classification="DRIFT_DATA_API_SCHEMA_FAIL_CLOSED",
                   reason="schema_exceeds_frozen_max_bytes",attempts=attempts)
else:
    receipt["transport"]=chosen["transport"]
    receipt["http_status"]=chosen["http_status"]
    receipt["effective_host"]=chosen.get("effective_host")
    receipt["schema_bytes"]=len(raw)
    receipt["schema_sha256"]=hashlib.sha256(raw).hexdigest()
    receipt["attempts"]=attempts
    try:
        spec=json.loads(raw)
        receipt["openapi"]=spec.get("openapi")
        info=spec.get("info") if isinstance(spec.get("info"),dict) else {}
        receipt["api_title"]=info.get("title")
        receipt["api_version"]=info.get("version")
        paths=spec.get("paths")
        if not isinstance(paths,dict):
            raise ValueError("paths_not_object")
        matches=[]
        for path,ops in paths.items():
            if not isinstance(ops,dict):
                continue
            for method,op in ops.items():
                if method.lower() not in {"get","post","put","patch","delete","options","head"} or not isinstance(op,dict):
                    continue
                tags=op.get("tags") if isinstance(op.get("tags"),list) else []
                hay=" ".join([
                    str(path),str(op.get("summary") or ""),str(op.get("description") or ""),
                    str(op.get("operationId") or "")," ".join(map(str,tags))
                ]).lower()
                if "liquidat" not in hay:
                    continue
                params=[]
                for p in op.get("parameters") or []:
                    if not isinstance(p,dict): continue
                    sch=p.get("schema") if isinstance(p.get("schema"),dict) else {}
                    params.append({
                      "name":p.get("name"),
                      "in":p.get("in"),
                      "required":bool(p.get("required",False)),
                      "type":sch.get("type"),
                      "format":sch.get("format")
                    })
                matches.append({
                  "path":path,
                  "method":method.upper(),
                  "operationId":op.get("operationId"),
                  "summary":op.get("summary"),
                  "tags":tags,
                  "parameters":params,
                  "security":op.get("security")
                })
        receipt["liquidation_route_count"]=len(matches)
        receipt["liquidation_routes"]=matches
        receipt["classification"]="DRIFT_DATA_API_SCHEMA_LIQUIDATION_ROUTE_PASS" if matches else "DRIFT_DATA_API_SCHEMA_NO_LIQUIDATION_ROUTE"
    except Exception as e:
        receipt.update(classification="DRIFT_DATA_API_SCHEMA_FAIL_CLOSED",reason=type(e).__name__)

OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
