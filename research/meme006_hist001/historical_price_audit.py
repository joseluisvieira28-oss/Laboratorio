#!/usr/bin/env python3
"""MEME006 HIST001: price-only historical *partial falsification*, never real PnL."""
import collections
import datetime as dt
import hashlib
import json
import math
import pathlib
import random
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BEGIN=dt.datetime(2026,10,1,tzinfo=dt.timezone.utc)
SPLIT=dt.datetime(2026,10,23,tzinfo=dt.timezone.utc)
END=dt.datetime(2026,11,15,tzinfo=dt.timezone.utc)
SOURCE_CUTOFF=dt.datetime(2026,11,16,tzinfo=dt.timezone.utc)
SEED_SHA="39ee74fb7521ca699b7e3bbbb83b37fcd133ac05fe8ee2349c79c360043889e4"
UA="CryptoLab-MEME006-HIST001-ReadOnly/0.1"
COST_STRESS=(0,1,2.5,5)
START_TS=int(BEGIN.timestamp())
END_TS=int(END.timestamp())
SPLIT_TS=int(SPLIT.timestamp())
CUTOFF_TS=int(SOURCE_CUTOFF.timestamp())

def utc():return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")

def finite(v):
    try:
        n=float(v)
        return n if math.isfinite(n) else None
    except (TypeError,ValueError,OverflowError):return None

def fetch(url):
    start=utc(); t0=time.monotonic(); raw=None; data=None;err=None;code=None
    retry_statuses=[]
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":UA},method="GET")
            with urllib.request.urlopen(req,timeout=35) as r:
                code=r.status;raw=r.read(3_500_000)
            data=json.loads(raw);err=None
            break
        except urllib.error.HTTPError as e:
            code=e.code;err="HTTP_"+str(e.code)
            if e.code==429 and attempt<3:
                retry_statuses.append(429)
                time.sleep(15+10*attempt)
                continue
            break
        except (OSError,ValueError,UnicodeError) as e:
            err=type(e).__name__+":"+str(e)[:100]
            break
    rec=dict(url=url,requested_at=start,received_at=utc(),
             response_status=code,response_sha256=hashlib.sha256(raw).hexdigest() if raw else None,
             retry_429_count=len(retry_statuses),
             bytes=len(raw) if raw else 0,elapsed_ms=round(1000*(time.monotonic()-t0)),error=err)
    return data,rec

def get_seed(path):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SEED_SHA:
        raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: seed hash")
    seed=json.loads(raw)
    selected=[x for x in seed.get("selection",[]) if (x.get("screen") or {}).get("status")=="SCREEN_PASS_ONLY"]
    if len(selected)!=6:
        raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: expected 6 mints")
    return [dict(coin_id=x["coingecko_id"],mint=x["mint"],
                 pool=x["pair"]["pair_address"]) for x in selected]

def candles(pool):
    result={}; receipts=[];invalid=dup=0;prev=None
    for page in range(3):
        base="https://api.geckoterminal.com/api/v2/networks/solana/pools/"+urllib.parse.quote(pool,safe="")+"/ohlcv/hour"
        query=urllib.parse.urlencode(dict(aggregate="1",limit="1000",currency="usd",
                             token="base",before_timestamp=str(prev or CUTOFF_TS)))
        data,rec=fetch(base+"?"+query)
        receipts.append(rec)
        if rec["error"] or not isinstance(data,dict):
            break
        lst=(((data.get("data") or {}).get("attributes") or {}).get("ohlcv_list"))
        if not isinstance(lst,list):
            receipts[-1]["error"]="SCHEMA_NO_OHLCV_LIST"
            break
        olds=[]
        for a in lst:
            if not isinstance(a,list) or len(a)<6:
                invalid+=1;continue
            try: ts=int(a[0])
            except (ValueError,TypeError):invalid+=1;continue
            if ts>=CUTOFF_TS or ts<START_TS-30*3600:continue
            price=finite(a[4]);vol=finite(a[5])
            if price is None or price<=0 or vol is None or vol<0:
                invalid+=1;continue
            if ts%3600!=0:
                invalid+=1;continue
            if ts in result:
                dup+=1;continue
            result[ts]=(price,vol)
            olds.append(ts)
        if not lst:break
        raw_timestamps=[int(x[0]) for x in lst if isinstance(x,list) and x and isinstance(x[0],(int,float))]
        if not raw_timestamps:break
        oldest=min(raw_timestamps)
        if oldest>= (prev or CUTOFF_TS):
            receipts[-1]["error"]="PAGINATION_STUCK"
            break
        prev=oldest
        if oldest<=START_TS-30*3600:break
        time.sleep(4.0)
    return result,receipts,invalid,dup

