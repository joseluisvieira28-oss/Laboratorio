"""LOR-RLE-001: historical source-verified breakout research, no exchange access.
Pre-outcome authority: LOR_RLE_001_PREOUTCOME_FREEZE_V0_1.json.
Only standard-library code. 2025 and 2026 market files are forbidden.
"""
from __future__ import annotations
import argparse
import calendar
import csv
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO, StringIO, TextIOWrapper
import json
import math
from pathlib import Path
import random
import re
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
FREEZE = ROOT / "LOR_RLE_001_PREOUTCOME_FREEZE_V0_1.json"
MS_H = 3600_000
MS_M = 60_000
SIGNAL_FIRST = int(datetime(2022,1,1,tzinfo=timezone.utc).timestamp()*1000)
SIGNAL_LAST = int(datetime(2024,12,28,tzinfo=timezone.utc).timestamp()*1000)
MINS_24H = 1440
TICK = 0.1
BASE = 26.0
STRESS = 40.0

class SourceBlocked(Exception):
    pass

@dataclass(frozen=True)
class Bar:
    t: int
    o: float
    h: float
    l: float
    c: float

@dataclass(frozen=True)
class Signal:
    t: int
    side: int
    group: str
    entry_stop: float
    protective_stop: float
    envelope: float
    q25: float

@dataclass(frozen=True)
class Trade:
    t: int
    exit_t: int
    side: int
    group: str
    entry: float
    exit: float
    gross_bps: float
    reason: str

def expected_month(interval, year, month):
    if interval not in ("1h","1m") or (year,month)<(2021,12) or (year,month)>(2024,12):
        raise SourceBlocked("FORBIDDEN_INTERVAL_OR_MONTH")
    if interval=="1m" and (year,month)<(2022,1):
        raise SourceBlocked("FORBIDDEN_1M_WARMUP")
    n=calendar.monthrange(year,month)[1]*(24 if interval=="1h" else 1440)
    start=int(datetime(year,month,1,tzinfo=timezone.utc).timestamp()*1000)
    return start, n, (MS_H if interval=="1h" else MS_M)

def remote_urls(interval,year,month):
    fname=f"BTCUSDT-{interval}-{year:04d}-{month:02d}.zip"
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/{interval}/{fname}"
    return url, url+".CHECKSUM", fname

def request_url(url,head=False):
    try:
        req=urllib.request.Request(url,method=("HEAD" if head else "GET"),headers={"User-Agent":"CryptoLab-RLE-ScienceSource/0.1"})
        with urllib.request.urlopen(req,timeout=45) as h:
            if h.status!=200:
                raise SourceBlocked(f"HTTP_{h.status}")
            return (h.headers, b"" if head else h.read())
    except Exception as e:
        raise SourceBlocked(f"SOURCE_TRANSPORT_{url.split('/')[-1]}:{type(e).__name__}") from e

def remote_checksum(url,expected_name):
    _,content=request_url(url)
    tokens=content.decode("ascii","strict").strip().split()
    if len(tokens)<1 or not re.fullmatch(r"[0-9a-fA-F]{64}",tokens[0]):
        raise SourceBlocked("INVALID_CHECKSUM_FORMAT")
    if len(tokens)>1 and tokens[1].lstrip("*").split("/")[-1]!=expected_name:
        raise SourceBlocked("CHECKSUM_NAME_MISMATCH")
    return tokens[0].lower()

def checksum_metadata(interval,year,month):
    url,shaurl,fname=remote_urls(interval,year,month)
    digest=remote_checksum(shaurl,fname)
    headers,_=request_url(url,head=True)
    size=int(headers.get("Content-Length","0"))
    if size<=0:
        raise SourceBlocked("MISSING_CONTENT_LENGTH")
    return {"interval":interval,"month":f"{year:04d}-{month:02d}","archive":fname,"sha256":digest,"zip_content_length":size}

