#!/usr/bin/env python3
# V2.0 transport-only diagnostic: counts/timestamp alignment/HTTP metadata only.
# NEVER prints prices, returns, PnL or outcome metrics.

import json, urllib.parse, urllib.request, urllib.error, time

EVENTS=[
("AIXBT",1736499327639,"KUCOIN"),
("SYRUP",1746530720814,"LBANK"),
("PUMP",1757590673797,"KUCOIN"),
("GIGGLE",1761361338417,"KUCOIN"),
("BANK",1763028026501,"BITGET"),
]

def ceilmin(x): return ((x+59999)//60000)*60000

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV20TransportDiag/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return {"http":r.status,"json":json.load(r),"error_body":None}
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8","replace")[:500]
        return {"http":e.code,"json":None,"error_body":body}
    except Exception as e:
        return {"http":None,"json":None,"error_body":type(e).__name__}

rows=[]
for ticker,t0,venue in EVENTS:
    entry=ceilmin(t0+60000)
    if venue=="KUCOIN":
        a=entry-2*60000;b=entry+61*60000
        q=urllib.parse.urlencode({"symbol":"BTC-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
        z=get_json("https://api.kucoin.com/api/v1/market/candles?"+q)
        ts=[]
        if z["json"]:
            for x in z["json"].get("data") or []:
                try: ts.append(int(x[0])*1000)
                except Exception: pass
        targets=[entry,entry+4*60000,entry+14*60000,entry+59*60000]
        rows.append({
          "case":ticker+"_BTC_KUCOIN",
          "http":z["http"],
          "api_code":(z["json"] or {}).get("code"),
          "n":len(ts),
          "target_present":[t in set(ts) for t in targets],
          "minute_aligned":all(t%60000==0 for t in ts),
          "error_body":z["error_body"],
        })
    elif venue=="BITGET":
        floor=(t0//60000)*60000
        a=floor-24*3600000-10*60000
        # Inspect a few small windows only, no values.
        for label,s,e in [
            ("pre24",a,a+60*60000),
            ("event",floor-10*60000,floor+70*60000),
            ("btc_exec",entry,entry+60*60000),
        ]:
            sym="BANKUSDT" if label!="btc_exec" else "BTCUSDT"
            q=urllib.parse.urlencode({"category":"SPOT","symbol":sym,"interval":"1m","startTime":s,"endTime":e,"limit":100})
            z=get_json("https://api.bitget.com/api/v3/market/history-candles?"+q)
            data=(z["json"] or {}).get("data") or []
            ts=[]
            for x in data:
                try: ts.append(int(x[0]))
                except Exception: pass
            rows.append({
              "case":"BANK_BITGET_"+label,
              "http":z["http"],
              "api_code":(z["json"] or {}).get("code"),
              "api_msg":(z["json"] or {}).get("msg"),
              "n":len(ts),
              "minute_aligned":all(t%60000==0 for t in ts),
              "error_body":z["error_body"],
            })
            time.sleep(.15)

print("V20_TRANSPORT_DIAG_BEGIN")
print(json.dumps({"rows":rows},indent=2,sort_keys=True))
print("V20_TRANSPORT_DIAG_END")

# trigger after workflow registration

# retrigger after YAML fix
