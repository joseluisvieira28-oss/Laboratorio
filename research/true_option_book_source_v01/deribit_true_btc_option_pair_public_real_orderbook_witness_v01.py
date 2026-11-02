#!/usr/bin/env python3
"""First-party real option order-book economic source-only probe, frozen before first request.
NO private APIs, user account, orders, keys, historical future outcomes, trading or fees paid.
See DERIBIT_PRE_PUBLIC_BOOK_QUOTE_ECONOMIC_FREEZE_2026_11_02.md (commit 8a67fa44...).
"""
import datetime as dt
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

ROOT=pathlib.Path("artifacts/deribit_real_btc_option_orderbook_source_v01")
BASE="https://www.deribit.com/api/v2"
FROZEN_COMMIT="8a67fa44d1ed0148cf5dff19990992cb80d94a33"
PAT=re.compile(r"^BTC-(\d{1,2}[A-Z]{3}\d{2})-(\d+)-([CP])$")
MIN_AMOUNT=Decimal("0.1")
FEE_COEFF=Decimal("0.0003")
FEE_CAP=Decimal("0.125")
MAX_BYTES=12_000_000
class SourceError(Exception):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req,fp,code,msg,headers,url):
        raise SourceError("UNPERMITTED_HTTP_REDIRECT")
def now():return dt.datetime.now(dt.timezone.utc)
def timestamp(d):return d.isoformat().replace("+00:00","Z")
def parse_number(v):
    try: x=Decimal(str(v))
    except (InvalidOperation,ValueError,TypeError):return None
    return x if x.is_finite() else None
def positive(v):
    x=parse_number(v)
    return x if x is not None and x>0 else None
def exact_expiry(s):
    d=dt.datetime.strptime(s,"%d%b%y")
    return d.replace(hour=8,tzinfo=dt.timezone.utc)
def extract_pair(arr,index,date):
    # Summary data contain only PUBLIC market metadata; NO future outcome or private info.
    names={}
    for x in arr:
        if not isinstance(x,dict):continue
        sym=x.get("instrument_name","")
        match=PAT.fullmatch(str(sym))
        if not match:continue
        expiry=exact_expiry(match.group(1))
        days=(expiry-date).total_seconds()/86400
        strike=Decimal(match.group(2))
        if not (Decimal("3.0")<=Decimal(str(days))<=Decimal("14.0")):continue
        if abs(strike/index-1)>Decimal(".025"):continue
        bid=positive(x.get("bid_price"));ask=positive(x.get("ask_price"))
        if bid is None or ask is None or ask<=bid:continue
        names[(match.group(1),strike,match.group(3))]=(sym,x,expiry,days)
    pairs=[]
    for expiry_str,strike,side in names:
        if side!="C" or (expiry_str,strike,"P") not in names:continue
        call=names[(expiry_str,strike,"C")]
        put=names[(expiry_str,strike,"P")]
        diff=abs(Decimal(str(call[3]))-7)
        moneyness=abs(strike/index-1)
        pairs.append(((diff,moneyness,call[2],strike,call[0],put[0]),call,put,strike))
    if not pairs:return None
    pairs.sort(key=lambda v:v[0])
    k,c,p,s=pairs[0]
    return {"call":c[0],"put":p[0],"strike_usd":str(s),
            "expiry_utc":timestamp(c[2]),
            "selection_days_to_expiry":str(c[3]),
            "selection_priority":[str(k[0]),str(k[1]),str(k[2]),str(k[3]),k[4],k[5]],
            "all_frozen_eligible_call_put_pairs":len(pairs),
            "original_summary_call_bid":str(c[1].get("bid_price")),
            "original_summary_call_ask":str(c[1].get("ask_price")),
            "original_summary_put_bid":str(p[1].get("bid_price")),
            "original_summary_put_ask":str(p[1].get("ask_price"))}
def first_level(rows,is_bid):
    if not isinstance(rows,list) or not rows:return None
    parsed=[]
    for x in rows:
        if not isinstance(x,list) or len(x)!=2:continue
        p=positive(x[0]);qty=positive(x[1])
        if p is not None and qty is not None:parsed.append((p,qty))
    if not parsed:return None
    return max(parsed,key=lambda z:z[0]) if is_bid else min(parsed,key=lambda z:z[0])