class Archives:
    def __init__(self):
        self.cache=OrderedDict()
        self.sha_receipts={}
    def read_month(self,interval,year,month):
        key=(interval,year,month)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        start,n,step=expected_month(interval,year,month)
        url,shaurl,fname=remote_urls(interval,year,month)
        expected=remote_checksum(shaurl,fname)
        _,blob=request_url(url)
        observed=sha256(blob).hexdigest()
        if observed!=expected:
            raise SourceBlocked(f"ZIP_SHA_MISMATCH:{fname}")
        try:
            with zipfile.ZipFile(BytesIO(blob)) as archive:
                names=[name for name in archive.namelist() if name.lower().endswith(".csv")]
                if len(names)!=1:
                    raise SourceBlocked(f"CSV_MEMBER_COUNT:{fname}")
                with archive.open(names[0]) as raw:
                    text=TextIOWrapper(raw,encoding="utf-8-sig",newline="")
                    rows=[]
                    for rec in csv.reader(text):
                        if not rec or not rec[0]:
                            continue
                        if rec[0].strip().lower() in ("open_time","opentime"):
                            continue
                        if len(rec)<5:
                            raise SourceBlocked(f"CSV_SHORT_ROW:{fname}")
                        t=int(rec[0])
                        if t>10**13:
                            raise SourceBlocked(f"TIMESTAMP_NOT_MILLISECONDS:{fname}")
                        o,h,l,c=(float(rec[i]) for i in range(1,5))
                        if not all(math.isfinite(x) for x in (o,h,l,c)) or l<=0 or o<=0 or h<max(o,c,l) or l>min(o,c,h):
                            raise SourceBlocked(f"INVALID_OHLC:{fname}")
                        rows.append(Bar(t,o,h,l,c))
        except SourceBlocked:
            raise
        except Exception as e:
            raise SourceBlocked(f"INVALID_ZIP_OR_CSV:{fname}:{type(e).__name__}") from e
        if len(rows)!=n:
            raise SourceBlocked(f"ROW_COUNT:{fname}:{len(rows)}_EXPECTED_{n}")
        if rows[0].t!=start or rows[-1].t!=start+(n-1)*step:
            raise SourceBlocked(f"MONTH_BOUNDS:{fname}")
        for i in range(1,len(rows)):
            if rows[i].t-rows[i-1].t!=step:
                raise SourceBlocked(f"GAP_OR_DUPLICATE:{fname}")
        self.sha_receipts[fname]=observed
        self.cache[key]=rows
        self.cache.move_to_end(key)
        while len(self.cache)>3:
            self.cache.popitem(last=False)
        return rows
    def minute(self,t):
        if t%MS_M:
            raise SourceBlocked("MINUTE_UNALIGNED")
        dt=datetime.fromtimestamp(t/1000,timezone.utc)
        rows=self.read_month("1m",dt.year,dt.month)
        first,n,step=expected_month("1m",dt.year,dt.month)
        i=(t-first)//MS_M
        if i<0 or i>=len(rows) or rows[i].t!=t:
            raise SourceBlocked("MISSING_MINUTE")
        return rows[i]

def nearest_q25(values):
    if len(values)!=120:
        raise ValueError("EXACT_120_VALUES_REQUIRED")
    return sorted(values)[29]  # nearest rank ceil(120 * .25) - 1

def moving_means(close):
    ema=[]; sma21=[]; sma200=[]
    e=close[0]
    for i,px in enumerate(close):
        e=px if i==0 else px*(2/10)+e*(8/10)
        ema.append(e)
        sma21.append(sum(close[i-20:i+1])/21 if i>=20 else None)
        sma200.append(sum(close[i-199:i+1])/200 if i>=199 else None)
    return ema,sma21,sma200

def detect_signals(series):
    if len(series)<340:
        return [],Counter()
    closes=[c.c for c in series]
    ema,sma21,sma200=moving_means(closes)
    widths=[None]*len(series)
    for end in range(7,len(series)):
        window=series[end-7:end+1]
        widths[end]=max(c.h for c in window)-min(c.l for c in window)
    signals=[]; counts=Counter()
    for i in range(200,len(series)):
        candle=series[i]
        if candle.t<SIGNAL_FIRST or candle.t>=SIGNAL_LAST:
            continue
        if i<136:
            continue
        last8=series[i-8:i]
        envelope=max(c.h for c in last8)-min(c.l for c in last8)
        refs=[widths[j] for j in range(i-128,i-8)]
        q25=nearest_q25(refs)
        range_now=candle.h-candle.l
        if range_now<=0 or abs(candle.c-candle.o)/range_now<0.8:
            continue
        if range_now<=max(c.h-c.l for c in series[i-20:i]):
            continue
        long=candle.c>max(c.h for c in last8) and candle.c>candle.o and ema[i]>sma21[i] and candle.c>sma200[i]
        short=candle.c<min(c.l for c in last8) and candle.c<candle.o and ema[i]<sma21[i] and candle.c<sma200[i]
        if not (long or short):
            continue
        group=("RLE_NARROW" if envelope<=q25 else "NON_NARROW_CONTROL")
        side=1 if long else -1
        entry=candle.h+TICK if side==1 else candle.l-TICK
        stop=candle.l-TICK if side==1 else candle.h+TICK
        if not entry>stop if side==1 else not entry<stop:
            raise SourceBlocked("BAD_PROTECTIVE_GEOMETRY")
        signals.append(Signal(candle.t,side,group,entry,stop,envelope,q25))
        counts[group]+=1
    return signals,counts

