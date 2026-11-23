#!/usr/bin/env python3
"""CARRY-001 price-source verification; not executable bid/ask."""
import urllib.request,urllib.error,datetime as dt,io,zipfile,json,hashlib,time,pathlib
OUT=pathlib.Path("carry001-evidence");OUT.mkdir(exist_ok=True)
def get(url,body=None):
    data=json.dumps(body).encode() if body else None
    req=urllib.request.Request(url,data=data,headers={"User-Agent":"CryptoLab-CARRY001-ReadOnly","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:raw=r.read(3000000)
        o={"status":200,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
        if raw[:2]==b"PK":
            z=zipfile.ZipFile(io.BytesIO(raw));o["first_lines"]=z.read(z.namelist()[0]).decode().splitlines()[:3]
        else:
            payload=json.loads(raw)
            o["count"]=len(payload) if isinstance(payload,list) else -1
            o["head"]=payload[:2] if isinstance(payload,list) else str(payload)[:300]
            o["tail"]=payload[-1:] if isinstance(payload,list) else None
        return o
    except Exception as e:return {"error":str(e)[:180]}
s=int(dt.datetime(2026,9,1,tzinfo=dt.timezone.utc).timestamp()*1000)
e=int(dt.datetime(2026,9,3,tzinfo=dt.timezone.utc).timestamp()*1000)
r={}
for coin in ("BTC","ETH","SOL"):
    r["HL_"+coin]=get("https://api.hyperliquid.xyz/info",{"type":"candleSnapshot","req":{"coin":coin,"interval":"1h","startTime":s,"endTime":e}})
    sym=coin+"USDT"
    r["BinanceMark_"+coin]=get(f"https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{sym}/1h/{sym}-1h-2026-09.zip")
for k,v in r.items():print("PRICE_PROBE",k,json.dumps(v,ensure_ascii=False)[:1900],flush=True)
(OUT/"price_probe.json").write_text(json.dumps(r,indent=2,ensure_ascii=False))
