#!/usr/bin/env python3
import json,time,urllib.parse,urllib.request
from datetime import datetime,timezone

E=[
("ACH",1641794176091),("IMX",1641794176091),("GLMR",1641881720254),("LOKA",1642673590158),
("API3",1642746484252),("ACA",1643076171074),("ANC",1643086336145),("WOO",1644286833903),
("ALPINE",1645437604601),("ASTR",1646033043037),("GMT",1646820132231),("KDA",1646975827515),
("APE",1647500570924),("BSW",1647855364219),("MOB",1651211915653),("NEXO",1651211915653),
("LDO",1652079437647),("LUNA",1653751029671),("OP",1654045214413),("STG",1660889501192),
("GMX",1664949629449),("APT",1666055040591),("OSMO",1666929652539),("HOOK",1669896165754),
("MAGIC",1670818244836),("RPL",1674014406526),("GNS",1676619260939),("SYN",1677047419653),
("LQTY",1677568518334),("ARB",1679306561345),("ID",1679479216978),("RDNT",1680146454557),
("EDU",1682676023060),("SUI",1683097345887),("FLOKI",1683285604106),("PEPE",1683285604106),
("MAV",1687856418603),("PENDLE",1688365335567),("ARKM",1689663609545),("WLD",1690182131620),
("CYBER",1691982500188),("SEI",1691982500188),("NTRN",1696923917379),("TIA",1698671932206),
("MEME",1698912078594),("ORDI",1699339453500),("BLUR",1700806187186),("JTO",1701950138787),
("1000SATS",1702361370579),("BONK",1702612713180),
]
# Stablecoins FDUSD/AEUR excluded mechanically before source scan.
def req(url):
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV03Source/1.0","Accept":"application/json"})
 try:
  with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),None
 except urllib.error.HTTPError as e:return e.code,None,e.read().decode("utf-8","replace")[:250]
 except Exception as e:return None,None,repr(e)
def iso(ms):return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()
def kc(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 st,j,err=req("https://api.kucoin.com/api/v1/market/candles?"+q)
 if not isinstance(j,dict):return {"http":st,"error":err,"ts":[]}
 xs=j.get("data") or [];ts=sorted(int(x[0])*1000 for x in xs)
 return {"http":st,"code":j.get("code"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None,"ts":ts}
def bg(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 st,j,err=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
 if not isinstance(j,dict):return {"http":st,"error":err,"ts":[]}
 xs=j.get("data") or [];ts=sorted(int(x[0]) for x in xs)
 return {"http":st,"code":j.get("code"),"msg":j.get("msg"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None,"ts":ts}
def compact(x):
 return {k:v for k,v in x.items() if k!="ts"}
rows=[]
for sym,t0 in E:
 a,b=t0-25*3600000,t0-23*3600000
 c,d=t0-10*60000,t0+10*60000
 kp=kc(sym,a,b);time.sleep(.06);ke=kc(sym,c,d);time.sleep(.06)
 bp=bg(sym,a,b);time.sleep(.06);be=bg(sym,c,d);time.sleep(.06)
 def ok(p,e):
  ts=p.get("ts",[]); es=e.get("ts",[])
  return any(x<=t0-24*3600000 for x in ts) and any(t0-10*60000<=x<t0 for x in es) and any(t0<=x<=t0+5*60000 for x in es)
 ko,bo=ok(kp,ke),ok(bp,be)
 rows.append({"ticker":sym,"t0":iso(t0),"kucoin_pass":ko,"bitget_pass":bo,
              "kucoin_pre":compact(kp),"kucoin_event":compact(ke),
              "bitget_pre":compact(bp),"bitget_event":compact(be)})
print("PRE2024_SOURCE_BEGIN")
print(json.dumps({"n_assets":len(E),
 "kucoin_valid":[r["ticker"] for r in rows if r["kucoin_pass"]],
 "bitget_valid":[r["ticker"] for r in rows if r["bitget_pass"]],
 "union_valid":[r["ticker"] for r in rows if r["kucoin_pass"] or r["bitget_pass"]],
 "rows":rows},indent=2))
print("PRE2024_SOURCE_END")
