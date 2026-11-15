#!/usr/bin/env python3
"""LIQUIDATION EXHAUSTION economic forward V1: deterministic causal quote-proxy evaluation.
RESEARCH ONLY. No API auth, orders or actual fills. Primary protocol pre-frozen in
ECONOMIC_FORWARD_FREEZE_2026-11-04.md. Never test old PR #332 source sample as edge.
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from statistics import mean, median

DURATION_MS=420_000
BASE_COST_BPS=20.0  # 16bps fee + 4bps extra slippage; bid/ask charged in gross
STRESS_COST_BPS=40.0  # 32bps fee + 8bps extra slippage

def n(x):
    q=float(x)
    if not (0 < q < float("inf")):
        raise ValueError("PRICE_OR_SIZE_NONPOSITIVE")
    return q

def book_update(book, msg, recv, previous):
    data=msg["data"]
    sym=data["s"]
    if sym!="BTCUSDT":return previous
    u, seq=data["u"],data["seq"]
    if msg["type"]=="snapshot":
        book["b"].clear();book["a"].clear()
    else:
        if previous is None or u != previous[0]+1 or seq < previous[1]:
            raise ValueError("BYBIT_ORDERBOOK_SEQUENCE_GAP")
    if abs(recv-msg["ts"])>2000:
        raise ValueError("BYBIT_BOOK_STALE")
    for side in ("b","a"):
        for p,qty in data[side]:
            p=float(p);qty=float(qty)
            if qty==0:book[side].pop(p,None)
            elif qty>0:book[side][p]=qty
            else:raise ValueError("NEGATIVE_BOOK_SIZE")
    if not book["b"] or not book["a"]:raise ValueError("EMPTY_BYBIT_BOOK")
    bid=max(book["b"]);ask=min(book["a"])
    if bid>=ask:raise ValueError("CROSSED_BYBIT_BOOK")
    bq=sum(q for _,q in sorted(book["b"].items(),reverse=True)[:5])
    aq=sum(q for _,q in sorted(book["a"].items())[:5])
    return (u,seq,round((bid+ask)/2,8),10000*(ask-bid)/((bid+ask)/2),bq/aq if aq else 0)

def mexc_quote(obj, recv):
    if obj.get("success") is not True or not isinstance(obj.get("data"),dict):
        raise ValueError("MEXC_DEPTH_RESPONSE_INVALID")
    d=obj["data"]
    bids=d.get("bids");asks=d.get("asks")
    if not bids or not asks or not isinstance(d.get("timestamp"),int):
        raise ValueError("MEXC_DEPTH_MISSING")
    bid=max(n(x[0]) for x in bids)
    ask=min(n(x[0]) for x in asks)
    if bid>=ask:raise ValueError("MEXC_CROSSED_BOOK")
    lag=recv-d["timestamp"]
    if lag<0 or lag>2000:raise ValueError("MEXC_DEPTH_STALE")
    return (recv,bid,ask,lag)

def net_bps(side, entry, exit_):
    _, eb, ea, _=entry
    _, xb, xa, _=exit_
    if side=="Buy":  # long liquidation -> forced SELL -> reversal LONG
        gross=10000*(xb/ea-1)
    elif side=="Sell":
        gross=10000*(eb/xa-1)
    else:raise ValueError("INVALID_LIQ_SIDE")
    return (gross,gross-BASE_COST_BPS,gross-STRESS_COST_BPS)

def preceding(times,events,target,age):
    i=bisect_right(times,target)-1
    if i<0:return None
    x=events[i]
    if target-x[0]>age:return None
    return x

def first_after(times,events,target,tolerance):
    i=bisect_left(times,target)
    if i>=len(events):return None
    x=events[i]
    if x[0]-target>tolerance:return None
    return x

def run(path):
    raw=Path(path).read_bytes()
    raw_sha=hashlib.sha256(raw).hexdigest()
    book={"b":{},"a":{}}
    last_book=None
    book_events=[];trades=[];liqs=[];mexc=[]
    counts=Counter();errors=[];last_received=-1
    started=None
    for lineno,line in enumerate(raw.splitlines(),1):
        try:
            env=json.loads(line)
            recv=env["received_utc_ms"]
            if type(recv)!=int or recv<last_received:raise ValueError("RECEIVE_ORDER_REGRESSION")
            last_received=recv
            if started is None:started=recv
            venue=env["venue"]
            msg=env["payload"]
            if venue=="BYBIT":
                if not isinstance(msg,dict):raise ValueError("BYBIT_NOT_OBJECT")
                topic=msg.get("topic")
                if topic=="orderbook.50.BTCUSDT":
                    last_book=book_update(book,msg,recv,last_book)
                    book_events.append((recv,last_book[2],last_book[3],last_book[4]))
                    counts["bybit_book"]+=1
                elif topic=="publicTrade.BTCUSDT":
                    for row in msg["data"]:
                        if row["s"]!="BTCUSDT" or recv-row["T"]<0 or recv-row["T"]>2000:
                            raise ValueError("BYBIT_TRADE_BAD_TIME")
                        n(row["v"]);n(row["p"])
                        trades.append((recv,row["S"]))
                        counts["bybit_trade_children"]+=1
                elif topic=="allLiquidation.BTCUSDT":
                    for row in msg["data"]:
                        if row["s"]!="BTCUSDT" or row["S"] not in ("Buy","Sell"):
                            raise ValueError("BYBIT_LIQ_BAD_SCHEMA")
                        if recv-row["T"]<0 or recv-row["T"]>2000:
                            raise ValueError("BYBIT_LIQ_BAD_TIME")
                        liqs.append((recv,row["S"],n(row["p"])*n(row["v"])))
                        counts["bybit_liq_children"]+=1
                elif topic is None:
                    if msg.get("op")=="subscribe" and msg.get("success") is False:
                        raise ValueError("BYBIT_SUBSCRIBE_REJECTED")
                else:
                    raise ValueError("UNEXPECTED_BYBIT_TOPIC")
            elif venue=="MEXC":
                mexc.append(mexc_quote(msg,recv))
                counts["mexc_quotes"]+=1
            else:raise ValueError("UNKNOWN_VENUE")
        except Exception as e:
            if len(errors)<30:errors.append(f"line_{lineno}:{type(e).__name__}:{str(e)[:110]}")
    source_quality=bool(started is not None and not errors and
        counts["bybit_book"]>20 and counts["bybit_trade_children"]>20 and counts["mexc_quotes"]>20 and
        last_received-started>=DURATION_MS-5000)
    m_times=[x[0] for x in mexc]
    b_times=[x[0] for x in book_events]
    t_times=[x[0] for x in trades]
    if any(m_times[i]-m_times[i-1]>4500 for i in range(1,len(m_times))):
        source_quality=False
        errors.append("MEXC_SNAPSHOT_GAP_OVER_4500MS")
    if any(b_times[i]-b_times[i-1]>1000 for i in range(1,len(b_times))):
        source_quality=False
        errors.append("BYBIT_BOOK_GAP_OVER_1000MS")
    liqs.sort(key=lambda x:x[0])
    episodes=[]
    last_trigger=-10**30
    for i,(now,side,notional) in enumerate(liqs):
        if started is None or now-started<60000 or now>started+DURATION_MS-90000:
            continue
        if now-last_trigger<120000:continue
        window=[x for x in liqs if now-10000<=x[0]<=now]
        if any(x[1]!=side for x in window):continue
        if len(window)<2 or sum(x[2] for x in window)<100000:continue
        before=preceding(b_times,book_events,now,1000)
        if before is None:continue
        last_trigger=now
        item={"trigger_ms":now,"side":side,"liquidation_children":len(window),
              "notional_bankruptcy_proxy_usd":round(sum(x[2] for x in window),2)}
        decision=first_after(b_times,book_events,now+5000,1000)
        if decision is None:
            item["status"]="NO_DECISION_BOOK"
        elif any(now<x[0]<=decision[0] for x in liqs):
            item["status"]="LIQUIDATION_CONTINUED"
        elif preceding(t_times,trades,decision[0],1000) is None:
            item["status"]="TRADE_STALE"
        elif decision[2]>3:
            item["status"]="SPREAD_WIDE"
        elif not ((side=="Buy" and (decision[1]/before[1]-1)*10000>=1.5 and decision[3]>=1.15) or
                   (side=="Sell" and (before[1]/decision[1]-1)*10000>=1.5 and decision[3]<=1/1.15)):
            item["status"]="EXHAUSTION_NOT_CONFIRMED"
        elif preceding(m_times,mexc,decision[0],1500) is None:
            item["status"]="MEXC_DECISION_QUOTE_MISSING"
        else:
            item["decision_ms"]=decision[0]
            entry=first_after(m_times,mexc,decision[0]+15000,1500)
            exit_=first_after(m_times,mexc,entry[0]+60000,1500) if entry else None
            if entry is None or exit_ is None:
                item["status"]="ENTRY_EXIT_QUOTE_MISSING"
            else:
                gross,base,stress=net_bps(side,entry,exit_)
                item.update(status="QUOTE_PROXY_COMPLETE",entry_ms=entry[0],exit_ms=exit_[0],
                            gross_quote_bps=round(gross,6),
                            primary_net_bps=round(base,6),
                            stress_net_bps=round(stress,6))
        episodes.append(item)
    valid=[x for x in episodes if x["status"]=="QUOTE_PROXY_COMPLETE"]
    dates={datetime.fromtimestamp(x["trigger_ms"]/1000,timezone.utc).strftime("%Y-%m-%d") for x in valid}
    if not source_quality:
        verdict="SOURCE_BLOCKED"
    elif len(valid)<60 or len(dates)<14:
        verdict="UNDERPOWERED_FORWARD"
    else:
        # No candidate verdict without pre-specified day-cluster bootstrap and
        # verified executable route/fees. Fail closed, never auto-promote.
        verdict="PROTOCOL_BLOCKED_INDEPENDENT_ECONOMIC_ADJUDICATION_REQUIRED"
    return {
        "experiment":"LIQUIDATION_EXHAUSTION_ECONOMIC_FORWARD_V1",
        "raw_sha256":raw_sha,"raw_lines":len(raw.splitlines()),
        "source_quality_pass":source_quality,"errors":errors,
        "source_counts":dict(counts),"episodes_triggered":len(episodes),
        "primary_quote_pairs":len(valid),
        "utc_days_with_quote_pairs":len(dates),
        "episode_status_counts":dict(Counter(x["status"] for x in episodes)),
        "primary_mean_net_bps_DESCRIPTIVE_UNDERPOWERED":round(mean(x["primary_net_bps"] for x in valid),6) if valid else None,
        "primary_median_net_bps_DESCRIPTIVE_UNDERPOWERED":round(median(x["primary_net_bps"] for x in valid),6) if valid else None,
        "stress_mean_net_bps_DESCRIPTIVE_UNDERPOWERED":round(mean(x["stress_net_bps"] for x in valid),6) if valid else None,
        "episodes":episodes,"verdict":verdict,
        "profit_certified":False,"actual_fills":0,"orders_placed":0,
        "mexc_account_fees_verified":False,"mexc_quote_is_fill":False,
        "previous_2026_11_04_source_window_excluded":True
    }

def synthetic_test():
    e=(1,100.0,101.0,0); x=(2,102.0,103.0,0)
    g,b,s=net_bps("Buy",e,x)
    assert round(g,6)==round(10000*(102/101-1),6)
    assert abs((g-b)-20)<1e-6 and abs((g-s)-40)<1e-6
    g2,b2,s2=net_bps("Sell",x,e)
    assert round(g2,6)==round(10000*(102/101-1),6)
    assert preceding([5,10],[(5,"old"),(10,"new")],9,10)==(5,"old")
    assert first_after([5,10],[(5,"old"),(10,"new")],6,3) is None
    try:mexc_quote({"success":True,"data":{"bids":[[101,1]],"asks":[[100,1]],"timestamp":1000}},1001)
    except ValueError:pass
    else:raise AssertionError("CROSSED_BOOK_NOT_REJECTED")
    print("SYNTHETIC_NO_LOOKAHEAD_AND_COST_GUARDS_PASS_NOT_ECONOMIC_EVIDENCE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw",type=Path)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test:synthetic_test()
    else:
        if not a.raw or not a.out:ap.error("--raw and --out required")
        result=run(a.raw)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if k!="episodes"},indent=2,sort_keys=True))
