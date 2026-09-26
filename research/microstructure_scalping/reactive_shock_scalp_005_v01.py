#!/usr/bin/env python3
from __future__ import annotations

import bisect,csv,gzip,json,statistics,sys,time,urllib.request,zipfile,re
from datetime import date,datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

BLS_URL="https://www.bls.gov/schedule/2023/home.htm"
MANIFEST_PATH=Path(__file__).with_name("REACTIVE_SHOCK_SCALP_005_BLS_2023_MANIFEST.json")
ARCHIVE_CUTOFF=date(2023,1,18)
BYBIT_L2="https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/{date}_BTCUSDT_ob500.data.zip"
BYBIT_TRADES="https://public.bybit.com/trading/BTCUSDT/BTCUSDT{date}.csv.gz"
UA={"User-Agent":"Crypto-Lab-Reactive-Shock-005/0.1 research-only"}

OBS={
 "PRICE_W1":1000,
 "FLOWPRICE_W1":1000,
 "FLOWPRICE_W2":2000,
 "PERSISTENT_W5":5000,
}
HORIZONS=(5000,15000,30000,60000)
NY=ZoneInfo("America/New_York")
MAX_DOWNLOAD_BYTES=800_000_000


def fetch(url,path=None):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=180) as r:
        if path is None:
            return r.read()
        total=0
        with open(path,"wb") as f:
            while True:
                c=r.read(1024*1024)
                if not c:break
                total+=len(c)
                if total>MAX_DOWNLOAD_BYTES:raise RuntimeError("DOWNLOAD_CAP_EXCEEDED")
                f.write(c)
        return total


