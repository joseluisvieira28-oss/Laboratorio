#!/usr/bin/env python3
import bisect, csv, gzip, io, json, statistics, sys, urllib.request, zipfile
from pathlib import Path

L2_URL="https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/2023-01-18_BTCUSDT_ob500.data.zip"
TRADES_URL="https://public.bybit.com/trading/BTCUSDT/BTCUSDT2023-01-18.csv.gz"
MAX_L2=250_000
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-Trade-L2-Join/0.1"}

def dl(url,path):
    req=urllib.request.Request(url,headers=UA)
    total=0
    with urllib.request.urlopen(req,timeout=90) as r, open(path,"wb") as f:
        while True:
            c=r.read(1024*1024)
            if not c: break
            total+=len(c); f.write(c)
    return total

def apply(book,rows):
    for row in rows or []:
        p=float(row[0]); q=float(row[1])
        if q==0: book.pop(p,None)
        else: book[p]=q

def load_l2(path):
    bids={}; asks={}; states=[]; prev=None
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None: raise RuntimeError("L2_CRC_FAIL")
        name=[n for n in zf.namelist() if not n.endswith("/")][0]
        with zf.open(name) as fh:
            for i,raw in enumerate(fh):
                if i>=MAX_L2: break
                m=json.loads(raw); d=m["data"]
                if m["type"]=="snapshot":
                    bids={float(p):float(q) for p,q,*_ in d["b"] if float(q)!=0}
                    asks={float(p):float(q) for p,q,*_ in d["a"] if float(q)!=0}
                else:
                    apply(bids,d.get("b")); apply(asks,d.get("a"))
                cts=m.get("cts")
                if cts is None: raise RuntimeError("MISSING_CTS")
                if prev is not None and cts<prev: raise RuntimeError("NONMONOTONIC_CTS")
                prev=cts
                if not bids or not asks: raise RuntimeError("EMPTY_BOOK")
                bb=max(bids); ba=min(asks)
                if bb>=ba: raise RuntimeError("CROSSED_BOOK")
                states.append((int(cts),bb,ba))
    return states

def audit_trades(path,states):
    times=[x[0] for x in states]
    lo,hi=times[0],times[-1]
    stats={"overlap_trades":0,"buy":0,"sell":0,"timestamp_nonmonotonic":0,
           "buy_at_or_above_prior_ask":0,"sell_at_or_below_prior_bid":0,
           "side_price_consistent":0,"no_prior_state":0}
    prev_t=None; prior_lags=[]; next_lags=[]; nearest_lags=[]
    with gzip.open(path,"rt",encoding="utf-8",newline="") as fh:
        reader=csv.DictReader(fh)
        for r in reader:
            t=int(round(float(r["timestamp"])*1000.0))
            if prev_t is not None and t<prev_t: stats["timestamp_nonmonotonic"]+=1
            prev_t=t
            if t<lo: continue
            if t>hi: break
            stats["overlap_trades"]+=1
            side=r["side"]; px=float(r["price"])
            if side=="Buy": stats["buy"]+=1
            elif side=="Sell": stats["sell"]+=1
            i=bisect.bisect_right(times,t)-1
            if i<0:
                stats["no_prior_state"]+=1; continue
            cts,bb,ba=states[i]
            prior_lags.append(t-cts)
            j=bisect.bisect_left(times,t)
            if j<len(times):
                next_lags.append(times[j]-t)
                nearest_lags.append(min(t-cts, times[j]-t))
            else:
                nearest_lags.append(t-cts)
            consistent=False
            if side=="Buy" and px>=ba:
                stats["buy_at_or_above_prior_ask"]+=1; consistent=True
            if side=="Sell" and px<=bb:
                stats["sell_at_or_below_prior_bid"]+=1; consistent=True
            if consistent: stats["side_price_consistent"]+=1

    def dist(xs):
        if not xs: return None
        s=sorted(xs)
        return {"median":statistics.median(xs),"p95":s[int(.95*(len(s)-1))],"p99":s[int(.99*(len(s)-1))],"max":max(xs)}
    n=stats["overlap_trades"]
    return {
      "l2_first_cts":lo,"l2_last_cts":hi,
      "stats":stats,
      "side_price_consistency_rate":stats["side_price_consistent"]/n if n else None,
      "prior_l2_lag_ms":dist(prior_lags),
      "next_l2_lag_ms":dist(next_lags),
      "nearest_l2_lag_ms":dist(nearest_lags),
    }

def main():
    l2="/tmp/bybit_l2.zip"; tr="/tmp/bybit_trades.csv.gz"
    receipt={"purpose":"TRADE/L2 CLOCK ALIGNMENT ONLY — NO STRATEGY OUTCOMES"}
    try:
        receipt["l2_bytes"]=dl(L2_URL,l2)
        receipt["trade_bytes"]=dl(TRADES_URL,tr)
        states=load_l2(l2)
        receipt["l2_states"]=len(states)
        receipt["audit"]=audit_trades(tr,states)
        a=receipt["audit"]; st=a["stats"]
        # Alignment gate is intentionally permissive about BBO consistency because
        # a trade and its book update can share/sub-ms event timing.
        receipt["gate"]="PASS_SAMPLE" if (
            len(states)>=100_000 and
            st["overlap_trades"]>=10_000 and
            st["timestamp_nonmonotonic"]==0 and
            (a["nearest_l2_lag_ms"] or {}).get("p95",9999)<=250
        ) else "BLOCKED"
    except Exception as e:
        receipt["gate"]="BLOCKED"; receipt["error"]=repr(e)
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"trade_l2_join_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if receipt["gate"]=="PASS_SAMPLE" else 2

if __name__=="__main__":
    sys.exit(main())
