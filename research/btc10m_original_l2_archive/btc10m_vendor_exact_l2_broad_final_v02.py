#!/usr/bin/env python3
"""Exact OKX BTC-USDT spot and MEXC BTC_USDT perpetual L2 ARCHIVE source metadata ONLY.
Never buy, sample huge ticks, subscribe, place orders or query prices.
"""
import datetime as dt
import hashlib
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

DIR=pathlib.Path("artifacts/btc10m_okx_mexc_broad_archive_v02")
PREFIX="https://cryptostruct.com"
TARGETS=[("okx_spot","/api/search?q=BTC&venue=okx&class=spot"),
         ("mexc_perp","/api/search?q=BTC&venue=mexc&class=perp")]
SAMPLES=None
MAX=3_000_000
REQ_CAP=4
def utc():return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
def sha(b):return hashlib.sha256(b).hexdigest()
class Blocked(Exception):pass
class ConfinedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not newurl.startswith(PREFIX+"/api/"):
            raise Blocked("UNAUTHORIZED_REDIRECT_ORIGIN_OR_PATH")
        return super().redirect_request(req,fp,code,msg,headers,newurl)
_opener=urllib.request.build_opener(ConfinedRedirect)
def call(path,filename,receipt):
    if len(receipt["requests"])>=REQ_CAP:raise Blocked("REQUEST_BUDGET_EXCEEDED")
    now=utc()
    url=PREFIX+path
    try:
        req=urllib.request.Request(url,method="GET",headers={
             "Accept":"application/json","User-Agent":"CryptoLab-BTC10m-HistoricL2-SourceCensus/1.0"})
        with _opener.open(req,timeout=12) as response:
            if response.status!=200:raise Blocked("HTTP_NOT_200_"+str(response.status))
            raw=response.read(MAX+1)
    except Exception as e:raise Blocked("VENDOR_GET_"+type(e).__name__+"_"+path[:80]) from e
    if not raw or len(raw)>MAX:raise Blocked("BODY_EMPTY_OR_TOO_BIG")
    (DIR/filename).write_bytes(raw)
    info={"uri":url,"read_utc":utc(),"start_utc":now,"size_bytes":len(raw),"raw_sha256":sha(raw),"file":filename}
    receipt["requests"].append(info)
    try:obj=json.loads(raw)
    except Exception as e:raise Blocked("JSON_PARSE_BAD") from e
    return obj
def flatten(x):
    if isinstance(x,list):return x
    if isinstance(x,dict):
        for key in ("results","data","items","instruments","markets"):
            if isinstance(x.get(key),list):return x[key]
            if isinstance(x.get(key),dict):
                for k2 in ("results","data","items"):
                    if isinstance(x[key].get(k2),list):return x[key][k2]
    raise Blocked("INSTRUMENT_SEARCH_RESPONSE_SCHEMA_UNKNOWN")
def label(item):
    e=item.get("exchange_code") or item.get("exchange") or item.get("venue") or {}
    if isinstance(e,dict):e=e.get("code") or e.get("name") or e.get("id") or ""
    v=item.get("code") or item.get("symbol") or item.get("ticker") or item.get("instrument") or ""
    k=item.get("type") or item.get("market_type") or item.get("instrument_type") or item.get("class") or ""
    if isinstance(k,dict):k=k.get("code") or k.get("name") or ""
    i=item.get("instrument_id",item.get("instrumentId",item.get("id")))
    return str(e).lower(),str(v).lower(),str(k).lower(),i
def strict_instrument(item,market):
    if not isinstance(item,dict):return False
    venue,sym,klass,ident=label(item)
    if market=="okx_spot":
        exch=venue in ("okx","okex")
        accepted_type=klass in ("spot","0")
        acceptable_symbol=sym.replace("_","-") in ("btc-usdt","btcusdt","btc-usdt-spot")
    else:
        exch=venue in ("mexc","mexc futures","mexc-futures")
        accepted_type=klass in ("perp","perpetual","perpetual_swap","swap","usdt-m futures","futures_perpetual","perpetual swap")
        acceptable_symbol=sym.replace("_","-") in ("btc-usdt","btcusdt","btc-usdt-swap","btcusdt-perp","btc-usdt-perp")
    try:uniqueid=int(ident)
    except Exception:return False
    return exch and accepted_type and acceptable_symbol and uniqueid>0
def summary(obj):
    if isinstance(obj,list):return {"type":"list","length":len(obj)}
    if isinstance(obj,dict):return {"type":"object","keys":sorted(obj.keys())[:30],
                "count":next((len(obj[k]) for k in ("results","items","data","instruments") if isinstance(obj.get(k),list)),None)}
    return {"type":type(obj).__name__}
