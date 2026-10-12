"""Research-only deterministic retrospective price-barrier diagnostics.
See RETRO_FIRST_TOUCH_FROZEN_PROTOCOL_V0.1.md. Not a fill or trading simulator.
"""
import base64, csv, gzip, hashlib, io, json, urllib.request, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("research/payoff_first_touch")
SEED=Path("research/margin_payoff_audit/evidence/btc-convex-trend-capture-001-v0.1/labs/btc-convex-trend-capture-001/evidence/SEED_TRADE_LEDGER_1H_V0.1.csv.gz.b64")
HASH="ca6903faf7d4f42a40d0b76d4e7d106edec36007075d2da4600c4800b08583fa"
BASE="https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1h/"
HOUR=3600000
F=.0008
TARGET=(.40/2+2*F)/(1-F)
STOP=(-.10/2+2*F)/(1-F)
END=datetime(2026,1,1,tzinfo=timezone.utc)

def date(s):
    x=datetime.fromisoformat(s.replace("Z","+00:00"))
    return (x.replace(tzinfo=timezone.utc) if x.tzinfo is None else x).astimezone(timezone.utc)

def load_seed():
    original=gzip.decompress(base64.b64decode(SEED.read_bytes()))
    if hashlib.sha256(original).hexdigest()!=HASH:
        raise ValueError("SEED_SHA_MISMATCH")
    reader=csv.DictReader(io.StringIO(original.decode("utf-8-sig")))
    fields=reader.fieldnames
    rows=list(reader)
    if len(rows)!=101: raise ValueError("SEED_COUNT_MISMATCH")
    return fields,rows

def price_from_source(row):
    for key in ("entry","entry_price","entry_px","price_entry"):
        if row.get(key):
            return float(row[key]),key
    for key in ("qty","quantity"):
        if row.get(key) and row.get("value") and float(row[key])>0:
            return float(row["value"])/float(row[key]),"value/"+key
    return None,"SOURCE_ENTRY_PRICE_MISSING"

def month_range(first,last):
    year,month=first.year,first.month
    while (year,month)<=(last.year,last.month):
        yield f"{year:04d}-{month:02d}"
        month+=1
        if month==13:year,month=year+1,1

def archive(month):
    name=f"BTCUSDT-1h-{month}.zip"
    headers={"User-Agent":"Crypto-Lab-Research-Only-V01"}
    def get(url,limit):
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=45) as r:
            data=r.read(limit+1)
        if len(data)>limit: raise ValueError("SOURCE_TOO_LARGE "+month)
        return data
    z=get(BASE+name,2000000)
    checksum=get(BASE+name+".CHECKSUM",4000).decode().strip().split()[0].lower()
    sha=hashlib.sha256(z).hexdigest()
    if len(checksum)!=64 or sha!=checksum:raise ValueError("CHECKSUM_MISMATCH "+month)
    with zipfile.ZipFile(io.BytesIO(z)) as f:
        members=[m for m in f.namelist() if m.endswith(".csv")]
        if len(members)!=1:raise ValueError("INVALID_ZIP_MEMBER "+month)
        text=f.read(members[0]).decode("utf-8-sig")
    bars={}
    for r in csv.reader(io.StringIO(text)):
        if not r or not r[0].isdigit():continue
        ts=int(r[0])
        if ts>10**14:ts//=1000
        o,h,l,c=map(float,r[1:5])
        if ts%HOUR or not (0<l<=min(o,c)<=max(o,c)<=h) or ts in bars:
            raise ValueError("INVALID_KLINE "+month)
        bars[ts]=(o,h,l,c)
    if not bars:raise ValueError("EMPTY_SOURCE "+month)
    return bars,{"month":month,"zip_sha256":sha,"rows":len(bars),
                 "first_timestamp_ms":min(bars),"last_timestamp_ms":max(bars)}

def classify(bars,start,end,entry,inclusive):
    if entry is None or entry<=0 or start>=end or start%HOUR or end%HOUR:
        return "INPUT_BLOCKED",None
    bottom=entry*(1+STOP)
    top=entry*(1+TARGET)
    for t in range(start if inclusive else start+HOUR,end,HOUR):
        if t not in bars:return "MISSING_PATH",t
        o,h,l,c=bars[t]
        if o<=bottom:return "STOP_GAP_FIRST",t
        if o>=top:return "TARGET_GAP_FIRST",t
        if l<=bottom and h>=top:return "AMBIGUOUS_SAME_BAR",t
        if l<=bottom:return "STOP_FIRST",t
        if h>=top:return "TARGET_FIRST",t
    return "NEITHER_CENSORED",None

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    out={"experiment":"PAYOFF-FIRST-TOUCH-RETRO-001",
         "science":"RETROSPECTIVE_POST_OUTCOME_ZERO_PROMOTION_CREDIT",
         "target_price_delta":TARGET,"stop_price_delta":STOP,
         "leverage":2,"illustrative_fee_per_side":F,"no_2026_data":True}
    try:
        fields,seed=load_seed()
        out["seed_columns"]=fields
        selected=[]
        skip=Counter()
        for r in seed:
            if r.get("open","").lower()=="true":skip["open"]+=1;continue
            first,last=date(r["entry_dt"]),date(r["exit_dt"])
            if first>=END or last>=END:skip["excluded_2026"]+=1;continue
            if first<datetime(2020,1,1,tzinfo=timezone.utc):skip["SOURCE_BLOCKED_2019"]+=1;continue
            if first>=last:skip["invalid_window"]+=1;continue
            selected.append((r,first,last))
        out["excluded"]=dict(skip)
        out["selected_count"]=len(selected)
        if not selected:raise ValueError("EMPTY_SAMPLE")
        bars={};manifest=[]
        for month in month_range(min(x[1] for x in selected),max(x[2] for x in selected)):
            part,receipt=archive(month)
            if set(part)&set(bars):raise ValueError("DUPLICATE_MONTHS "+month)
            bars.update(part);manifest.append(receipt)
        out["source_manifests"]=manifest
        events=[]
        for r,first,last in selected:
            price,method=price_from_source(r)
            a=int(first.timestamp()*1000);b=int(last.timestamp()*1000)
            outcome={}
            for name,inclusive in (("entry_hour_inclusive",True),("next_full_hour",False)):
                state,t=classify(bars,a,b,price,inclusive)
                outcome[name]={"status":state,"first_ts":t}
            e={"trade_n":r.get("n"),"entry_dt":first.isoformat(),
               "exit_dt":last.isoformat(),"source_entry_price":price,
               "price_method":method,**outcome}
            if price and a in bars:e["entry_open_mismatch_fraction"]=bars[a][0]/price-1
            events.append(e)
        out["summary"]={name:dict(Counter(e[name]["status"] for e in events))
                        for name in ("entry_hour_inclusive","next_full_hour")}
        out["entry_open_mismatch_gt_1pct"]=sum(abs(e.get("entry_open_mismatch_fraction",0))>.01 for e in events)
        out["status"]="RETRO_FIRST_TOUCH_DESCRIPTIVE_READY"
        (ROOT/"retro_events.json").write_text(json.dumps(events,indent=2)+"\n")
    except Exception as exc:
        out["status"]="DATA_SOURCE_BLOCKED"
        out["reason"]=repr(exc)
    (ROOT/"retro_verdict.json").write_text(json.dumps(out,indent=2)+"\n")
    print("PAYOFF_SOURCE_VERDICT="+json.dumps({k:v for k,v in out.items() if k!="source_manifests"},sort_keys=True))
    if out["status"]=="DATA_SOURCE_BLOCKED":raise SystemExit(2)

if __name__=="__main__":
    main()
