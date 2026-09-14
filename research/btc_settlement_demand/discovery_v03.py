#!/usr/bin/env python3
import argparse, csv, hashlib, io, json, math, os, random, statistics, sys, urllib.request, zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

FAMILY_ID = "BTC-SETTLEMENT-DEMAND-001"
MVE_ID = "BSD-WOW7D-1D-001"
AUTHORITY_PATH = Path("research/btc_settlement_demand/BTC_SETTLEMENT_DEMAND_001_DISCOVERY_AUTHORITY_V0_3.md")
AUTHORITY_SHA256 = "18a45507ac36e15a5824043b46e7a4f43e377cc2775e54893e88b26395b12c7e"
AUTHORITY_GIT_COMMIT = "6fd4f4e9ae1f3bb030795919528229b44cdfee23"
AUTHORITY_DRIVE_ID = "1uE1QmcrIWUG-aV0kkFg1qXllQoQ5OJcX"
SOURCE_GATE_ID = "BSD-TXCOUNT-002"
SOURCE_RUN_ID = 34864390599
SOURCE_ARTIFACT_ID = 10355248843
SOURCE_ARTIFACT_ZIP_SHA256 = "d58b3e06683d827f393760112927b8c9314cdfdfb6ae559fbf1301b29383f163"
SOURCE_RAW_SHA256 = "e0488714ce6023589de3e9cd15524c5f1e643a0ae0028147c8cb830b313ffa7f"
SOURCE_MANIFEST_SHA256 = "108525b5d3c3f331f8aef4dbcfcec05c8ab0221ba7c8cbc179d8c944c239b9cd"
DISCOVERY_ENTRY_START = date(2018,1,1)
DISCOVERY_ENTRY_END = date(2024,12,30)
MAX_EXIT_DATE = date(2024,12,31)
BOOTSTRAP_SEED = 20260914
BOOTSTRAP_N = 10000
OUT = Path("btc_settlement_demand_discovery_v03_out")
RAW_MARKET = OUT / "raw_binance"
OUT.mkdir(parents=True, exist_ok=True)
RAW_MARKET.mkdir(parents=True, exist_ok=True)
FLAGS = {"live_trading":False,"exchange_mutation":False,"merge_to_main":False,"render_deployment":False,"access_2025":False,"access_2026":False}

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def write_json(path,obj): path.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")
def terminal(status,reason,extra=None,code=2):
    obj={"family_id":FAMILY_ID,"mve_id":MVE_ID,"phase":"DISCOVERY","status":status,"reason":reason,"authority_git_commit":AUTHORITY_GIT_COMMIT,"authority_drive_id":AUTHORITY_DRIVE_ID,**FLAGS}
    if extra: obj.update(extra)
    write_json(OUT/"discovery_result.json",obj); print(json.dumps(obj,indent=2,sort_keys=True)); raise SystemExit(code)

def verify_authority():
    if not AUTHORITY_PATH.exists(): terminal("TECHNICAL_FAILURE_PREOUTCOME","Frozen authority file missing",code=20)
    b=AUTHORITY_PATH.read_bytes(); got=sha256_bytes(b)
    if got!=AUTHORITY_SHA256: terminal("PROVENANCE_FAILURE","Frozen authority SHA256 mismatch",{"expected":AUTHORITY_SHA256,"got":got},21)
    text=b.decode("utf-8")
    required=["MVE_ID: BSD-WOW7D-1D-001","ACCEL(t)   = RECENT7(t) / PRIOR7(t) - 1.","Entry = BTCUSDT daily OPEN at 00:00 UTC on t+2.","Exit  = BTCUSDT daily OPEN at 00:00 UTC on t+3.","Eligible entries: 2018-01-01 through 2024-12-30 UTC.","2025 LOCKED.","2026 LOCKED."]
    missing=[x for x in required if x not in text]
    if missing: terminal("PROVENANCE_FAILURE","Frozen authority semantic binding missing",{"missing":missing},22)

