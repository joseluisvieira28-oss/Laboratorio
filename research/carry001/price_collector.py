#!/usr/bin/env python3
"""CARRY-001 actual historical price-CANDLE data, not orderbook quotes.
Provider mismatches (Binance mark price vs Hyperliquid traded candle) prevent tradable PnL claims.
Source window: 2026-05-01 through 2026-11-01 UTC exclusive.
"""
import csv,datetime as dt,hashlib,io,json,pathlib,time,urllib.request,urllib.error,zipfile,gzip
from collections import Counter
OUT=pathlib.Path("carry001-evidence");OUT.mkdir(exist_ok=True);RAW=OUT/"raw";RAW.mkdir(exist_ok=True)
UTC=dt.timezone.utc; COINS=("BTC","ETH","SOL")
MONTHS=["2026-%02d"%m for m in range(5,11)]
def ms(y,m):return int(dt.datetime(y,m,1,tzinfo=UTC).timestamp()*1000)
def request(url,body=None):
    b=json.dumps(body,separators=(",",":")).encode() if body else None
    req=urllib.request.Request(url,data=b,headers={"User-Agent":"CryptoLab-CARRY001/0.1 Read-Only",
        "Content-Type":"application/json" if b else "application/octet-stream"})
    err=None
    for delay in [0,2,4,8,20]:
        if delay:time.sleep(delay)
        try:
            with urllib.request.urlopen(req,timeout=30) as r:return r.read(5_000_000)
        except Exception as e:err=repr(e)
    raise RuntimeError(f"PRICE SOURCE BLOCKED {url} {err}")
def check_number(val):
    x=float(val)
    if x<=0 or x>1e7:raise ValueError("invalid price")
    return x
def check_hour(val):
    n=int(val)
    if n>100_000_000_000_000:n//=1000
    if n<1_500_000_000_000 or n>1_900_000_000_000:raise ValueError("invalid time unit")
    return n//3_600_000*3_600_000
def collect():
    out=[];manifest={"data_provenance":"HL candleSnapshot is traded candles; Binance markPriceKlines is mark. NOT matched executable fill or margin mark","sources":[],"missing":[]}
    for coin in COINS:
        for mo in MONTHS:
            y,m=map(int,mo.split("-"))
            nxt=ms(y+1,1) if m==12 else ms(y,m+1)
            req={"type":"candleSnapshot","req":{"coin":coin,"interval":"1h","startTime":ms(y,m),"endTime":nxt-1}}
            try:
                raw=request("https://api.hyperliquid.xyz/info",req)
                digest=hashlib.sha256(raw).hexdigest()
                obj=json.loads(raw)
                if not isinstance(obj,list):raise ValueError("not a list")
                (RAW/f"HL_{coin}_1h_{mo}.json.gz").write_bytes(gzip.compress(raw,mtime=0))
                n=0
                for row in obj:
                    tm=check_hour(row["t"])
                    if not(ms(y,m)<=tm<nxt):continue
                    out.append({"venue":"Hyperliquid_TradeCandle","coin":coin,"hour_ms":tm,
                        "open":check_number(row["o"]),"high":check_number(row["h"]),
                        "low":check_number(row["l"]),"close":check_number(row["c"])})
                    n+=1
                manifest["sources"].append({"coin":coin,"venue":"Hyperliquid_TradeCandle","month":mo,"sha256":digest,"rows":n})
            except Exception as e:
                manifest["missing"].append({"coin":coin,"venue":"Hyperliquid","month":mo,"error":repr(e)[:200]})
            sym=coin+"USDT"
            path=f"https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{sym}/1h/{sym}-1h-{mo}.zip"
            try:
                raw=request(path)
                digest=hashlib.sha256(raw).hexdigest()
                (RAW/f"BIN_{coin}_mark_1h_{mo}.zip").write_bytes(raw)
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    arr=list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode("utf-8-sig"))))
                n=0
                for row in arr:
                    try:tm=check_hour(row[0])
                    except (ValueError,IndexError):continue
                    if not(ms(y,m)<=tm<nxt):continue
                    out.append({"venue":"Binance_MarkCandle","coin":coin,"hour_ms":tm,
                        "open":check_number(row[1]),"high":check_number(row[2]),
                        "low":check_number(row[3]),"close":check_number(row[4])})
                    n+=1
                manifest["sources"].append({"coin":coin,"venue":"Binance_MarkCandle","month":mo,"sha256":digest,"rows":n})
            except Exception as e:manifest["missing"].append({"coin":coin,"venue":"Binance","month":mo,"error":repr(e)[:200]})
            print("PRICE_MONTH",coin,mo,"HL_BIN_COUNTS",[(z["venue"],z["rows"]) for z in manifest["sources"] if z["coin"]==coin and z["month"]==mo],
                "FAILED",[(z["venue"],z["error"]) for z in manifest["missing"] if z["coin"]==coin and z["month"]==mo],flush=True)
    duplicates=0;unique={}
    for r in out:
        k=(r["venue"],r["coin"],r["hour_ms"])
        if k in unique:
            duplicates+=1
            if unique[k]!=r:raise ValueError("conflicting duplicate 1h candles")
        unique[k]=r
    dest=OUT/"price_candles.csv"
    with dest.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["venue","coin","hour_ms","open","high","low","close"])
        w.writeheader();w.writerows(sorted(unique.values(),key=lambda r:(r["coin"],r["hour_ms"],r["venue"])))
    manifest["duplicates"]=duplicates
    manifest["csv_sha256"]=hashlib.sha256(dest.read_bytes()).hexdigest()
    (OUT/"price_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    print("PRICE_COMPLETE",json.dumps({"rows":len(unique),"duplicates":duplicates,
      "missing_count":len(manifest["missing"]),"sha256":manifest["csv_sha256"]}),flush=True)
    if manifest["missing"]:raise RuntimeError("SOURCE_BLOCKED: price archives not complete; economic GO disabled")
if __name__=="__main__":collect()
