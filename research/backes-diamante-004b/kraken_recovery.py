#!/usr/bin/env python3
"""004B: Kraken 1d public candles cross-venue execution-price replication.
Use Binance FROZEN002 decision signal, NOT Kraken-generated signal. NO TRADING.
"""
import concurrent.futures as cf
import datetime as dt
import hashlib
import importlib.util
import json
import math
import pathlib
import urllib.parse
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent;OUT=HERE/"results"
BASEPATH=HERE.parent/"backes-diamante-002"/"rotation_backtest.py"
spec=importlib.util.spec_from_file_location("frozen002",BASEPATH)
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
START=dt.date(2025,1,6); END=dt.date(2026,11,22)
N=((END-START).days+1)//7
SYMBOLS={"BTC":"XBTUSD","ETH":"ETHUSD","RATIO":"ETHXBT"}
COSTS=(10,35,60,80,100)

def kraken_daily(symbol,receipts):
    url="https://api.kraken.com/0/public/OHLC?"+urllib.parse.urlencode(
        {"pair":SYMBOLS[symbol],"interval":1440,
         "since":int(dt.datetime(2024,12,1,tzinfo=dt.timezone.utc).timestamp())})
    req=urllib.request.Request(url,headers={"User-Agent":"BACKES-004B-Kraken-Public-ReadOnly"})
    with urllib.request.urlopen(req,timeout=40) as f:raw=f.read(400000)
    receipts.append({"symbol":symbol,"url":url,"raw_sha256":hashlib.sha256(raw).hexdigest(),
                     "bytes":len(raw),"utc":dt.datetime.now(dt.timezone.utc).isoformat()})
    obj=json.loads(raw)
    if obj.get("error"):raise ValueError("Kraken "+symbol+" API "+repr(obj["error"]))
    data=obj.get("result",{})
    keys=[k for k in data if k!="last"]
    if len(keys)!=1:raise ValueError("Kraken returned wrong pair")
    daily={}
    for row in data[keys[0]]:
        date=dt.datetime.fromtimestamp(int(row[0]),dt.timezone.utc)
        if date.time()!=dt.time():raise ValueError("Kraken daily non-midnight")
        day=date.date()
        if START<=day<=END:
            if day in daily:raise ValueError("Kraken duplicate day")
            o,h,l,c=map(float,row[1:5])
            if not 0<l<=min(o,c)<=max(o,c)<=h or not all(math.isfinite(x) for x in (o,h,l,c)):
                raise ValueError("Kraken invalid OHLC on "+str(day))
            daily[day]={"open":o,"high":h,"low":l,"close":c}
    if len(daily)!=N*7:raise ValueError("SOURCE_BLOCKED daily coverage "+symbol+" "+str(len(daily))+" need "+str(N*7))
    weekly=[]
    for i in range(N):
        monday=START+dt.timedelta(days=7*i)
        rows=[]
        for j in range(7):
            date=monday+dt.timedelta(days=j)
            if date not in daily:raise ValueError("Kraken missing "+str(date))
            rows.append(daily[date])
        weekly.append({"date":str(monday),"open":rows[0]["open"],
                       "high":max(x["high"] for x in rows),
                       "low":min(x["low"] for x in rows),
                       "close":rows[-1]["close"]})
    return weekly

def official_binance(receipts):
    jobs=b.jobs()
    source=[];errors=[]
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        future={pool.submit(b.download,item):item for item in jobs}
        for f in cf.as_completed(future):
            try:source.append(f.result())
            except Exception as e:errors.append(str(e))
    if errors or len(source)!=384:raise ValueError("BINANCE_SOURCE_BLOCKED "+repr(errors[:3]))
    receipts.extend({"url":x["url"],"raw_sha256":x["sha256"],"bytes":x["bytes"]} for x in source)
    w={k:b.parse(source,symbol) for k,symbol in (("BTC","BTCUSDT"),("ETH","ETHUSDT"),("RATIO","ETHBTC"))}
    return w