def download_source_artifact():
    target=OUT/"source_gate_artifact.zip"
    if target.exists(): b=target.read_bytes()
    else:
        token=os.environ.get("GITHUB_TOKEN","")
        if not token: terminal("TECHNICAL_FAILURE_PREOUTCOME","GITHUB_TOKEN missing for source artifact binding",code=23)
        url=f"https://api.github.com/repos/joseluisvieira28-oss/Laboratorio/actions/artifacts/{SOURCE_ARTIFACT_ID}/zip"
        req=urllib.request.Request(url,headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","User-Agent":"crypto-lab-bsd-discovery/0.3"})
        try:
            with urllib.request.urlopen(req,timeout=90) as r: b=r.read()
        except Exception as e: terminal("TECHNICAL_FAILURE_PREOUTCOME",f"Source artifact download failed: {type(e).__name__}: {e}",code=24)
        target.write_bytes(b)
    got=sha256_bytes(b)
    if got!=SOURCE_ARTIFACT_ZIP_SHA256: terminal("PROVENANCE_FAILURE","Source Gate artifact ZIP SHA256 mismatch",{"expected":SOURCE_ARTIFACT_ZIP_SHA256,"got":got},25)
    return b

def extract_bound_source(artifact_bytes):
    try: z=zipfile.ZipFile(io.BytesIO(artifact_bytes))
    except Exception as e: terminal("DATA_FAILURE",f"Source artifact is not a valid ZIP: {e}",code=26)
    names=z.namelist(); raw_names=[n for n in names if n.endswith("raw_n_transactions.json")]; man_names=[n for n in names if n.endswith("source_manifest.json")]
    if len(raw_names)!=1 or len(man_names)!=1: terminal("PROVENANCE_FAILURE","Bound Source Gate artifact missing unique raw/manifest files",{"names":names},27)
    raw=z.read(raw_names[0]); manifest=z.read(man_names[0])
    if sha256_bytes(raw)!=SOURCE_RAW_SHA256: terminal("PROVENANCE_FAILURE","Bound source raw SHA256 mismatch",{"got":sha256_bytes(raw)},28)
    if sha256_bytes(manifest)!=SOURCE_MANIFEST_SHA256: terminal("PROVENANCE_FAILURE","Bound source manifest SHA256 mismatch",{"got":sha256_bytes(manifest)},29)
    try: payload=json.loads(raw)
    except Exception as e: terminal("DATA_FAILURE",f"Bound source raw JSON invalid: {e}",code=30)
    if payload.get("name")!="Confirmed Transactions Per Day" or payload.get("unit")!="Transactions" or payload.get("period")!="day": terminal("PROVENANCE_FAILURE","Bound source semantics mismatch",{"name":payload.get("name"),"unit":payload.get("unit"),"period":payload.get("period")},31)
    vals=payload.get("values")
    if not isinstance(vals,list): terminal("DATA_FAILURE","Bound source values[] missing",code=32)
    tx={}
    for i,row in enumerate(vals):
        if not isinstance(row,dict) or set(row.keys())!={"x","y"}: terminal("PROVENANCE_FAILURE",f"Unexpected bound source schema row {i}",code=33)
        dt=datetime.fromtimestamp(int(row["x"]),tz=timezone.utc)
        if dt.year>=2025:
            FLAGS["access_2025"]=dt.year==2025; FLAGS["access_2026"]=dt.year>=2026
            terminal("PROVENANCE_FAILURE","Protected source timestamp present in bound Source Gate artifact",{"timestamp":dt.isoformat()},34)
        if dt.time()!=datetime.min.time(): terminal("PROVENANCE_FAILURE","Source timestamp not UTC midnight",{"timestamp":dt.isoformat()},35)
        v=float(row["y"])
        if not math.isfinite(v) or v<0: terminal("DATA_FAILURE","Invalid source value",{"timestamp":dt.isoformat(),"value":row["y"]},36)
        d=dt.date()
        if d in tx: terminal("DATA_FAILURE","Duplicate source date",{"date":d.isoformat()},37)
        tx[d]=v
    expected_start,expected_end=date(2017,1,1),date(2024,12,31); expected_n=(expected_end-expected_start).days+1
    if len(tx)!=expected_n or min(tx)!=expected_start or max(tx)!=expected_end: terminal("DATA_FAILURE","Bound source coverage mismatch",{"count":len(tx),"min":min(tx).isoformat(),"max":max(tx).isoformat(),"expected":expected_n},38)
    return tx

def preflight():
    verify_authority(); artifact=download_source_artifact(); tx=extract_bound_source(artifact)
    obj={"family_id":FAMILY_ID,"mve_id":MVE_ID,"phase":"PREOUTCOME_PREFLIGHT","status":"PREOUTCOME_PREFLIGHT_PASS","authority_sha256":AUTHORITY_SHA256,"source_gate_id":SOURCE_GATE_ID,"source_artifact_id":SOURCE_ARTIFACT_ID,"source_artifact_zip_sha256":SOURCE_ARTIFACT_ZIP_SHA256,"source_raw_sha256":SOURCE_RAW_SHA256,"source_manifest_sha256":SOURCE_MANIFEST_SHA256,"source_days":len(tx),"source_first":min(tx).isoformat(),"source_last":max(tx).isoformat(),"price_values_opened":False,"returns_computed":False,"pnl_computed":False,**FLAGS}
    write_json(OUT/"preoutcome_preflight.json",obj); print(json.dumps(obj,indent=2,sort_keys=True)); return tx

def month_iter():
    y,m=2018,1
    while (y,m)<=(2024,12):
        yield y,m; m+=1
        if m==13: y+=1; m=1

def download_binance_market():
    opens={}; manifest=[]
    for y,m in month_iter():
        tag=f"{y:04d}-{m:02d}"; fn=f"BTCUSDT-1d-{tag}.zip"; url=f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/{fn}"; path=RAW_MARKET/fn
        if path.exists(): b=path.read_bytes()
        else:
            req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-bsd-discovery/0.3"})
            try:
                with urllib.request.urlopen(req,timeout=90) as r: b=r.read()
            except Exception as e: terminal("DATA_FAILURE",f"Binance archive acquisition failed for {tag}: {type(e).__name__}: {e}",code=40)
            path.write_bytes(b)
        zsha=sha256_bytes(b)
        try:
            z=zipfile.ZipFile(io.BytesIO(b)); csv_names=[n for n in z.namelist() if n.endswith(".csv")]
            if len(csv_names)!=1: terminal("DATA_FAILURE","Unexpected Binance archive layout",{"month":tag,"names":z.namelist()},41)
            csv_bytes=z.read(csv_names[0])
        except Exception as e: terminal("DATA_FAILURE",f"Invalid Binance ZIP {tag}: {e}",code=42)
        rows=0
        for row in csv.reader(io.StringIO(csv_bytes.decode("utf-8"))):
            if not row: continue
            try: ts=int(row[0]); op=float(row[1])
            except Exception as e: terminal("DATA_FAILURE",f"Invalid Binance row {tag}: {e}",{"row":row[:3]},43)
            dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc)
            if dt.year>=2025:
                FLAGS["access_2025"]=dt.year==2025; FLAGS["access_2026"]=dt.year>=2026
                terminal("PROVENANCE_FAILURE","Protected market timestamp encountered",{"timestamp":dt.isoformat(),"month":tag},44)
            if dt.time()!=datetime.min.time(): terminal("PROVENANCE_FAILURE","Binance daily open_time not UTC midnight",{"timestamp":dt.isoformat()},45)
            if not math.isfinite(op) or op<=0: terminal("DATA_FAILURE","Invalid Binance open",{"timestamp":dt.isoformat(),"open":row[1]},46)
            d=dt.date()
            if d in opens: terminal("DATA_FAILURE","Duplicate Binance market date",{"date":d.isoformat()},47)
            opens[d]=op; rows+=1
        manifest.append({"month":tag,"file":fn,"zip_sha256":zsha,"zip_bytes":len(b),"rows":rows})
    expected_start,expected_end=date(2018,1,1),date(2024,12,31); expected_n=(expected_end-expected_start).days+1; missing=[]; d=expected_start
    while d<=expected_end:
        if d not in opens: missing.append(d.isoformat())
        d+=timedelta(days=1)
    write_json(OUT/"market_source_manifest.json",{"source":"Binance Data Vision BTCUSDT 1d monthly klines","months":manifest,"unique_dates":len(opens),"expected_dates":expected_n,"missing_dates":missing,"first_date":min(opens).isoformat() if opens else None,"last_date":max(opens).isoformat() if opens else None,"protected_access_2025":FLAGS["access_2025"],"protected_access_2026":FLAGS["access_2026"]})
    if missing or len(opens)!=expected_n or min(opens)!=expected_start or max(opens)!=expected_end: terminal("DATA_FAILURE","Binance 2018-2024 market coverage incomplete",{"missing_count":len(missing),"missing_first":missing[:20],"count":len(opens),"expected":expected_n},48)
    return opens

