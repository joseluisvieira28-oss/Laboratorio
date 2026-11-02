#!/usr/bin/env python3
"""One-shot official Kraken PUBLIC derivatives metadata (NOT RFQ or executable options).
Original pre-source freeze PRE_SOURCE_PRE_OUTCOME_EXACT_VENUE_ECONOMIC_GATE_2026_11_02.md.
No authentication, account, trade, private endpoint, market history, options RFQ.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import pathlib
import urllib.request
OUT=pathlib.Path("artifacts/real_quote_economics_v01/public_kraken_source")
URLS={
    "instruments":"https://futures.kraken.com/derivatives/api/v3/instruments",
    "tickers":"https://futures.kraken.com/derivatives/api/v3/tickers"
}
LIMIT=8_000_000
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,url):
        raise ValueError("NO_REDIRECT_OR_ALTERNATE_ENDPOINT")
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    out={"study":"REAL_QUOTE_ECONOMICS_KRAKEN_PUBLIC_METADATA_ONLY_V01",
         "pre_source_freeze_commit":"010525fd11bd23e3bcef2460cc8041970ec07f2b",
         "started_utc":utc(),"status":"SOURCE_TRANSPORT_UNAVAILABLE",
         "open_option_rfq_quote_verified":False,"kraken_options_swiss_user_eligibility_verified":False,
         "option_entry_exit_bidask_verified":False,"mexc_event_payout_observed":False,
         "account_calls":0,"trades":0,"payments":0,"requests":[]}
    opener=urllib.request.build_opener(StrictRedirect)
    for name,url in URLS.items():
        item={"resource":name,"url":url,"requested_utc":utc(),"request_type":"PUBLIC_ANONYMOUS_GET"}
        try:
            req=urllib.request.Request(url,method="GET",headers={
                "Accept":"application/json","User-Agent":"CryptoLab-SourceMetadataOnly/1.0"})
            with opener.open(req,timeout=12) as resp:
                raw=resp.read(LIMIT+1)
                item["http_status"]=resp.status
            if len(raw)>LIMIT:raise ValueError("RESPONSE_OVERSIZE")
            (OUT/(name+"_original.json")).write_bytes(raw)
            j=json.loads(raw)
            if not isinstance(j,dict):raise ValueError("NOT_JSON_OBJECT")
            item["bytes"]=len(raw)
            item["raw_sha256"]=hashlib.sha256(raw).hexdigest()
            item["top_keys"]=sorted(j.keys())
            item["exchange_result"]=str(j.get("result",""))[:80]
            v=j.get(name)
            item["entries_count"]=len(v) if isinstance(v,list) else None
            item["first_entry_keys"]=sorted(v[0].keys()) if isinstance(v,list) and v and isinstance(v[0],dict) else None
            item["option_like_descriptive_count"]=sum(
               any(word in str(k).lower() for word in ("option","strike","expiry"))
               for elem in v if isinstance(elem,dict) for k in list(elem)[:1]
            ) if isinstance(v,list) else None
            item["status"]="PUBLIC_JSON_METADATA_ACCESSIBLE" if resp.status==200 and j.get("result")=="success" and isinstance(v,list) else "PUBLIC_JSON_SCHEMA_NOT_VALIDATED"
        except Exception as e:
            item["status"]="PUBLIC_METADATA_ENDPOINT_BLOCKED"
            item["error"]=type(e).__name__+":"+str(e)[:180]
        out["requests"].append(item)
    if all(v["status"]=="PUBLIC_JSON_METADATA_ACCESSIBLE" for v in out["requests"]):
        out["status"]="KRAKEN_PUBLIC_DERIVATIVES_METADATA_PASS_NOT_RfQ_OPTION_QUOTES"
    out["finished_utc"]=utc()
    (OUT/"receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("KRAKEN_PUBLIC_DERIVATIVES_SOURCE_GATE",json.dumps(out,sort_keys=True),flush=True)
    if out["status"]=="SOURCE_TRANSPORT_UNAVAILABLE":raise SystemExit(2)
if __name__=="__main__":main()