def extract_book(obj,sym,request_utc):
    if not isinstance(obj,dict) or obj.get("instrument_name")!=sym:
        raise SourceError("SOURCE_INSTRUMENT_IDENTITY_MISMATCH")
    bb=first_level(obj.get("bids"),True);aa=first_level(obj.get("asks"),False)
    if bb is None or aa is None or bb[0]>=aa[0]:raise SourceError("NO_UNCROSSED_BID_ASK")
    epoch=obj.get("timestamp")
    if not isinstance(epoch,(int,float)):raise SourceError("NO_EXCHANGE_BOOK_TIMESTAMP")
    age=request_utc.timestamp()-float(epoch)/1000
    if age< -3 or age>10:raise SourceError("BOOK_SOURCE_STALE_OR_FUTURE_CLOCK")
    return {"instrument_name":sym,"best_bid_btc":str(bb[0]),"best_bid_contracts":str(bb[1]),
            "best_ask_btc":str(aa[0]),"best_ask_contracts":str(aa[1]),
            "age_seconds":round(age,3),"exchange_source_timestamp_ms":int(epoch),
            "depth_0p1_sufficient":all(k[1]>=MIN_AMOUNT for k in (bb,aa)),
            "source_book_bids_levels":len(obj.get("bids",[])),
            "source_book_asks_levels":len(obj.get("asks",[]))}
def fee(p):return min(FEE_COEFF,FEE_CAP*p)
def economic(call,put,index):
    a=Decimal(call["best_ask_btc"]);ab=Decimal(call["best_bid_btc"])
    p=Decimal(put["best_ask_btc"]);pb=Decimal(put["best_bid_btc"])
    entry_fees=(fee(a)+fee(p))*MIN_AMOUNT
    exit_fees=(fee(ab)+fee(pb))*MIN_AMOUNT
    entry_premium=(a+p)*MIN_AMOUNT
    exit_bid=(ab+pb)*MIN_AMOUNT
    spread_friction=entry_premium-exit_bid
    total_friction=spread_friction+entry_fees+exit_fees
    return {
      "frozen_min_contracts_per_leg":str(MIN_AMOUNT),
      "actual_0p1_book_depth_sufficient_both_legs":bool(call["depth_0p1_sufficient"] and put["depth_0p1_sufficient"]),
      "call_best_bid_btc":str(ab),"call_best_ask_btc":str(a),
      "put_best_bid_btc":str(pb),"put_best_ask_btc":str(p),
      "combined_entry_premium_btc_before_fee":str(entry_premium),
      "combined_buy_entry_fees_btc":str(entry_fees),
      "combined_exit_proceeds_at_best_bid_btc_before_fee":str(exit_bid),
      "combined_sell_exit_fees_btc":str(exit_fees),
      "combined_straddle_cross_spread_cost_btc":str(spread_friction),
      "instant_hypothetical_roundtrip_total_cost_btc":str(total_friction),
      "instant_hypothetical_roundtrip_total_cost_usd_at_index":str(total_friction*index),
      "combined_entry_premium_usd_at_index_before_fee":str(entry_premium*index),
      "instant_hypothetical_cost_over_entry_premium_pct":str(total_friction/entry_premium*100),
      "real_option_fills_observed":False,
      "independent_positive_option_fair_value_observed":False,
      "actual_option_expected_profit_proven":False,
      "fee_formula_deribit_standard_per_contract":"min(0.0003 BTC,0.125*observed_executed_option_price_BTC)*contract_count",
      "snapshot_bidask_not_guaranteed_fill":True}
