#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, math, os, tempfile, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests

CBASE="https://contract.mexc.com/api/v1/contract"
SBASE="https://api.mexc.com/api/v3"
UA={"User-Agent":"CryptoLab-MultiStable-Forward/0.3"}
THRESHOLDS={"BTC":7.464945216995034,"ETH":9.80929964899957}
ASSETS={
    "BTC":{"USDT":"BTC_USDT","USDC":"BTC_USDC","USD1":"BTC_USD1"},
    "ETH":{"USDT":"ETH_USDT","USDC":"ETH_USDC","USD1":"ETH_USD1"},
}
NORM_SPOT={"USDC":"USDCUSDT","USD1":"USD1USDT"}
NOTIONALS=[10.0,25.0,50.0,100.0]
PRIMARY_NOTIONAL="25"
PRIMARY_FEE_BPS_PER_EXEC=8.0
STRESS_FEE_BPS_PER_EXEC=12.0
COOLDOWN_SEC=15*60
HORIZON_SEC=15*60
MAX_CAPTURE_DELAY_SEC=30.0
BOUNDARY=datetime.fromisoformat("2026-10-07T15:44:50+00:00").timestamp()

def atomic_json(path:Path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(obj,f,indent=2,sort_keys=True)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def req(url,params=None,timeout=12,retries=3):
    last=None
    for i in range(retries):
        started=datetime.now(timezone.utc)
        t0=time.perf_counter()
        try:
            r=requests.get(url,params=params,headers=UA,timeout=timeout)
            completed=datetime.now(timezone.utc)
            body=r.content
            ev={
                "request_started_utc":started.isoformat(),
                "request_completed_utc":completed.isoformat(),
                "captured_epoch":completed.timestamp(),
                "latency_ms":round((time.perf_counter()-t0)*1000,3),
                "status_code":r.status_code,
                "url":r.url,
                "body_sha256":hashlib.sha256(body).hexdigest(),
                "body_bytes":len(body),
            }
            if r.status_code==200:
                return r,ev
            last=RuntimeError(f"HTTP_{r.status_code}:{r.url}")
        except Exception as exc:
            last=exc
        time.sleep(0.2*(i+1))
    raise last

def wait_until(dt):
    while True:
        d=(dt-datetime.now(timezone.utc)).total_seconds()
        if d<=0:return
        time.sleep(min(d,5))

def parse_iso(x):
    return datetime.fromisoformat(x.replace("Z","+00:00")).astimezone(timezone.utc)

def contract_close(symbol,t_close):
    open_ts=int(t_close)-60
    r,ev=req(f"{CBASE}/kline/{symbol}",{"interval":"Min1","start":str(open_ts),"end":str(open_ts)})
    j=r.json()
    if not (isinstance(j,dict) and j.get("success") is True):
        raise RuntimeError(f"MEXC_KLINE_SUCCESS_FALSE:{symbol}")
    d=j.get("data") or {}
    pairs={int(t):float(c) for t,c in zip(d.get("time") or [],d.get("close") or [])}
    if open_ts not in pairs:
        raise RuntimeError(f"MEXC_KLINE_EXACT_MISSING:{symbol}:{open_ts}")
    return pairs[open_ts],ev

def spot_close(symbol,t_close):
    open_ms=(int(t_close)-60)*1000
    end_ms=int(t_close)*1000-1
    r,ev=req(f"{SBASE}/klines",{"symbol":symbol,"interval":"1m","startTime":str(open_ms),"endTime":str(end_ms),"limit":"1"})
    j=r.json()
    if not isinstance(j,list):
        raise RuntimeError(f"SPOT_KLINE_BAD:{symbol}")
    for row in j:
        if isinstance(row,list) and len(row)>=7 and int(row[0])==open_ms:
            return float(row[4]),ev
    raise RuntimeError(f"SPOT_KLINE_EXACT_MISSING:{symbol}:{open_ms}")

def scan_inputs(t_close):
    evidence={}
    usdc,evidence["USDCUSDT"]=spot_close("USDCUSDT",t_close)
    usd1,evidence["USD1USDT"]=spot_close("USD1USDT",t_close)
    conv={"USDT":1.0,"USDC":usdc,"USD1":usd1}
    results={}
    for asset,legs in ASSETS.items():
        vals={}
        for coin,sym in legs.items():
            px,ev=contract_close(sym,t_close)
            evidence[sym]=ev
            vals[coin]=px*conv[coin]
        logs={k:math.log(v) for k,v in vals.items()}
        ordered=sorted(logs.items(),key=lambda kv:kv[1])
        cheap,lo=ordered[0]; rich,hi=ordered[-1]
        ambiguous=(abs(ordered[1][1]-lo)<1e-12 or abs(hi-ordered[1][1])<1e-12)
        spread=10000.0*(hi-lo)
        results[asset]={
            "range_bps":spread,
            "rich_coin":rich,
            "cheap_coin":cheap,
            "rich_symbol":legs[rich],
            "cheap_symbol":legs[cheap],
            "trigger":bool((not ambiguous) and spread>=THRESHOLDS[asset]),
            "ambiguous":ambiguous,
        }
    return results,evidence

def contract_meta():
    r,ev=req(f"{CBASE}/detail")
    j=r.json()
    if not (isinstance(j,dict) and j.get("success") is True):
        raise RuntimeError("CONTRACT_DETAIL_FAILED")
    needed={s for x in ASSETS.values() for s in x.values()}
    out={}
    for x in j.get("data") or []:
        if not isinstance(x,dict) or x.get("symbol") not in needed:
            continue
        try:
            cs=float(x["contractSize"]); vu=float(x["volUnit"]); mv=float(x["minVol"]); mx=float(x.get("maxVol") or 1e18)
            if min(cs,vu,mv,mx)<=0:raise ValueError
            out[x["symbol"]]={"contract_size":cs,"vol_unit":vu,"min_vol":mv,"max_vol":mx}
        except Exception:
            continue
    missing=sorted(needed-set(out))
    if missing:raise RuntimeError("MISSING_CONTRACT_META:"+",".join(missing))
    return out,ev

def level(x):
    if isinstance(x,(list,tuple)) and len(x)>=2:return float(x[0]),float(x[1])
    if isinstance(x,dict):
        return float(x.get("price",x.get("p"))),float(x.get("vol",x.get("v",x.get("quantity",x.get("q")))))
    raise ValueError("BAD_LEVEL")

def depth(symbol):
    r,ev=req(f"{CBASE}/depth/{symbol}",{"limit":"20"})
    j=r.json(); d=(j.get("data") or {}) if isinstance(j,dict) else {}
    if isinstance(j,dict) and j.get("success") is False:raise RuntimeError(f"DEPTH_SUCCESS_FALSE:{symbol}")
    bids=sorted([level(x) for x in (d.get("bids") or j.get("bids") or [])],key=lambda z:z[0],reverse=True)
    asks=sorted([level(x) for x in (d.get("asks") or j.get("asks") or [])],key=lambda z:z[0])
    if not bids or not asks:raise RuntimeError(f"EMPTY_BOOK:{symbol}")
    captured=datetime.now(timezone.utc)
    return {"symbol":symbol,"captured_at_utc":captured.isoformat(),"captured_epoch":captured.timestamp(),"bids":bids,"asks":asks,"source_evidence":ev}

def spot_mid(symbol):
    r,ev=req(f"{SBASE}/ticker/bookTicker",{"symbol":symbol})
    j=r.json()
    if not isinstance(j,dict) or j.get("symbol")!=symbol:
        raise RuntimeError(f"BOOKTICKER_BAD:{symbol}")
    bid=float(j["bidPrice"]); ask=float(j["askPrice"])
    if not (bid>0 and ask>0 and ask>=bid):raise RuntimeError(f"BOOKTICKER_INVALID:{symbol}")
    return {"mid":(bid+ask)/2,"bid":bid,"ask":ask,"captured_epoch":ev["captured_epoch"],"source_evidence":ev}

def valuation_snapshot():
    u=spot_mid("USDCUSDT"); d=spot_mid("USD1USDT")
    return {"USDT":{"mid":1.0},"USDC":u,"USD1":d}

def funding_next(symbol):
    r,ev=req(f"{CBASE}/funding_rate/{symbol}")
    j=r.json()
    if not (isinstance(j,dict) and j.get("success") is True):
        raise RuntimeError(f"FUNDING_FAILED:{symbol}")
    d=j.get("data") or {}
    nxt=d.get("nextSettleTime")
    if nxt is None:raise RuntimeError(f"FUNDING_NEXT_MISSING:{symbol}")
    return int(nxt)/1000.0,ev

def crosses_funding(symbols,t_close):
    due=t_close+HORIZON_SEC
    rows={}
    for s in symbols:
        nxt,ev=funding_next(s)
        rows[s]={"next_settle_epoch":nxt,"source_evidence":ev}
        if t_close < nxt <= due:
            return True,rows
    return False,rows

def quantized_contracts(target_usdt,top_price,conv,meta):
    raw=target_usdt/(top_price*meta["contract_size"]*conv)
    units=math.ceil(raw/meta["vol_unit"]-1e-12)
    qty=max(meta["min_vol"],units*meta["vol_unit"])
    if qty>meta["max_vol"]:raise ValueError("QTY_EXCEEDS_MAX_VOL")
    return qty

def fill_contracts(book,action,contracts,contract_size):
    levels=book["asks"] if action=="BUY" else book["bids"]
    remain=contracts; quote=0.0; used=0
    for price,avail in levels:
        take=min(remain,max(0.0,avail))
        if take<=0:continue
        quote+=price*take*contract_size; remain-=take; used+=1
        if remain<=1e-12:break
    if remain>1e-9:
        return {"fillable":False,"requested_contracts":contracts,"unfilled_contracts":remain,"levels_used":used}
    base_qty=contracts*contract_size
    avg=quote/base_qty
    top=levels[0][0]
    slip=(avg/top-1)*10000 if action=="BUY" else (top/avg-1)*10000
    return {"fillable":True,"contracts":contracts,"base_qty":base_qty,"quote_notional_settle":quote,"avg_price":avg,"top_price":top,"book_slippage_bps":slip,"levels_used":used}

def entry_fill(book,action,target_usdt,conv,meta):
    top=(book["asks"] if action=="BUY" else book["bids"])[0][0]
    contracts=quantized_contracts(target_usdt,top,conv,meta)
    z=fill_contracts(book,action,contracts,meta["contract_size"])
    z.update({"target_usdt":target_usdt,"settle_to_usdt":conv,"contract_meta":meta})
    return z

def capture_entry(asset_sig,t_close,meta):
    rich=asset_sig["rich_symbol"]; cheap=asset_sig["cheap_symbol"]
    cross,fund=crosses_funding([rich,cheap],t_close)
    if cross:
        return {**asset_sig,"eligible":False,"ineligible_reason":"FUNDING_WINDOW_INELIGIBLE","funding_evidence":fund}
    val=valuation_snapshot()
    rb=depth(rich); cb=depth(cheap)
    latest=max(rb["captured_epoch"],cb["captured_epoch"],val["USDC"].get("captured_epoch",0),val["USD1"].get("captured_epoch",0))
    lag=latest-t_close
    out={**asset_sig,"eligible":True,"funding_evidence":fund,"entry_capture_delay_sec":lag,"entry_timing_valid":0<=lag<=MAX_CAPTURE_DELAY_SEC,"entry_valuation":val,"entry_books":{"rich":rb,"cheap":cb},"entry_fills":{}}
    rc=asset_sig["rich_coin"]; cc=asset_sig["cheap_coin"]
    for n in NOTIONALS:
        key=str(int(n))
        out["entry_fills"][key]={
            "rich_short":entry_fill(rb,"SELL",n,val[rc]["mid"],meta[rich]),
            "cheap_long":entry_fill(cb,"BUY",n,val[cc]["mid"],meta[cheap]),
        }
    return out

def capture_exit(asset,t_due):
    if not asset.get("eligible") or not asset.get("entry_timing_valid"):return
    rich=asset["rich_symbol"]; cheap=asset["cheap_symbol"]; rc=asset["rich_coin"]; cc=asset["cheap_coin"]
    val=valuation_snapshot(); rb=depth(rich); cb=depth(cheap)
    latest=max(rb["captured_epoch"],cb["captured_epoch"],val["USDC"].get("captured_epoch",0),val["USD1"].get("captured_epoch",0))
    lag=latest-t_due
    asset["exit_capture_delay_sec"]=lag
    asset["exit_timing_valid"]=0<=lag<=MAX_CAPTURE_DELAY_SEC
    asset["exit_valuation"]=val
    asset["exit_books"]={"rich":rb,"cheap":cb}
    asset["exit_fills"]={}
    for n in NOTIONALS:
        key=str(int(n)); ef=asset["entry_fills"].get(key) or {}
        r=ef.get("rich_short") or {}; c=ef.get("cheap_long") or {}
        if not (r.get("fillable") and c.get("fillable")):
            asset["exit_fills"][key]={"fillable":False,"reason":"ENTRY_UNFILLABLE"}; continue
        xr=fill_contracts(rb,"BUY",float(r["contracts"]),float(r["contract_meta"]["contract_size"]))
        xc=fill_contracts(cb,"SELL",float(c["contracts"]),float(c["contract_meta"]["contract_size"]))
        asset["exit_fills"][key]={"fillable":bool(xr.get("fillable") and xc.get("fillable")),"rich_cover":xr,"cheap_sell":xc,"rich_exit_settle_to_usdt":val[rc]["mid"],"cheap_exit_settle_to_usdt":val[cc]["mid"]}

def receipt(a,meta_ev,scans,events,pending,errors,started):
    return {
        "family_id":"MEXC-MULTI-STABLE-BASIS-001",
        "forward_version":"0.3",
        "authority_freeze_commit":"bbc8291d0302f6776f75cb19d8c62df16b68bf25",
        "threshold_receipt_commit":"289fddb48ffbe34421914d2356eb5fa7f7f20ea7",
        "thresholds_q99_bps":THRESHOLDS,
        "segment":a.segment,
        "start_close_utc":a.start,
        "end_close_utc":a.end,
        "started_utc":started,
        "updated_utc":datetime.now(timezone.utc).isoformat(),
        "expected_scan_minutes":int((parse_iso(a.end)-parse_iso(a.start)).total_seconds()//60)+1,
        "scan_records":scans,
        "events":events,
        "pending_event_timestamps":[p["event"]["signal_close_utc"] for p in pending],
        "errors":errors,
        "contract_detail_source_evidence":meta_ev,
        "primary_notional_usdt_per_leg":25.0,
        "notionals_usdt_per_leg":NOTIONALS,
        "primary_fee_bps_per_execution":PRIMARY_FEE_BPS_PER_EXEC,
        "stress_fee_bps_per_execution":STRESS_FEE_BPS_PER_EXEC,
        "horizon_sec":HORIZON_SEC,
        "cooldown_sec":COOLDOWN_SEC,
        "orders":False,"account_reads":False,"private_endpoints_used":False,
        "exchange_mutation":False,"live_trading":False,"post_outcome_tuning":False,
    }

def validate_args(a):
    start=parse_iso(a.start); end=parse_iso(a.end)
    if not start<end:raise SystemExit("FAIL_CLOSED_BAD_WINDOW")
    if start.timestamp()<=BOUNDARY:raise SystemExit("FAIL_CLOSED_PRE_THRESHOLD_BOUNDARY")
    if start.second or end.second:raise SystemExit("FAIL_CLOSED_NON_MINUTE_BOUNDARY")
    if (end-start)>timedelta(hours=4):raise SystemExit("FAIL_CLOSED_SEGMENT_TOO_LONG")
    return start,end

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--start",required=True)
    ap.add_argument("--end",required=True)
    ap.add_argument("--segment",required=True)
    a=ap.parse_args()
    start,end=validate_args(a)
    outdir=Path("artifacts/mexc_multistable_basis/forward_v03")/start.date().isoformat()/a.segment
    path=outdir/f"receipt_{a.segment}.json"
    meta,meta_ev=contract_meta()
    scans=[]; events=[]; pending=[]; errors=[]; last_admitted=None
    started=datetime.now(timezone.utc).isoformat()
    minute=start
    while minute<=end:
        wait_until(minute+timedelta(seconds=2))
        # exits due first
        due=[x for x in pending if x["due"]<=datetime.now(timezone.utc)]
        pending=[x for x in pending if x not in due]
        for p in due:
            for asset in p["event"]["assets"]:
                try:capture_exit(asset,p["due"].timestamp())
                except Exception as exc:asset["exit_error"]=str(exc)
            events.append(p["event"])
        now=datetime.now(timezone.utc)
        lag=(now-minute).total_seconds()
        scan={"signal_close_utc":minute.isoformat(),"complete":False,"triggered_assets":[]}
        if lag>MAX_CAPTURE_DELAY_SEC:
            scan["error"]="LATE_SCAN_FAIL_CLOSED"; errors.append({"minute":minute.isoformat(),"error":scan["error"],"delay_sec":lag})
            scans.append(scan); atomic_json(path,receipt(a,meta_ev,scans,events,pending,errors,started)); minute+=timedelta(minutes=1); continue
        try:
            sigs,evidence=scan_inputs(int(minute.timestamp()))
            scan["complete"]=True
            scan["source_hashes"]={k:v["body_sha256"] for k,v in evidence.items()}
            for asset,z in sigs.items():
                scan[asset]={"range_bps":z["range_bps"],"trigger":z["trigger"],"rich_coin":z["rich_coin"],"cheap_coin":z["cheap_coin"]}
                if z["trigger"]:scan["triggered_assets"].append(asset)
        except Exception as exc:
            scan["error"]=str(exc);errors.append({"minute":minute.isoformat(),"error":str(exc)})
            scans.append(scan);atomic_json(path,receipt(a,meta_ev,scans,events,pending,errors,started));minute+=timedelta(minutes=1);continue
        if scan["triggered_assets"]:
            t=int(minute.timestamp())
            raw_assets=[]
            for asset in scan["triggered_assets"]:
                z={**sigs[asset],"underlying":asset}
                try:raw_assets.append(capture_entry(z,t,meta))
                except Exception as exc:raw_assets.append({**z,"eligible":False,"entry_error":str(exc)})
            funding_eligible=[x for x in raw_assets if x.get("eligible")]
            suppressed=bool(last_admitted is not None and t-last_admitted<COOLDOWN_SEC)
            scan["cooldown_suppressed"]=suppressed
            if funding_eligible:
                event={
                    "timestamp":t,
                    "signal_close_utc":minute.isoformat(),
                    "cooldown_suppressed":suppressed,
                    "assets":raw_assets,
                }
                pending.append({"due":minute+timedelta(seconds=HORIZON_SEC),"event":event})
                if suppressed:
                    scan["event_admitted"]=False
                else:
                    last_admitted=t
                    scan["event_admitted"]=True
            else:
                scan["event_admitted"]=False
        scans.append(scan)
        atomic_json(path,receipt(a,meta_ev,scans,events,pending,errors,started))
        minute+=timedelta(minutes=1)

    for p in sorted(pending,key=lambda x:x["due"]):
        wait_until(p["due"]+timedelta(seconds=2))
        for asset in p["event"]["assets"]:
            try:capture_exit(asset,p["due"].timestamp())
            except Exception as exc:asset["exit_error"]=str(exc)
        events.append(p["event"])
        atomic_json(path,receipt(a,meta_ev,scans,events,[],errors,started))

    final=receipt(a,meta_ev,scans,events,[],errors,started)
    atomic_json(path,final)
    print(json.dumps({
        "segment":a.segment,
        "expected_scan_minutes":final["expected_scan_minutes"],
        "complete_scan_minutes":sum(1 for x in scans if x.get("complete")),
        "raw_trigger_minutes":sum(1 for x in scans if x.get("triggered_assets")),
        "admitted_events":sum(1 for x in events if not x.get("cooldown_suppressed")),\n        "cooldown_suppressed_events":sum(1 for x in events if x.get("cooldown_suppressed")),
        "errors":len(errors),
        "orders":False,
        "path":str(path),
    },sort_keys=True))

if __name__=="__main__":
    main()
