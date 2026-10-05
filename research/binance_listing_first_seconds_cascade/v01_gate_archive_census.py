#!/usr/bin/env python3
# V0.1 Gate deals archive existence census.
# SOURCE-ONLY. Does not read or emit prices/returns.

import json
import urllib.request
import urllib.error

EVENTS=[
 ("AIXBT",1736499327639),
 ("CGPT",1736499327639),
 ("COOKIE",1736499327639),
 ("TRUMP",1737259542151),
 ("1000CHEEMS",1739085031264),
 ("TST",1739085031264),
 ("SYRUP",1746530720814),
 ("KMNO",1746530720814),
 ("WLFI",1756691345082),
 ("PUMP",1757590673797),
 ("AVNT",1757908021934),
 ("ASTER",1759736929954),
 ("GIGGLE",1761361338417),
 ("F",1761361338417),
 ("BANK",1763028026501),
 ("MET",1763028026501),
]

def ym_from_ms(ms):
    import datetime
    return datetime.datetime.fromtimestamp(ms/1000, tz=datetime.timezone.utc).strftime("%Y%m")

def probe(url):
    req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"Mozilla/5.0 CryptoLabFirstSeconds/0.1"})
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            return {"http":r.status,"content_length":r.headers.get("Content-Length"),"content_type":r.headers.get("Content-Type")}
    except urllib.error.HTTPError as e:
        return {"http":e.code,"content_length":e.headers.get("Content-Length"),"content_type":e.headers.get("Content-Type")}
    except Exception as e:
        return {"http":None,"error_type":type(e).__name__}

rows=[]
for ticker,t0 in EVENTS:
    ym=ym_from_ms(t0)
    market=ticker+"_USDT"
    url=f"https://download.gatedata.org/spot/deals/{ym}/{market}-{ym}.csv.gz"
    x=probe(url)
    rows.append({"ticker":ticker,"ym":ym,"market":market,**x})

print("FIRST_SECONDS_V01_ARCHIVE_CENSUS_BEGIN")
print(json.dumps({"n_candidates":len(rows),"rows":rows},indent=2,sort_keys=True))
print("FIRST_SECONDS_V01_ARCHIVE_CENSUS_END")
