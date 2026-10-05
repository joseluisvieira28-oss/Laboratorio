#!/usr/bin/env python3
import json,time,urllib.parse,urllib.request
from datetime import datetime,timezone

# Official Binance CMS releaseDate values from the full 2024 "Binance Will List..." census.
EVENTS=[
("JUP",1706684813622,"7b5c643c3d8a4c9a9d443b1ceefb0015"),
("PYTH",1706860207072,"f36074f9caa6474fa44fdb18503183d6"),
("RONIN",1707124296210,"dfea1e2ae7fd475196b215e673193c63"),
("DYM",1707211617933,"00095277601046a38159f649b5f0e55b"),
("STRK",1708395922135,"cb15311b17c440d0b0cf077a9b9979a3"),
("AXL",1709277537028,"2eb66d061d214c31a096cff35ede9360"),
("WIF",1709632897364,"90ad67fe5be7483ea058191bfde677e4"),
("METIS",1710143970976,"a73748f501dc48f6ba3d68d724052492"),
("BOME",1710581406588,"bca0f355cf004367b90d7e48fee3470c"),
("W",1712054366812,"49b5a226723e407cb7044d749bfda5b2"),
("TNSR",1712576657942,"6eeb77d6863948eb8e79fc40bacabdbc"),
("TAO",1712817838489,"dd856efc9c1a4a209eb48992e190e4d6"),
("ZK",1718589610865,"d87a9b01d6634ad1a36d984cc54595ee"),
("ZRO",1718864370953,"28a21b10ed23416386b40d263b71cd99"),
("TON",1723095568744,"abba626aa0974b828f91c166bdc12afd"),
("EURI",1724655603568,"e8c6134371e945df961ae1854e863a62"),
("NEIRO",1726465502167,"4336ae4908154736acff8302509f7a05"),
("TURBO",1726465502167,"4336ae4908154736acff8302509f7a05"),
("1MBABYDOGE",1726465502167,"4336ae4908154736acff8302509f7a05"),
("EIGEN",1727684397115,"29494a3db1034233b65522b9e122d079"),
("BNSOL",1728457213876,"56398cfbd9c4419d9c0b54a0d1da2a7b"),
("COW",1730869807602,"2faa229be2ba4b758bbeb1859f63ba36"),
("CETUS",1730869807602,"2faa229be2ba4b758bbeb1859f63ba36"),
("ACT",1731303569462,"d16d96c136154680a6373225d592bca1"),
("PNUT",1731303569462,"d16d96c136154680a6373225d592bca1"),
("ACX",1733474058953,"b8b988973b88493192f2e43ba26da331"),
("ORCA",1733474058953,"b8b988973b88493192f2e43ba26da331"),
("ME",1733815340546,"d4f72bdd82d44a0591ee40d41f0b44d5"),
("VELODROME",1734077277826,"4f8e9e0b5dd54e9095b7d718f289d9d4"),
]
ALIASES={"1MBABYDOGE":["BABYDOGE","1MBABYDOGE"],"NEIRO":["NEIRO","NEIROETH"]}
EXCLUDE_SOURCE_ONLY={"EURI":"stablecoin","BNSOL":"staked/wrapped derivative"}

def req(url):
  r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabFullCensus/2.0","Accept":"application/json"})
  try:
    with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),None
  except urllib.error.HTTPError as e:return e.code,None,e.read().decode("utf-8","replace")[:300]
  except Exception as e:return None,None,repr(e)

def iso(ms): return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()

def kc(sym,a,b):
  q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
  st,j,err=req("https://api.kucoin.com/api/v1/market/candles?"+q)
  if not j:return {"http":st,"error":err}
  xs=j.get("data",[]); ts=sorted(int(x[0])*1000 for x in xs)
  return {"http":st,"code":j.get("code"),"n":len(ts),
          "first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}

rows=[]
for ticker,t0,code in EVENTS:
  if ticker in EXCLUDE_SOURCE_ONLY:
    rows.append({"ticker":ticker,"announcement":code,"status":"EXCLUDED_SOURCE_RULE","reason":EXCLUDE_SOURCE_ONLY[ticker]})
    continue
  found=None
  for alias in ALIASES.get(ticker,[ticker]):
    pre=kc(alias,t0-25*3600000,t0-23*3600000); time.sleep(.08)
    evt=kc(alias,t0-10*60000,t0+65*60000); time.sleep(.08)
    ok=pre.get("n",0)>0 and evt.get("n",0)>0
    if ok:
      found={"ticker":ticker,"alias":alias,"announcement":code,"t0_ms":t0,"t0":iso(t0),
             "status":"SOURCE_COVERAGE_PASS","pre24h":pre,"event":evt}
      break
    if found is None:
      found={"ticker":ticker,"alias":alias,"announcement":code,"t0_ms":t0,"t0":iso(t0),
             "status":"NO_KUCOIN_PRET0_COVERAGE","pre24h":pre,"event":evt}
  rows.append(found)
valid=[r for r in rows if r["status"]=="SOURCE_COVERAGE_PASS"]
print("FULL_SOURCE_COVERAGE_JSON_BEGIN")
print(json.dumps({"n_assets":len(EVENTS),"n_valid":len(valid),"valid_tickers":[r["ticker"] for r in valid],"rows":rows},indent=2))
print("FULL_SOURCE_COVERAGE_JSON_END")

# trigger after workflow registration
