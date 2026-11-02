#!/usr/bin/env python3
"""Strict independent replay of original SHA-verified official BTC option books, not importer of primary code."""
import datetime as dt
import hashlib
import json
import pathlib
import re
from decimal import Decimal

D=pathlib.Path("original")
OUT=pathlib.Path("artifacts/deribit_btc_option_book_original_sha_independent_audit_v01a")
OUT.mkdir(parents=True,exist_ok=True)
SHA={
"btc_usd_index":"55e6caffd1e833afd55cde0644a2d2d680423f4b52bdf0837c236961b06e8707",
"btc_option_summaries":"064a9d4c6d840b2db0f10369f37ab2d27978c55a6da22cb02c3525ba42e0881e",
"call_selected_option_book":"443891262500b9cd96e5fea108cb119321ac247f9d671e3f835330f527dc7fed",
"put_selected_option_book":"00c62663a51067e4dc14ead517088b63ed6427caf4662c5bc37584cbf5950925"}
def V(x):return Decimal(str(x))
def load(key):
    raw=(D/("ORIGINAL_"+key+".json")).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA[key]:raise ValueError("ORIGINAL_SOURCE_BODY_SHA256_CHANGED_"+key)
    j=json.loads(raw)
    if j.get("testnet") is not False:raise ValueError("NOT_DERIBIT_PRODUCTION_JSON_"+key)
    if j.get("error") or "result" not in j:raise ValueError("INVALID_DERIBIT_PUBLIC_JSON_"+key)
    return j["result"]
def independent_pick(raw,index,at):
    symrx=re.compile(r"^BTC-([0-9]{1,2}[A-Z]{3}[0-9]{2})-([0-9]+)-([CP])$")
    valid={}
    for s in raw:
        m=symrx.fullmatch(str(s.get("instrument_name","")))
        if not m:continue
        ex=dt.datetime.strptime(m.group(1),"%d%b%y").replace(hour=8,tzinfo=dt.timezone.utc)
        days=V((ex-at).total_seconds())/Decimal(86400)
        strike=V(m.group(2))
        if not (3<=days<=14 and abs(strike/index-1)<=Decimal("0.025")):continue
        bid=s.get("bid_price");ask=s.get("ask_price")
        if bid is None or ask is None:continue
        if V(bid)<=0 or V(ask)<=V(bid):continue
        valid[(m.group(1),strike,m.group(3))]=(s["instrument_name"],ex,days)
    pairs=[]
    for e,strike,side in valid:
        if side!="C" or (e,strike,"P") not in valid:continue
        c=valid[(e,strike,"C")];p=valid[(e,strike,"P")]
        pairs.append(((abs(c[2]-7),abs(strike/index-1),c[1],strike,c[0],p[0]),c[0],p[0]))
    pairs.sort(key=lambda x:x[0])
    if not pairs:raise ValueError("NO_PAIR_UNDER_IDENTICAL_PRE_SOURCE_RULE")
    return pairs[0][1],pairs[0][2],len(pairs)
def original_best(data,sym,read_utc):
    if data.get("instrument_name")!=sym:raise ValueError("ORIGINAL_BOOK_INSTRUMENT_ID_DIFFERENT")
    if "timestamp" not in data:raise ValueError("NO_ORIGINAL_EXCHANGE_TIMESTAMP")
    age=read_utc.timestamp()-data["timestamp"]/1000
    if not(-3<=age<=10):raise ValueError("ORIGINAL_BOOK_TIMESTAMP_AGE_INVALID")
    bids=data.get("bids");asks=data.get("asks")
    if not isinstance(bids,list) or not isinstance(asks,list) or not bids or not asks:
        raise ValueError("NO_ORIGINAL_DUAL_SIDED_REAL_BOOK")
    if any(len(x)!=2 for x in bids+asks):raise ValueError("ORIGINAL_BOOK_SHAPE_INVALID")
    bids2=[(V(x[0]),V(x[1])) for x in bids]
    asks2=[(V(x[0]),V(x[1])) for x in asks]
    best_bid=max(bids2,key=lambda x:x[0]);best_ask=min(asks2,key=lambda x:x[0])
    if best_bid[0]<=0 or best_ask[0]<=best_bid[0] or best_bid[1]<Decimal(".1") or best_ask[1]<Decimal(".1"):
        raise ValueError("ORIGINAL_ORDERBOOK_MIN_0P1_DEPTH_OR_PRICE_FAILED")
    return best_bid,best_ask,age
