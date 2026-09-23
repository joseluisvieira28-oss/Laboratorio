#!/usr/bin/env python3
import json, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

HOSTS=[
 "https://fapi.binance.com",
 "https://fapi1.binance.com",
 "https://fapi2.binance.com",
 "https://fapi3.binance.com",
 "https://fapi4.binance.com",
 "https://fapi-gcp.binance.com",
 "https://www.binance.com",
 "https://data-api.binance.vision",
]
symbol="ETHUSDT"
start=int(datetime(2024,1,1,tzinfo=timezone.utc).timestamp()*1000)
end=int(datetime(2024,1,3,tzinfo=timezone.utc).timestamp()*1000)
out=[]
for h in HOSTS:
    qs=urllib.parse.urlencode({"symbol":symbol,"startTime":start,"endTime":end,"limit":10})
    url=h+"/fapi/v1/fundingRate?"+qs
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-FundingTransportProbe/1.0"})
        with urllib.request.urlopen(req,timeout=20) as r:
            body=r.read()
            parsed=json.loads(body.decode())
            ok=isinstance(parsed,list) and len(parsed)>0 and all("fundingRate" in x and "fundingTime" in x for x in parsed)
            out.append({"host":h,"status":getattr(r,"status",200),"ok":ok,"count":len(parsed) if isinstance(parsed,list) else None,
                        "sample":parsed[0] if ok else parsed})
    except Exception as e:
        out.append({"host":h,"ok":False,"error":repr(e)})
p=Path(__file__).resolve().parent/"evidence"/"FUNDING_TRANSPORT_PROBE_V0.1.json"
p.parent.mkdir(exist_ok=True)
p.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
