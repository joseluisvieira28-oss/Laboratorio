#!/usr/bin/env python3
"""FROZEN OCT 1-2 NVDA Event10m retrospective index-proxy discovery ONLY.

Exact immutable November rule, adapted to pre-exposed Oct dates (NOT changing
production date guard). No real order, no real Event Futures payout/settlement.
"""
import collections,datetime as dt,hashlib,json,math,pathlib
import nvda_oct01_02_source_gate_v01 as sg

OUT=pathlib.Path("artifacts/nvda_event10m_oct01_02")
DAYS=sg.DAYS
EXPECTED_SHA={
 "YAHOO":"b7ce782e2f37675191ecd5a0938be9fdd7f3ea1e2ec2517911d",
 "2026-10-01":"422a190f2b0b4e5b883a2b52ec88b75db63cb4f95805a5b86ef6c37cbf9eb34b",
 "2026-10-02":"f0829459f63a61efd5bfad8d3d1fc1f78a993d85da3dc73730fad77046736282",
}
Q=(0.80,0.85)
def positive(x):
    return x is not None and isinstance(x,(float,int)) and math.isfinite(float(x)) and float(x)>0

def market_raw():
    yahoo_url=("https://query1.finance.yahoo.com/v8/finance/chart/NVDA?"+
        sg.urllib.parse.urlencode({"period1":int(sg.START.timestamp()),
                                 "period2":int(sg.END.timestamp()),
                                 "interval":"1m","includePrePost":"false"}))
    cash_raw,receipt=sg.get(yahoo_url)
    if receipt["response_sha256"]!=EXPECTED_SHA["YAHOO"]:
        raise RuntimeError("YAHOO_RAW_HASH_CHANGED__NO_OUTCOMES_AUTHORIZED")
    chart=cash_raw.get("chart") or {}
    rows=chart.get("result") or []
    if chart.get("error") or len(rows)!=1 or (rows[0].get("meta") or {}).get("symbol")!="NVDA":
        raise RuntimeError("WRONG_YAHOO_CASH_SOURCE")
    item=rows[0]
    quotes=(item.get("indicators") or {}).get("quote") or []
    if len(quotes)!=1:raise RuntimeError("YAHOO_CASH_SCHEMA")
    cash=build_table(item.get("timestamp"),quotes[0].get("open"),quotes[0].get("close"))
    idx={}
    receipts={"YAHOO":receipt}
    for day in DAYS:
        start=sg.ts(day,13,20);end=sg.ts(day,15,40)
        url=("https://contract.mexc.com/api/v1/contract/kline/index_price/NVIDIA_USDT?"+
            sg.urllib.parse.urlencode({"interval":"Min1","start":start,"end":end}))
        raw,rec=sg.get(url)
        if rec["response_sha256"]!=EXPECTED_SHA[day]:
            raise RuntimeError("MEXC_RAW_HASH_CHANGED__"+day)
        if raw.get("success") is not True or not isinstance(raw.get("data"),dict):
            raise RuntimeError("MEXC_INDEX_SOURCE_SCHEMA")
        d=raw["data"]
        idx[day]=build_table(d.get("time"),d.get("open"),d.get("close"))
        receipts[day]=rec
    return cash,idx,receipts

def build_table(ts,opening,closing):
    if not isinstance(ts,list) or not isinstance(opening,list) or not isinstance(closing,list) or not(len(ts)==len(opening)==len(closing)):
        raise ValueError("SOURCE_ARRAY_SCHEMA")
    table={}
    for t,op,cl in zip(ts,opening,closing):
        if t is None:continue
        try:t=int(t)
        except (ValueError,TypeError):continue
        if t%60:raise ValueError("NON_MINUTE_TIMESTAMP")
        if t in table:raise ValueError("DUPLICATE_SOURCE_MINUTE")
        # Restrict all positive/finite validation to actual needed bars only below.
        table[t]=(op,cl)
    return table

def price(table,t,kind):
    if t not in table:raise ValueError("REQUIRED_SOURCE_BAR_MISSING")
    p=table[t][0 if kind=="open" else 1]
    if not positive(p):raise ValueError("REQUIRED_SOURCE_PRICE_INVALID")
    return float(p)

def frozen_signal(cash_old,cash_recent,index_old,index_recent):
    """Exact November frozen sign, >=10bps cash, >=5bps lag gap."""
    b_cash=10000.0*(cash_recent/cash_old-1)
    b_idx=10000.0*(index_recent/index_old-1)
    gap=b_cash-b_idx
    qualified=abs(b_cash)>=10 and abs(gap)>=5 and b_cash*gap>0
    side="UP" if qualified and b_cash>0 else ("DOWN" if qualified else "ABSTAIN")
    cash_only="UP" if abs(b_cash)>=10 and b_cash>0 else "DOWN" if abs(b_cash)>=10 else "ABSTAIN"
    return side,cash_only,b_cash,b_idx,gap

def outcome(side,entry,expiry):
    if side=="ABSTAIN":return "ABSTAIN"
    if expiry==entry:return "TIE"
    return "WIN" if ((expiry>entry)==(side=="UP")) else "LOSS"

