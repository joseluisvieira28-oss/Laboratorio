#!/usr/bin/env python3
import hashlib, json, os, requests
from datetime import datetime, timezone

URL="https://www.mexc.com/api/platform/futures/api/v1/event_contract/detail"
TARGETS={"BTC_USDT","ETH_USDT","NVIDIA_USDT","MUSTOCK_USDT","SPCXSTOCK_USDT"}
HEADERS={
 "User-Agent":"Mozilla/5.0 (compatible; CryptoLab-SourceResearch/0.12)",
 "Accept":"application/json,text/plain,*/*",
 "Accept-Language":"en-US,en;q=0.9",
}

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    s=requests.Session()
    s.headers.update(HEADERS)
    s.cookies.clear()
    r=s.get(URL,timeout=30,allow_redirects=True)
    body=r.content
    out={
      "lab":"MEXC_EVENT_FUTURES_EXACT_GET_V0.12",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "url":URL,"final_url":r.url,"status_code":r.status_code,
      "content_type":r.headers.get("content-type"),"bytes":len(body),
      "sha256":sha(body),
      "authenticated_requests":0,"orders":0,"account_mutations":0,
      "records":[],
    }
    try:
        j=r.json()
        out["top_level_type"]=type(j).__name__
        out["top_level_keys"]=sorted(j.keys()) if isinstance(j,dict) else []
        out["success"]=j.get("success") if isinstance(j,dict) else None
        out["code"]=j.get("code") if isinstance(j,dict) else None
        data=j.get("data") if isinstance(j,dict) else None
        if isinstance(data,list):
            out["record_count"]=len(data)
            out["all_symbols"]=[x.get("symbol") for x in data if isinstance(x,dict)]
            for x in data:
                if isinstance(x,dict) and x.get("symbol") in TARGETS:
                    out["records"].append(x)
        else:
            out["record_count"]=None
            out["data_type"]=type(data).__name__
    except Exception as e:
        out["json_error"]=repr(e)

    if r.status_code==200 and out.get("success") is True and out["records"]:
        verdict="EXACT_PUBLIC_PRODUCT_ROUTE_CONFIRMED"
    elif r.status_code==200:
        verdict="PUBLIC_ROUTE_FOUND_BUT_SCHEMA_INSUFFICIENT"
    else:
        verdict="PUBLIC_ROUTE_BLOCKED"
    out["verdict"]=verdict

    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    p="artifacts/mexc_event_futures/exact_get_v012.json"
    with open(p,"w",encoding="utf-8") as f:
        json.dump(out,f,indent=2,sort_keys=True)

    print("VERDICT="+verdict)
    print("STATUS="+str(r.status_code))
    print("RECORD_COUNT="+str(out.get("record_count")))
    print("TARGET_RECORDS="+str(len(out["records"])))
    print("ALL_SYMBOLS="+json.dumps(out.get("all_symbols",[]),ensure_ascii=False))
    for rec in out["records"]:
        print("CONTRACT_RECORD="+json.dumps(rec,ensure_ascii=False,sort_keys=True))
    print("NO_AUTH=PASS")
    print("NO_ORDERS=PASS")
    print("NO_MUTATION=PASS")
    print("WROTE "+p)

if __name__=="__main__":
    main()
