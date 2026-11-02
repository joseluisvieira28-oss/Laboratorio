"""Frozen BTC10M triangular hypothesis. Python 3 standard library only."""
import array, concurrent.futures, csv, datetime as dt, hashlib, io, json, math, pathlib, random, urllib.request, zipfile
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raw"
START=int(dt.datetime(2023,4,1,tzinfo=dt.UTC).timestamp()*1000)
END=int(dt.datetime(2025,1,1,tzinfo=dt.UTC).timestamp()*1000)
N=(END-START)//60000
MONTHS=[f"{y}-{m:02d}" for y in (2023,2024) for m in range(1,13) if (y,m)>=(2023,4)]
SYMBOLS=["BTCUSDT","BTCUSDC","USDCUSDT"]
def sha(b):return hashlib.sha256(b).hexdigest()
def bounds(m):
    d=dt.datetime.fromisoformat(m+"-01").replace(tzinfo=dt.UTC)
    e=dt.datetime(d.year+(d.month==12),1 if d.month==12 else d.month+1,1,tzinfo=dt.UTC)
    return int(d.timestamp()*1000),int(e.timestamp()*1000)
def fetch(pair):
    s,m=pair
    name=f"{s}-1m-{m}.zip"
    url=f"https://data.binance.vision/data/spot/monthly/klines/{s}/1m/{name}"
    p=DATA/name
    receipt={"symbol":s,"month":m,"url":url,"checksum_url":url+".CHECKSUM"}
    try:
        for suffix in (".CHECKSUM",""):
            dest=pathlib.Path(str(p)+suffix)
            if not dest.exists():
                with urllib.request.urlopen(url+suffix,timeout=60) as r:
                    body=r.read(20000001)
                if len(body)>20000000:raise ValueError("download size cap")
                dest.write_bytes(body)
        raw=p.read_bytes()
        check=pathlib.Path(str(p)+".CHECKSUM").read_text().strip().split()
        assert len(check)==2 and check[1].lstrip("*")==name,"checksum filename"
        assert len(check[0])==64 and sha(raw)==check[0].lower(),"checksum mismatch"
        receipt.update(status="PASS",sha256=sha(raw),bytes=len(raw))
    except Exception as e:receipt.update(status="SOURCE_FAIL",error=type(e).__name__+":"+str(e))
    return receipt
