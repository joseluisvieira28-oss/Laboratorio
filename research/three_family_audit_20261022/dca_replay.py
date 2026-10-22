"""ADCA-BTC-SMA200-001: frozen research-only replay, standard library only."""
import argparse, calendar, concurrent.futures, csv, datetime as dt, hashlib, io, json, math, pathlib, time, urllib.request, zipfile
UTC=dt.timezone.utc
ROOT=pathlib.Path(__file__).resolve().parent
BASE="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/"
FREEZE="1d746cd94451829d5b70402f0f70fbee8f761421"
def now(): return dt.datetime.now(UTC).isoformat()
def digest(b): return hashlib.sha256(b).hexdigest()
def emit(name,obj): (ROOT/name).write_text(json.dumps(obj,indent=2,allow_nan=False),encoding="utf-8")
def timestamp(s):
    n=int(s)
    return dt.datetime.fromtimestamp(n/(1000000 if n>=10**15 else 1000),UTC)
def buy(cash,units,budget,price,c):
    spend=min(cash,budget)
    q=spend/(price*(1+c))
    return cash-spend,units+q,q*price*c,q*price
def simulate(rows,year,c,mode):
    cash=units=total=friction=turnover=0.
    peak=index=1.; mdd=0.; prev=None; ledger=[]
    for i,r in enumerate(rows):
        if r["date"].year!=year: continue
        contribution=0.
        if r["date"].weekday()==0:
            contribution=100.; cash+=contribution; total+=contribution
            if mode=="adaptive":
                hist=rows[i-200:i]
                assert len(hist)==200 and hist[-1]["date"]<r["date"]
                sma=sum(x["close"] for x in hist)/200
                budget=150. if hist[-1]["close"]<sma else 50.
            else:
                sma=None; budget={"fixed":100.,"delayed":75.,"cash":0.}[mode]
            cash,units,f,n=buy(cash,units,budget,r["open"],c)
            friction+=f; turnover+=n
            ledger.append({"date":r["date"].isoformat(),"contribution":100.,"budget":budget,
                           "sma":sma,"price":r["open"],"cash":cash,"units":units,"friction":f,"notional":n})
        assert cash>=-1e-9 and units>=0
        wealth=cash+units*r["close"]
        # Cash flow at start of day: remove external flow from performance denominator.
        if prev is not None: index*=wealth/(prev+contribution)
        elif contribution: index=wealth/contribution
        peak=max(peak,index); mdd=min(mdd,index/peak-1); prev=wealth
    last=[x for x in rows if x["date"].year==year][-1]
    sell_notional=units*last["close"]; sell_cost=sell_notional*c
    net=cash+sell_notional-sell_cost
    friction+=sell_cost; turnover+=sell_notional
    if prev and prev>0:
        index*=net/prev; mdd=min(mdd,index/peak-1)
    return {"year":year,"mode":mode,"cost_bps_per_side":c*10000,"contributions":total,
            "deposit_count":len(ledger),"terminal_cash_before_sale":cash,"terminal_units_before_sale":units,
            "net_terminal_wealth":net,"net_gain_on_contributions":net/total-1,
            "total_friction":friction,"gross_turnover":turnover,
            "twr_max_drawdown":mdd,"terminal_sell_cost":sell_cost,"ledger":ledger}
def tests():
    assert timestamp("1735689600000")==timestamp("1735689600000000")
    cash,q,f,n=buy(100.,0.,150.,10.,.0015)
    assert cash==0 and abs(n+f-100)<1e-10
    assert abs(q*10*(1-.0015)-100*(1-.0015)/(1+.0015))<1e-10
    start=dt.date(2020,1,1)
    flat=[{"date":start+dt.timedelta(days=i),"open":10.,"high":10.,"low":10.,"close":10.,"volume":1.} for i in range(731)]
    a=simulate(flat,2021,0.,"adaptive"); b=simulate(flat,2021,0.,"fixed")
    assert a["net_terminal_wealth"]==b["net_terminal_wealth"]==a["contributions"]
    assert a["terminal_cash_before_sale"]>0 and b["terminal_cash_before_sale"]==0
    changed=[dict(x) for x in flat]; changed[-1]["close"]=100.
    d=simulate(changed,2021,0.,"adaptive")
    assert [(x["date"],x["budget"]) for x in a["ledger"]]==[(x["date"],x["budget"]) for x in d["ledger"]]
    for mode in ("adaptive","fixed","delayed","cash"):
        v=simulate(flat,2021,.0015,mode)
        assert v["contributions"]==5200.
        assert abs(v["net_terminal_wealth"]+v["total_friction"]-5200)<1e-8
    return {"passed":True,"cases":["ms_us_equivalence","cash_cap_no_leverage","flat_price_roundtrip_cost","same_external_contributions","cash_conservation","future_close_does_not_change_signals"],"at_utc":now()}
def acquire_one(ym):
    name="BTCUSDT-1d-"+ym+".zip"; path=ROOT/"raw"/name
    stamp=now(); objects=[]
    for suffix in ("",".CHECKSUM"):
        p=pathlib.Path(str(path)+suffix); url=BASE+name+suffix
        if not p.exists():
            req=urllib.request.Request(url,headers={"User-Agent":"Research-only historical data audit"})
            with urllib.request.urlopen(req,timeout=25) as r: data=r.read()
            p.write_bytes(data)
        data=p.read_bytes()
        objects.append({"url":url,"retrieved_or_revalidated_at_utc":stamp,"bytes":len(data),"sha256":digest(data)})
    expected=pathlib.Path(str(path)+".CHECKSUM").read_text().split()[0].lower()
    assert digest(path.read_bytes())==expected, "CHECKSUM mismatch "+name
    return {"month":ym,"checksum_verified":True,"objects":objects}
