#!/usr/bin/env python3
import json, os, hashlib
import requests

BASE="https://www.mexc.com/api/platform/futures/api/v1"
SYMBOLS=["BTC_USDT","ETH_USDT","NVIDIA_USDT","MUSTOCK_USDT","SPCXSTOCK_USDT"]
ENDPOINTS=[
  ("/event_contract/detail",None),
  ("/event_contract/listPlaceCarouse",None),
  ("/event_contract/listWinCarouse",None),
]
for s in SYMBOLS:
    ENDPOINTS.append(("/event_contract/trade_date_time",{"symbol":s}))
    ENDPOINTS.append(("/event_contract/last_trade_date_time",{"symbol":s}))

HEADERS={
  "User-Agent":"Mozilla/5.0 (compatible; CryptoLab-SourceResearch/0.11.5)",
  "Accept":"application/json,text/plain,*/*",
  "Accept-Language":"en-GB,en;q=0.9",
}

KEYS_HINT=[
  "payout","rate","profit","reward","cycle","timeunit","time_unit","amount","min","max",
  "symbol","settle","index","price","status","trade","contract","direction","side"
]

def sha(b): return hashlib.sha256(b).hexdigest()

def walk(obj,path="",out=None):
    if out is None: out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            p=f"{path}.{k}" if path else str(k)
            out.append((p,v))
            walk(v,p,out)
    elif isinstance(obj,list):
        for i,v in enumerate(obj[:200]):
            p=f"{path}[{i}]"
            walk(v,p,out)
    return out

def summarize_json(j):
    flat=walk(j)
    hits=[]
    for p,v in flat:
        pl=p.lower()
        if any(k in pl for k in KEYS_HINT):
            if isinstance(v,(str,int,float,bool)) or v is None:
                hits.append({"path":p,"value":v})
    return hits[:500]

def main():
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    sess=requests.Session()
    sess.headers.update(HEADERS)
    sess.cookies.clear()

    evidence={
      "lab":"MEXC_EVENT_FUTURES_EXACT_PRODUCT_V0.11.5",
      "base":BASE,
      "authenticated_requests":0,
      "orders":0,
      "account_mutations":0,
      "private_routes_called":0,
      "probes":[]
    }

    for path,params in ENDPOINTS:
        url=BASE+path
        try:
            r=sess.get(url,params=params,timeout=20,allow_redirects=False)
            body=r.content
            rec={
              "url":r.url,
              "status":r.status_code,
              "content_type":r.headers.get("content-type"),
              "bytes":len(body),
              "sha256":sha(body),
            }
            text=body.decode("utf-8","replace")
            try:
                j=r.json()
                rec["json"]=j
                rec["schema_hits"]=summarize_json(j)
            except Exception:
                rec["preview"]=text[:3000]
            evidence["probes"].append(rec)
        except Exception as e:
            evidence["probes"].append({"url":url,"params":params,"error":repr(e)})

    product_schema=False
    payout_fields=False
    for rec in evidence["probes"]:
        if rec.get("status")==200 and isinstance(rec.get("json"),(dict,list)):
            product_schema=True
            low=json.dumps(rec["json"],ensure_ascii=False).lower()
            if "payout" in low or "profitrate" in low or "profit_rate" in low or "winrate" in low:
                payout_fields=True

    if payout_fields:
        verdict="EXACT_PAYOUT_FIELDS_FOUND"
    elif product_schema:
        verdict="EXACT_PRODUCT_SCHEMA_FOUND"
    elif any(rec.get("status") for rec in evidence["probes"]):
        verdict="PUBLIC_ENDPOINT_FOUND_BUT_SCHEMA_INCOMPLETE"
    else:
        verdict="PUBLIC_ENDPOINT_BLOCKED"

    evidence["verdict"]=verdict
    evidence["payout_fields_found"]=payout_fields
    evidence["product_schema_found"]=product_schema

    path="artifacts/mexc_event_futures/exact_product_v0115.json"
    with open(path,"w",encoding="utf-8") as f:
        json.dump(evidence,f,indent=2,sort_keys=True,ensure_ascii=False)

    compact={
      "verdict":verdict,
      "payout_fields_found":payout_fields,
      "product_schema_found":product_schema,
      "probe_count":len(evidence["probes"]),
      "statuses":[{"url":x.get("url"),"status":x.get("status"),"content_type":x.get("content_type")} for x in evidence["probes"]],
      "authenticated_requests":0,"orders":0,"account_mutations":0,"private_routes_called":0
    }
    print(json.dumps(compact,indent=2,sort_keys=True,ensure_ascii=False))
    print("SCHEMA_HITS=")
    for rec in evidence["probes"]:
        if rec.get("schema_hits"):
            print(json.dumps({"url":rec["url"],"hits":rec["schema_hits"][:120]},indent=2,ensure_ascii=False))
    print("WROTE",path)

if __name__=="__main__":
    main()