def load():
    DATA.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        manifest=list(pool.map(fetch,[(s,m) for s in SYMBOLS for m in MONTHS]))
    (ROOT/"source_manifest.json").write_text(json.dumps(manifest,indent=2))
    if any(x["status"]!="PASS" for x in manifest):raise ValueError("SOURCE_DOWNLOAD_FAIL")
    markets={}
    quality=[]
    for s in SYMBOLS:
        op=array.array("d",[float("nan")])*N
        cl=array.array("d",[float("nan")])*N
        valid=bytearray(N)
        for m in MONTHS:
            p=DATA/f"{s}-1m-{m}.zip"
            lo,hi=bounds(m);previous=lo-60000;count=0
            with zipfile.ZipFile(p) as z:
                assert z.namelist()==[f"{s}-1m-{m}.csv"],"unexpected zip member"
                with z.open(z.namelist()[0]) as f:
                    for row in csv.reader(io.TextIOWrapper(f,encoding="utf8")):
                        assert len(row)==12,"column count"
                        t=int(row[0]);assert lo<=t<hi and t%60000==0 and t>previous,"timestamp"
                        assert int(row[6])==t+59999,"close timestamp"
                        o,h,l,c,v=map(float,row[1:6])
                        assert all(math.isfinite(x) and x>0 for x in (o,h,l,c)),"prices"
                        assert l<=min(o,c)<=max(o,c)<=h,"OHLC"
                        assert math.isfinite(v) and v>=0,"volume"
                        trades=int(row[8]);assert trades>=0,"trades"
                        idx=(t-START)//60000
                        op[idx]=o;cl[idx]=c;valid[idx]=int(v>0 and trades>0)
                        previous=t;count+=1
            coverage=count/((hi-lo)//60000)
            quality.append({"symbol":s,"month":m,"minutes":count,"coverage":coverage})
            assert coverage>=.9995,"coverage "+s+" "+m
        markets[s]=(op,cl,valid)
    (ROOT/"source_quality.json").write_text(json.dumps(quality,indent=2))
    return markets
def side_at(markets,i):
    residuals=[]
    for j in range(i-3,i):
        if j<0 or any(not markets[s][2][j] for s in SYMBOLS):return 0,[]
        r=10000*math.log(markets["BTCUSDC"][1][j]*markets["USDCUSDT"][1][j]/markets["BTCUSDT"][1][j])
        residuals.append(r)
    side=1 if min(residuals)>=5 else -1 if max(residuals)<=-5 else 0
    return side,residuals
def events(markets):
    out=[]
    btc=markets["BTCUSDT"]
    for i in range(0,N-10,10):
        t=START+i*60000
        if dt.datetime.fromtimestamp(t/1000,dt.UTC).year!=dt.datetime.fromtimestamp((t+600000)/1000,dt.UTC).year:continue
        side,r=side_at(markets,i)
        if not side or not btc[2][i] or not btc[2][i+10]:continue
        entry,exit=btc[0][i],btc[0][i+10]
        truth=(exit>entry)-(exit<entry)
        mom=(btc[1][i-1]>btc[1][i-3])-(btc[1][i-1]<btc[1][i-3])
        out.append({"time_ms":t,"side":side,"truth":truth,"entry":entry,"exit":exit,"r3":r,
                    "momentum3":mom})
    return out
def pay(side,truth,q):
    return 0. if side==0 or truth==0 else q if side==truth else -1.
def quant(v,p):
    v=sorted(v);x=(len(v)-1)*p;j=int(x)
    return v[j]+(v[min(j+1,len(v)-1)]-v[j])*(x-j)
def stats(rows,year):
    rows=[r for r in rows if dt.datetime.fromtimestamp(r["time_ms"]/1000,dt.UTC).year==year]
    n=len(rows);wins=sum(r["side"]==r["truth"] for r in rows);ties=sum(r["truth"]==0 for r in rows);loss=n-wins-ties
    ndays=(dt.date(year+1,1,1)-dt.date(year,1,1)).days
    totals=[[0.,0.,0.,0.,0.] for _ in range(ndays)]
    quarters=[[] for _ in range(4)];months={}
    for r in rows:
        d=dt.datetime.fromtimestamp(r["time_ms"]/1000,dt.UTC).date()
        a=pay(r["side"],r["truth"],.7);b=pay(r["side"],r["truth"],.8)
        u=pay(1,r["truth"],.7);mom=pay(r["momentum3"],r["truth"],.7)
        day=totals[(d-dt.date(year,1,1)).days]
        for j,x in enumerate([1,a,b,a-u,a-mom]):day[j]+=x
        quarters[(d.month-1)//3].append(a)
        months.setdefault(str(d)[:7],[]).append(a)
    rng=random.Random(20261102);boots=[[] for _ in range(4)];empty=0
    for _ in range(10000):
        sums=[0.]*5
        for _ in range(ndays):
            a=totals[rng.randrange(ndays)]
            for j in range(5):sums[j]+=a[j]
        if not sums[0]:empty+=1;continue
        for j in range(4):boots[j].append(sums[j+1]/sums[0])
    mean=lambda v:sum(v)/len(v) if v else None
    lower=[quant(b,.025) if b else None for b in boots]
    qmeans=[mean(q) for q in quarters]
    sample=(n-ties>=300 and sum(x[0]>0 for x in totals)>=20)
    economic=(n-ties>0 and wins/(n-ties)>1/1.7 and all(lower[j] is not None and lower[j]>0 for j in (0,2,3)) and sum(x is not None and x>0 for x in qmeans)>=3)
    return {"year":year,"signals":n,"wins":wins,"losses":loss,"ties":ties,
            "accuracy_non_tie":wins/(n-ties) if n>ties else None,
            "signal_days":sum(x[0]>0 for x in totals),
            "q70_ev":sum(x[1] for x in totals)/n if n else None,
            "q80_ev":sum(x[2] for x in totals)/n if n else None,
            "lower_025_q70":lower[0],"lower_025_q80":lower[1],
            "lower_025_paired_vs_up":lower[2],"lower_025_paired_vs_mom3":lower[3],
            "quarter_q70":qmeans,"month_q70":{k:mean(v) for k,v in months.items()},
            "bootstrap_empty":empty,"verdict":"FAIL_SAMPLE" if not sample else "PASS_PROXY" if economic else "FAIL_ECONOMIC"}
def selftest():
    mk={s:(array.array("d",[100.]*30),array.array("d",[100.]*30),bytearray([1]*30)) for s in SYMBOLS}
    mk["USDCUSDT"][1][:]=array.array("d",[1.001]*30)
    a=side_at(mk,10)
    assert a[0]==1
    for s in SYMBOLS:
        for j in range(10,30):
            mk[s][0][j]=999999;mk[s][1][j]=999999
    assert side_at(mk,10)==a
    assert pay(1,-1,.7)==-1 and pay(1,0,.7)==0
    assert pay(1,1,.7)==.7
if __name__=="__main__":
    selftest()
    try:
        markets=load()
        ev=events(markets)
        (ROOT/"events.json").write_text(json.dumps(ev,separators=(",",":")))
        result={"study":"BTC10M_TRIANGULAR_NUMERAIRE_001","protocol_commit":"02b21b4a5ae9f800272685a3699119e755f81abc",
                "development":stats(ev,2023),"oos":stats(ev,2024),"live_go":False,"accessed_2025_or_2026":False,
                "settlement_parity_proven":False}
    except Exception as e:result={"status":"SOURCE_FAIL","error":type(e).__name__+":"+str(e),"live_go":False}
    (ROOT/"results.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
