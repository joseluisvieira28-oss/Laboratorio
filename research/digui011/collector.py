#!/usr/bin/env python3
"""DIGUI-011 immutable public monthly USD-M perpetual 1h klines; READ-ONLY."""
import calendar,csv,datetime as dt,hashlib,io,json,pathlib,urllib.request,urllib.error,zipfile,time
OUT=pathlib.Path("digui011-evidence");OUT.mkdir(exist_ok=True)
COINS=("BTC","ETH","SOL");START=(2023,6);END=(2026,10)
HEAD=["coin","time_ms","open","high","low","close","volume","quote_volume","ntrades"]
def months():
    y,m=START
    while (y,m)<=END:
        yield y,m
        m+=1
        if m>12:y,m=y+1,1
def url(coin,y,m):
    s=f"{coin}USDT";a=f"{y}-{m:02d}"
    return f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/1h/{s}-1h-{a}.zip"
def get(url):
    last=None
    for delay in (0,1,3,7,15):
        if delay:time.sleep(delay)
        req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-DIGUI011/0.1 (read-only)"})
        try:
            with urllib.request.urlopen(req,timeout=30) as f:
                if f.status!=200:raise ValueError("HTTP non200")
                return f.read(2000000)
        except Exception as e:
            last=repr(e)
            if isinstance(e,urllib.error.HTTPError) and e.code in (404,403,451):break
    raise RuntimeError(f"SOURCE_BLOCKED {url} {last}")
def stamp(v):
    x=int(v)
    if x>10**15:x//=1000   # Binance Vision switched to microseconds in 2025
    elif x>10**14:x//=1000
    if x<1_500_000_000_000 or x>1_900_000_000_000:raise ValueError("invalid kline time scale")
    if x%3_600_000!=0:raise ValueError("non-hourly open time")
    return x
def val(v):
    x=float(v)
    if not (-1e300<x<1e300):raise ValueError("non-finite")
    return x
def run():
    allrows=[];manifest={"source":"Binance Vision USD-M perpetual klines","start":"2023-06","end":"2026-10",
                          "raw":[],"blocked":[],"no_trades":True}
    for coin in COINS:
        last_timestamp=None
        for y,m in months():
            address=url(coin,y,m)
            try:
                raw=get(address)
                digest=hashlib.sha256(raw).hexdigest()
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    files=z.namelist()
                    if len(files)!=1 or not files[0].endswith(".csv"):raise ValueError("Unexpected archive contents")
                    inputdata=z.read(files[0]).decode("utf-8-sig")
                rows=list(csv.reader(io.StringIO(inputdata)))
                n=0;gaps=0
                for row in rows:
                    if len(row)<9:continue
                    try:t=stamp(row[0])
                    except ValueError as e:
                        if row[0].lower().startswith(("open","time")):continue
                        raise e
                    d=dt.datetime.fromtimestamp(t/1000,tz=dt.timezone.utc)
                    if d.year!=y or d.month!=m:raise ValueError("month/time mismatch")
                    op,hi,lo,cl,vol=(val(row[j]) for j in (1,2,3,4,5))
                    quote=val(row[7]);count=int(row[8])
                    if min(op,hi,lo,cl)<=0 or lo>min(op,cl) or hi<max(op,cl) or vol<0 or quote<0 or count<0:
                        raise ValueError("unusable OHLCV")
                    if last_timestamp is not None:
                        if t<=last_timestamp:raise ValueError("non-increasing/duplicate hourly bars")
                        if t-last_timestamp!=3_600_000:gaps+=int((t-last_timestamp)//3_600_000-1)
                    last_timestamp=t
                    allrows.append((coin,t,op,hi,lo,cl,vol,quote,count))
                    n+=1
                expected=calendar.monthrange(y,m)[1]*24
                if n<expected*.8:raise ValueError(f"Missing >20% monthly bars: {n}/{expected}")
                manifest["raw"].append({"coin":coin,"year":y,"month":m,"sha256_zip":digest,
                    "source_url":address,"rows":n,"expected_hours":expected,"internal_or_previous_gaps":gaps,
                    "bytes":len(raw)})
                print("MONTH",coin,f"{y}-{m:02d}","bars",n,"gaps",gaps,flush=True)
            except Exception as e:
                manifest["blocked"].append({"coin":coin,"month":f"{y}-{m:02d}","error":str(e)[:300]})
                print("BLOCKED",coin,f"{y}-{m:02d}",str(e)[:150],flush=True)
        print("COMPLETE_COIN",coin,"rows",sum(r[0]==coin for r in allrows),flush=True)
    p=OUT/"ohlcv_1h.csv"
    with p.open("w",newline="") as f:
        w=csv.writer(f);w.writerow(HEAD);w.writerows(allrows)
    manifest["csv_sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()
    manifest["num_bars"]=len(allrows)
    (OUT/"source_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    print("SOURCE_COMPLETE",json.dumps({"bars":len(allrows),"files":len(manifest["raw"]),
         "blocked":len(manifest["blocked"]),"sha256":manifest["csv_sha256"]}),flush=True)
    if manifest["blocked"]:raise RuntimeError("Historical source incomplete: economic NO-GO")
if __name__=="__main__":run()