def matches(meta,target):
    arr=flatten(meta)
    candidates=[x for x in arr if strict_instrument(x,target)]
    return arr,candidates
def iso_date(s):
    return isinstance(s,str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}",s) is not None
def coverage(meta):
    if not isinstance(meta,dict):raise Blocked("COVERAGE_INVALID_RESPONSE")
    obj=meta.get("data",meta)
    if not isinstance(obj,dict):raise Blocked("COVERAGE_SCHEMA_UNKNOWN")
    first=obj.get("first_day") or obj.get("firstDay") or obj.get("first_date")
    last=obj.get("last_day") or obj.get("lastDay") or obj.get("last_date")
    return {"first_day":first,"last_day":last,
      "covers_2025_calendar":iso_date(first) and iso_date(last) and first<="2025-01-01" and last>="2025-12-31",
      "days_with_data":obj.get("days_with_data") or obj.get("daysWithData"),
      "metadata_only":True}
def sample_meta(x):
    if not isinstance(x,dict):return {"type":type(x).__name__}
    return {k:x.get(k) for k in ("id","instrument_id","date","day","exchange","venue","symbol","code","type")
            if k in x}
def main():
    DIR.mkdir(parents=True,exist_ok=True)
    rec={"study":"BTC10M_ORIGINAL_OKX_SPOT_MEXC_PERP_HISTORIC_L2_BROAD_CENSUS_V02",
         "pre_source_freeze":"research/btc10m_original_l2_archive/BTC10M_VENDOR_BROAD_SEARCH_V02_PRE_SOURCE_FREEZE.md",
         "start_utc":utc(),"status":"SOURCE_BLOCKED_FAIL_CLOSED","requests":[],
         "exact_venue_instruments":{},"coverage":{},"free_sample_summary":{},
         "original_orderbook_backtest_performed":False,
         "market_price_outcomes_read":0,"account_or_wallet_access":0,
         "purchase_or_payment":0,"real_orders":0,"main_branch_changes":0}
    try:
        # Calls in completely fixed order independent of outcomes.
        responses={}
        for target,path in TARGETS:
            responses[target]=call(path,target+"_search.json",rec)
        ids={}
        for target in ("okx_spot","mexc_perp"):
            obj=responses[target]
            rec[target+"_query_response_shape"]=summary(obj)
            arr,candidates=matches(obj,target)
            rec[target+"_search_returned_candidates"]=len(arr)
            rec[target+"_strict_matches"]=len(candidates)
            if len(candidates)==1:
                v,s,k,i=label(candidates[0])
                ids[target]=int(i)
                rec["exact_venue_instruments"][target]={
                   "instrument_id":int(i),"exchange":v,"symbol":s,"product_type":k,
                   "identity_verified_from_first_party_vendor_metadata":True}
            else:
                rec["exact_venue_instruments"][target]={"status":"AMBIGUOUS_OR_ABSENT","matching_count":len(candidates),
                    "candidate_metadata_preview":[{k:v for k,v in item.items() if k in
                       ("instrument_id","instrumentId","id","exchange_code","exchange","venue","code","symbol","type","market_type")}
                       for item in arr[:12] if isinstance(item,dict)]}
        # Use no other metadata endpoints if ID identity not established.
        if len(ids)==2:
            for target in ("okx_spot","mexc_perp"):
                obj=call("/api/instrument/"+str(ids[target])+"/coverage",target+"_coverage.json",rec)
                rec["coverage"][target]=coverage(obj)
            a,b=rec["coverage"]["okx_spot"],rec["coverage"]["mexc_perp"]
            if a["covers_2025_calendar"] and b["covers_2025_calendar"]:
                rec["status"]="BOTH_EXACT_INSTRUMENTS_VENDOR_COVERAGE_2025_METADATA_PASS"
                rec["decision"]="SOURCE_METADATA_PASS_ONLY_NO_L2_BYTES_OR_PRICE_LABELS_VALIDATED"
            else:
                rec["status"]="EXACT_IDENTITIES_KNOWN_2025_OVERLAP_NOT_PROVEN"
        else:rec["status"]="SOURCE_PAIR_IDENTITY_UNPROVEN"
        # This phase deliberately never claims the snapshots have passed any real 2025 per-day availability checks.
    except Exception as exc:
        rec["status"]="SOURCE_BLOCKED_FAIL_CLOSED"
        rec["blocked_reason"]=type(exc).__name__+":"+str(exc)[:320]
    finally:
        rec["finish_utc"]=utc()
        rec["directional_10m_hit_rate"]=None
        rec["economic_edge_certified"]=False
        (DIR/"source_receipt.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf8")
        print("FINAL_SOURCE_RECEIPT",json.dumps(rec,indent=2,sort_keys=True),flush=True)
    if rec["status"]=="SOURCE_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if __name__=="__main__":main()