def aggregate(records,side_key,eligible=None):
    selected=[x for x in records if x[side_key]!="ABSTAIN" and (eligible is None or eligible(x))]
    counts=collections.Counter(x[side_key+"_outcome"] for x in selected)
    n=len(selected);w=counts["WIN"];loss=counts["LOSS"];ties=counts["TIE"]
    return {"n":n,"wins":w,"losses":loss,"ties":ties,
       "accuracy_ex_ties":w/(w+loss) if w+loss else None,
       "ev_hypothetical_q80":(0.8*w-loss)/n if n else None,
       "ev_hypothetical_q85":(0.85*w-loss)/n if n else None}

def evaluate(cash,indexes):
    result=[]
    for day in DAYS:
        slots,needed_cash,needed_index=sg.required(day)
        index=indexes[day]
        for t in slots:
            # 1m bar starts are frozen t-4 and t-1; cash/index last closed
            # before decision time t+10s, no same-minute feature.
            old=t-240;recent=t-60
            c_old=price(cash,old,"close");c_recent=price(cash,recent,"close")
            i_old=price(index,old,"close");i_recent=price(index,recent,"close")
            side,cash_only,b_cash,b_idx,gap=frozen_signal(c_old,c_recent,i_old,i_recent)
            # Minute OPEN(t) and OPEN(t+10) are approximate *index-price*
            # proxies at 10 sec before modeled entry and expiry.
            first=price(index,t,"open");last=price(index,t+600,"open")
            base={"UTC_decision_boundary":dt.datetime.fromtimestamp(t,dt.timezone.utc).isoformat(),
              "NY_decision_clock":dt.datetime.fromtimestamp(t,dt.timezone(dt.timedelta(hours=-4))).isoformat(),
              "hypothetical_decision_ms":(t+10)*1000,
              "expiry_target_ms":(t+610)*1000,
              "cash_3m_bps":b_cash,"mexc_index_3m_bps":b_idx,"cash_minus_index_bps":gap,
              "index_proxy_entry":first,"index_proxy_expiry":last,
              "signal":side,"cash_only":cash_only,
              "signal_outcome":outcome(side,first,last),
              "cash_only_outcome":outcome(cash_only,first,last),
              "always_up":"UP","always_up_outcome":outcome("UP",first,last),
              "always_down":"DOWN","always_down_outcome":outcome("DOWN",first,last),
              "ny_day":day}
            result.append(base)
    if len(result)!=24:raise ValueError("FROZEN_24_SLOTS_NOT_PRESENT")
    return result

def total(rows):
    result={}
    result["qualified_candidate"]=aggregate(rows,"signal")
    result["cash_only_all_impulses"]=aggregate(rows,"cash_only")
    result["always_up_all_slots"]=aggregate(rows,"always_up")
    result["always_down_all_slots"]=aggregate(rows,"always_down")
    for key in ("cash_only","always_up","always_down"):
        result["matched_qualified_"+key]=aggregate(rows,key,lambda row:row["signal"]!="ABSTAIN")
    result["candidate_up_count"]=sum(x["signal"]=="UP" for x in rows)
    result["candidate_down_count"]=sum(x["signal"]=="DOWN" for x in rows)
    result["abstentions"]=sum(x["signal"]=="ABSTAIN" for x in rows)
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"study":"NVIDIA_EVENT10M_CASH_LAG_OCT01_02_HIST_REPLAY_V01",
       "status":"BLOCKED_BEFORE_RESULTS","window":"2026-10-01_and_2026-10-02",
       "pre_outcome_freeze_commit":"54bb0766a5444db3ebc046ad385dc7015e5f45b9",
       "model_logic":"FROZEN_NOVEMBER_CASH_3M_10BPS_GAP_5BPS_SAME_SIGN",
       "symbols":["NVDA","NVIDIA_USDT"],"fixed_slots_total":24,
       "protected_NVDA_Oct05_30_forward_opened":False,
       "protected_September_holdout_opened":False,
       "historical_Event_Futures_payout_available":False,
       "hypothetical_payout_q80":0.8,
       "historical_product_online_status":"UNKNOWN",
       "historical_data_asof_receipts":"UNAVAILABLE",
       "proxy_price_type":"MEXC_STANDARD_FUTURES_INDEX_OPEN_MIN1_NOT_SERVER_EVENT_ORDER_PRICE",
       "model_decision_at_second":10,
       "minute_proxy_time_mismatch_seconds":10,
       "economic_verdict":"HISTORICAL_DISCOVERY_ONLY__NO_CERTIFIED_EDGE",
       "receipts":{},"rows":[]}
    try:
        cash,idx,receipts=market_raw()
        report["receipts"]=receipts
        report["rows"]=evaluate(cash,idx)
        report["summary"]=total(report["rows"])
        report["by_day"]={day:total([x for x in report["rows"] if x["ny_day"]==day]) for day in DAYS}
        report["status"]="HISTORICAL_PROXY_REPLAY_COMPLETED"
    except Exception as e:
        report["error"]=type(e).__name__+":"+str(e)[:220]
        raise
    finally:
        (OUT/"historical_proxy_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2,sort_keys=True),flush=True)

if __name__=="__main__":main()