def returns(series,obs_ts):
    # Observation UTC at HH:37; last complete bar OPEN time H-1:00, closed at H:00.
    hour=obs_ts//3600*3600
    anchor=hour-3600
    for delta in (0,-1,-6):
        if anchor+delta*3600 not in series:return None
    p=series[anchor][0];p1=series[anchor-3600][0];p6=series[anchor-6*3600][0]
    return anchor,100*(p/p1-1),100*(p/p6-1)

def bootstrap_lower(event_pairs):
    by_day=collections.defaultdict(list)
    for t,v in event_pairs:
        by_day[dt.datetime.fromtimestamp(t,dt.timezone.utc).date().isoformat()].append(v)
    days=sorted(by_day)
    if len(days)<3:return None
    rng=random.Random(20261119)
    values=[]
    for i in range(2000):
        selected=rng.choices(days,k=len(days))
        vals=[v for day in selected for v in by_day[day]]
        values.append(statistics.mean(vals))
    values.sort()
    return round(values[int(.025*(len(values)-1))],5)

def summarize(entries):
    results={}
    for policy in ("BASELINE_4H","H_REVERSAL_PRICE_ONLY","H_MOMENTUM_PRICE_ONLY"):
        sub=[e for e in entries if e["policy"]==policy]
        results[policy]={"candidates":len(sub),
            "unverified_buyer_gate":len(sub),
            "unverified_historical_liquidity_and_router_gate":len(sub)}
        for horizon in (4,24):
            vals=[e for e in sub if e["h"+str(horizon)+"_gross_pct"] is not None]
            gross=[e["h"+str(horizon)+"_gross_pct"] for e in vals]
            item={"observed":len(vals),"missing":len(sub)-len(vals),
                  "mean_gross_pct":round(statistics.mean(gross),5) if gross else None,
                  "median_gross_pct":round(statistics.median(gross),5) if gross else None}
            for stress in COST_STRESS:
                net=[x-stress for x in gross]
                item["cost_"+str(stress)+"pct"]={
                    "mean_proxy_pct":round(statistics.mean(net),5) if net else None,
                    "fraction_above_zero":round(sum(x>0 for x in net)/len(net),5) if net else None,
                    "bootstrap_95pct_lower_day_cluster":bootstrap_lower([(e["observed_at"],e["h"+str(horizon)+"_gross_pct"]-stress) for e in vals])}
            results[policy]["h"+str(horizon)]=item
    return results

def evaluate_one(coin,series):
    events=[];cnt=collections.Counter();last={"H_REVERSAL_PRICE_ONLY":-1e20,
                        "H_MOMENTUM_PRICE_ONLY":-1e20}
    obs=START_TS+(37*60)
    while obs<END_TS:
        if (dt.datetime.fromtimestamp(obs,dt.timezone.utc).hour%2)==0:
            signal=returns(series,obs)
            if signal is None:cnt["MISSING_HISTORIC_H1_H6"]+=1
            else:
                anchor,h1,h6=signal
                cnt["OBSERVATION_PRICE_CONTEXT_OK"]+=1
                # 2h cadence, at most one 4h token position per policy.
                # Unconditional control is precisely every 4h on a 0,4,8,... UTC grid.
                policies=[]
                hour=dt.datetime.fromtimestamp(obs,dt.timezone.utc).hour
                if hour%4==0:policies.append("BASELINE_4H")
                if h6<=-4 and h1>=1.5 and obs-last["H_REVERSAL_PRICE_ONLY"]>=4*3600:
                    policies.append("H_REVERSAL_PRICE_ONLY");last["H_REVERSAL_PRICE_ONLY"]=obs
                if h6>=5 and h1>=2 and obs-last["H_MOMENTUM_PRICE_ONLY"]>=4*3600:
                    policies.append("H_MOMENTUM_PRICE_ONLY");last["H_MOMENTUM_PRICE_ONLY"]=obs
                for policy in policies:
                    x=dict(coin_id=coin["coin_id"],policy=policy,observed_at=obs,
                           anchor_bar_start=anchor,h1_pct=round(h1,5),h6_pct=round(h6,5),
                           date_group="DISCOVERY" if obs<SPLIT_TS else "HISTORIC_SPLIT_AFTER_2026_10_23",
                           h4_gross_pct=None,h24_gross_pct=None)
                    price=series[anchor][0]
                    for h in (4,24):
                        # This bar was not known on the observation date, used strictly for outcome evaluation.
                        fut=series.get(anchor+h*3600)
                        if fut:
                            x["h"+str(h)+"_gross_pct"]=round(100*(fut[0]/price-1),6)
                    events.append(x)
        obs+=2*3600
    return events,dict(cnt)

