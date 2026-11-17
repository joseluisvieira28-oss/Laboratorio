#!/usr/bin/env python3
"""CARRY-001 SOURCE PROBE; read-only, no wallet, no orders."""
import urllib.request,urllib.error,json,io,zipfile,datetime as dt,hashlib,time,pathlib
OUT=pathlib.Path("carry001-evidence");OUT.mkdir(exist_ok=True)
UA="CryptoLab-CARRY001/0.1 (research; no-trade)"
def fetch(url,body=None):
    data=json.dumps(body).encode() if body is not None else None
    head={"User-Agent":UA,"Accept":"application/json"}
    if data:head["Content-Type"]="application/json"
    req=urllib.request.Request(url,data=data,headers=head)
    start=time.monotonic()
    rec={"url":url,"request":body,"timestamp":dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(req,timeout=25) as resp:
            b=resp.read(2500000)
            rec.update(status=resp.status,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),elapsed_s=round(time.monotonic()-start,3))
            if b[:2]==b"PK":
                z=zipfile.ZipFile(io.BytesIO(b)); rec["members"]=z.namelist()
                rec["first_lines"]=z.read(z.namelist()[0]).decode("utf8").splitlines()[:4]
            else:
                obj=json.loads(b)
                rec["count"]=len(obj) if isinstance(obj,list) else -1
                rec["sample"]=obj[:2] if isinstance(obj,list) else str(obj)[:450]
    except Exception as e:
        rec["error"]=repr(e)[:250]
    return rec
start=int(dt.datetime(2024,9,1,tzinfo=dt.timezone.utc).timestamp()*1000)
end=int(dt.datetime(2024,9,5,tzinfo=dt.timezone.utc).timestamp()*1000)
records={}
for coin in ["BTC","ETH","SOL"]:
    records["HL_"+coin]=fetch("https://api.hyperliquid.xyz/info",{"type":"fundingHistory","coin":coin,"startTime":start,"endTime":end})
    symbol=coin+"USDT"
    records["BINANCE_API_"+coin]=fetch("https://fapi.binance.com/fapi/v1/fundingRate?symbol="+symbol+"&startTime="+str(start)+"&endTime="+str(end)+"&limit=1000")
    records["BINANCE_VISION_"+coin]=fetch("https://data.binance.vision/data/futures/um/monthly/fundingRate/"+symbol+"/"+symbol+"-fundingRate-2024-09.zip")
for name,row in records.items():
    print("PROBE",name,json.dumps(row,ensure_ascii=False)[:1500],flush=True)
(OUT/"source_probe.json").write_text(json.dumps(records,indent=2,ensure_ascii=False))
print("PROBE_DONE",sum("error" not in v for v in records.values()),"/",len(records),flush=True)
