#!/usr/bin/env python3
"""CARRY-001 adversarial prehistory: 2023-05-01 to 2024-09-01, if market listed.
Official sources only. Save immutable raw bytes; no keys or trades.
"""
import csv,datetime as dt,gzip,hashlib,io,json,pathlib,time,urllib.request,urllib.error,zipfile
START=dt.datetime(2023,5,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2024,9,1,tzinfo=dt.timezone.utc)
S=int(START.timestamp()*1000);E=int(END.timestamp()*1000)
OUT=pathlib.Path("carry001-evidence");OUT.mkdir(exist_ok=True)
RAW=OUT/"prehistory_raw";RAW.mkdir(exist_ok=True)
RETRY=(0,1,4,10,20,30,60)
COINS=("BTC","ETH","SOL")
def request(url,body=None):
    data=json.dumps(body).encode() if body else None
    req=urllib.request.Request(url,data=data,headers={"User-Agent":"CryptoLab-CARRY001/0.1 read-only",
           "Content-Type":"application/json" if body else "application/octet-stream"})
    last=None
    for delay in RETRY:
        if delay:time.sleep(delay)
        try:
            with urllib.request.urlopen(req,timeout=30) as r:return r.read(4_000_000)
        except (urllib.error.HTTPError,urllib.error.URLError,OSError,TimeoutError) as e:
            last=repr(e)
            if isinstance(e,urllib.error.HTTPError) and e.code in (403,404,451):break
    raise RuntimeError(last)
def months():
    y,m=2023,5
    while (y,m)<(2024,9):
        yield "%04d-%02d"%(y,m)
        m+=1
        if m==13:y,m=y+1,1
def bounded(rate):
    v=float(rate)
    if not(-0.25<=v<=0.25):raise ValueError("extreme historic rate")
    return v
def main():
    provenance={"range":[START.isoformat(),END.isoformat()],"BTC_ETH_SOL":{},"failure_gate":"NO economic GO if payments unavailable"}
    allrows=[];issues=[]
    for coin in COINS:
        b=[];h=[];files=[]
        sym=coin+"USDT"
        for mon in months():
            name=f"{sym}-fundingRate-{mon}.zip"
            url=f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{sym}/{name}"
            try:
                p=RAW/name
                raw=p.read_bytes() if p.exists() else request(url)
                p.write_bytes(raw)
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    parsed=list(csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode("utf-8-sig"))))
                for r in parsed:
                    t=int(r["calc_time"])
                    if S<=t<E:b.append({"venue":"Binance","coin":coin,"timestamp_ms":t,
                       "rate":bounded(r["last_funding_rate"]),"interval_hours":int(r["funding_interval_hours"])})
                files.append({"name":name,"sha256":hashlib.sha256(raw).hexdigest(),"rows":len(parsed)})
            except Exception as e:
                issues.append({"coin":coin,"month":mon,"error":repr(e)[:220]})
            print("EARLY_BN",coin,mon,"n",len(b),flush=True)
        cursor=S;n=0;meta=[]
        while cursor<E and n<80:
            body={"type":"fundingHistory","coin":coin,"startTime":cursor,"endTime":E-1}
            fname=RAW/f"EARLY_HL_{coin}_{n:02}.json.gz"
            raw=gzip.decompress(fname.read_bytes()) if fname.is_file() else request("https://api.hyperliquid.xyz/info",body)
            fname.write_bytes(gzip.compress(raw,mtime=0))
            z=json.loads(raw)
            if not isinstance(z,list):raise ValueError("HL response not list")
            for x in z:
                t=int(x["time"])
                if S<=t<E:h.append({"venue":"Hyperliquid","coin":coin,"timestamp_ms":t,
                    "rate":bounded(x["fundingRate"]),"interval_hours":1})
            meta.append({"page":n,"first":int(z[0]["time"]) if z else None,
               "last":int(z[-1]["time"]) if z else None,"rows":len(z),
               "sha256":hashlib.sha256(raw).hexdigest()})
            if not z:break
            last=int(z[-1]["time"])
            if last<cursor:raise ValueError("non-progressing HL cursor")
            cursor=last+1
            n+=1
            if n%10==0:print("EARLY_HL_PROGRESS",coin,n,len(h),dt.datetime.fromtimestamp(last/1000,tz=dt.timezone.utc).isoformat(),flush=True)
            if len(z)<500:break
            time.sleep(.7)
        if n>=80:raise RuntimeError("HL history truncated by page cap")
        provenance["BTC_ETH_SOL"][coin]={"binance_rows":len(b),"hyperliquid_rows":len(h),"binance_archives":files,"hyperliquid_pages":meta}
        print("EARLY_COIN",coin,"BN",len(b),"HL",len(h),"missing_zip",len([x for x in issues if x["coin"]==coin]),flush=True)
        allrows.extend(b+h)
    if len(allrows)<10000:raise RuntimeError("Not enough prehistory")
    prior=list(csv.DictReader((OUT/"funding_events.csv").open()))
    merged={}
    for r in prior+allrows:
        key=(r["venue"],r["coin"],int(r["timestamp_ms"]))
        n={"venue":r["venue"],"coin":r["coin"],
            "timestamp_ms":int(r["timestamp_ms"]),"rate":bounded(r["rate"]),"interval_hours":int(r["interval_hours"])}
        if key in merged and merged[key]!=n:raise ValueError("Conflicting duplicated payments")
        merged[key]=n
    with (OUT/"extended_funding_events.csv").open("w",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=["venue","coin","timestamp_ms","rate","interval_hours"])
        wr.writeheader();wr.writerows(sorted(merged.values(),key=lambda v:(v["coin"],v["timestamp_ms"],v["venue"])))
    provenance["issues"]=issues
    provenance["prehistory_rows"]=len(allrows)
    provenance["full_merged_rows"]=len(merged)
    provenance["full_sha256"]=hashlib.sha256((OUT/"extended_funding_events.csv").read_bytes()).hexdigest()
    (OUT/"prehistory_manifest.json").write_text(json.dumps(provenance,indent=2,ensure_ascii=False))
    print("HISTORICAL_EXTENSION_COMPLETE",json.dumps({"prehistory":len(allrows),
         "merged":len(merged),"sha256":provenance["full_sha256"],
         "binance_missing":len(issues)},ensure_ascii=False),flush=True)
    if issues:raise RuntimeError("Missing Binance months; economic decision blocked")
if __name__=="__main__":main()