def avg(vals): return sum(vals)/len(vals)
def pctile_sorted(xs,p):
    k=(len(xs)-1)*p; f=math.floor(k); c=math.ceil(k)
    return xs[int(k)] if f==c else xs[f]*(c-k)+xs[c]*(k-f)

def build_trades(tx,opens):
    trades=[]; t=date(2017,12,30); last_signal=date(2024,12,28)
    while t<=last_signal:
        recent_dates=[t-timedelta(days=i) for i in range(0,7)]; prior_dates=[t-timedelta(days=i) for i in range(7,14)]
        if any(d not in tx for d in recent_dates+prior_dates): terminal("DATA_FAILURE","Missing source date during frozen signal construction",{"signal_date":t.isoformat()},50)
        recent7=avg([tx[d] for d in recent_dates]); prior7=avg([tx[d] for d in prior_dates])
        if prior7<=0: terminal("DATA_FAILURE","Nonpositive PRIOR7 mean",{"signal_date":t.isoformat(),"prior7":prior7},51)
        accel=recent7/prior7-1.0; side=1 if accel>0 else (-1 if accel<0 else 0); entry=t+timedelta(days=2); exitd=t+timedelta(days=3)
        if entry<DISCOVERY_ENTRY_START or entry>DISCOVERY_ENTRY_END: t+=timedelta(days=1); continue
        if exitd>MAX_EXIT_DATE or exitd.year>=2025: terminal("PROVENANCE_FAILURE","Frozen trade would cross protected period",{"signal_date":t.isoformat(),"entry":entry.isoformat(),"exit":exitd.isoformat()},52)
        if side!=0:
            if entry not in opens or exitd not in opens: terminal("DATA_FAILURE","Missing frozen market open",{"entry":entry.isoformat(),"exit":exitd.isoformat()},53)
            entry_open=opens[entry]; exit_open=opens[exitd]; raw=exit_open/entry_open-1.0; gross=side*raw*10000.0
            trades.append({"signal_date":t.isoformat(),"entry_date":entry.isoformat(),"exit_date":exitd.isoformat(),"recent7":recent7,"prior7":prior7,"accel":accel,"side":side,"entry_open":entry_open,"exit_open":exit_open,"gross_bps":gross,"net6_bps":gross-6.0,"net10_bps":gross-10.0,"net20_bps":gross-20.0,"entry_year":entry.year})
        t+=timedelta(days=1)
    return trades