def acquire():
    (ROOT/"raw").mkdir(exist_ok=True)
    months=[f"{y}-{m:02}" for y in range(2020,2026) for m in range(1,13)]
    out=[]; errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(acquire_one,x):x for x in months}
        for fut in concurrent.futures.as_completed(futures):
            try: out.append(fut.result())
            except Exception as e: errors.append({"month":futures[fut],"error":str(e)})
    receipt={"freeze_commit":FREEZE,"at_utc":now(),"expected_months":72,"verified_months":len(out),
             "objects":sorted(out,key=lambda x:x["month"]),"errors":errors,"money_spent":0}
    emit("SOURCE_MANIFEST.json",receipt)
    if errors: raise RuntimeError("SOURCE_BLOCKED: "+str(len(errors))+" months")
    return receipt
def parse_gate(manifest):
    rows=[]; stamps=[]
    for item in manifest["objects"]:
        ym=item["month"]; p=ROOT/"raw"/("BTCUSDT-1d-"+ym+".zip")
        # Recheck frozen bytes before any outcome calculation.
        assert digest(p.read_bytes())==item["objects"][0]["sha256"]
        with zipfile.ZipFile(p) as z:
            assert len(z.namelist())==1
            text=z.read(z.namelist()[0]).decode("utf-8")
        month=[]
        for r in csv.reader(io.StringIO(text)):
            assert len(r)==12
            t=timestamp(r[0]); end=timestamp(r[6])
            assert t.strftime("%Y-%m")==ym and t.hour==t.minute==t.second==t.microsecond==0
            assert abs((end-t).total_seconds()-86400)<.01
            o,h,l,c,v=map(float,r[1:6])
            assert all(math.isfinite(x) for x in (o,h,l,c,v))
            assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
            month.append({"date":t.date(),"open":o,"high":h,"low":l,"close":c,"volume":v})
            stamps.append(t.date())
        assert len(month)==calendar.monthrange(int(ym[:4]),int(ym[5:]))[1]
        assert [x["date"] for x in month]==sorted(x["date"] for x in month)
        rows+=month
    expected=[dt.date(2020,1,1)+dt.timedelta(days=i) for i in range(2192)]
    assert stamps==expected and len(set(stamps))==2192
    receipt={"status":"SOURCE_PASS","at_utc":now(),"rows":len(rows),"first":str(stamps[0]),"last":str(stamps[-1]),
             "missing_days":0,"duplicates":0,"verified_zip_count":72,"source_manifest_sha256":digest((ROOT/"SOURCE_MANIFEST.json").read_bytes()),
             "outcomes_computed_at_gate":False,"2026_downloaded":False}
    emit("SOURCE_GATE.json",receipt)
    return rows
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--test",action="store_true"); ap.add_argument("--source-only",action="store_true")
    args=ap.parse_args(); started=time.monotonic()
    test=tests(); emit("TEST_RECEIPT.json",test)
    if args.test: print(json.dumps(test)); return
    try:
        manifest=acquire(); rows=parse_gate(manifest)
        if args.source_only: print("SOURCE_PASS; outcomes sealed"); return
        results=[simulate(rows,y,c,m) for y in range(2021,2026) for c in (.0015,.003) for m in ("adaptive","fixed","delayed","cash")]
        effects=[]
        for y in range(2021,2026):
            for c in (15,30):
                a=next(x for x in results if x["year"]==y and round(x["cost_bps_per_side"])==c and x["mode"]=="adaptive")
                b=next(x for x in results if x["year"]==y and round(x["cost_bps_per_side"])==c and x["mode"]=="fixed")
                effects.append({"year":y,"cost_bps_per_side":c,"effect_on_contributions":(a["net_terminal_wealth"]-b["net_terminal_wealth"])/a["contributions"]})
        passes=all(x["effect_on_contributions"]>0 for x in effects if x["year"] in (2024,2025))
        summary={"lab_id":"ADCA-BTC-SMA200-001","freeze_commit":FREEZE,"at_utc":now(),
                 "runner_sha256":digest(pathlib.Path(__file__).read_bytes()),"elapsed_seconds":time.monotonic()-started,
                 "historical_gate": "POSITIVE_TEMPORAL_CANDIDATE" if passes else "HISTORICAL_SUPERIORITY_NOT_REPLICATED",
                 "economic_verdict":"INCONCLUSIVE_NO_INDEPENDENT_EXECUTABLE_EDGE","effects":effects,
                 "results":[{k:v for k,v in x.items() if k!="ledger"} for x in results],
                 "limitations":["Two temporal OOS years only","Laboratory-wide prior exposure","Daily OHLC reference is not executable quote","Cost scenarios, not verified execution costs","BTC only and one venue","USDT numeraire, no tax or custody counterparty loss modeled"]}
        emit("DCA_RESULTS.json",summary); emit("DCA_LEDGERS.json",results)
        print(json.dumps({k:v for k,v in summary.items() if k not in ("results",)}))
    except Exception as e:
        emit("BLOCKER.json",{"at_utc":now(),"error":str(e),"outcomes_opened":False})
        raise
if __name__=="__main__": main()