def pnl_bps(side,entry,exit_price):
    return side*(exit_price/entry-1)*10000

def step_trade(signal, minute):
    side=signal.side
    entry_limit=signal.entry_stop
    protective=signal.protective_stop
    entry_hit=(minute.h>=entry_limit if side==1 else minute.l<=entry_limit)
    invalid=(minute.l<=protective if side==1 else minute.h>=protective)
    if not entry_hit:
        return ("CANCEL" if invalid else "WAIT"),None
    fill=(max(entry_limit,minute.o) if side==1 else min(entry_limit,minute.o))
    if (side==1 and fill<=protective) or (side==-1 and fill>=protective):
        raise SourceBlocked("GAP_INVALID_ENTRY")
    target=fill + side*2*abs(fill-protective)
    if invalid:
        exit_price=(min(protective,minute.o) if side==1 else max(protective,minute.o))
        return "STOP",Trade(minute.t,minute.t,side,signal.group,fill,exit_price,pnl_bps(side,fill,exit_price),"STOP_SAME_MINUTE")
    hit_target=(minute.h>=target if side==1 else minute.l<=target)
    if hit_target:
        return "TARGET",Trade(minute.t,minute.t,side,signal.group,fill,target,pnl_bps(side,fill,target),"TARGET_SAME_MINUTE")
    return "ENTER",(fill,target)

def simulate_one(signal,archive):
    start=signal.t+MS_H
    for j in range(180):
        t=start+j*MS_M
        bar=archive.minute(t)
        state,obj=step_trade(signal,bar)
        if state=="CANCEL":
            return None,t,"CANCEL"
        if state=="WAIT":
            continue
        if isinstance(obj,Trade):
            return obj,t,"EXIT"
        fill,target=obj
        side=signal.side
        stop=signal.protective_stop
        for k in range(j+1,j+1441):
            mt=start+k*MS_M
            cb=archive.minute(mt)
            stop_hit=(cb.l<=stop if side==1 else cb.h>=stop)
            target_hit=(cb.h>=target if side==1 else cb.l<=target)
            if stop_hit:
                ep=(min(stop,cb.o) if side==1 else max(stop,cb.o))
                return Trade(t,mt,side,signal.group,fill,ep,pnl_bps(side,fill,ep),"STOP"),mt,"EXIT"
            if target_hit:
                return Trade(t,mt,side,signal.group,fill,target,pnl_bps(side,fill,target),"TARGET"),mt,"EXIT"
            if k==j+1440:
                ep=cb.o
                return Trade(t,mt,side,signal.group,fill,ep,pnl_bps(side,fill,ep),"TIMEOUT"),mt,"EXIT"
        raise SourceBlocked("UNREACHABLE_TRADE_TERMINATION")
    return None,start+180*MS_M,"EXPIRED"

def trade_group(signals,archive,group):
    lock_until=-1
    trades=[]
    status=Counter()
    for sig in signals:
        if sig.group!=group:
            continue
        if sig.t<lock_until:
            status["OVERLAP_SUPPRESSED"]+=1
            continue
        trade,t_end,state=simulate_one(sig,archive)
        status[state]+=1
        lock_until=t_end
        if trade is not None:
            trades.append(trade)
    return trades,status

def iso_week(t):
    dt=datetime.fromtimestamp(t/1000,timezone.utc)
    y,w,_=dt.isocalendar()
    return f"{y:04d}-W{w:02d}"

