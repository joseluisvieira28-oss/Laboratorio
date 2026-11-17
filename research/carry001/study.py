#!/usr/bin/env python3
"""CARRY-001 reproducible offline, timestamp-safe weekly 2-venue carry study.

Output is historical funding-only and indicative *mismatched* price candle accounting.
NOT executable PnL; no trades, accounts, credentials, orders, signing or transfers.
No in-sample optimisation: all strategies and cost scenarios predeclared.

Positive rate => longs pay shorts at both venues.
spread B-H = receive funding if SHORT BINANCE / LONG HYPERLIQUID.
Every week Monday 01:05 UTC, open two equal-USD notionals; eligible settlements
Monday 02:00 ... next Monday 01:00; close next Monday 01:05. No future rate in signal.
"""
import collections,csv,datetime as dt,hashlib,json,math,pathlib,random,statistics
OUT=pathlib.Path("carry001-evidence");OUT.mkdir(exist_ok=True)
UTC=dt.timezone.utc; HOUR=3600000; WEEK=168*HOUR
ANCHOR=int(dt.datetime(2024,9,2,2,tzinfo=UTC).timestamp()*1000)
B_TAKER=.0005; H_TAKER=.00045
B_MAKER=.0002; H_MAKER=.00015
SLIPS=(0,.0002,.0005,.001)
COST=lambda slip:2*(B_TAKER+H_TAKER)+4*slip
COINS=("BTC","ETH","SOL")
STRATEGIES=("shortBN_longHL_fixed","shortHL_longBN_fixed","prev_week_sign",
            "prev_week_fee_gate","trailing4_fee_gate","oracle_hindsight_NOT_TRADABLE")
