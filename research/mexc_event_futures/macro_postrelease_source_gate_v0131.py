#!/usr/bin/env python3
"""MACRO-POSTRELEASE-FWD-001 public source gate. Zero outcomes."""
import argparse, asyncio, json, re, urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from priority_source_gates_v013 import Evidence, now_ms, positive, fresh

ICS="https://www.bls.gov/schedule/news_release/bls.ics"
PAGES={
    "CPI":"https://www.bls.gov/news.release/cpi.htm",
    "EMPLOYMENT_SITUATION":"https://www.bls.gov/news.release/empsit.htm",
}
WS="wss://futures.mexc.com/edge"
SYMS=("BTC_USDT","ETH_USDT")

def http_get(url,evidence,name):
    req=urllib.request.Request(
        url,
        headers={
            "User-Agent":"Mozilla/5.0 (compatible; CryptoLabSourceGate/1.0; public-read-only)",
            "Accept":"text/calendar,text/html,application/xhtml+xml,*/*;q=0.8",
        },
        method="GET",
    )
    sent=now_ms()
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read()
        recv=now_ms()
        ref=evidence.save(name,raw,source_url=url,http_status=r.status,requested_at_ms=sent,received_at_ms=recv)
        return raw,r.status,recv,ref

def unfold_ics(text):
    out=[]
    for line in text.replace("\r\n","\n").replace("\r","\n").split("\n"):
        if line.startswith((" ","\t")) and out:
            out[-1]+=line[1:]
        else:
            out.append(line)
    return out

