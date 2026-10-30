#!/usr/bin/env python3
"""ROLL002 public read-only Morpho Midnight Base market roll event source gate."""
import datetime as dt
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request

ROOT=pathlib.Path("artifacts/morpho_roll_firstparty_rest_v02")
BASE="https://api.morpho.org"
COUNT=12
ASOF=1793361600
SINCE=1790812800
MARKET=re.compile(r"^0x[0-9a-fA-F]{64}$")
class Blocked(Exception):pass
def utc():return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
def sha(raw):return hashlib.sha256(raw).hexdigest()
def http(path,filename,maxbytes):
    uri=BASE+path
    req=urllib.request.Request(uri,method="GET",
        headers={"Accept":"application/json","User-Agent":"CryptoLab-ROLL002-ReadOnly/1.0"})
    start=utc()
    try:
        with urllib.request.urlopen(req,timeout=10) as response:
            status=response.status
            raw=response.read(maxbytes+1)
    except Exception as exc:
        raise Blocked("OFFICIAL_MORPHO_PUBLIC_GET_"+type(exc).__name__+"_PATH_"+path[:130]) from exc
    received=utc()
    if status!=200 or len(raw)>maxbytes:raise Blocked("HTTP_STATUS_OR_PAYLOAD_LIMIT")
    file=ROOT/filename
    file.write_bytes(raw)
    try:payload=json.loads(raw)
    except Exception as exc:raise Blocked("JSON_SCHEMA_INVALID") from exc
    return payload,{"path":path,"http":status,"utc_started":start,
                    "utc_received":received,"raw_sha256":sha(raw),"bytes":len(raw),"file":filename}
def selection(data):
    if not isinstance(data,dict) or not isinstance(data.get("data"),list):raise Blocked("MARKETS_LIST_SCHEMA")
    if data.get("cursor") not in (None,""):raise Blocked("MARKET_LIST_HAS_UNREAD_PAGES")
    markets=[]
    seen=set()
    for raw in data["data"]:
        if not isinstance(raw,dict):raise Blocked("MARKET_RECORD_NOT_OBJECT")
        mid=raw.get("market_id")
        if not isinstance(mid,str) or not MARKET.fullmatch(mid):raise Blocked("BAD_MARKET_ID")
        if mid.lower() in seen:raise Blocked("DUPLICATE_MARKET_ID")
        seen.add(mid.lower())
        if raw.get("chain_id") not in (8453,"8453"):raise Blocked("NOT_BASE_MARKET")
        try:maturity=int(raw["maturity"])
        except Exception as exc:raise Blocked("MARKET_MATURITY_UNKNOWN") from exc
        markets.append({"market_id":mid,"maturity":maturity,"loan_token":raw.get("loan_token")})
    markets.sort(key=lambda x:(abs(x["maturity"]-ASOF),x["market_id"].lower()))
    return len(markets),markets[:COUNT]
def extract_events(payload,mid):
    if not isinstance(payload,dict) or not isinstance(payload.get("data"),list):
        raise Blocked("TRANSACTION_RESPONSE_SCHEMA")
    if payload.get("cursor") not in (None,""):
        raise Blocked("TRANSACTIONS_HAS_UNREAD_CURSOR")
    output=[]
    for ev in payload["data"]:
        if not isinstance(ev,dict):raise Blocked("EVENT_NOT_OBJECT")
        event_type=ev.get("event_type") or ev.get("type")
        if event_type!="roll":raise Blocked("UNEXPECTED_EVENT_TYPE")
        explicit=ev.get("data") if isinstance(ev.get("data"),dict) else ev
        # Do not infer event payout if the documented field isn't present.
        raw=explicit.get("incentive_assets",explicit.get("incentiveAssets"))
        if raw is None:raise Blocked("ROLL_EVENT_HAS_NO_EXPLICIT_INCENTIVE_FIELD")
        if not str(raw).isdigit():raise Blocked("ROLL_INCENTIVE_RAW_NOT_INTEGER")
        event_mid=ev.get("market_id") or (ev.get("data") or {}).get("market_id") if isinstance(ev.get("data"),dict) else ev.get("market_id")
        if event_mid is not None and str(event_mid).lower()!=mid.lower():raise Blocked("EVENT_MARKET_ID_MISMATCH")
        output.append({"market_id":mid,"incentive_assets_raw_loan_token_units":str(raw),
            "positive":int(raw)>0,"hash_or_tx":ev.get("transaction_hash") or ev.get("tx_hash") or ev.get("hash"),
            "timestamp":ev.get("created_at"),"not_usd_or_user_net":True})
    return output
