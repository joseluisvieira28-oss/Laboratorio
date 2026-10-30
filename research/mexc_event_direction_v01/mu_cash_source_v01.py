#!/usr/bin/env python3
"""Source-only dual MU cash/MUSTOCK index required-bar canonical checks."""
import datetime as dt,hashlib,json,math,pathlib,time,urllib.parse,urllib.request
DAYS=("2026-10-28","2026-10-29")
OUT=pathlib.Path("artifacts/mu_event10m_transfer_v01")
START=int(dt.datetime(2026,10,28,tzinfo=dt.timezone.utc).timestamp())
END=int(dt.datetime(2026,10,30,tzinfo=dt.timezone.utc).timestamp())
def ts(day,h=0,m=0):
    return int(dt.datetime.fromisoformat(day+"T00:00:00+00:00").timestamp())+h*3600+m*60
def slots(day):return [ts(day,13,35)+i*600 for i in range(12)]
def needed(day):
    s=slots(day)
    cash={t-240 for t in s}|{t-60 for t in s}
    return cash,cash|set(s)|{t+600 for t in s}
def urls():
    u={"MU_CASH":"https://query1.finance.yahoo.com/v8/finance/chart/MU?"+urllib.parse.urlencode(
        {"period1":START,"period2":END,"interval":"1m","includePrePost":"false"})}
    for d in DAYS:
        u[d]="https://contract.mexc.com/api/v1/contract/kline/index_price/MUSTOCK_USDT?"+urllib.parse.urlencode(
            {"interval":"Min1","start":ts(d,13,20),"end":ts(d,15,40)})
    return u
def get(url):
    q=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-MU-SourceGate/0.1"})
    with urllib.request.urlopen(q,timeout=35) as r:
        if r.status!=200:raise ValueError("HTTP_FAIL")
        raw=r.read(3000001)
    if len(raw)>3000000:raise ValueError("BODY_TOO_LARGE")
    return json.loads(raw),hashlib.sha256(raw).hexdigest()
def vectors(obj,key):
    if key=="MU_CASH":
        chart=obj.get("chart") or {};x=chart.get("result") or []
        if chart.get("error") or len(x)!=1 or (x[0].get("meta") or {}).get("symbol")!="MU":
            raise ValueError("CASH_NOT_MU")
        q=(x[0].get("indicators") or {}).get("quote") or []
        if len(q)!=1:raise ValueError("NO_CASH_QUOTES")
        data={"time":x[0].get("timestamp"),"open":q[0].get("open"),"close":q[0].get("close")}
    else:
        if obj.get("success") is not True or not isinstance(obj.get("data"),dict):
            raise ValueError("MUSTOCK_INDEX_UNAVAILABLE")
        data=obj["data"]
    a,b,c=(data.get(k) for k in ("time","open","close"))
    if not all(isinstance(v,list) for v in (a,b,c)) or not(len(a)==len(b)==len(c)):
        raise ValueError("BAR_SCHEMA")
    return a,b,c
def canon(a,b,c,required):
    rows={}
    for t,o,p in zip(a,b,c):
        try:t=int(t)
        except (ValueError,TypeError):continue
        if t not in required:continue
        if t in rows or t%60:raise ValueError("REQUIRED_TIME_DUPLICATE_OR_UNALIGNED")
        try:o=float(o);p=float(p)
        except (ValueError,TypeError):raise ValueError("REQUIRED_PRICE_MISSING")
        if not(math.isfinite(o) and math.isfinite(p) and o>0 and p>0):
            raise ValueError("REQUIRED_PRICE_INVALID")
        rows[t]=[t,o,p]
    if set(rows)!=required:raise ValueError("REQUIRED_BARS_MISSING_"+str(len(required-set(rows))))
    data=json.dumps([rows[t] for t in sorted(rows)],separators=(",",":"),allow_nan=False)
    return {"sha256":hashlib.sha256(data.encode()).hexdigest(),"n":len(required)}
def capture():
    result={}
    for key,url in urls().items():
        obj,rawsha=get(url)
        a,b,c=vectors(obj,key)
        d=DAYS if key=="MU_CASH" else (key,)
        hashes={}
        for day in d:
            hashes[day]=canon(a,b,c,needed(day)[0 if key=="MU_CASH" else 1])
        result[key]={"url":url,"raw_sha256":rawsha,"canonical":hashes}
    return result
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    r={"study":"MU_MUSTOCK_10M_SOURCE_V01","gate":"SOURCE_BLOCKED","raw_captures":[],
       "market_outcomes_opened":0,"signal_scores":0,
       "protected_2026_september_read":False,"nvda_old_forward_read":False}
    try:
        x=capture();time.sleep(.7);y=capture()
        r["raw_captures"]=[x,y]
        for k in x:
            if x[k]["canonical"]!=y[k]["canonical"]:
                raise ValueError("CANONICAL_SOURCE_CHANGED_"+k)
        r["gate"]="CANONICAL_REQUIRED_CASH_AND_INDEX_PASS"
        r["canonical_pinned"]={k:x[k]["canonical"] for k in x}
        r["raw_response_changed"]={k:x[k]["raw_sha256"]!=y[k]["raw_sha256"] for k in x}
    except Exception as e:r["error"]=type(e).__name__+":"+str(e)[:220]
    (OUT/"source_gate.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in r.items() if k!="raw_captures"},indent=2,sort_keys=True),flush=True)
    if r["gate"]!="CANONICAL_REQUIRED_CASH_AND_INDEX_PASS":raise SystemExit(2)
if __name__=="__main__":main()
