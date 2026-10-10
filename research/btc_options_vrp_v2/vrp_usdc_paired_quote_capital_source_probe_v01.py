#!/usr/bin/env python3
"""BTC_USDC 0.01 option pair public one-shot, source/cost and margin only.
No account/auth/private endpoints, orders, PnL, forward outcomes or snapshots bank writes.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, math, os, pathlib, time, urllib.parse, urllib.request, traceback
OUT=pathlib.Path("research/btc_options_vrp_v2/VRP_USDC_001_PAIRED_SOURCE_RESULT_2026_10_10.json")
BASE="https://www.deribit.com/api/v2"
AMOUNT=.01;TARGET_DTE=30.;DTE_MIN=14.;DTE_MAX=60.;FRESH_MAX_MS=30000
def api(method,params):
 t0=int(time.time()*1000)
 url=f"{BASE}/{method}?{urllib.parse.urlencode(params)}"
 req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-VRP-SourceOnly-OneShot-0.1","Accept":"application/json"},method="GET")
 with urllib.request.urlopen(req,timeout=35) as r:
  body=r.read(4_000_001)
  status=r.status
 t1=int(time.time()*1000)
 if len(body)>4_000_000:raise ValueError("RESPONSE_SIZE_CAP_EXCEEDED")
 obj=json.loads(body)
 if "error" in obj:raise ValueError(f"DERIBIT_PUBLIC_ERROR:{method}:{obj['error']}")
 if not isinstance(obj.get("result"),(list,dict)):raise ValueError("DERIBIT_PUBLIC_SCHEMA_INVALID")
 return obj["result"],{"url":url,"http":status,"sha256":hashlib.sha256(body).hexdigest(),
   "request_start_ms":t0,"response_received_ms":t1,"bytes":len(body)}
def safe(x,n):
 a=float(x)
 if not math.isfinite(a) or a<=0:raise ValueError("INVALID_POSITIVE_"+n)
 return a
def top(book,side):
 rows=book.get(side) or []
 if not rows:return None,None
 return safe(rows[0][0],"BEST_"+side),safe(rows[0][1],"SIZE_"+side)
def observe(name):
 b,receipt=api("public/get_order_book",{"instrument_name":name,"depth":5})
 bid,bidqty=top(b,"bids");ask,askqty=top(b,"asks")
 stamp=b.get("timestamp")
 age=receipt["response_received_ms"]-int(stamp) if stamp is not None else None
 valid=(bid is not None and ask is not None and bid<=ask and
   bidqty>=AMOUNT and askqty>=AMOUNT and age is not None and abs(age)<=FRESH_MAX_MS)
 return {"instrument":name,"source":receipt,"source_timestamp_ms":stamp,
   "source_age_ms":age,"fresh_within_30s":age is not None and abs(age)<=FRESH_MAX_MS,
   "bid":bid,"bid_amount":bidqty,"ask":ask,"ask_amount":askqty,
   "mark":b.get("mark_price"),"mark_iv":b.get("mark_iv"),
   "bid_iv":b.get("bid_iv"),"ask_iv":b.get("ask_iv"),
   "index":b.get("index_price"),"underlying":b.get("underlying_price"),
   "quote_valid_for_0_01_instant_2sided":valid}
def fee(index,price):
 return min(.0003*index,.125*price)*AMOUNT
def main():
 now=dt.datetime.now(dt.timezone.utc)
 report={"status":"SOURCE_NOT_YET_CLASSIFIED","diagnostic_at_utc":now.isoformat(),
    "separate_saturday_snapshot_not_thursday_forward_bank":True,
    "source_only":True,"investment_or_profit_prediction":False,"no_future_path":True,
    "returns_computed":False,"pnl_computed":False,"orders":False,"authenticated":False,"live_go":False}
 try:
  index_obj,source_idx=api("public/get_index_price",{"index_name":"btc_usdc"})
  index=safe(index_obj["index_price"],"BTC_USDC_INDEX")
  inst,src_insts=api("public/get_instruments",{"currency":"USDC","kind":"option","expired":"false"})
  now_ms=int(now.timestamp()*1000)
  btc=[x for x in inst if str(x.get("instrument_name","")).startswith("BTC_USDC-") and x.get("is_active",True)]
  pairs={}
  for x in btc:
   exp=x.get("expiration_timestamp"); strike=x.get("strike");typ=x.get("option_type")
   if exp is None or strike is None or typ not in ("call","put"):continue
   exp=int(exp);strike=float(strike)
   dte=(exp-now_ms)/86400000.
   if not DTE_MIN<=dte<=DTE_MAX:continue
   pairs.setdefault((exp,strike),{})[typ]=x
  cands=[]
  for (exp,strike),legs in pairs.items():
   if "call" in legs and "put" in legs:
    cands.append((abs((exp-now_ms)/86400000.-TARGET_DTE),exp,
       abs(math.log(strike/index)),strike,legs))
  cands.sort(key=lambda x:x[:4])
  report.update({"index_btc_usdc":index,"index_receipt":source_idx,
    "instrument_list_receipt":src_insts,"btc_usdc_option_listed":len(btc),
    "same_strike_pair_candidates_14_to_60_dte":len(cands)})
  if not cands:
   report["status"]="SOURCE_BLOCKED_NO_FROZEN_CALL_PUT_PAIR"
  else:
   _,exp,_,strike,legs=cands[0]
   callname=legs["call"]["instrument_name"];putname=legs["put"]["instrument_name"]
   selected={"call":callname,"put":putname,"strike":strike,
    "expiry_ms":exp,"dte":(exp-now_ms)/86400000.,"amount_each_leg":AMOUNT,
    "call_min_trade":legs["call"].get("min_trade_amount"),
    "put_min_trade":legs["put"].get("min_trade_amount"),
    "call_contract_size":legs["call"].get("contract_size"),
    "put_contract_size":legs["put"].get("contract_size")}
   call=observe(callname);put=observe(putname)
   try:perp=observe("BTC_USDC-PERPETUAL")
   except Exception as e:perp={"status":"PUBLIC_PERPETUAL_BOOK_BLOCKED","reason":repr(e)}
   report.update({"selected_pair":selected,"call":call,"put":put,"perpetual":perp})
   cmin=float(legs["call"].get("min_trade_amount") or 1e9)
   pmin=float(legs["put"].get("min_trade_amount") or 1e9)
   ok=(cmin<=AMOUNT and pmin<=AMOUNT and
    call["quote_valid_for_0_01_instant_2sided"] and put["quote_valid_for_0_01_instant_2sided"] and
    isinstance(perp,dict) and perp.get("quote_valid_for_0_01_instant_2sided",False))
   if not ok:
    report["status"]="SOURCE_BLOCKED_OPTION_OR_HEDGE_FRESHNESS_SIZE_OR_MINIMUM"
   else:
    # Price of 1 linear USDC option is USDC per 1 BTC of amount.
    # This is snapshot entry liquidity/friction only. It is NOT a future payoff.
    cb=call["bid"];ca=call["ask"];pb=put["bid"];pa=put["ask"]
    quote_premium=(cb+pb)*AMOUNT
    sell_fee=fee(index,cb)+fee(index,pb)
    immediate_buyback_fee=fee(index,ca)+fee(index,pa)
    cross_spread=(ca-cb+pa-pb)*AMOUNT
    under=safe(call.get("underlying") or call.get("index") or index,"BTC_UNDERLYING")
    mark_c=safe(call.get("mark"),"CALL_MARK");mark_p=safe(put.get("mark"),"PUT_MARK")
    im_call=(max(.15-max(strike-under,0.)/under,.10)*index+mark_c)*AMOUNT
    im_put=(max((.15-max(under-strike,0.)/under)*index,.10*strike)+mark_p)*AMOUNT
    total_im=im_call+im_put
    report["status"]="PAIRED_ENTRY_BBO_SOURCE_PASS_ONLY_NOT_EXECUTION_OR_PNL"
    report["source_only_hypothetical_microstructure"]={
     "sell_bid_premium_received_usdc":round(quote_premium,8),
     "two_option_sell_open_taker_fees_usdc":round(sell_fee,8),
     "instant_opposite_quote_buyback_spread_cost_usdc":round(cross_spread,8),
     "instant_opposite_quote_buyback_fees_usdc":round(immediate_buyback_fee,8),
     "instant_round_trip_friction_usdc":round(sell_fee+immediate_buyback_fee+cross_spread,8),
     "instant_round_trip_friction_as_pct_of_bid_premium":round(100*(sell_fee+immediate_buyback_fee+cross_spread)/quote_premium,5) if quote_premium>0 else None,
     "gross_call_short_standard_initial_margin_usdc":round(im_call,8),
     "gross_put_short_standard_initial_margin_usdc":round(im_put,8),
     "gross_pair_standard_margin_proxy_usdc":round(total_im,8),
     "margin_proxy_to_received_premium_multiple":round(total_im/quote_premium,5) if quote_premium>0 else None,
     "perp_hedge_margin_and_future_funding":"NOT_MODELED",
     "short_options_worst_case_loss":"NOT_CAPPED_BY_INITIAL_MARGIN",
     "future_exit_fee":"UNKNOWN_FUTURE_PREMIUM",
     "unwind_price_status":"SAME_SNAPSHOT_CROSS_QUOTE_ONLY_NOT_ACTUAL_TRADE"}
  OUT.parent.mkdir(parents=True,exist_ok=True)
  OUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
  print("VRP_USDC_PUBLIC_PAIR_SOURCE_GATE",json.dumps({
   "status":report["status"],"selected":report.get("selected_pair"),
   "call":{k:report.get("call",{}).get(k) for k in ("bid","ask","bid_amount","ask_amount","source_age_ms")},
   "put":{k:report.get("put",{}).get(k) for k in ("bid","ask","bid_amount","ask_amount","source_age_ms")},
   "hedge":{k:report.get("perpetual",{}).get(k) for k in ("bid","ask","source_age_ms")},
   "costs":report.get("source_only_hypothetical_microstructure"),
   "no_performance_test":True},sort_keys=True),flush=True)
 except Exception as e:
  report["status"]="SOURCE_OR_CALCULATION_BLOCKED";report["reason"]=repr(e)
  OUT.parent.mkdir(parents=True,exist_ok=True)
  OUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
  traceback.print_exc()
if __name__=="__main__":main()
