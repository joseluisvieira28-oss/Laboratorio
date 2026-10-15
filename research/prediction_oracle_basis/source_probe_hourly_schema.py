#!/usr/bin/env python3
"""Schema-only diagnostic for current future Polymarket hourly BTC threshold event."""

import datetime as dt
import json
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

UA="CryptoLab-POB-HourlySchema/0.1"
NY=ZoneInfo("America/New_York")
KBASE="https://api.elections.kalshi.com/trade-api/v2"
GAMMA="https://gamma-api.polymarket.com/events"

def get(url, params=None):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode())

def parse_iso(v):
    return dt.datetime.fromisoformat(str(v).replace("Z","+00:00")).astimezone(dt.timezone.utc)

now=dt.datetime.now(dt.timezone.utc)
k=get(KBASE+"/markets",{"series_ticker":"KXBTCD","status":"open","limit":1000})
future=[]
for m in k.get("markets",[]):
    t=parse_iso(m.get("close_time") or m.get("latest_expiration_time"))
    if t>now:
        future.append(t)
if not future:
    raise SystemExit("NO_FUTURE_KALSHI")
t=min(future)
local=t.astimezone(NY)
suffix="am" if local.hour<12 else "pm"
h=local.hour%12 or 12
slug=f"bitcoin-above-on-{local.strftime('%B').lower()}-{local.day}-{local.year}-{h}{suffix}-et"
p=get(GAMMA,{"slug":slug})
events=p if isinstance(p,list) else p.get("events",[])
print("SCHEMA_ONLY_SLUG",slug)
print("EVENT_COUNT",len(events))
for e in events[:1]:
    print("EVENT_KEYS",sorted(e.keys()))
    print("EVENT_TITLE",e.get("title"))
    markets=e.get("markets") or []
    print("MARKET_COUNT",len(markets))
    for m in markets[:3]:
        print("MARKET_KEYS",sorted(m.keys()))
        for key in ["question","title","description","groupItemTitle","resolutionSource","endDate","slug"]:
            v=m.get(key)
            if v is not None:
                s=str(v)
                print(key.upper(),s[:1200])
        print("---")
print("NO_QUOTES_NO_OUTCOMES_NO_PNL")