def analyze(seed_path):
    cohort=get_seed(seed_path)
    receipts=[];event_rows=[];coverage=[]
    for coin in cohort:
        series,rr,invalid,dup=candles(coin["pool"])
        receipts.extend([dict(coin_id=coin["coin_id"],**x) for x in rr])
        valid_historic={t:bar for t,bar in series.items() if START_TS<=t<END_TS}
        times=sorted(valid_historic)
        gap_count=sum(b-a!=3600 for a,b in zip(times,times[1:]))
        events,counts=evaluate_one(coin,series)
        event_rows.extend(events)
        coverage.append(dict(coin_id=coin["coin_id"],mint=coin["mint"],pool=coin["pool"],
            candle_count=len(valid_historic),source_http_codes=[r["response_status"] for r in rr],
            source_errors=[r["error"] for r in rr if r["error"]],
            candles_earliest_utc=dt.datetime.fromtimestamp(times[0],dt.timezone.utc).isoformat() if times else None,
            candles_latest_utc=dt.datetime.fromtimestamp(times[-1],dt.timezone.utc).isoformat() if times else None,
            observed_gaps=gap_count,invalid_rows=invalid,duplicate_timestamp_rows=dup,
            candidate_events=len(events),observation_metrics=counts))
        time.sleep(6.0)
    totals={}
    for group in ("DISCOVERY","HISTORIC_SPLIT_AFTER_2026_10_23","ALL"):
        selected=[e for e in event_rows if group=="ALL" or e["date_group"]==group]
        totals[group]=summarize(selected)
    result=dict(protocol="MEME006-HIST001-price-only-v0.1",
        executed_at=utc(),data_window_utc=[BEGIN.isoformat(),END.isoformat()],
        selected_at_2026_11_18_survivorship_bias=True,cohort=cohort,
        source_receipts=receipts,coverage=coverage,proxy_price_events=event_rows,
        comparisons=totals,expected_original_buy_sell_1h_availability=False,
        expected_original_historical_liquidity_availability=False,
        expected_original_historical_executable_quotes_availability=False,
        exact_frozen_signal_backtest_possible=False,actual_orders=0,actual_fills=0,
        economic_verdict="NO-GO: historical OHLCV price-only proxy, NOT frozen strategy executable PnL")
    return result

if __name__=="__main__":
    report=analyze(pathlib.Path(sys.argv[1]))
    out=pathlib.Path("meme006-hist001")
    out.mkdir(exist_ok=True)
    raw=json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False).encode()
    (out/"report.json").write_bytes(raw)
    (out/"report.sha256").write_text(hashlib.sha256(raw).hexdigest()+"  report.json\n")
    compact=dict(cohort_count=len(report["cohort"]),coverage=report["coverage"],
        totals=report["comparisons"],signal_events=len(report["proxy_price_events"]),
        exact_backtest_possible=False,real_orders=0,
        report_sha256=hashlib.sha256(raw).hexdigest())
    print("MEME006_HIST001_RESULT="+json.dumps(compact,ensure_ascii=False,sort_keys=True))
