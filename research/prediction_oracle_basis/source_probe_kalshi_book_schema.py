#!/usr/bin/env python3
"""Kalshi KXBTCD public order-book schema diagnostic.

Prints schema/key/count information only. It never prints price or size values,
never reads matured outcomes, and computes no economics.
"""
import datetime as dt
import json
import urllib.parse
import urllib.request

BASE="https://api.elections.kalshi.com/trade-api/v2"
UA="CryptoLab-POB-KalshiBookSchema/0.1"

def get(url, params=None):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode())

def pi(v):
    if not v: return None
    x=dt.datetime.fromisoformat(str(v).replace("Z","+00:00"))
    if x.tzinfo is None: x=x.replace(tzinfo=dt.timezone.utc)
    return x.astimezone(dt.timezone.utc)

now=dt.datetime.now(dt.timezone.utc)
payload=get(BASE+"/markets",{"series_ticker":"KXBTCD","status":"open","limit":1000})
rows=[]
for m in payload.get("markets",[]):
    t=pi(m.get("close_time") or m.get("latest_expiration_time"))
    if t and t>now:
        rows.append((t,str(m.get("ticker") or "")))
if not rows:
    raise SystemExit("NO_FUTURE_KXBTCD")
t,ticker=min(rows)
book=get(BASE+"/markets/"+urllib.parse.quote(ticker)+"/orderbook")
print("FUTURE_TICKER",ticker)
print("RESOLUTION_UTC",t.isoformat())
print("TOP_KEYS",sorted(book.keys()) if isinstance(book,dict) else type(book).__name__)
ob=book.get("orderbook",book) if isinstance(book,dict) else {}
print("ORDERBOOK_KEYS",sorted(ob.keys()) if isinstance(ob,dict) else type(ob).__name__)
if isinstance(ob,dict):
    for k,v in sorted(ob.items()):
        if isinstance(v,list):
            print("LIST_FIELD",k,"COUNT",len(v))
            if v:
                first=v[0]
                if isinstance(first,dict):
                    print("LIST_SCHEMA",k,sorted(first.keys()))
                elif isinstance(first,list):
                    print("LIST_SCHEMA",k,[f"index_{i}" for i in range(len(first))])
                else:
                    print("LIST_SCHEMA",k,type(first).__name__)
        elif isinstance(v,dict):
            print("DICT_FIELD",k,"KEYS",sorted(v.keys()))
        else:
            print("SCALAR_FIELD",k,"TYPE",type(v).__name__)
print("NO_PRICE_VALUES_NO_SIZE_VALUES_NO_OUTCOMES_NO_PNL")
