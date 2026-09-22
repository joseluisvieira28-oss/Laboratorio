#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math,urllib.error,urllib.parse,urllib.request
from pathlib import Path

UA="CED1D-0031-V02C-OFFICIAL-MIRROR-PROBE"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--freeze",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    fr=json.loads(Path(a.freeze).read_text(encoding="utf-8"))
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    p=fr["probe"]
    q=urllib.parse.urlencode({"symbol":p["symbol"],"startTime":p["startTime"],"endTime":p["endTime"],"limit":p["limit"]})
    results=[]; winners=[]
    for host in fr["hosts"]:
        url=host+fr["endpoint"]+"?"+q
        rec={"host":host,"url":url}
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=30) as r:
                body=r.read(); rec["http_status"]=r.status
            rec["body_sha256"]=hashlib.sha256(body).hexdigest()
            data=json.loads(body)
            rec["json_list"]=isinstance(data,list)
            rec["row_count"]=len(data) if isinstance(data,list) else None
            ok=isinstance(data,list) and len(data)>0
            if ok:
                for row in data:
                    if any(k not in row for k in fr["required_fields"]):
                        ok=False; rec["missing_required_fields"]=True; break
                    if row.get("symbol")!=p["symbol"]:
                        ok=False; rec["symbol_mismatch"]=row.get("symbol"); break
                    ft=int(row["fundingTime"])
                    if not p["startTime"]<=ft<=p["endTime"]:
                        ok=False; rec["time_outside_probe"]=ft; break
                    if not math.isfinite(float(row["fundingRate"])):
                        ok=False; rec["invalid_funding_rate"]=True; break
                rec["first_row_keys"]=sorted(data[0]) if data else []
            rec["schema_pass"]=bool(ok)
            if rec["http_status"]==200 and ok:
                winners.append(host)
                (out/(host.split("//",1)[1].replace(".","_")+".json")).write_bytes(body)
        except urllib.error.HTTPError as e:
            rec["http_status"]=e.code; rec["error"]="HTTPError"
            try:
                eb=e.read(); rec["error_body_sha256"]=hashlib.sha256(eb).hexdigest()
            except Exception:
                pass
        except Exception as e:
            rec["error"]=f"{type(e).__name__}:{e}"
        results.append(rec)
    receipt={
        "document_id":"CED1D_0031_OFFICIAL_BINANCE_FAPI_MIRROR_SOURCE_PROBE_RECEIPT_V0.2C",
        "classification":"OFFICIAL_MIRROR_SCHEMA_PASS" if winners else "OFFICIAL_MIRROR_TRANSPORT_BLOCKED",
        "accessible_exact_schema_hosts":winners,
        "results":results,
        "used_as_forward_evidence":False,
        "returns_computed":False,
        "pnl_computed":False,
        "orders":False,
        "exchange_mutation":False,
        "collector_adoption_authorized":False
    }
    raw=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
    receipt["fingerprint"]=hashlib.sha256(raw).hexdigest()
    (out/"CED1D_0031_OFFICIAL_FAPI_MIRROR_PROBE_RECEIPT_V0.2C.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