def stats(trades):
    values=[t.gross_bps-BASE for t in trades]
    gains=sum(v for v in values if v>0)
    losses=-sum(v for v in values if v<0)
    pnl_week=defaultdict(float)
    for t,v in zip(trades,values):
        if v>0:
            pnl_week[iso_week(t.t)]+=v
    dtset={datetime.fromtimestamp(t.t/1000,timezone.utc).date().isoformat() for t in trades}
    yearly={str(y):[tr.gross_bps-BASE for tr in trades if datetime.fromtimestamp(tr.t/1000,timezone.utc).year==y] for y in (2022,2023,2024)}
    return {"n":len(trades),"dates":len(dtset),"weeks":len({iso_week(tr.t) for tr in trades}),
            "gross_mean_bps":sum(t.gross_bps for t in trades)/len(trades) if trades else None,
            "net16_mean_bps":sum(t.gross_bps-16 for t in trades)/len(trades) if trades else None,
            "net26_mean_bps":sum(values)/len(values) if values else None,
            "net40_mean_bps":sum(t.gross_bps-STRESS for t in trades)/len(trades) if trades else None,
            "pf_net26":(gains/losses if losses else (999999 if gains else 0)),
            "yearly_net26_mean":{y:(sum(v)/len(v) if v else None) for y,v in yearly.items()},
            "max_week_positive_pnl_share":(max(pnl_week.values())/gains if gains and pnl_week else 0),
            "exit_reasons":dict(Counter(t.reason for t in trades))}

def weekly_bootstrap(trades,seed,reps=3000):
    w=defaultdict(list)
    for t in trades:
        w[iso_week(t.t)].append(t.gross_bps-BASE)
    if not w:
        return (None,None)
    weeks=list(w)
    rng=random.Random(seed)
    values=[]
    for _ in range(reps):
        selected=[w[rng.choice(weeks)] for _ in range(len(weeks))]
        flat=[v for block in selected for v in block]
        values.append(sum(flat)/len(flat))
    values.sort()
    return (values[int(.025*reps)],values[int(.975*reps)-1])

def uplift_bootstrap(rle,control,seed,reps=3000):
    a=defaultdict(list);b=defaultdict(list)
    for t in rle:
        a[iso_week(t.t)].append(t.gross_bps-BASE)
    for t in control:
        b[iso_week(t.t)].append(t.gross_bps-BASE)
    weeks=sorted(set(a)|set(b))
    if not (a and b):
        return (None,None)
    rng=random.Random(seed)
    vals=[]
    for _ in range(reps):
        ids=[rng.choice(weeks) for _ in weeks]
        va=[v for w in ids for v in a[w]]
        vb=[v for w in ids for v in b[w]]
        if not va or not vb:
            raise SourceBlocked("PAIRED_BOOTSTRAP_EMPTY_GROUP")
        vals.append(sum(va)/len(va)-sum(vb)/len(vb))
    vals.sort()
    return (vals[int(.025*reps)],vals[int(.975*reps)-1])

def verdict(rle,control):
    a=stats(rle);b=stats(control)
    eligible=(a["n"]>=100 and b["n"]>=100 and a["dates"]>=70 and b["dates"]>=70 and a["weeks"]>=24)
    result={"rle":a,"non_narrow_control":b,"sample_gate":eligible,"test":"RLE minus equally-strong non-narrow breakout controls"}
    if not eligible:
        result.update({"classification":"SIGNAL_SAMPLE_INSUFFICIENT","failed":["MINIMUM_EVIDENCE_NOT_MET"],"economic_gate_unlocked":False})
        return result
    ci=weekly_bootstrap(rle,20261009)
    diff=a["net26_mean_bps"]-b["net26_mean_bps"]
    dci=uplift_bootstrap(rle,control,20261010)
    result.update({"rle_bootstrap95_net26_bps":ci,"incremental_net26_bps":diff,"paired_week_uplift_bootstrap95_bps":dci})
    gates={
        "NET26_POSITIVE":a["net26_mean_bps"]>0,
        "NET40_POSITIVE":a["net40_mean_bps"]>0,
        "RLE_WEEK_LCB_POSITIVE":ci[0]>0,
        "PF_NET26_GTE_1_15":a["pf_net26"]>=1.15,
        "POSITIVE_2_OF_3_YEARS":sum(v>0 for v in a["yearly_net26_mean"].values() if v is not None)>=2,
        "UPLIFT_GTE_5_BPS":diff>=5,
        "UPLIFT_WEEK_LCB_POSITIVE":dci[0]>0,
        "WEEK_CONCENTRATION_LE_25PCT":a["max_week_positive_pnl_share"]<=.25
    }
    result["gates"]=gates
    result["failed"]=[k for k,v in gates.items() if not v]
    result["classification"]="DISCOVERY_SURVIVES_REQUIRE_SEPARATE_OOS_AUTHORIZATION" if all(gates.values()) else "NO_EDGE_DISCOVERY"
    result["economic_gate_unlocked"]=True
    return result