def tests():
    vals=[{"market_id":"0x"+f"{i:064x}","chain_id":8453,"maturity":ASOF+offset}
          for i,offset in enumerate((300,50,-10,12),1)]
    c,sel=selection({"data":vals,"cursor":None})
    assert c==4 and sel[0]["market_id"]==vals[2]["market_id"]
    assert extract_events({"data":[{"type":"roll","data":{"incentive_assets":"100"}}]},
                          "0x"+"01"*32)[0]["positive"] is True
    try:extract_events({"data":[{"type":"roll","data":{}}]},"0x"+"01"*32);raise AssertionError("MISSING_INCENTIVE_ACCEPTED")
    except Blocked:pass
def main():
    ROOT.mkdir(exist_ok=True,parents=True)
    tests()
    result={"study":"ROLL002_FIRST_PARTY_MORPHO_MIDNIGHT_PUBLIC_REST",
        "started_at_utc":utc(),"status":"SOURCE_BLOCKED_FAIL_CLOSED",
        "no_trade":True,"no_wallet":True,"no_private_api":True,"no_main_merge":True,
        "onchain_event_origin":None,"operator_receipts":0,
        "source_requests":[],"selected_markets":[],"events":[]}
    try:
        data,meta=http("/v0/midnight/markets?chain_ids=8453","00_markets.json",5_000_000)
        result["source_requests"].append(meta)
        count,selected=selection(data)
        result["total_listed_markets"]=count
        result["selected_markets"]=selected
        if len(selected)<3:
            result["status"]="SOURCE_INCOMPLETE_TOO_FEW_MARKETS"
        else:
            for n,item in enumerate(selected,1):
                mid=item["market_id"]
                path=("/v0/midnight/markets/"+urllib.parse.quote(mid,safe="")+
                      "/transactions?event_types=roll&created_at_gte="+str(SINCE))
                response,meta=http(path,f"{n:02d}_transactions.json",2_000_000)
                result["source_requests"].append(meta)
                result["events"].extend(extract_events(response,mid))
            result["positive_raw_incentive_events"]=sum(x["positive"] for x in result["events"])
            result["selected_market_event_count"]=len(result["events"])
            result["status"]=("SOURCE_PASS_VERIFIED_ROLL_EVENTS_WITH_POSITIVE_RAW_INCENTIVE"
                if result["positive_raw_incentive_events"]>0 else
                "SOURCE_COMPLETE_NO_POSITIVE_ROLLS_IN_SELECTED_SAMPLE")
    except Blocked as exc:
        result["status"]="SOURCE_BLOCKED_FAIL_CLOSED"
        result["blocked_reason"]=str(exc)
    except Exception as exc:
        result["status"]="SOURCE_BLOCKED_FAIL_CLOSED"
        result["blocked_reason"]="UNEXPECTED_"+type(exc).__name__+":"+str(exc)[:150]
    finally:
        result["finished_at_utc"]=utc()
        result["net_profit_certified"]=False
        result["active_roll_config_available"]=False
        result["gas_or_competition_measured"]=False
        (ROOT/"receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:result.get(k) for k in ("study","status","blocked_reason",
            "total_listed_markets","selected_market_event_count","positive_raw_incentive_events",
            "selected_markets","net_profit_certified")},indent=2,sort_keys=True))
    if result["status"]=="SOURCE_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if __name__=="__main__":main()