def profit_factor(xs):
    pos=sum(x for x in xs if x>0); neg=-sum(x for x in xs if x<0)
    return float("inf") if neg==0 and pos>0 else (pos/neg if neg>0 else 0.0)

def bootstrap_mean_stats(xs):
    rnd=random.Random(BOOTSTRAP_SEED); n=len(xs); means=[]
    for _ in range(BOOTSTRAP_N):
        s=0.0
        for _j in range(n): s+=xs[rnd.randrange(n)]
        means.append(s/n)
    means.sort(); p_nonpos=sum(1 for x in means if x<=0)/BOOTSTRAP_N
    return {"seed":BOOTSTRAP_SEED,"resamples":BOOTSTRAP_N,"p_mean_net10_le_zero":p_nonpos,"ci95_low":pctile_sorted(means,0.025),"ci95_high":pctile_sorted(means,0.975)}

def max_drawdown_from_bps(xs):
    equity=1.0; peak=1.0; maxdd=0.0
    for b in xs:
        equity*=1.0+b/10000.0; peak=max(peak,equity); maxdd=min(maxdd,equity/peak-1.0)
    return equity-1.0,maxdd

def summarize(trades):
    if not trades: terminal("DATA_FAILURE","No trades generated under frozen signal",code=60)
    gross=[x["gross_bps"] for x in trades]; n6=[x["net6_bps"] for x in trades]; n10=[x["net10_bps"] for x in trades]; n20=[x["net20_bps"] for x in trades]; by_year=defaultdict(list); gross_by_year=defaultdict(list)
    for tr in trades: by_year[tr["entry_year"]].append(tr["net10_bps"]); gross_by_year[tr["entry_year"]].append(tr["gross_bps"])
    year_means={str(y):sum(by_year[y])/len(by_year[y]) for y in sorted(by_year)}; year_counts={str(y):len(by_year[y]) for y in sorted(by_year)}
    nonneg=sum(1 for v in year_means.values() if v>=0); last4_nonneg=sum(1 for y in (2021,2022,2023,2024) if year_means.get(str(y),-float("inf"))>=0)
    gross_year_totals={str(y):sum(gross_by_year[y]) for y in sorted(gross_by_year)}; positive={y:v for y,v in gross_year_totals.items() if v>0}; pos_total=sum(positive.values()); concentration=max(positive.values())/pos_total if pos_total>0 else 1.0
    boot=bootstrap_mean_stats(n10); cum,maxdd=max_drawdown_from_bps(n10)
    stats={"n":len(trades),"long_count":sum(1 for x in trades if x["side"]==1),"short_count":sum(1 for x in trades if x["side"]==-1),"mean_gross_bps":sum(gross)/len(gross),"median_gross_bps":statistics.median(gross),"mean_net6_bps":sum(n6)/len(n6),"mean_net10_bps":sum(n10)/len(n10),"mean_net20_bps":sum(n20)/len(n20),"profit_factor_net10":profit_factor(n10),"win_rate_net10":sum(1 for x in n10 if x>0)/len(n10),"calendar_year_net10_mean_bps":year_means,"calendar_year_counts":year_counts,"nonnegative_years_2018_2024":nonneg,"nonnegative_years_2021_2024":last4_nonneg,"gross_year_totals_bps":gross_year_totals,"max_positive_year_gross_contribution_share":concentration,"bootstrap":boot,"cumulative_net10_compounded":cum,"max_drawdown_net10_compounded":maxdd}
    gates={"n_ge_1000":stats["n"]>=1000,"mean_net10_gt_0":stats["mean_net10_bps"]>0,"pf_net10_gt_1":stats["profit_factor_net10"]>1.0,"median_gross_gt_0":stats["median_gross_bps"]>0,"years_nonnegative_ge_5_of_7":nonneg>=5,"last4_nonnegative_ge_3_of_4":last4_nonneg>=3,"bootstrap_p_le_0_20":boot["p_mean_net10_le_zero"]<=0.20,"positive_year_concentration_le_0_70":concentration<=0.70,"source_binding_pass":True,"timing_firewall_pass":True,"protected_period_firewall_pass":not FLAGS["access_2025"] and not FLAGS["access_2026"]}
    return stats,gates

