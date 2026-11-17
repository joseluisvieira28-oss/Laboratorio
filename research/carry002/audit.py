#!/usr/bin/env python3
"""ETH 8/12wk cross-venue collateral stress from CARRY-001 official-source artifacts.
READ ONLY; no orders, accounts or execution. All model profits are mark proxies.
CARRY-001 horizons were chosen POST-HOC; not new prospective confirmation.
"""
import csv,datetime as dt,hashlib,json,pathlib,collections
OUT=pathlib.Path("carry002-evidence");OUT.mkdir(exist_ok=True)
SOURCE=pathlib.Path("carry001-evidence")
HOUR=3600000
SHA={
"extended_funding_events.csv":"a7fdd25b7155ca1a81db7aba0d9e6d7d4ee43c070d4cc15de98114a80c935ce0",
"price_candles.csv":"8bbef4ef4d412a06c080d0fb2741c2857edfbdca2664bad64724da8eb893945a"}
COST=0.0027 # two taker roundtrips, slippage 0.02% PER ORDER, hypothetical
ENTRY_COST={"Binance":.0005+.0002,"Hyperliquid":.00045+.0002}
VENUES=("Binance","Hyperliquid")
MARGINS=(.10,.25,.50,1.00,1.50)
MMR={"Binance":.01,"Hyperliquid":.02} # Binance hypothetical, HL current tier approx; NOT historical rule
# Frozen dates + past-block-sign from CARRY-001 (dir -1=long Binance, short HL)
CASES=(("2026-06-22",8,-1,25.858426),("2026-08-17",8,-1,45.538890),
       ("2026-06-22",12,-1,55.578448))
def stamp(s):
    return int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()*1000)
def utc(ms):
    return dt.datetime.fromtimestamp(ms/1000,tz=dt.timezone.utc).isoformat()
def load():
    for name,digest in SHA.items():
        p=SOURCE/name
        if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            raise ValueError("SOURCE DRIFT - "+name)
    events=collections.defaultdict(list)
    with (SOURCE/"extended_funding_events.csv").open() as f:
        for x in csv.DictReader(f):
            if x["coin"]=="ETH":
                events[x["venue"]].append((int(x["timestamp_ms"]),float(x["rate"])))
    candle=collections.defaultdict(dict)
    with (SOURCE/"price_candles.csv").open() as f:
        for x in csv.DictReader(f):
            if x["coin"]!="ETH":continue
            venue="Binance" if x["venue"]=="Binance_MarkCandle" else "Hyperliquid" if x["venue"]=="Hyperliquid_TradeCandle" else None
            if venue:
                t=int(x["hour_ms"])
                candle[venue][t]=(float(x["open"]),float(x["high"]),float(x["low"]),float(x["close"]))
    return events,candle
def side(venue,direction):
    # Long = +1, short = -1, positive funding means long pays short.
    return -direction if venue=="Binance" else direction
