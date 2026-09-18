#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,urllib.parse,urllib.request,urllib.error
from pathlib import Path

UA="CED1D-FUNDING-MIRROR-PROBE/0.1"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--freeze",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args(); fr=json.loads(Path(a.freeze).read_text()); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    p=fr["probe"]; results=[]; accessible=[]
    q=urllib.parse.urlencode({"symbol":p["symbol"],"startTime":p["startTime"],"endTime":p["endTime"],"limit":p["limit"]})
    for host in fr["hosts"]:
        url=host+fr["endpoint"]+"?"+q
        rec={"host":host,"url":url}
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=30) as r:
                body=r.read(); rec["http_status"]=r.status
            rec["raw_sha256"]=hashlib.sha256(body).hexdigest()
            data=json.loads(body)
            rec["json_list"]=isinstance(data,list); rec["row_count"]=len(data) if isinstance(data,list) else None
            required=fr["required_fields"]
            ok=isinstance(data,list) and len(data)>0
            if ok:
                for row in data:
                    if any(k not in row for k in required): ok=False; rec["missing_required_fields"]=True; break
                    if str(row["symbol"])!=p["symbol"]: ok=False; rec["symbol_mismatch"]=True; break
                    ft=int(row["fundingTime"])
                    if not(p["startTime"]<=ft<=p["endTime"]): ok=False; rec["time_outside_probe"]=ft; break
                rec["first_row_keys"]=sorted(data[0].keys()) if data else []
                rec["sample_first_row"]=data[0] if data else None
            rec["schema_pass"]=ok
            if r.status==200 and ok:
                accessible.append(host)
                (out/(host.split("//",1)[1].replace(".","_")+".json")).write_bytes(body)
        except urllib.error.HTTPError as e:
            rec["http_status"]=e.code; rec["error"]="HTTPError"
            try: rec["error_body_sha256"]=hashlib.sha256(e.read()).hexdigest()
            except Exception: pass
        except Exception as e:
            rec["error"]=f"{type(e).__name__}:{e}"
        results.append(rec)
    receipt={"document_id":"CED_1D_2025_FUNDING_REST_MIRROR_TRANSPORT_PROBE_RECEIPT_V0.1",
             "status":"MIRROR_WITH_EXACT_SCHEMA_FOUND" if accessible else "NO_EXACT_SCHEMA_MIRROR_AVAILABLE",
             "accessible_exact_schema_hosts":accessible,"results":results,
             "outcomes_computed":False,"returns_computed":False,"pnl_computed":False,"access_2026_plus":False}
    raw=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode(); receipt["fingerprint"]=hashlib.sha256(raw).hexdigest()
    (out/"mirror_probe_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2))
if __name__=="__main__": main()