def official_get(op,params,name,receipt):
    url=BASE+"/"+op+"?"+urllib.parse.urlencode(params)
    rec={"name":name,"url":url,"request_started_utc":timestamp(now())}
    receipt["http_sources"].append(rec)
    req=urllib.request.Request(url,method="GET",headers={
        "Accept":"application/json","User-Agent":"CryptoLab-OneShot-RealOptionQuoteSourceOnly/1.0"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=15) as response:
            rec["http_status"]=response.status
            if response.status!=200:raise SourceError("HTTP_NOT_200")
            raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES or not raw:raise SourceError("BODY_MISSING_OR_OVERSIZE")
        rec["raw_body_sha256"]=hashlib.sha256(raw).hexdigest()
        rec["body_bytes"]=len(raw)
        rec["response_received_utc"]=timestamp(now())
        (ROOT/("ORIGINAL_"+name+".json")).write_bytes(raw)
        data=json.loads(raw)
        if not isinstance(data,dict) or data.get("error"):
            raise SourceError("DERIBIT_API_ERROR")
        if "result" not in data:raise SourceError("JSONRPC_RESULT_MISSING")
        rec["schema_keys"]=sorted(data.keys())
        return data["result"]
    except Exception as exc:
        rec["error"]=type(exc).__name__+":"+str(exc)[:200]
        raise
def synthetics():
    a={"instrument_name":"BTC-06NOV26-100000-C","timestamp":int(now().timestamp()*1000),
       "bids":[[.008,2]],"asks":[[.009,1]]}
    p={"instrument_name":"BTC-06NOV26-100000-P","timestamp":int(now().timestamp()*1000),
       "bids":[[.007,1]],"asks":[[.008,1]]}
    c=extract_book(a,a["instrument_name"],now())
    put=extract_book(p,p["instrument_name"],now())
    e=economic(c,put,Decimal("100000"))
    assert Decimal(e["instant_hypothetical_roundtrip_total_cost_btc"])>0
    assert fee(Decimal("0.001"))==Decimal("0.000125")
    assert fee(Decimal("0.01"))==Decimal("0.0003")
    assert e["actual_option_expected_profit_proven"] is False
    assert c["depth_0p1_sufficient"] and put["depth_0p1_sufficient"]
    assert extract_pair([],Decimal("100000"),now()) is None
    return "OFFLINE_SYNTHETIC_GUARD_PASS"
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    receipt={"freeze_commit":FROZEN_COMMIT,"study":"TRUE_DERIBIT_PUBLIC_BTC_OPTIONS_CALL_PUT_ORDERBOOK_ECONOMIC_SOURCE_V01",
             "started_utc":timestamp(now()),"status":"PUBLIC_SOURCE_UNAVAILABLE",
             "source_only_no_history_or_future_outcomes":True,
             "http_sources":[],"private_api_requests":0,"live_orders":0,"wallet_reads":0,
             "money_spent":0,"main_modified":False,"swiss_individual_option_eligibility_proven":False,
             "net_economic_edge_certified":False}
    try:
        receipt["synthetic_guards"]=synthetics()
        # Exactly two public meta calls, then frozen option pair selection.
        index_obj=official_get("public/get_index_price",{"index_name":"btc_usd"},"btc_usd_index",receipt)
        index=positive(index_obj.get("index_price")) if isinstance(index_obj,dict) else None
        if index is None:raise SourceError("OFFICIAL_BTC_INDEX_PRICE_MISSING")
        receipt["official_btc_index_usd"]=str(index)
        arr=official_get("public/get_book_summary_by_currency",
                         {"currency":"BTC","kind":"option"},"btc_option_summaries",receipt)
        if not isinstance(arr,list):raise SourceError("BTC_OPTION_CATALOG_NOT_LIST")
        receipt["original_btc_option_summaries_count"]=len(arr)
        receipt["frozen_candidate_selection_time_utc"]=timestamp(now())
        chosen=extract_pair(arr,index,now())
        receipt["frozen_selected_pair"]=chosen
        if chosen is None:
            receipt["status"]="CANDIDATE_PAIR_NOT_FOUND"
            raise SourceError("NO_FROZEN_3_TO_14DAY_STRIKE_CLOSE_PAIR_WITH_CROSSABLE_BBO")
        # After frozen selection, exactly two book GETs; never search for a nicer quote.
        out={}
        for kind in ("call","put"):
            sym=chosen[kind]
            book_obj=official_get("public/get_order_book",
              {"instrument_name":sym,"depth":5},kind+"_selected_option_book",receipt)
            out[kind]=extract_book(book_obj,sym,now())
        receipt["actual_selected_live_public_option_books"]=out
        if not all(v["depth_0p1_sufficient"] for v in out.values()):
            receipt["status"]="BOOK_NOT_AFFORDABLE_AT_FROZEN_MIN_SIZE"
        else:
            receipt["economic_witness"]=economic(out["call"],out["put"],index)
            receipt["status"]="REAL_BTC_OPTION_BOOK_BOTH_SIDES_SOURCE_PASS_NO_NET_EDGE_PROVEN"
    except Exception as e:
        receipt["error"]=type(e).__name__+":"+str(e)[:250]
    finally:
        receipt["finished_utc"]=timestamp(now())
        (ROOT/"receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
        print("DERIBIT_REAL_OPTIONS_PUBLIC_BOOK_SOURCE_VERDICT",json.dumps(receipt,sort_keys=True),flush=True)
    if receipt["status"]!="REAL_BTC_OPTION_BOOK_BOTH_SIDES_SOURCE_PASS_NO_NET_EDGE_PROVEN":
        raise SystemExit(2)
if __name__=="__main__":main()
