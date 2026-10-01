#!/usr/bin/env python3
import csv,hashlib,io,json,re,urllib.error,urllib.request,zipfile
from pathlib import Path

SYMBOL="SOLUSDT"
DAY="2024-07-05"  # already outcome-contaminated; source-format probe only
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
OUT.mkdir(parents=True,exist_ok=True)
REC=OUT/"BINANCE_SOLUSDT_BBO_HISTORICAL_SOURCE_PROBE_V0.1.json"

candidates=[
 ("bookTicker",f"https://data.binance.vision/data/futures/um/daily/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-{DAY}.zip"),
 ("bookDepth",f"https://data.binance.vision/data/futures/um/daily/bookDepth/{SYMBOL}/{SYMBOL}-bookDepth-{DAY}.zip"),
]

def get(url):
    try:
        q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-bbo-source-probe-v01/0.1"})
        with urllib.request.urlopen(q,timeout=60) as r:
            return int(r.status),r.read(),dict(r.headers)
    except urllib.error.HTTPError as e:
        return int(e.code),e.read(),{}
    except Exception as e:
        return None,str(e).encode(),{}

out={"schema_version":"0.1","symbol":SYMBOL,"probe_day":DAY,"fresh_oos_opened":False,"candidates":[]}
for kind,url in candidates:
    st,raw,h=get(url)
    item={"kind":kind,"url":url,"http":st,"bytes":len(raw) if isinstance(raw,(bytes,bytearray)) else None}
    if st!=200:
        item["status"]="UNAVAILABLE"
        out["candidates"].append(item);continue
    cs,cb,_=get(url+".CHECKSUM")
    item["checksum_http"]=cs
    item["observed_sha256"]=hashlib.sha256(raw).hexdigest()
    if cs==200:
        m=re.search(rb"([0-9a-fA-F]{64})",cb)
        item["expected_sha256"]=m.group(1).decode().lower() if m else None
        item["checksum_match"]=bool(m and item["expected_sha256"]==item["observed_sha256"])
    try:
        z=zipfile.ZipFile(io.BytesIO(raw))
        members=[n for n in z.namelist() if not n.endswith("/")]
        item["zip_members"]=members
        if len(members)!=1:
            item["status"]="ZIP_MEMBER_COUNT_INVALID";out["candidates"].append(item);continue
        with z.open(members[0]) as fh:
            txt=io.TextIOWrapper(fh,encoding="utf-8")
            rdr=csv.reader(txt)
            rows=[]
            for i,row in enumerate(rdr):
                rows.append(row)
                if i>=9:break
        item["first_rows"]=rows
        item["status"]="AVAILABLE_PARSEABLE"
    except Exception as e:
        item["status"]="PARSE_FAIL";item["error"]=f"{type(e).__name__}:{e}"
    out["candidates"].append(item)

usable=[x for x in out["candidates"] if x.get("kind")=="bookTicker" and x.get("status")=="AVAILABLE_PARSEABLE" and x.get("checksum_match") is not False]
out["classification"]="BINANCE_SOLUSDT_BOOKTICKER_HISTORICAL_SOURCE_PASS" if usable else "BINANCE_SOLUSDT_BOOKTICKER_HISTORICAL_SOURCE_BLOCKED"
out["firewall"]={
 "probe_day_already_contaminated":True,
 "oct_dec_2024_market_outcomes_opened":False,
 "market_2025_opened":False,
 "market_2026_opened":False,
 "live_trading":False,
 "orders":False,
 "exchange_mutation":False,
 "merge_main":False
}
REC.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))
if out["classification"]!="BINANCE_SOLUSDT_BOOKTICKER_HISTORICAL_SOURCE_PASS":
    raise SystemExit(2)
