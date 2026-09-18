#!/usr/bin/env python3
"""CED1D-0031 prospective shadow collector V0.2.

Research-only, public/read-only data. Reuses the exact frozen CED-1D V0.3
hypothesis implementation. No authenticated endpoints, orders, wallets, live
mutation, parameter tuning or pre-boundary performance backfill.

The collector is deterministic over the exact post-freeze signal-day interval
[2026-09-18, through_signal_day]. It reconstructs:
- reference-track economics with frozen 14/20 bps nonfunding costs,
- actual public funding rates with conservative markPrice low/high bounds,
- frozen 100-USDT aggTrades execution proxy,
- frozen +/-1% bookDepth capacity corroboration,
- operational and Tier-1-evidence gate diagnostics.

V0.2 prospectively corrects only lookback-input acquisition: the 20D signal uses 20 PRIOR VALID daily observations, so pre-boundary source acquisition walks backward until exactly that valid-observation requirement is satisfied. No real shadow collector run occurred under V0.1.\n\nIt does not automatically promote or demote the candidate.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib,io,json,math,re,statistics,sys,tempfile,time,urllib.parse,urllib.request,zipfile
from collections import defaultdict
from datetime import date,datetime,timedelta,timezone
from pathlib import Path

SYMBOL="AVAXUSDT"
TARGET="CED1D-0031"
V03_ZIP_SHA="df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958"
HYPOTHESES_SHA="dc52cdc16aee0ba586ec7081a39ce68d62c5544e9bd27186255b4d9a87368693"

FIRST_SIGNAL_DAY=date(2026,9,18)
FIRST_SIGNAL_COMPLETION=datetime(2026,9,19,0,0,tzinfo=timezone.utc)
FIRST_ENTRY_TS=int(datetime(2026,9,19,0,1,tzinfo=timezone.utc).timestamp()*1000)

LOOKBACK=20
HORIZON=1
BASE_REFERENCE_COST_BPS=14.0
STRESS_REFERENCE_COST_BPS=20.0
RESEARCH_NOTIONAL_USDT=100.0
AGG_WINDOW_MS=5000
BASE_EXEC_FEE_RT_BPS=8.0
STRESS_EXEC_FEE_RT_BPS=10.0
BOOKDEPTH_MAX_AGE_MS=60000
BOOKDEPTH_BUY_PCT=1.0
BOOKDEPTH_SELL_PCT=-1.0

OP_CHECKPOINT_EVENTS=10
OP_CHECKPOINT_DAYS=14
TIER1_MIN_EVENTS=60
TIER1_MIN_COMPLETE_WEEKS=8
TIER1_MIN_EXEC_PAIRS=50

VISION="https://data.binance.vision/data/futures/um/daily"
PUBLIC_API="https://data-api.binance.vision"
UA="CED1D-0031-PROSPECTIVE-SHADOW/0.2"
HEADER_ALIASES={"open_time","opentime","timestamp","time","start_time"}

class GateError(RuntimeError): pass

def sha256_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def canonical(o):return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def mean(xs):return math.fsum(xs)/len(xs) if xs else None
def pf(vals):
    gains=math.fsum(v for v in vals if v>0); losses=-math.fsum(v for v in vals if v<0)
    return gains/losses if losses>0 else None
def pct(vals,p):
    a=sorted(vals)
    if not a:return None
    q=(len(a)-1)*p; lo=math.floor(q); hi=math.ceil(q)
    return a[lo]+(a[hi]-a[lo])*(q-lo)
def norm_header(s):return re.sub(r"[^a-z0-9_]+","",str(s).strip().lower().replace(" ","_"))
def norm_ms(v):
    n=int(float(v))
    while n>10**14:n//=1000
    return n
def week_start(d:date):return d-timedelta(days=d.weekday())

def fetch(url,attempts=3,timeout=180):
    last=None
    for i in range(attempts):
        req=urllib.request.Request(url,headers={"User-Agent":UA})
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:
                if r.status!=200:raise GateError(f"HTTP_{r.status}:{url}")
                return r.read()
        except Exception as e:
            last=e
            if i+1<attempts:time.sleep(i+1)
    if isinstance(last,GateError):raise last
    raise GateError(f"FETCH_FAIL:{type(last).__name__}:{last}:{url}") from last

def verified_zip(url):
    raw=fetch(url)
    check=fetch(url+".CHECKSUM").decode("utf-8",errors="replace")
    m=re.search(r"([0-9a-fA-F]{64})",check)
    if not m:raise GateError(f"CHECKSUM_PARSE:{url}")
    expected=m.group(1).lower(); got=sha256_bytes(raw)
    if got!=expected:raise GateError(f"CHECKSUM_MISMATCH:{url}:{got}:{expected}")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad is not None:raise GateError(f"ZIP_CRC_FAIL:{url}:{bad}")
        members=[x for x in z.namelist() if not x.endswith("/")]
        if len(members)!=1:raise GateError(f"ZIP_MEMBER_COUNT:{url}:{len(members)}")
    return raw,got

def load_original_hypotheses(v03_zip:Path,tmp:Path):
    if sha256_file(v03_zip)!=V03_ZIP_SHA:raise GateError("V03_RUNNER_ZIP_SHA_MISMATCH")
    with zipfile.ZipFile(v03_zip) as z:
        bad=z.testzip()
        if bad is not None:raise GateError("V03_ZIP_CRC_FAIL")
        member="CED_1D_V1_RUNNER_FREEZE_V0.3/ced1d/hypotheses.py"
        raw=z.read(member)
        if hashlib.sha256(raw).hexdigest()!=HYPOTHESES_SHA:raise GateError("HYPOTHESES_SHA_MISMATCH")
        z.extractall(tmp)
    root=tmp/"CED_1D_V1_RUNNER_FREEZE_V0.3"
    sys.path.insert(0,str(root))
    return importlib.import_module("ced1d.hypotheses")

def daily_kline_url(kind,day):
    ds=day.isoformat()
    return f"{VISION}/{kind}/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"

def daily_agg_url(day):
    ds=day.isoformat()
    return f"{VISION}/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{ds}.zip"

def daily_bookdepth_url(day):
    ds=day.isoformat()
    return f"{VISION}/bookDepth/{SYMBOL}/{SYMBOL}-bookDepth-{ds}.zip"

def parse_price_zip(raw:bytes,expected_day:date):
    rows=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        member=[n for n in z.namelist() if not n.endswith("/")][0]
        rdr=csv.reader(io.TextIOWrapper(z.open(member),encoding="utf-8-sig",newline=""))
        first=True
        for row in rdr:
            if not row:continue
            if first:
                first=False
                if len(row)>=5 and norm_header(row[0]) in HEADER_ALIASES:continue
            if len(row)<5:raise GateError(f"PRICE_SHORT_ROW:{expected_day}:{row}")
            ts=norm_ms(row[0]); o,h,l,c=map(float,row[1:5])
            dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc)
            if dt.date()!=expected_day:raise GateError(f"PRICE_DAY_BOUNDS:{expected_day}:{ts}")
            if not all(math.isfinite(x) for x in (o,h,l,c)) or min(o,h,l,c)<=0:raise GateError(f"PRICE_NUMERIC:{row}")
            rows.append((ts,o,h,l,c))
    rows.sort()
    return rows

def daybar_from_rows(day,rows):
    if not rows:return None
    mask=0; dup=0; open0001=None; first_ts=None; last_ts=None
    o=rows[0][1]; h=max(x[2] for x in rows); l=min(x[3] for x in rows); c=rows[-1][4]
    for ts,op,hi,lo,cl in rows:
        dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc); minute=dt.hour*60+dt.minute
        bit=1<<minute
        if mask&bit:dup+=1
        else:mask|=bit
        if minute==1:open0001=op
        first_ts=ts if first_ts is None else min(first_ts,ts); last_ts=ts if last_ts is None else max(last_ts,ts)
    minutes=mask.bit_count()
    return {"date":day.isoformat(),"open":o,"high":h,"low":l,"close":c,"first_ts":first_ts,"last_ts":last_ts,
            "duplicates":dup,"open_0001":open0001,"minutes":minutes,
            "valid_day":minutes==1440 and dup==0 and open0001 is not None}

def build_price_bars(start_day,end_day,role="SHADOW_PATH"):
    bars=[]; source=[]
    d=start_day
    while d<=end_day:
        url=daily_kline_url("klines",d)
        raw,h=verified_zip(url)
        rows=parse_price_zip(raw,d); bar=daybar_from_rows(d,rows)
        if bar is None:raise GateError(f"EMPTY_PRICE_DAY:{d}")
        source.append({"kind":"klines","role":role,"day":d.isoformat(),"url":url,"sha256":h,"rows":len(rows),"valid_day":bar["valid_day"]})
        bars.append(bar); d+=timedelta(days=1)
    return bars,source

def build_shadow_price_bars(through_signal_day):
    """Acquire the minimum prior VALID-day history required by frozen Series semantics."""
    end=through_signal_day+timedelta(days=HORIZON+1)
    main,source=build_price_bars(FIRST_SIGNAL_DAY,end,"SHADOW_SIGNAL_OR_PATH")
    warm=[]; valid_prior=0; scanned=0; d=FIRST_SIGNAL_DAY-timedelta(days=1)
    while valid_prior<LOOKBACK:
        if scanned>=WARMUP_MAX_CALENDAR_DAYS:
            raise GateError(f"WARMUP_VALID_OBSERVATION_FAIL:{valid_prior}:{scanned}")
        one,src=build_price_bars(d,d,"LOOKBACK_INPUT_ONLY")
        bar=one[0]; warm.append(bar); source.extend(src)
        if bar["valid_day"]: valid_prior+=1
        scanned+=1; d-=timedelta(days=1)
    bars=sorted(warm+main,key=lambda x:x["date"])
    if sum(1 for b in bars if b["date"]<FIRST_SIGNAL_DAY.isoformat() and b["valid_day"])<LOOKBACK:
        raise GateError("WARMUP_VALID_OBSERVATION_ASSERT")
    return bars,source

def generate_events(hyp,bars,through_signal_day):
    series=hyp.Series(bars)
    cfg={"family":"A_MOMENTUM","symbol":SYMBOL,"lookback":LOOKBACK,"horizon":HORIZON,"direction":"CONTINUATION"}
    cache={"daily_rets":series.completed_daily_log_returns(),"rv20":series.rv20_map()}
    active_exit=None; out=[]
    for ds in series.valid_dates:
        sd=date.fromisoformat(ds)
        if sd<FIRST_SIGNAL_DAY or sd>through_signal_day:continue
        completion=datetime(sd.year,sd.month,sd.day,tzinfo=timezone.utc)+timedelta(days=1)
        if completion<FIRST_SIGNAL_COMPLETION:raise GateError("PRE_BOUNDARY_SIGNAL_ADMISSION")
        direction=hyp.signal_for(series,cfg,ds,cache)
        if direction is None:
            out.append({"event_id":f"{TARGET}:{ds}","signal_day":ds,"status":"NO_SIGNAL"})
            continue
        ex,status=series.execution(ds,HORIZON)
        if status!="OK":
            out.append({"event_id":f"{TARGET}:{ds}","signal_day":ds,"status":"DATA_UNAVAILABLE"})
            continue
        entry=date.fromisoformat(ex["entry_day"]); exitd=date.fromisoformat(ex["exit_day"])
        if active_exit is not None and entry<active_exit:
            out.append({"event_id":f"{TARGET}:{ds}","signal_day":ds,"status":"OVERLAP_BLOCKED",
                        "entry_day":ex["entry_day"],"exit_day":ex["exit_day"]})
            continue
        active_exit=exitd
        ets=int(datetime(entry.year,entry.month,entry.day,0,1,tzinfo=timezone.utc).timestamp()*1000)
        xts=int(datetime(exitd.year,exitd.month,exitd.day,0,1,tzinfo=timezone.utc).timestamp()*1000)
        if ets<FIRST_ENTRY_TS:raise GateError("PRE_BOUNDARY_ENTRY_ADMISSION")
        out.append({"event_id":f"{TARGET}:{ds}","signal_day":ds,"status":"TRADE","direction":int(direction),
                    **ex,"entry_ts_ms":ets,"exit_ts_ms":xts,
                    "reference_gross_bps":int(direction)*float(ex["raw_return"])*10000})
    return out

def public_funding(start_ms,end_ms):
    params=urllib.parse.urlencode({"symbol":SYMBOL,"startTime":int(start_ms),"endTime":int(end_ms),"limit":1000})
    url=f"{PUBLIC_API}/fapi/v1/fundingRate?{params}"
    raw=fetch(url); rows=json.loads(raw.decode("utf-8"))
    if not isinstance(rows,list):raise GateError("FUNDING_NOT_LIST")
    out=[]
    for r in rows:
        if r.get("symbol")!=SYMBOL:raise GateError(f"FUNDING_SYMBOL:{r}")
        ft=int(r["fundingTime"]); rate=float(r["fundingRate"])
        if not(start_ms<=ft<=end_ms):raise GateError(f"FUNDING_TIME_BOUNDS:{ft}")
        if not math.isfinite(rate):raise GateError(f"FUNDING_NUMERIC:{r}")
        out.append({"fundingTime":ft,"fundingRate":rate})
    out.sort(key=lambda x:x["fundingTime"])
    return out,{"url":url,"canonical_sha256":sha256_bytes(canonical(out)),"records":len(out)}

def mark_interval_map(days):
    out={}; source=[]
    for d in sorted(set(days)):
        url=daily_kline_url("markPriceKlines",d)
        raw,h=verified_zip(url); rows=parse_price_zip(raw,d)
        for ts,o,hi,lo,c in rows:out[ts]={"low":lo,"high":hi}
        source.append({"kind":"markPriceKlines","day":d.isoformat(),"url":url,"sha256":h,"rows":len(rows)})
    return out,source

def add_funding_bounds(events,funding_rows,markmap):
    for e in events:
        if e.get("status")!="TRADE":continue
        ep=float(e["entry_open"]); direction=int(e["direction"]); lo=hi=0.0; n=0
        for r in funding_rows:
            ft=int(r["fundingTime"])
            if not(e["entry_ts_ms"]<ft<e["exit_ts_ms"]):continue
            minute=(ft//60000)*60000
            m=markmap.get(minute)
            if m is None:raise GateError(f"MARK_PRICE_MINUTE_MISSING:{e['event_id']}:{minute}")
            coeff=-direction*float(r["fundingRate"])/ep
            a=coeff*float(m["low"])*10000; b=coeff*float(m["high"])*10000
            lo+=min(a,b); hi+=max(a,b); n+=1
        e["funding_lower_bps"]=lo;e["funding_upper_bps"]=hi;e["funding_settlements"]=n
        e["reference_base_lower_bps"]=float(e["reference_gross_bps"])-BASE_REFERENCE_COST_BPS+lo
        e["reference_stress_lower_bps"]=float(e["reference_gross_bps"])-STRESS_REFERENCE_COST_BPS+lo
        e["reference_base_upper_bps"]=float(e["reference_gross_bps"])-BASE_REFERENCE_COST_BPS+hi
        e["reference_stress_upper_bps"]=float(e["reference_gross_bps"])-STRESS_REFERENCE_COST_BPS+hi
    return events

def parse_agg_zip(raw:bytes,expected_day:date):
    rows=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        member=[n for n in z.namelist() if not n.endswith("/")][0]
        rdr=csv.reader(io.TextIOWrapper(z.open(member),encoding="utf-8-sig",newline=""));first=True;prev_ts=None;prev_id=None
        for r in rdr:
            if not r:continue
            if first:
                first=False
                try:int(float(r[0]))
                except Exception:continue
            if len(r)<7:raise GateError(f"AGG_SHORT:{expected_day}:{r}")
            aid=int(float(r[0])); price=float(r[1]); qty=float(r[2]); ts=norm_ms(r[5]); bm=str(r[6]).strip().lower() in ("true","1")
            if datetime.fromtimestamp(ts/1000,tz=timezone.utc).date()!=expected_day:raise GateError(f"AGG_DAY_BOUNDS:{expected_day}:{ts}")
            if prev_ts is not None and ts<prev_ts:raise GateError(f"AGG_TIME_REVERSED:{expected_day}")
            if prev_id is not None and aid<=prev_id:raise GateError(f"AGG_ID_NONASC:{expected_day}")
            if price<=0 or qty<=0 or not(math.isfinite(price) and math.isfinite(qty)):raise GateError(f"AGG_NUMERIC:{r}")
            rows.append((ts,price,qty,bm));prev_ts=ts;prev_id=aid
    return rows

def agg_proxy(rows,target_ts,side):
    required_maker=(side=="SELL")
    filled_quote=0.0;base_qty=0.0;quote_value=0.0;last=None
    for ts,price,qty,bm in rows:
        if ts<target_ts:continue
        if ts>target_ts+AGG_WINDOW_MS:break
        if bm!=required_maker:continue
        q=price*qty;need=RESEARCH_NOTIONAL_USDT-filled_quote
        take=min(q,need)
        if take<=0:continue
        base_qty+=take/price;quote_value+=take;filled_quote+=take;last=ts
        if filled_quote+1e-9>=RESEARCH_NOTIONAL_USDT:
            return {"filled":True,"vwap":quote_value/base_qty,"latency_ms":last-target_ts,"filled_quote":filled_quote}
    return {"filled":False,"vwap":None,"latency_ms":None,"filled_quote":filled_quote}

def attach_agg(events):
    needed=defaultdict(list)
    for e in events:
        if e.get("status")!="TRADE":continue
        direction=int(e["direction"])
        needed[date.fromisoformat(e["entry_day"])].append((e,"ENTRY","BUY" if direction==1 else "SELL",e["entry_ts_ms"]))
        needed[date.fromisoformat(e["exit_day"])].append((e,"EXIT","SELL" if direction==1 else "BUY",e["exit_ts_ms"]))
    source=[]
    for d,legs in sorted(needed.items()):
        url=daily_agg_url(d);raw,h=verified_zip(url);rows=parse_agg_zip(raw,d)
        source.append({"kind":"aggTrades","day":d.isoformat(),"url":url,"sha256":h,"rows":len(rows)})
        for e,typ,side,ts in legs:
            x=agg_proxy(rows,ts,side)
            pre=typ.lower()
            e[f"{pre}_agg_filled"]=x["filled"];e[f"{pre}_agg_vwap"]=x["vwap"];e[f"{pre}_agg_latency_ms"]=x["latency_ms"]
    for e in events:
        if e.get("status")!="TRADE":continue
        complete=bool(e.get("entry_agg_filled") and e.get("exit_agg_filled"))
        e["agg_complete_pair"]=complete
        if complete:
            eg=int(e["direction"])*(float(e["exit_agg_vwap"])/float(e["entry_agg_vwap"])-1)*10000
            drag=float(e["reference_gross_bps"])-eg
            e["execution_gross_bps"]=eg;e["execution_drag_bps"]=drag
            e["execution_total_nonfunding_base_proxy_bps"]=BASE_EXEC_FEE_RT_BPS+drag
            e["execution_base_funded_bps"]=eg-BASE_EXEC_FEE_RT_BPS+float(e["funding_lower_bps"])
            e["execution_stress_funded_bps"]=eg-STRESS_EXEC_FEE_RT_BPS+float(e["funding_lower_bps"])
    return events,source

def parse_bookdepth_zip(raw:bytes,expected_day:date):
    snaps=defaultdict(dict);prev=None
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        member=[n for n in z.namelist() if not n.endswith("/")][0]
        rdr=csv.reader(io.TextIOWrapper(z.open(member),encoding="utf-8-sig",newline=""));first=True
        for r in rdr:
            if not r:continue
            if first:
                first=False
                if str(r[0]).strip().lower()=="timestamp":continue
            if len(r)<4:raise GateError(f"BOOK_SHORT:{expected_day}:{r}")
            ts=norm_ms(r[0]);per=float(r[1]);depth=float(r[2]);notional=float(r[3])
            if datetime.fromtimestamp(ts/1000,tz=timezone.utc).date()!=expected_day:raise GateError(f"BOOK_DAY_BOUNDS:{expected_day}:{ts}")
            if prev is not None and ts<prev:raise GateError(f"BOOK_TIME_REVERSED:{expected_day}")
            if not all(math.isfinite(x) for x in (per,depth,notional)) or depth<0 or notional<0:raise GateError(f"BOOK_NUMERIC:{r}")
            if per in snaps[ts]:raise GateError(f"BOOK_DUP_PERCENTAGE:{expected_day}:{ts}:{per}")
            snaps[ts][per]={"depth":depth,"notional":notional};prev=ts
    return dict(snaps)

def book_capacity(snaps,target_ts,side):
    prior=[t for t in snaps if t<=target_ts]
    band=BOOKDEPTH_BUY_PCT if side=="BUY" else BOOKDEPTH_SELL_PCT
    if not prior:return {"snapshot_ok":False,"capacity_ok":False,"snapshot_ts_ms":None,"snapshot_age_ms":None,"notional":None}
    ts=max(prior);age=target_ts-ts
    if age<0 or age>BOOKDEPTH_MAX_AGE_MS:return {"snapshot_ok":False,"capacity_ok":False,"snapshot_ts_ms":ts,"snapshot_age_ms":age,"notional":None}
    row=snaps[ts].get(band)
    if row is None:return {"snapshot_ok":True,"capacity_ok":False,"snapshot_ts_ms":ts,"snapshot_age_ms":age,"notional":None}
    n=float(row["notional"])
    return {"snapshot_ok":True,"capacity_ok":n>=RESEARCH_NOTIONAL_USDT,"snapshot_ts_ms":ts,"snapshot_age_ms":age,"notional":n}

def attach_bookdepth(events):
    needed=defaultdict(list)
    for e in events:
        if e.get("status")!="TRADE":continue
        direction=int(e["direction"])
        needed[date.fromisoformat(e["entry_day"])].append((e,"ENTRY","BUY" if direction==1 else "SELL",e["entry_ts_ms"]))
        needed[date.fromisoformat(e["exit_day"])].append((e,"EXIT","SELL" if direction==1 else "BUY",e["exit_ts_ms"]))
    source=[]
    for d,legs in sorted(needed.items()):
        url=daily_bookdepth_url(d);raw,h=verified_zip(url);snaps=parse_bookdepth_zip(raw,d)
        source.append({"kind":"bookDepth","day":d.isoformat(),"url":url,"sha256":h,"snapshots":len(snaps)})
        for e,typ,side,ts in legs:
            x=book_capacity(snaps,ts,side);pre=typ.lower()
            for k,v in x.items():e[f"{pre}_book_{k}"]=v
    for e in events:
        if e.get("status")!="TRADE":continue
        e["book_both_snapshot_ok"]=bool(e.get("entry_book_snapshot_ok") and e.get("exit_book_snapshot_ok"))
        e["book_both_capacity_ok"]=bool(e.get("entry_book_capacity_ok") and e.get("exit_book_capacity_ok"))
    return events,source

def concentration(rows,field):
    vals=[float(r[field]) for r in rows if r.get(field) is not None]
    if not vals:return {"single_month":None,"top5":None,"single_day":None,"pass":False}
    total=math.fsum(abs(v) for v in vals)
    if total<=0:return {"single_month":None,"top5":None,"single_day":None,"pass":False}
    months=defaultdict(float);days=defaultdict(float)
    for r in rows:
        if r.get(field) is None:continue
        v=abs(float(r[field]));d=date.fromisoformat(r["entry_day"]);months[d.strftime("%Y-%m")]+=v;days[d.isoformat()]+=v
    m=max(months.values())/total;dy=max(days.values())/total;t=math.fsum(sorted((abs(v) for v in vals),reverse=True)[:5])/total
    return {"single_month":m,"top5":t,"single_day":dy,"pass":m<=.30 and t<=.20 and dy<=.10}

def complete_signal_weeks(through_day):
    # Only Monday-Sunday UTC weeks fully contained after the first eligible signal day.
    first_monday=FIRST_SIGNAL_DAY+timedelta(days=(7-FIRST_SIGNAL_DAY.weekday())%7)
    if first_monday==FIRST_SIGNAL_DAY and FIRST_SIGNAL_DAY.weekday()!=0:first_monday+=timedelta(days=7)
    weeks=[];w=first_monday
    while w+timedelta(days=6)<=through_day:
        weeks.append(w);w+=timedelta(days=7)
    return weeks

def metrics_and_routing(events,through_signal_day):
    trades=[e for e in events if e.get("status")=="TRADE"]
    span=(through_signal_day-FIRST_SIGNAL_DAY).days+1
    weeks=complete_signal_weeks(through_signal_day)
    ref=[float(e["reference_base_lower_bps"]) for e in trades if e.get("reference_base_lower_bps") is not None]
    refstress=[float(e["reference_stress_lower_bps"]) for e in trades if e.get("reference_stress_lower_bps") is not None]
    execrows=[e for e in trades if e.get("agg_complete_pair")]
    execvals=[float(e["execution_base_funded_bps"]) for e in execrows]
    execstress=[float(e["execution_stress_funded_bps"]) for e in execrows]
    lat=[]
    for e in trades:
        for k in ("entry_agg_latency_ms","exit_agg_latency_ms"):
            if e.get(k) is not None:lat.append(float(e[k]))
    costs=[float(e["execution_total_nonfunding_base_proxy_bps"]) for e in execrows]
    legs=2*len(trades)
    snap_ok=sum(int(e.get("entry_book_snapshot_ok",False))+int(e.get("exit_book_snapshot_ok",False)) for e in trades)
    cap_ok=sum(int(e.get("entry_book_capacity_ok",False))+int(e.get("exit_book_capacity_ok",False)) for e in trades)
    month=defaultdict(lambda:{"legs":0,"capacity":0})
    for e in trades:
        m=date.fromisoformat(e["entry_day"]).strftime("%Y-%m")
        month[m]["legs"]+=1;month[m]["capacity"]+=int(e.get("entry_book_capacity_ok",False))
        m2=date.fromisoformat(e["exit_day"]).strftime("%Y-%m")
        month[m2]["legs"]+=1;month[m2]["capacity"]+=int(e.get("exit_book_capacity_ok",False))
    month_rates={m:(v["capacity"]/v["legs"] if v["legs"] else None) for m,v in sorted(month.items())}
    week_sums={}
    for w in weeks:
        vals=[float(e["reference_base_lower_bps"]) for e in trades if w<=date.fromisoformat(e["signal_day"])<=w+timedelta(days=6)]
        week_sums[w.isoformat()]=math.fsum(vals)
    pos_week_frac=(sum(v>0 for v in week_sums.values())/len(week_sums)) if week_sums else None
    conc=concentration(execrows,"execution_base_funded_bps")
    operational_checkpoint=len(trades)>=OP_CHECKPOINT_EVENTS and span>=OP_CHECKPOINT_DAYS
    tier1_sample=len(trades)>=TIER1_MIN_EVENTS and len(weeks)>=TIER1_MIN_COMPLETE_WEEKS
    execution_sample=len(execrows)>=TIER1_MIN_EXEC_PAIRS
    reference_gates={
      "base_mean_gt_0":mean(ref) is not None and mean(ref)>0,
      "base_pf_gt_1":pf(ref) is not None and pf(ref)>1,
      "stress_mean_ge_0":mean(refstress) is not None and mean(refstress)>=0,
      "complete_week_positive_fraction_ge_050":pos_week_frac is not None and pos_week_frac>=.50,
    }
    execution_gates={
      "sample_ge_50":execution_sample,
      "base_mean_gt_0":mean(execvals) is not None and mean(execvals)>0,
      "base_pf_gt_1":pf(execvals) is not None and pf(execvals)>1,
      "stress_mean_ge_0":mean(execstress) is not None and mean(execstress)>=0,
      "median_latency_le_1000":statistics.median(lat)<=1000 if lat else False,
      "p95_latency_le_5000":pct(lat,.95)<=5000 if lat else False,
      "mean_nonfunding_le_14":mean(costs)<=14 if costs else False,
      "p95_nonfunding_le_20":pct(costs,.95)<=20 if costs else False,
    }
    book_gates={
      "snapshot_coverage_ge_099":(snap_ok/legs)>=.99 if legs else False,
      "capacity_coverage_ge_099":(cap_ok/legs)>=.99 if legs else False,
      "every_active_month_ge_095":bool(month_rates) and all(v is not None and v>=.95 for v in month_rates.values()),
    }
    full_positive=tier1_sample and all(reference_gates.values()) and all(execution_gates.values()) and all(book_gates.values()) and conc["pass"]
    if not tier1_sample:
        routing="SHADOW_ACCUMULATING"
    elif not execution_sample:
        routing="SHADOW_BLOCKED_OR_INSUFFICIENT"
    elif full_positive:
        routing="TIER1_ADJUDICATION_ELIGIBLE"
    else:
        routing="TIER2_RETAINED_FORWARD_FRAGILITY__REQUIRES_V3_READJUDICATION"
    return {
      "resolved_trade_events":len(trades),"calendar_days_since_first_signal":span,
      "complete_utc_signal_weeks":len(weeks),"complete_week_starts":[w.isoformat() for w in weeks],
      "operational_checkpoint_pass":operational_checkpoint,"tier1_minimum_sample_pass":tier1_sample,
      "reference":{"mean_base_bps":mean(ref),"pf_base":pf(ref),"mean_stress_bps":mean(refstress),
                   "complete_week_positive_fraction":pos_week_frac,"week_base_sums":week_sums,"gates":reference_gates},
      "execution":{"complete_pairs":len(execrows),"mean_base_bps":mean(execvals),"pf_base":pf(execvals),
                   "mean_stress_bps":mean(execstress),"median_leg_latency_ms":statistics.median(lat) if lat else None,
                   "p95_leg_latency_ms":pct(lat,.95),"mean_nonfunding_proxy_bps":mean(costs),
                   "p95_nonfunding_proxy_bps":pct(costs,.95),"gates":execution_gates},
      "bookdepth":{"legs_required":legs,"snapshot_ok":snap_ok,"capacity_ok":cap_ok,
                   "snapshot_coverage":snap_ok/legs if legs else None,"capacity_coverage":cap_ok/legs if legs else None,
                   "month_capacity_rates":month_rates,"gates":book_gates},
      "concentration":conc,"routing":routing
    }

def write_csv(path,rows):
    if not rows:return
    fields=sorted({k for r in rows for k in r})
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--activation",required=True)
    ap.add_argument("--v03-runner-zip",required=True)
    ap.add_argument("--through-signal-day",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--today-utc",default=None,help="QA only; production omits this and uses real UTC date")
    a=ap.parse_args()
    activation=json.load(open(a.activation))
    if activation.get("status")!="PROSPECTIVE_PUBLIC_DATA_SHADOW_ACTIVATION_AUTHORIZED":raise GateError("ACTIVATION_STATUS")
    if activation["candidate"]["combination_id"]!=TARGET:raise GateError("ACTIVATION_CANDIDATE")
    if activation["activation_scope"]["first_eligible_signal_completion"]!="2026-09-19T00:00:00Z":raise GateError("BOUNDARY_MISMATCH")
    through=date.fromisoformat(a.through_signal_day)
    if through<FIRST_SIGNAL_DAY:raise GateError("THROUGH_BEFORE_BOUNDARY")
    today=date.fromisoformat(a.today_utc) if a.today_utc else datetime.now(timezone.utc).date()
    if through>today-timedelta(days=3):raise GateError(f"SOURCE_READINESS_GUARD:through={through}:today={today}")
    out=Path(a.output)
    if out.exists():raise GateError("OUTPUT_EXISTS")
    out.mkdir(parents=True)
    source=[]
    try:
        bars,src=build_shadow_price_bars(through);source+=src
        with tempfile.TemporaryDirectory() as td:
            hyp=load_original_hypotheses(Path(a.v03_runner_zip),Path(td))
            events=generate_events(hyp,bars,through)
        trades=[e for e in events if e.get("status")=="TRADE"]
        if any(date.fromisoformat(e["signal_day"])<FIRST_SIGNAL_DAY for e in trades):raise GateError("PRE_BOUNDARY_TRADE")
        if trades:
            fs=min(e["entry_ts_ms"] for e in trades);fe=max(e["exit_ts_ms"] for e in trades)
            funding,fmeta=public_funding(fs,fe);source.append({"kind":"fundingRate_public_api",**fmeta})
            markdays={datetime.fromtimestamp(r["fundingTime"]/1000,tz=timezone.utc).date() for r in funding}
            markmap,msrc=mark_interval_map(markdays);source+=msrc
            add_funding_bounds(events,funding,markmap)
            events,asrc=attach_agg(events);source+=asrc
            events,bsrc=attach_bookdepth(events);source+=bsrc
        metrics=metrics_and_routing(events,through)
        status="SHADOW_COLLECTION_COMPLETE"
        error=None
    except Exception as e:
        status="SHADOW_COLLECTION_FAIL_CLOSED";error=f"{type(e).__name__}:{e}"
        receipt={"document_id":"CED1D_0031_PROSPECTIVE_SHADOW_RECEIPT_V0.1","status":status,
                 "candidate":TARGET,"through_signal_day":through.isoformat(),"error":error,
                 "source":source,"governance":{"pre_boundary_performance_backfill":False,"live_trading":False,
                 "orders":False,"wallets":False,"exchange_mutation":False,"authenticated_trading_endpoints":False,
                 "parameter_changes":False,"merge_main":False}}
        receipt["fingerprint"]=sha256_bytes(canonical(receipt))
        (out/"CED1D_0031_PROSPECTIVE_SHADOW_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        print(json.dumps(receipt,indent=2,sort_keys=True))
        raise

    write_csv(out/"CED1D_0031_PROSPECTIVE_SHADOW_LEDGER.csv",events)
    receipt={"document_id":"CED1D_0031_PROSPECTIVE_SHADOW_RECEIPT_V0.1","status":status,
             "candidate":TARGET,"first_eligible_signal_day":FIRST_SIGNAL_DAY.isoformat(),
             "first_eligible_signal_completion":"2026-09-19T00:00:00Z",
             "through_signal_day":through.isoformat(),"source":source,"metrics":metrics,
             "governance":{"pre_boundary_performance_backfill":False,"warmup_input_only":True,"warmup_valid_observation_semantics":True,
               "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
               "authenticated_trading_endpoints":False,"parameter_changes":False,"notional_per_leg_usdt":100,
               "merge_main":False}}
    receipt["fingerprint"]=sha256_bytes(canonical(receipt))
    (out/"CED1D_0031_PROSPECTIVE_SHADOW_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":status,"through_signal_day":through.isoformat(),"metrics":metrics,
                      "fingerprint":receipt["fingerprint"]},indent=2,sort_keys=True))

if __name__=="__main__":main()