def write_trades_csv(trades):
    fields=["signal_date","entry_date","exit_date","recent7","prior7","accel","side","entry_open","exit_open","gross_bps","net6_bps","net10_bps","net20_bps","entry_year"]
    with (OUT/"trades.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(trades)

def discovery():
    tx=preflight(); opens=download_binance_market(); trades=build_trades(tx,opens); write_trades_csv(trades); stats,gates=summarize(trades); all_pass=all(gates.values())
    result={"family_id":FAMILY_ID,"mve_id":MVE_ID,"phase":"ONE_SHOT_DISCOVERY","status":"DISCOVERY_PASS_CANDIDATE" if all_pass else "DISCOVERY_FAIL_NO_PROMOTION","authority_git_commit":AUTHORITY_GIT_COMMIT,"authority_drive_id":AUTHORITY_DRIVE_ID,"authority_sha256":AUTHORITY_SHA256,"source_gate_id":SOURCE_GATE_ID,"source_run_id":SOURCE_RUN_ID,"source_artifact_id":SOURCE_ARTIFACT_ID,"discovery_entry_start":DISCOVERY_ENTRY_START.isoformat(),"discovery_entry_end":DISCOVERY_ENTRY_END.isoformat(),"max_exit_date":MAX_EXIT_DATE.isoformat(),"signal":"RECENT7 mean / PRIOR7 mean - 1; sign => long/short","publication_buffer_days":1,"hold_days":1,"primary_cost_bps":10,"stats":stats,"promotion_gates":gates,"price_values_opened":True,"returns_computed":True,"pnl_computed":True,**FLAGS}
    write_json(OUT/"discovery_result.json",result); write_json(OUT/"promotion_gates.json",gates); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if all_pass else 3

def main():
    ap=argparse.ArgumentParser(); g=ap.add_mutually_exclusive_group(required=True); g.add_argument("--preflight-only",action="store_true"); g.add_argument("--discovery",action="store_true"); args=ap.parse_args(); branch=os.environ.get("GITHUB_REF_NAME","")
    if branch and branch!="btc-settlement-demand-v0.3-discovery": terminal("TECHNICAL_FAILURE_PREOUTCOME","Wrong branch for frozen Discovery",{"branch":branch},19)
    if args.preflight_only: preflight(); return 0
    return discovery()

if __name__=="__main__": sys.exit(main())