def parse_bls_events():
    """Load the persisted official-BLS-derived manifest.

    The CI runner receives HTTP 403 from BLS, so source retrieval is separated
    from execution. This does not alter event selection or scientific rules.
    """
    raw=json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if raw.get("authority")!="U.S. Bureau of Labor Statistics official 2023 release calendar":
        raise RuntimeError("BLS_MANIFEST_AUTHORITY_MISMATCH")
    events=[]
    seen=set()
    for x in raw.get("events",[]):
        d=date.fromisoformat(x["date"])
        if d<ARCHIVE_CUTOFF or d.year!=2023:
            raise RuntimeError("EVENT_OUTSIDE_BYBIT_ARCHIVE_ELIGIBILITY")
        if x["type"] not in {"CPI","NFP"}:
            raise RuntimeError("INVALID_EVENT_TYPE")
        if x.get("release_time_et")!="08:30 AM":
            raise RuntimeError("INVALID_RELEASE_TIME")
        key=(x["type"],x["date"])
        if key in seen:
            raise RuntimeError("DUPLICATE_EVENT")
        seen.add(key)
        local=datetime(d.year,d.month,d.day,8,30,tzinfo=NY)
        utc=local.astimezone(timezone.utc)
        events.append({
            "type":x["type"],"date":x["date"],
            "release_name":x["release_name"],
            "t0_ms":int(utc.timestamp()*1000),
            "release_utc":utc.isoformat().replace("+00:00","Z")
        })
    events.sort(key=lambda x:x["t0_ms"])
    if len(events)!=8:
        raise RuntimeError("SELECTED_EVENT_CARDINALITY")
    if sum(x["type"]=="CPI" for x in events)!=4 or sum(x["type"]=="NFP" for x in events)!=4:
        raise RuntimeError("TYPE_CARDINALITY")
    quarters={(x["type"],(date.fromisoformat(x["date"]).month-1)//3+1) for x in events}
    if len(quarters)!=8:
        raise RuntimeError("QUARTER_TYPE_COVERAGE")
    return events

def row_price_qty(row):
    return float(row[0]),float(row[-1])


def load_event_l2(path,t0):
    bids={};asks={}
    states=[]
    pre=None
    stop=t0+70_000
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None:raise RuntimeError("L2_CRC_FAIL")
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1:raise RuntimeError("L2_MEMBERS")
        with zf.open(names[0]) as fh:
            for raw in fh:
                m=json.loads(raw);d=m.get("data") or {}
                typ=m.get("type")
                if typ=="snapshot":
                    bids={float(p):float(q) for p,q,*_ in d.get("b",[]) if float(q)!=0}
                    asks={float(p):float(q) for p,q,*_ in d.get("a",[]) if float(q)!=0}
                elif typ=="delta":
                    for side,book in ((d.get("b",[]),bids),(d.get("a",[]),asks)):
                        for row in side:
                            p=float(row[0]);q=float(row[1])
                            if q==0:book.pop(p,None)
                            else:book[p]=q
                else:continue
                if not bids or not asks:continue
                bb=max(bids);ba=min(asks)
                if bb>=ba:raise RuntimeError("CROSSED_BOOK")
                ts=m.get("cts")
                if ts is None:ts=m.get("ts")
                ts=int(ts)
                if ts<t0:
                    pre=(ts,bb,ba)
                    continue
                if ts>stop:break
                states.append((ts,bb,ba))
    if pre is None:raise RuntimeError("NO_PRE_RELEASE_BBO")
    if not states:raise RuntimeError("NO_EVENT_STATES")
    return pre,states


def load_event_trades(path,t0):
    rows=[]
    lo=t0;hi=t0+5000
    prev=None
    with gzip.open(path,"rt",encoding="utf-8",newline="") as fh:
        for r in csv.DictReader(fh):
            t=int(round(float(r["timestamp"])*1000))
            if prev is not None and t<prev:raise RuntimeError("NONMONOTONIC_TRADES")
            prev=t
            if t<lo:continue
            if t>=hi:break
            rows.append((t,r["side"],float(r["size"])*float(r["price"])))
    return rows


def first_state_at(states,t):
    times=[x[0] for x in states]
    i=bisect.bisect_left(times,t)
    return states[i] if i<len(states) else None


def flow(trades,start,end):
    b=s=0.0
    for t,side,n in trades:
        if t<start:continue
        if t>=end:break
        if side=="Buy":b+=n
        elif side=="Sell":s+=n
    tot=b+s
    return (b-s)/tot if tot else 0.0


def sign(x):
    return 1 if x>0 else (-1 if x<0 else 0)


def bps(a,b):
    return (b-a)/a*10000.0


def eval_variant(event,pre,states,trades,name):
    t0=event["t0_ms"];obs=OBS[name]
    entry=first_state_at(states,t0+obs)
    if entry is None:return None
    _,ebid,eask=entry
    pre_mid=(pre[1]+pre[2])/2
    entry_mid=(ebid+eask)/2
    pdir=sign(entry_mid-pre_mid)
    if pdir==0:return None

    if name=="FLOWPRICE_W1":
        f=flow(trades,t0,t0+1000)
        if sign(f)!=pdir:return None
    elif name=="FLOWPRICE_W2":
        f=flow(trades,t0,t0+2000)
        if sign(f)!=pdir:return None
    elif name=="PERSISTENT_W5":
        f1=flow(trades,t0,t0+2000)
        f2=flow(trades,t0+2000,t0+5000)
        if sign(f1)==0 or sign(f1)!=sign(f2) or sign(f1)!=pdir:return None

    out={"event_type":event["type"],"event_date":event["date"],
         "entry_ms":entry[0],"direction":pdir,
         "observed_displacement_bps":pdir*bps(pre_mid,entry_mid),
         "horizons":{}}
    for h in HORIZONS:
        fu=first_state_at(states,entry[0]+h)
        if fu is None:continue
        _,fbid,fask=fu
        fmid=(fbid+fask)/2
        mid=pdir*bps(entry_mid,fmid)
        if pdir>0:
            tg=bps(eask,fbid);mg=bps(ebid,fask)
        else:
            tg=(ebid-fask)/ebid*10000.0
            mg=(eask-fbid)/eask*10000.0
        out["horizons"][str(h)]={
            "directional_mid_bps":mid,
            "taker_gross_bps":tg,
            "mexc_taker_net_bps":tg-16,
            "maker_ceiling_gross_bps":mg,
            "mexc_maker_ceiling_net_bps":mg-12,
            "bybit_maker_ceiling_net_bps_ref":mg-4,
            "bybit_taker_net_bps_ref":tg-11,
        }
    return out


def summarize(vals):
    return statistics.fmean(vals) if vals else None


def main():
    events=parse_bls_events()
    root=Path("/tmp/reactive_shock_005");root.mkdir(exist_ok=True)
    event_results=[]
    source=[]
    for e in events:
        d=e["date"]
        l2p=root/f"{d}_l2.zip";trp=root/f"{d}_trades.csv.gz"
        lb=fetch(BYBIT_L2.format(date=d),l2p)
        tb=fetch(BYBIT_TRADES.format(date=d),trp)
        pre,states=load_event_l2(l2p,e["t0_ms"])
        trades=load_event_trades(trp,e["t0_ms"])
        rec={"event":e,"variants":{}}
        for name in OBS:
            rec["variants"][name]=eval_variant(e,pre,states,trades,name)
        event_results.append(rec)
        source.append({"date":d,"type":e["type"],"release_utc":e["release_utc"],
                       "l2_bytes":lb,"trade_bytes":tb,
                       "event_l2_states":len(states),"trades_0_5s":len(trades)})

    result={"status":"REACTIVE_SHOCK_SCALP_005_DISCOVERY_MVE",
            "bls_source":BLS_URL,"events":events,"source_receipts":source,
            "variants":{},"survivors":[],
            "oos_2025_opened":False,"holdout_2026_opened":False,
            "consensus_used":False}

    for name in OBS:
        vr={"resolved_events":0,"horizons":{}}
        resolved=[x["variants"][name] for x in event_results if x["variants"][name] is not None]
        vr["resolved_events"]=len(resolved)
        for h in HORIZONS:
            hs=str(h)
            allv=[];cpi=[];nfp=[]
            for x in resolved:
                if hs not in x["horizons"]:continue
                y=x["horizons"][hs]
                z=(x["event_type"],y)
                allv.append(z)
                (cpi if x["event_type"]=="CPI" else nfp).append(y)
            def pack(items):
                return {
                  "n":len(items),
                  "mean_directional_mid_bps":summarize([y["directional_mid_bps"] for y in items]),
                  "mean_maker_ceiling_gross_bps":summarize([y["maker_ceiling_gross_bps"] for y in items]),
                  "mean_mexc_maker_ceiling_net_bps":summarize([y["mexc_maker_ceiling_net_bps"] for y in items]),
                  "mean_mexc_taker_net_bps":summarize([y["mexc_taker_net_bps"] for y in items]),
                  "mean_bybit_maker_ceiling_net_bps_ref":summarize([y["bybit_maker_ceiling_net_bps_ref"] for y in items]),
                }
            pooled=pack([y for _,y in allv]);pcpi=pack(cpi);pnfp=pack(nfp)
            vr["horizons"][hs]={"pooled":pooled,"CPI":pcpi,"NFP":pnfp}
            if (pooled["n"]>=6 and
                pooled["mean_mexc_maker_ceiling_net_bps"] is not None and pooled["mean_mexc_maker_ceiling_net_bps"]>0 and
                pcpi["n"]>=3 and pcpi["mean_mexc_maker_ceiling_net_bps"]>0 and
                pnfp["n"]>=3 and pnfp["mean_mexc_maker_ceiling_net_bps"]>0):
                result["survivors"].append({"variant":name,"horizon_ms":h,
                    "pooled_n":pooled["n"],
                    "mean_mexc_maker_net_bps":pooled["mean_mexc_maker_ceiling_net_bps"]})
        result["variants"][name]=vr

    result["event_results"]=event_results
    result["decision"]="REACTIVE_CEILING_SURVIVOR_EXISTS" if result["survivors"] else "NO_REACTIVE_CEILING_SURVIVOR_MVE"

    out=Path("research/microstructure_scalping/receipts");out.mkdir(parents=True,exist_ok=True)
    (out/"reactive_shock_scalp_005_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