def validate():
    original=json.loads((D/"receipt.json").read_text())
    if original.get("status")!="REAL_BTC_OPTION_BOOK_BOTH_SIDES_SOURCE_PASS_NO_NET_EDGE_PROVEN":
        raise ValueError("FIRST_PARTY_GATE_NOT_PASS")
    if original.get("freeze_commit")!="8a67fa44d1ed0148cf5dff19990992cb80d94a33":
        raise ValueError("ORIGINAL_IMMUTABLE_FREEZE_ID_NOT_MATCHED")
    idx=load("btc_usd_index")
    index=V(idx["index_price"])
    if index<=0:raise ValueError("ORIGINAL_BTC_INDEX_NOT_POSITIVE")
    summary=load("btc_option_summaries")
    if not isinstance(summary,list) or len(summary)!=original.get("original_btc_option_summaries_count"):
        raise ValueError("ORIGINAL_OPTION_CATALOG_COUNT_NOT_REPRODUCED")
    at=dt.datetime.fromisoformat(original["frozen_candidate_selection_time_utc"].replace("Z","+00:00"))
    call,put,npairs=independent_pick(summary,index,at)
    if call!=original["frozen_selected_pair"]["call"] or put!=original["frozen_selected_pair"]["put"] or npairs!=original["frozen_selected_pair"]["all_frozen_eligible_call_put_pairs"]:
        raise ValueError("RESELECTED_FROZEN_PAIR_MISMATCH")
    bbo={}
    for side,sym in (("call",call),("put",put)):
        book=load(side+"_selected_option_book")
        item=next(z for z in original["http_sources"] if z["name"]==side+"_selected_option_book")
        read=dt.datetime.fromisoformat(item["response_received_utc"].replace("Z","+00:00"))
        bid,ask,age=original_best(book,sym,read)
        bbo[side]={"bid":bid[0],"ask":ask[0],"bid_contracts":bid[1],"ask_contracts":ask[1],"age_seconds_as_http_receive":age}
        primary=original["actual_selected_live_public_option_books"][side]
        if V(primary["best_bid_btc"])!=bid[0] or V(primary["best_ask_btc"])!=ask[0]:
            raise ValueError("ORIGINAL_BBO_PRICE_MISMATCH_"+side)
        if V(primary["best_bid_contracts"])!=bid[1] or V(primary["best_ask_contracts"])!=ask[1]:
            raise ValueError("ORIGINAL_BBO_DEPTH_MISMATCH_"+side)
    qty=Decimal(".1")
    buy=sum((bbo[x]["ask"] for x in ("call","put")),Decimal("0"))*qty
    sale=sum((bbo[x]["bid"] for x in ("call","put")),Decimal("0"))*qty
    f_buy=sum((min(Decimal(".0003"),Decimal(".125")*bbo[x]["ask"]) for x in ("call","put")),Decimal("0"))*qty
    f_sale=sum((min(Decimal(".0003"),Decimal(".125")*bbo[x]["bid"]) for x in ("call","put")),Decimal("0"))*qty
    spread=buy-sale
    friction=spread+f_buy+f_sale
    field=original["economic_witness"]
    fields={"combined_entry_premium_btc_before_fee":buy,
      "combined_exit_proceeds_at_best_bid_btc_before_fee":sale,
      "combined_buy_entry_fees_btc":f_buy,
      "combined_sell_exit_fees_btc":f_sale,
      "combined_straddle_cross_spread_cost_btc":spread,
      "instant_hypothetical_roundtrip_total_cost_btc":friction,
      "instant_hypothetical_roundtrip_total_cost_usd_at_index":friction*index,
      "combined_entry_premium_usd_at_index_before_fee":buy*index,
      "instant_hypothetical_cost_over_entry_premium_pct":friction/buy*100}
    for key,x in fields.items():
        if abs(V(field[key])-x)>Decimal("1e-12"):raise ValueError("INDEPENDENT_COST_ACCOUNTING_MISMATCH_"+key)
    return {
      "status":"INDEPENDENT_ORIGINAL_DERIBIT_BTC_TRUE_CALLPUT_SOURCE_REPLAY_PASS",
      "original_source_artifact_id":13146457847,
      "original_source_workflow":41455540344,
      "original_public_json_sha256_verifications":4,
      "all_option_summaries_source_count":len(summary),
      "same_expiry_strike_bbo_pairs_frozen_eligible":npairs,
      "independently_selected_call":call,"independently_selected_put":put,
      "original_live_index_usd":str(index),
      "call_bid_btc":str(bbo["call"]["bid"]),"call_ask_btc":str(bbo["call"]["ask"]),
      "put_bid_btc":str(bbo["put"]["bid"]),"put_ask_btc":str(bbo["put"]["ask"]),
      "call_bid_depth_contracts":str(bbo["call"]["bid_contracts"]),
      "call_ask_depth_contracts":str(bbo["call"]["ask_contracts"]),
      "put_bid_depth_contracts":str(bbo["put"]["bid_contracts"]),
      "put_ask_depth_contracts":str(bbo["put"]["ask_contracts"]),
      "min_contracts_per_leg":str(qty),
      "combined_premium_btc":str(buy),
      "combined_premium_usd_index_conversion":str(buy*index),
      "instant_modelled_straddle_roundtrip_spread_btc":str(spread),
      "instant_modelled_straddle_roundtrip_4trades_fee_btc":str(f_buy+f_sale),
      "instant_modelled_straddle_roundtrip_cost_btc":str(friction),
      "instant_modelled_straddle_roundtrip_cost_usd_index_conversion":str(friction*index),
      "instant_modelled_cost_relative_to_entry_premium_pct":str(friction/buy*100),
      "true_option_fill_realized":False,
      "economic_edge_certified":False,
      "net_fair_value_verified":False,
      "swiss_user_account_eligible_verified":False,
      "private_api_calls":0,"orders":0,"money_spent":0}
try:
    result=validate()
except Exception as e:
    result={"status":"INDEPENDENT_ORIGINAL_SOURCE_REPLAY_AUDIT_FAIL",
            "error":type(e).__name__+":"+str(e)[:350],
            "private_api_calls":0,"orders":0,"money_spent":0}
(OUT/"receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print("INDEPENDENT_DERIBIT_REAL_OPTION_BOOK_AND_COST_SOURCE_REPLAY",json.dumps(result,sort_keys=True),flush=True)
if result["status"]!="INDEPENDENT_ORIGINAL_DERIBIT_BTC_TRUE_CALLPUT_SOURCE_REPLAY_PASS":
    raise SystemExit(2)
