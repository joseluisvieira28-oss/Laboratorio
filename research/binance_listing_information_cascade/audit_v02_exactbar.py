#!/usr/bin/env python3
# Exact-bar technical integrity audit. No gate changes; no holdout.
import json,urllib.parse,urllib.request
from pathlib import Path

ROOT=Path("research/binance_listing_information_cascade")
stored=json.loads((ROOT/"results_v02/events.json").read_text())

def req(u):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 CryptoLabExactBar/1.0","Accept":"application/json"})
    with urllib.request.urlopen(r,timeout=20) as x:return json.load(x)

def bitget(sym,a,b):
    q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
    j=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
    return {int(x[0]):{"o":float(x[1]),"h":float(x[2]),"l":float(x[3]),"c":float(x[4]),"v":float(x[5])} for x in (j.get("data") or [])}

def kucoin(sym,a,b):
    q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
    j=req("https://api.kucoin.com/api/v1/market/candles?"+q)
    return {int(x[0])*1000:{"o":float(x[1]),"h":float(x[3]),"l":float(x[4]),"c":float(x[2]),"v":float(x[5])} for x in (j.get("data") or [])}

rows=[]
for s in stored:
    if "r15" not in s: continue
    t0=s["t0"]; minute=(t0//60000)*60000
    fn=bitget if s["venue"]=="BITGET" else kucoin
    a=minute-10*60000;b=minute+61*60000
    bars=fn(s["symbol"],a,b)
    p0bar=bars.get(minute-60000)
    row={"ticker":s["ticker"],"venue":s["venue"],"symbol":s["symbol"],"t0":t0,
         "p0_target_ts":minute-60000,"stored_p0":s["p0"],
         "exact_p0":p0bar["c"] if p0bar else None,
         "bars_n":len(bars)}
    if p0bar:
        p0=p0bar["c"]
        for n in [1,5,15,60]:
            bar=bars.get(minute+n*60000)
            exact=(bar["c"]/p0-1) if bar else None
            row[f"stored_r{n}"]=s.get(f"r{n}")
            row[f"exact_r{n}"]=exact
            row[f"delta_r{n}"]=(exact-s.get(f"r{n}")) if exact is not None and s.get(f"r{n}") is not None else None
            row[f"target_ts_r{n}"]=minute+n*60000
    rows.append(row)

valid=[r for r in rows if r.get("exact_r15") is not None]
maxd=max(abs(r["delta_r15"]) for r in valid) if valid else None
changed=sum(abs(r["delta_r15"])>1e-12 for r in valid) if valid else 0
summary={"audit_only":True,"v02_verdict_before_audit":"NO_EDGE_DISCOVERY","n":len(valid),
         "r15_changed_count":changed,"max_abs_delta_r15":maxd,
         "technical_integrity":"PASS" if changed==0 else "FAIL_RECOMPUTE_REQUIRED",
         "holdout_opened":False,"gates_changed":False}
out=ROOT/"audits";out.mkdir(exist_ok=True)
(out/"V02_EXACT_BAR_INTEGRITY_AUDIT.json").write_text(json.dumps({"summary":summary,"rows":rows},indent=2))
print("EXACT_BAR_AUDIT",json.dumps(summary,indent=2))
print("ROWS",json.dumps(rows,indent=2))