def dtstr(ms):return dt.datetime.fromtimestamp(ms/1000,tz=UTC).isoformat()
def timeweek(ms):
    return ANCHOR+((ms-ANCHOR)//WEEK)*WEEK
def read_rates():
    rows=list(csv.DictReader((OUT/"funding_events.csv").open()))
    m=collections.defaultdict(lambda:collections.defaultdict(lambda:{"B":[],"H":[]}))
    raw_counts=collections.Counter()
    for r in rows:
        coin=r["coin"];venue=r["venue"]
        t=int(r["timestamp_ms"]); rate=float(r["rate"]); interval=int(r["interval_hours"])
        if not(math.isfinite(rate) and abs(rate)<=.25):raise ValueError("invalid funding magnitude")
        k=timeweek(t)
        if venue=="Binance":m[coin][k]["B"].append((t,rate,interval))
        elif venue=="Hyperliquid":m[coin][k]["H"].append((t,rate,1))
        else:raise ValueError("Unknown source")
        raw_counts[(coin,venue)]+=1
    data={};quality={}
    for coin in COINS:
        q=[];blocked=collections.Counter()
        for k,v in sorted(m[coin].items()):
            b=sorted(v["B"]);h=sorted(v["H"])
            dup_b=len(set((x[0]//HOUR) for x in b))!=len(b)
            dup_h=len(set((x[0]//HOUR) for x in h))!=len(h)
            bn_total=sum(x[1] for x in b);hl_total=sum(x[1] for x in h)
            b_cover=sum(x[2] for x in b);h_cover=len(h)
            reason=[]
            if dup_b or dup_h:reason.append("duplicate_funding_hour")
            if h_cover<165 or h_cover>168:reason.append("hyperliquid_hour_gap")
            if not 164<=b_cover<=172:reason.append("binance_settlement_hours_gap")
            if len(b)<14:reason.append("binance_too_few_settlements")
            if not reason:
                q.append({"week_ms":k,"week_utc":dtstr(k),"bn_settlement_events":len(b),
                  "hl_hourly_events":len(h),"bn_covered_h":b_cover,
                  "bn_paid":bn_total,"hl_paid":hl_total,"spread_b_minus_h":bn_total-hl_total,
                  "bn_intervals":dict(collections.Counter(x[2] for x in b))})
            else:blocked[";".join(reason)]+=1
        data[coin]=q
        quality[coin]={"rows_total":{v:raw_counts[(coin,v)] for v in ["Binance","Hyperliquid"]},
             "complete_weeks":len(q),"weeks_blocked":dict(blocked),
             "first_complete":q[0]["week_utc"] if q else None,
             "last_complete":q[-1]["week_utc"] if q else None,
             "rates_sign":"positive = long pays short on both exchanges"}
        print("FUNDING_COVERAGE",coin,json.dumps(quality[coin]),flush=True)
    return data,quality
def read_candles():
    path=OUT/"price_candles.csv"
    if not path.exists():return {},{"status":"missing"}
    rows=list(csv.DictReader(path.open()))
    candles={};duplicates=0
    for r in rows:
        key=(r["coin"],r["venue"],int(r["hour_ms"]))
        vals=tuple(float(r[k]) for k in ("open","high","low","close"))
        if not all(math.isfinite(x) and x>0 for x in vals):continue
        if key in candles:
            duplicates+=1
            if candles[key]!=vals:raise ValueError("conflicting candles")
        candles[key]=vals
    return candles,{"rows":len(candles),"duplicates":duplicates,
      "warning":"Binance mark OHLC vs Hyperliquid traded OHLC, not execution quotes"}
def pricebasis(coin,week,c):
    t0=week-HOUR;t1=week+WEEK-HOUR
    a=c.get((coin,"Hyperliquid_TradeCandle",t0))
    b=c.get((coin,"Binance_MarkCandle",t0))
    x=c.get((coin,"Hyperliquid_TradeCandle",t1))
    y=c.get((coin,"Binance_MarkCandle",t1))
    if not all([a,b,x,y]):return None
    hl_ret=x[0]/a[0]-1
    bn_ret=y[0]/b[0]-1
    # For short Binance / long HL. Opposite sign reverses result.
    signed_diff=hl_ret-bn_ret
    # Approximate maximum adverse standalone mark/traded-candle move during week.
    weekly_h=[c[(coin,"Hyperliquid_TradeCandle",k)] for k in range(t0,t1+HOUR,HOUR) if (coin,"Hyperliquid_TradeCandle",k) in c]
    weekly_b=[c[(coin,"Binance_MarkCandle",k)] for k in range(t0,t1+HOUR,HOUR) if (coin,"Binance_MarkCandle",k) in c]
    if len(weekly_h)<161 or len(weekly_b)<161:return None
    shock_h_long=min(v[2] for v in weekly_h)/a[0]-1
    shock_h_short=1-max(v[1] for v in weekly_h)/a[0]
    shock_b_long=min(v[2] for v in weekly_b)/b[0]-1
    shock_b_short=1-max(v[1] for v in weekly_b)/b[0]
    return {"entry_ms":t0,"exit_ms":t1,"hl_return":hl_ret,"bn_return":bn_ret,
       "net_short_bn_long_hl":signed_diff,
       "worst_leg_short_bn_long_hl":min(shock_h_long,shock_b_short),
       "worst_leg_short_hl_long_bn":min(shock_h_short,shock_b_long),
       "source_warning":"Hyperliquid TRADED candles, Binance MARK candles. No bid-ask or USDC/USDT conversion."}
def sign(x):
    if x>0:return 1
    if x<0:return -1
    return 0
def choose(name,history,cur,cost):
    if name=="shortBN_longHL_fixed":return 1
    if name=="shortHL_longBN_fixed":return -1
    if name=="oracle_hindsight_NOT_TRADABLE":return sign(cur["spread_b_minus_h"])
    if not history:return 0
    if name=="prev_week_sign":return sign(history[-1]["spread_b_minus_h"])
    if name=="prev_week_fee_gate":
        x=history[-1]["spread_b_minus_h"]
        return sign(x) if abs(x)>cost else 0
    if name=="trailing4_fee_gate":
        if len(history)<4:return 0
        x=sum(w["spread_b_minus_h"] for w in history[-4:])/4
        return sign(x) if abs(x)>cost else 0
    raise ValueError("unknown strategy")
def eval_trades(rows):
    done=[x for x in rows if x["direction"]!=0]
    vals=[x["funding_net"] for x in done]
    price=[x for x in done if x["basis_price_proxy"] is not None]
    pxnet=[x["funding_net"]+x["basis_price_proxy"] for x in price]
    risk=[x["worst_leg_adverse_pct"] for x in price if x["worst_leg_adverse_pct"] is not None]
    out={"weeks_observed":len(rows),"traded_weeks":len(done),"gross_funding_bps":round(sum(x["funding_gross"] for x in done)*1e4,3),
       "fees_and_slippage_bps":round(sum(x["fee_and_slippage"] for x in done)*1e4,3),
       "net_funding_only_bps":round(sum(vals)*1e4,3),
       "net_funding_only_usd_per_1000_each_leg":round(sum(vals)*1000,3),
       "net_funding_only_winning_week_pct":round(100*sum(v>0 for v in vals)/len(vals),2) if vals else None,
       "net_funding_only_worst_week_bps":round(min(vals)*1e4,3) if vals else None,
       "basis_proxy_coverage_weeks":len(price),
       "funding_plus_indicative_basis_net_bps_on_paired_weeks":round(sum(pxnet)*1e4,3),
       "paired_basis_proxy_median_week_bps":round(statistics.median(x["basis_price_proxy"] for x in price)*1e4,3) if price else None,
       "combined_proxy_winning_weeks_pct":round(100*sum(v>0 for v in pxnet)/len(pxnet),2) if price else None,
       "worst_standalone_leg_intraweek_pct":round(min(risk)*100,2) if risk else None,
       "weeks_indicative_leg_adverse_beyond_18pct":sum(v<-18 for v in risk) if risk else None}
    return out
def main():
    data,q=read_rates()
    candles,cq=read_candles()
    meta={"created":"2026-11-17","data_period":"2024-09-01 .. 2026-10-31 UTC",
         "not_trades":True,"no_forward_live_profit_claim":True,
         "fees":{"binance_taker_per_side":B_TAKER,"hyperliquid_taker_per_side":H_TAKER,
           "roundtrip_both_legs_taker":COST(0),"maker_roundtrip_both_legs_hypothetical":2*(B_MAKER+H_MAKER),
           "slippage_per_leg_side_scenarios":SLIPS},
         "source_coverage":q,"price_coverage":cq,"economic_gate":"NO-GO until marketable bids, FX, collateral/liquidation proven"}
    out={"meta":meta,"by_coin":{}}
    artifact_rows=[]
    for coin,weeks in data.items():
        idx={r["week_ms"]:r for r in weeks}
        combined=[]
        # require *consecutive valid prior weeks* rather than silently bridge missing data
        for week in weeks:
            prev=idx.get(week["week_ms"]-WEEK)
            if prev is None:continue
            history=[idx[week["week_ms"]-j*WEEK] for j in range(1,5)
                if week["week_ms"]-j*WEEK in idx]
            history=history[::-1]
            # Extra ensure trailing four are consecutive only if each in date range
            if not history or history[-1]["week_ms"]!=week["week_ms"]-WEEK:continue
            basis=pricebasis(coin,week["week_ms"],candles)
            phase=("train" if week["week_ms"]<int(dt.datetime(2025,7,1,tzinfo=UTC).timestamp()*1000)
               else "validation" if week["week_ms"]<int(dt.datetime(2026,1,1,tzinfo=UTC).timestamp()*1000)
               else "test")
            for slip in SLIPS:
                cost=COST(slip)
                for strat in STRATEGIES:
                    direction=choose(strat,history,week,cost)
                    gross=direction*week["spread_b_minus_h"]
                    fee=cost if direction else 0
                    basis_pnl=direction*basis["net_short_bn_long_hl"] if (basis and direction) else (0 if direction==0 and basis else None)
                    worst_leg=(100*basis["worst_leg_short_bn_long_hl"] if direction==1 else
                          100*basis["worst_leg_short_hl_long_bn"] if direction==-1 else None) if basis else None
                    row={"coin":coin,"week_ms":week["week_ms"],"week":week["week_utc"],
                       "phase":phase,"scenario_slip_per_leg_side":slip,"strategy":strat,
                       "direction":direction,"observed_week_spread":week["spread_b_minus_h"],
                       "funding_gross":gross,"fee_and_slippage":fee,"funding_net":gross-fee,
                       "basis_price_proxy":basis_pnl,"worst_leg_adverse_pct":worst_leg}
                    artifact_rows.append(row)
                    if phase=="test":combined.append(row)
        summaries={}
        for slip in SLIPS:
            strat_res={}
            for strat in STRATEGIES:
                r=[v for v in combined if v["strategy"]==strat and v["scenario_slip_per_leg_side"]==slip]
                strat_res[strat]=eval_trades(r)
            summaries[str(slip)]=strat_res
        out["by_coin"][coin]={"coverage":q[coin],"test":summaries,
          "2026_test_week_total":len(set(x["week_ms"] for x in combined))}
        # print concise 2bp base scenario
        for name in ("prev_week_sign","prev_week_fee_gate","trailing4_fee_gate","shortBN_longHL_fixed","shortHL_longBN_fixed","oracle_hindsight_NOT_TRADABLE"):
            print("CARRY_TEST",coin,name,json.dumps(summaries[str(.0002)][name]),flush=True)
    with (OUT/"weekly_funding_scenarios.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(artifact_rows[0].keys()))
        w.writeheader();w.writerows(artifact_rows)
    (OUT/"funding_study.json").write_text(json.dumps(out,indent=2,ensure_ascii=False))
    print("CARRY_FINAL",json.dumps({"source_coverage":q,"price_candles":cq,
       "test_summary_2bps":{c:{s:out["by_coin"][c]["test"][str(.0002)][s] for s in STRATEGIES}
           for c in COINS},"decision":"NO-GO economic absent tradable mark/bid/ask/collateral"},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