def one(casespec,events,candles):
    day,number_weeks,direction,reported=casespec
    entry=stamp(day+"T02:00:00")
    exit_=entry+number_weeks*7*24*HOUR
    hours=list(range(entry,exit_,HOUR))
    result={"start_utc":utc(entry),"end_utc":utc(exit_),"weeks":number_weeks,
       "long_leg":"Binance" if direction==-1 else "Hyperliquid",
       "short_leg":"Hyperliquid" if direction==-1 else "Binance",
       "reported_original_funding_net_bps":reported,
       "entry_quote_type":"Binance mark versus Hyperliquid TRADE candle; NOT executable bids",
       "missing_hourly_candles":{},"funding_per_leg_bps":{},
       "status":"NO-GO economic; execution not proven","scenario":[]}
    funding_by_hour={}
    totalfund=0
    for venue in VENUES:
        sgn=side(venue,direction)
        missing=[h for h in hours if h not in candles[venue]]
        result["missing_hourly_candles"][venue]=len(missing)
        record=collections.defaultdict(float)
        # Settle only after nominal open at +5min to nominal close at +5min.
        for time,rate in events[venue]:
            if entry+5*60_000<time<=exit_+5*60_000:
                record[(time//HOUR)*HOUR]+=-sgn*rate
        funding_by_hour[venue]=record
        value=sum(record.values());totalfund+=value
        result["funding_per_leg_bps"][venue]=round(10000*value,6)
    result["gross_funding_bps"]=10000*totalfund
    result["cost_bps"]=10000*COST
    result["funding_net_bps"]=10000*(totalfund-COST)
    result["netfund_vs_original_bps"]=result["funding_net_bps"]-reported
    if abs(result["netfund_vs_original_bps"])>0.25:raise AssertionError("Original carry payout inconsistent; fail closed")
    if any(entry not in candles[venue] or exit_ not in candles[venue] for venue in VENUES):
        result["status"]="SOURCE_BLOCKED: Missing entry/exit price"
        return result
    prices={}
    for venue in VENUES:
        prices[venue]={"entry":candles[venue][entry][0],"exit":candles[venue][exit_][0]}
    result["indicative_price_pnl_per_leg_bps"]={venue:10000*side(venue,direction)*
        (prices[venue]["exit"]/prices[venue]["entry"]-1) for venue in VENUES}
    result["combined_indicative_price_pnl_bps"]=sum(result["indicative_price_pnl_per_leg_bps"].values())
    result["combined_indicative_net_bps"]=result["combined_indicative_price_pnl_bps"]+result["funding_net_bps"]
    result["combined_indicative_usd_per_1000_notional_each_leg"]=result["combined_indicative_net_bps"]/10
    result["complete_candle_coverage"]=not any(result["missing_hourly_candles"].values())
    for margin in MARGINS:
        scenario={"initial_margin_pct_per_leg":100*margin,
          "total_initial_margin_usd_at_1000_notional_per_leg":2000*margin,
          "hypothetical_maintenance":MMR,
          "per_leg":{},"one_leg_potential_breach":False,"breach_NOT_actual_liquidation":True,
          "if_missing_source":"NO SAFE CONCLUSION"}
        for venue in VENUES:
            sgn=side(venue,direction)
            px0=prices[venue]["entry"];cum_fund=0.
            worst=10**6;at=None;observed=0
            for hour in hours:
                if hour not in candles[venue]:continue
                observed+=1
                cum_fund+=funding_by_hour[venue].get(hour,0.)
                open_,high,low,close=candles[venue][hour]
                adverse=low if sgn==1 else high
                ratio=adverse/px0
                equity=margin-ENTRY_COST[venue]+sgn*(ratio-1)+cum_fund
                cushion=equity-MMR[venue]*ratio
                if cushion<worst:worst,at=cushion,hour
            broke=worst<=0
            scenario["one_leg_potential_breach"]|=broke
            scenario["per_leg"][venue]={"observed_hours":observed,"worst_cushion_pct_initial_notional":round(100*worst,5),
                "worst_utc":utc(at) if at else None,
                "potential_maintenance_breach":broke,
                "missing_hourly_candles":result["missing_hourly_candles"][venue]}
        scenario["indicative_return_pct_total_collateral"]=(result["combined_indicative_net_bps"]/100)/(2*margin)
        result["scenario"].append(scenario)
    return result
def run():
    events,candles=load()
    cases=[one(c,events,candles) for c in CASES]
    result={"study":"CARRY-002","source_sha256":SHA,
       "ethical_controls":{"read_only":True,"orders":0,"no_keys":True,"no_funds":True},
       "price_history":"May-Oct 2026: Binance mark vs HL trade; no pair-executable quotes",
       "basis_model":"equal INITIAL dollar notionals; no rebalances, not true neutral through price changes",
       "fx":"USDT/USDC par assumed, not proven",
       "collateral_model":"separate margin by exchange, no transfers or netting across platforms",
       "risk_engine":"intrahour worst HIGH/LOW per venue, hourly data can miss paths; current indicative MMR, not exact rules",
       "incomplete_source_fail_closed":True,
       "strategies_post_hoc":True,
       "economic_verdict":"NO-GO until actual historical L2 bid/ask, synchronized historical entry/exit and signed venue-specific margin rules",
       "cases":cases}
    raw=json.dumps(result,indent=2,ensure_ascii=False).encode()
    (OUT/"stress.json").write_bytes(raw)
    (OUT/"stress.sha256").write_text(hashlib.sha256(raw).hexdigest()+"  stress.json\n")
    for c in cases:
        print("MARGIN_STRESS",json.dumps({"start":c["start_utc"],"weeks":c["weeks"],
          "funding_net_bps":c.get("funding_net_bps"),"net_after_price_bps":c.get("combined_indicative_net_bps"),
          "missing_hours":c["missing_hourly_candles"],
          "breach_by_margin_pct":{s["initial_margin_pct_per_leg"]:s["one_leg_potential_breach"] for s in c.get("scenario",[])},
          "complete_candle_coverage":c.get("complete_candle_coverage")},ensure_ascii=False),flush=True)
if __name__=="__main__":run()