def parse_dt(value,params):
    # BLS ICS may use local TZID or UTC Z form.
    if value.endswith("Z"):
        dt=datetime.strptime(value,"%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return dt
    tzid=params.get("TZID")
    tz=ZoneInfo(tzid) if tzid else ZoneInfo("America/New_York")
    fmt="%Y%m%dT%H%M%S" if len(value)>=15 else "%Y%m%dT%H%M"
    return datetime.strptime(value,fmt).replace(tzinfo=tz).astimezone(timezone.utc)

def parse_events(raw):
    text=raw.decode("utf-8","replace")
    lines=unfold_ics(text)
    events=[];cur=None
    for line in lines:
        if line=="BEGIN:VEVENT":
            cur={}
            continue
        if line=="END:VEVENT":
            if cur is not None: events.append(cur)
            cur=None;continue
        if cur is None or ":" not in line: continue
        left,val=line.split(":",1)
        parts=left.split(";")
        key=parts[0].upper()
        params={}
        for p in parts[1:]:
            if "=" in p:
                k,v=p.split("=",1);params[k.upper()]=v
        if key in ("SUMMARY","DESCRIPTION","UID"):
            cur[key]=val
        elif key=="DTSTART":
            cur["DTSTART_RAW"]=val
            cur["DTSTART_UTC"]=parse_dt(val,params).isoformat().replace("+00:00","Z")
    return events

def classify(e):
    s=(e.get("SUMMARY") or "").lower()
    if "consumer price index" in s:
        return "CPI"
    if "employment situation" in s:
        return "EMPLOYMENT_SITUATION"
    return None

def validate_page(kind,raw):
    t=raw.decode("utf-8","replace").lower()
    if kind=="CPI":
        return "consumer price index" in t and ("8:30 a.m." in t or "08:30" in t)
    return "employment situation" in t and ("8:30 a.m." in t or "08:30" in t)

async def index_probe(evidence,seconds=20):
    import websockets
    ticks={s:[] for s in SYMS};acks=[];errors=[];seq=0
    try:
        async with websockets.connect(
            WS,origin="https://www.mexc.com",open_timeout=20,ping_interval=15,ping_timeout=10,max_size=4*1024*1024
        ) as ws:
            for s in SYMS:
                await ws.send(json.dumps({"method":"sub.index.price","param":{"symbol":s}},separators=(",",":")))
            deadline=asyncio.get_running_loop().time()+seconds
            while asyncio.get_running_loop().time()<deadline and not all(ticks[s] for s in SYMS):
                try:
                    raw=await asyncio.wait_for(ws.recv(),timeout=5)
                except asyncio.TimeoutError:
                    continue
                recv=now_ms();seq+=1
                ref=evidence.save(f"index-{seq:06d}.json",raw,source_url=WS,received_at_ms=recv)
                try:j=json.loads(raw)
                except Exception:
                    continue
                ch=j.get("channel")
                if ch and str(ch).startswith("rs.sub.index.price"):
                    acks.append({"channel":ch,"raw_sha256":ref["sha256"]})
                if ch!="push.index.price":
                    continue
                data=j.get("data") or {}
                sym=j.get("symbol") or data.get("symbol")
                ts=j.get("ts")
                try:price=float(data.get("price"))
                except Exception:price=None
                if sym in ticks and positive(price) and fresh(ts,recv):
                    ticks[sym].append({
                        "ts":ts,"price":price,"received_at_ms":recv,"raw_sha256":ref["sha256"]
                    })
    except Exception as exc:
        errors.append({"type":type(exc).__name__,"error":str(exc)})
    return ticks,acks,errors

async def main(out):
    ev=Evidence(out)
    errors=[];page_status={};events=[];future=[]
    now=datetime.now(timezone.utc)
    try:
        raw,status,recv,ref=http_get(ICS,ev,"bls-calendar.ics")
        events=parse_events(raw)
        eligible=[]
        for e in events:
            k=classify(e)
            if not k or "DTSTART_UTC" not in e: continue
            row={**e,"kind":k}
            eligible.append(row)
            dt=datetime.fromisoformat(row["DTSTART_UTC"].replace("Z","+00:00"))
            if dt>now: future.append(row)
    except Exception as exc:
        errors.append({"source":"BLS_ICS","type":type(exc).__name__,"error":str(exc)})
        eligible=[]
    for kind,url in PAGES.items():
        try:
            raw,status,recv,ref=http_get(url,ev,f"bls-{kind.lower()}.html")
            page_status[kind]={
                "http_status":status,
                "valid_schema":validate_page(kind,raw),
                "raw_sha256":ref["sha256"],
                "received_at_ms":recv,
            }
        except Exception as exc:
            errors.append({"source":kind,"type":type(exc).__name__,"error":str(exc)})
            page_status[kind]={"http_status":None,"valid_schema":False}
    ticks,acks,ws_errors=await index_probe(ev)
    errors.extend({"source":"MEXC_INDEX",**e} for e in ws_errors)

    kinds={e["kind"] for e in eligible}
    conditions={
        "calendar_has_cpi":"CPI" in kinds,
        "calendar_has_employment":"EMPLOYMENT_SITUATION" in kinds,
        "future_eligible_event":len(future)>0,
        "cpi_page_valid":page_status.get("CPI",{}).get("valid_schema") is True,
        "employment_page_valid":page_status.get("EMPLOYMENT_SITUATION",{}).get("valid_schema") is True,
        "btc_index_tick":bool(ticks["BTC_USDT"]),
        "eth_index_tick":bool(ticks["ETH_USDT"]),
        "no_source_errors":not errors,
    }
    if all(conditions.values()):
        verdict="SOURCE_GATE_PASS"
    elif any(conditions.values()):
        verdict="PARTIAL_SOURCE"
    else:
        verdict="SOURCE_BLOCKED"

    future_sorted=sorted(future,key=lambda e:e["DTSTART_UTC"])
    receipt={
        "family_id":"MACRO-POSTRELEASE-FWD-001",
        "verdict":verdict,
        "conditions":conditions,
        "eligible_calendar_event_count":len(eligible),
        "future_eligible_events":future_sorted[:12],
        "page_status":page_status,
        "index_ticks":ticks,
        "subscription_acks":acks,
        "errors":errors,
        "research_outcomes_opened":0,
        "macro_outcomes_scored":0,
        "consensus_data_accessed":False,
    }
    ev.finish(receipt)
    print(json.dumps(receipt,indent=2,sort_keys=True))
    if verdict=="SOURCE_BLOCKED":
        raise SystemExit(2)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    asyncio.run(main(a.output))
