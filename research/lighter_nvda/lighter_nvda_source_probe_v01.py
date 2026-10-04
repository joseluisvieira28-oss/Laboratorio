#!/usr/bin/env python3
"""Lighter NVDA public/free SOURCE + EXECUTION FEASIBILITY probe. No outcomes."""
from __future__ import annotations
import json,hashlib,requests,time
from pathlib import Path
OUT=Path("artifacts/lighter_nvda/v01_source_gate")
UA="CryptoLab-Lighter-NVDA-SourceGate/0.1"
BASES=["https://mainnet.zklighter.elliot.ai","https://api.lighter.xyz"]
ENDPOINTS=[
 "/api/v1/orderBookDetails",
 "/api/v1/orderBooks",
 "/api/v1/orderBookOrders?market_id=0&limit=10",
 "/api/v1/funding-rates"
]
def H(b):return hashlib.sha256(b).hexdigest()
def get(url):
    try:
        r=requests.get(url,headers={"User-Agent":UA},timeout=30)
        return {"url":url,"http":r.status_code,"sha256":H(r.content),"text":r.text[:500000]}
    except Exception as e:return {"url":url,"error":repr(e)}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    probes=[]
    for b in BASES:
        for ep in ENDPOINTS:
            x=get(b+ep);probes.append(x);print(x["url"],x.get("http"),x.get("error"))
            time.sleep(.1)
    parsed=[]
    for x in probes:
        if x.get("http")!=200:continue
        try:j=json.loads(x["text"])
        except:continue
        parsed.append({"url":x["url"],"json":j})
    # Recursively locate dicts mentioning NVDA.
    hits=[]
    def walk(o,path=""):
        if isinstance(o,dict):
            blob=json.dumps(o,sort_keys=True)
            if "NVDA" in blob.upper():hits.append({"path":path,"object":o})
            for k,v in o.items():walk(v,path+"/"+str(k))
        elif isinstance(o,list):
            for i,v in enumerate(o):walk(v,path+f"/{i}")
    for p in parsed:walk(p["json"],p["url"])
    # Deduplicate approximate hits by JSON.
    uniq=[];seen=set()
    for x in hits:
        s=json.dumps(x["object"],sort_keys=True)
        if s not in seen:seen.add(s);uniq.append(x)
    report={
      "gate_id":"LIGHTER_NVDA_PORTABILITY_SOURCE_GATE_V0_1",
      "source_only":True,"outcomes_opened":0,
      "public_base_candidates":BASES,
      "probes":[{k:v for k,v in x.items() if k!="text"} for x in probes],
      "nvda_hits":uniq[:100],
      "nvda_hit_count":len(uniq),
      "historical_candle_endpoint_proven":False,
      "fee_claim_from_probe_only":None,
      "orders":False,"account_reads":False,"private_endpoints_used":False,
      "wallets":False,"live_trading_authorized":False
    }
    # Inspect hit keys for fee/market identity only.
    fee_fields=[]
    for x in uniq:
        o=x["object"]
        if isinstance(o,dict):
            ff={k:v for k,v in o.items() if any(z in k.lower() for z in ["fee","symbol","market","min_quote","min_base","ticker"])}
            if ff:fee_fields.append(ff)
    report["nvda_fee_and_identity_fields"]=fee_fields[:50]
    if uniq:
        report["verdict"]="LIGHTER_NVDA_MARKET_PUBLIC_METADATA_FOUND__HISTORY_NOT_YET_PROVEN"
    else:report["verdict"]="LIGHTER_NVDA_PUBLIC_MARKET_NOT_PROVEN_BY_PROBE"
    (OUT/"LIGHTER_NVDA_SOURCE_GATE_V01.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps({"verdict":report["verdict"],"nvda_hit_count":len(uniq),
      "fee_and_identity_fields":fee_fields[:10]},indent=2))
if __name__=="__main__":main()