def evaluate_weekly(prices,global_states,bps):
    w=prices["BTC"];e=prices["ETH"]; NAV={"BTC":1.,"ETH":1.,"ROT":1.}
    path={k:[1.] for k in NAV}
    prev=None;switch=0
    for j,row in enumerate(w):
        if j+1<len(w):
            bt=w[j+1]["open"]/w[j]["open"]
            et=e[j+1]["open"]/e[j]["open"]
        else:
            bt=w[j]["close"]/w[j]["open"]
            et=e[j]["close"]/e[j]["open"]
        day=dt.date.fromisoformat(row["date"])
        index=(day-b.START).days//7
        held="ETH" if index>0 and global_states[index-1]=="ETH" else "BTC"
        if j and held!=prev:switch+=1
        for k,growth in (("BTC",bt),("ETH",et),("ROT",et if held=="ETH" else bt)):
            fees=(j==0 or k=="ROT" and held!=prev)
            NAV[k]*=(1-bps/10000 if fees else 1)*growth
            path[k].append(NAV[k])
        prev=held
    result={}
    for k,v in NAV.items():
        peak=1.;dd=0.
        for x in path[k]:peak=max(peak,x);dd=min(dd,x/peak-1)
        result[k]={"total_return_pct":round((v-1)*100,5),
                   "max_drawdown_pct":round(dd*100,5)}
    result["switches"]=switch
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    receipts=[];status={"status":"SOURCE_BLOCKED","study":"BACKES-004B",
      "cutoff":"2026-11-22","no_trading":True,
      "source_variant":"Kraken 1440m daily rebucketed Monday-Sunday",
      "signal_source":"UNCHANGED BINANCE BACKES-002; NOT independent Kraken signal",
      "samples_weeks":N}
    try:
        prices={k:kraken_daily(k,receipts) for k in SYMBOLS}
        bsource=official_binance(receipts)
        states=b.signals(bsource["RATIO"])
        # Binance whole-period data and Kraken short period must be date-aligned.
        bidx=(START-b.START).days//7
        b_prices={k:v[bidx:bidx+N] for k,v in bsource.items()}
        if any([q["date"] for q in b_prices[k]]!=[q["date"] for q in prices[k]] for k in SYMBOLS):
            raise ValueError("CROSS_VENUE_WEEK_MISMATCH")
        # Require consistent traded ETHBTC ratio, not a synthetic high/low.
        mismatch=[]
        for a,c in zip(prices["RATIO"],b_prices["RATIO"]):
            mismatch.append(abs(a["close"]/c["close"]-1)*100)
        if any(x>20 for x in mismatch):raise ValueError("Kraken-Binance ETHBTC close >20% divergence")
        results={}
        for fee in COSTS:
            results[str(fee)]={"KrakenUSD":evaluate_weekly(prices,states,fee),
                               "BinanceUSDT":evaluate_weekly(b_prices,states,fee)}
        baseline=results["10"]["BinanceUSDT"]["ROT"]["total_return_pct"]
        if abs(baseline-(-4.0107))>0.0002:raise ValueError("BACKES002_PARITY_FAILURE "+str(baseline))
        status.update({
          "status":"SOURCE_PASS_EXECUTION_REPLICATION",
          "markets":["XBTUSD","ETHUSD","ETHXBT"],"start":str(START),"end":str(END),
          "ratio_close_mismatch_pct_median":round(sorted(mismatch)[len(mismatch)//2],5),
          "ratio_close_mismatch_pct_max":round(max(mismatch),5),
          "results":results,
          "limitations":["Kraken USD vs Binance USDT numeraire","Kraken signal itself NOT computed due only 720 daily bars",
              "no historical spread/orderbook fills","fees are scenarios only","all evidence retrospective"]
        })
        lines=["# BACKES-004B — Kraken recent independent price replication","",
          "The allocation decision signal was FROZEN002 from Binance and held fixed on Kraken.",
          "Kraken BTCUSD/ETHUSD/ETHXBT DAILY public candles were aggregated to UTC Monday-Sunday.",
          "This is **NOT an independent Kraken predictor**, and USD differs from Binance USDT.",
          "",f"Source date {START}..{END}, {N} complete weeks.",
          f"Median ETHBTC closing divergence: {status['ratio_close_mismatch_pct_median']}%; maximum {status['ratio_close_mismatch_pct_max']}%.",
          "","| Fee scenario | Kraken rotation | Binance rotation | Kraken BTC | Binance BTC |",
          "|---:|---:|---:|---:|---:|"]
        for fee in COSTS:
            rec=results[str(fee)]
            lines.append("| "+str(fee)+"bps | "+
                " | ".join(str(rec[v][k]["total_return_pct"])+"%"
                    for v,k in (("KrakenUSD","ROT"),("BinanceUSDT","ROT"),
                                ("KrakenUSD","BTC"),("BinanceUSDT","BTC")))+" |")
        lines+=["","## Verdict","This only checks cross-venue price sensitivity of a historical frozen signal.",
           "No true prospective outcome, no active fees or actual fills, no GO for capital."]
        (OUT/"RESULT.md").write_text("\n".join(lines)+"\n")
    except Exception as e:
        status["error"]=type(e).__name__+": "+str(e)
        (OUT/"RESULT.md").write_text("# SOURCE_BLOCKED\n\n"+status["error"]+"\n")
    status["sources_receipts"]=receipts
    (OUT/"RESULT.json").write_text(json.dumps(status,indent=2)+"\n")
    print("BACKES004B",status["status"],status.get("error",""))
    if status["status"]!="SOURCE_PASS_EXECUTION_REPLICATION":raise RuntimeError(status["error"])
if __name__=="__main__":main()