def freeze_check():
    freeze=json.loads(FREEZE.read_text(encoding="utf-8"))
    if (freeze.get("lab_id")!="LOR-RLE-001" or freeze.get("status")!="FROZEN_BEFORE_ANY_RLE_OUTCOME_ACCESS"
        or freeze["source_authority"]["oos_2025"]!="SEALED" or freeze["source_authority"]["holdout_2026"]!="SEALED"
        or freeze["execution"]["target_r_multiple"]!=2 or freeze["economic"]["primary_roundtrip_bps"]!=BASE
        or freeze["economic"]["stress_roundtrip_bps"]!=STRESS
        or freeze["mechanical_signal"]["compression_quantile"]!=.25
        or freeze["mechanical_signal"]["lookback_range_bars"]!=8):
        raise SourceBlocked("FREEZE_PARAMETER_MISMATCH")
    return freeze

def month_list(interval):
    yield (2021,12) if interval=="1h" else (2022,1)
    for y in (2022,2023,2024):
        for m in range(1,13):
            if interval=="1h" and (y,m)==(2021,12):
                continue
            if interval=="1m" and (y,m)==(2022,1):
                continue
            yield y,m

def run_source_gate():
    freeze_check()
    manifest=[]
    for interval in ("1h","1m"):
        for y,m in month_list(interval):
            manifest.append(checksum_metadata(interval,y,m))
            print(f"SOURCE_OK {interval} {y}-{m:02d}",flush=True)
    receipt={"lab_id":"LOR-RLE-001","state":"SOURCE_METADATA_PASS","meta_rows":len(manifest),
             "by_interval":dict(Counter(x["interval"] for x in manifest)),
             "price_content_opened":False,"market_returns_opened":False,
             "oos_2025_opened":False,"holdout_2026_opened":False,"manifest":manifest}
    (ROOT/"LOR_RLE_001_SOURCE_METADATA_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"state":receipt["state"],"meta_rows":len(manifest)}))

def run_discovery():
    freeze_check()
    archive=Archives()
    hourly=[]
    for y,m in month_list("1h"):
        hourly.extend(archive.read_month("1h",y,m))
    if any(hourly[i].t-hourly[i-1].t!=MS_H for i in range(1,len(hourly))):
        raise SourceBlocked("GLOBAL_1H_CONTINUITY")
    signals,raw_counts=detect_signals(hourly)
    # Immediately reject any signal whose execution could escape the frozen window.
    if any(not SIGNAL_FIRST<=s.t<SIGNAL_LAST for s in signals):
        raise SourceBlocked("SIGNAL_TIME_ESCAPE")
    rle,rle_counts=trade_group(signals,archive,"RLE_NARROW")
    controls,control_counts=trade_group(signals,archive,"NON_NARROW_CONTROL")
    decision=verdict(rle,controls)
    decision.update({"lab_id":"LOR-RLE-001","development":"2022-2024_ONLY",
        "source_authority":"OFFICIAL_BINANCE_UM_MONTHLY_SHA256",
        "checksum_verified_files":len(archive.sha_receipts),
        "downloaded_archive_fingerprints":archive.sha_receipts,
        "signal_counts":dict(raw_counts),"rle_execution_counts":dict(rle_counts),
        "control_execution_counts":dict(control_counts),
        "oos_2025_opened":False,"holdout_2026_opened":False,
        "broker_execution_proven":False,"trading_authority":"NONE"})
    out=ROOT/"LOR_RLE_001_DISCOVERY_RECEIPT.json"
    out.write_text(json.dumps(decision,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in decision.items() if k not in ("downloaded_archive_fingerprints",)},indent=2))
    return decision

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("source","discovery"),required=True)
    args=parser.parse_args()
    try:
        if args.mode=="source":
            run_source_gate()
        else:
            run_discovery()
    except SourceBlocked as ex:
        receipt={"lab_id":"LOR-RLE-001","classification":"SOURCE_BLOCKED",
                 "reason":str(ex),"oos_2025_opened":False,"holdout_2026_opened":False,
                 "trading_authority":"NONE"}
        path=ROOT/("LOR_RLE_001_SOURCE_METADATA_RECEIPT.json" if args.mode=="source" else "LOR_RLE_001_DISCOVERY_RECEIPT.json")
        path.write_text(json.dumps(receipt,indent=2)+"\n")
        print(json.dumps(receipt),file=sys.stderr)
        raise SystemExit(2)

if __name__=="__main__":
    main()
