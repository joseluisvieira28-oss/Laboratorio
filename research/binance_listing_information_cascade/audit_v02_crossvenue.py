#!/usr/bin/env python3
# Post-outcome integrity audit only. Does NOT alter V0.2 gates or verdict.
import json,time,urllib.parse,urllib.request,statistics
from pathlib import Path

EVENTS=[
("PYTH",1706860207072),("AXL",1709277537028),("WIF",1709632897364),
("METIS",1710143970976),("TAO",1712817838489),("1MBABYDOGE",1726465502167),
("CETUS",1730869807602),("ACT",1731303569462),("ORCA",1733474058953)]
ALIASES={"1MBABYDOGE":["BABYDOGE","1MBABYDOGE"]}

def req(u):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 CryptoLabIntegrity/1.0","Accept":"application/json"})
    with urllib.request.urlopen(r,timeout=20) as x:return json.load(x)

def bitget(sym,a,b):
    q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
    j=req("https://api.bitget.com/api/v3/market/history-candles?"+q);o=[]
    for x in j.get("data") or []: o.append((int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])))
    return sorted(o)

def kucoin(sym,a,b):
    q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
    j=req("https://api.kucoin.com/api/v1/market/candles?"+q);o=[]
    for x in j.get("data") or []: o.append((int(x[0])*1000,float(x[1]),float(x[3]),float(x[4]),float(x[2]),float(x[5])))
    return sorted(o)

def allbars(fn,sym,t0):
    out={};a=t0-25*3600000;b=t0+65*60000
    while a<b:
        z=min(a+90*60000,b)
        for x in fn(sym,a,z): out[x[0]]=x
        a=z+60000;time.sleep(.03)
    return sorted(out.values())

def metrics(bars,t0):
    minute=(t0//60000)*60000
    pre=[x for x in bars if x[0]<minute]
    witness=[x for x in bars if x[0]<=t0-24*3600000+10*60000]
    evt=[x for x in bars if minute<=x[0]<=minute+60*60000]
    if not(pre and witness and evt): return None
    p0=pre[-1][4]
    out={"p0":p0,"p0_ts":pre[-1][0],"n_bars":len(bars)}
    for n in [1,5,15,60]:
        w=[x for x in evt if x[0]<=minute+n*60000]
        out["r"+str(n)]=w[-1][4]/p0-1 if w else None
    return out

rows=[]
for ticker,t0 in EVENTS:
    row={"ticker":ticker,"t0":t0}
    for sym in ALIASES.get(ticker,[ticker]):
        try:
            bm=metrics(allbars(bitget,sym,t0),t0)
        except Exception as e: bm={"error":repr(e)}
        try:
            km=metrics(allbars(kucoin,sym,t0),t0)
        except Exception as e: km={"error":repr(e)}
        if bm and km and "r15" in bm and "r15" in km:
            row.update({"symbol":sym,"bitget":bm,"kucoin":km,
                        "same_sign_r15":(bm["r15"]>0)==(km["r15"]>0),
                        "abs_gap_r15":abs(bm["r15"]-km["r15"]),
                        "ratio_r15":(bm["r15"]/km["r15"]) if km["r15"] else None})
            break
    rows.append(row)

valid=[r for r in rows if "same_sign_r15" in r]
summary={
 "audit_only":True,
 "v02_verdict_unchanged":"NO_EDGE_DISCOVERY",
 "n_overlap_valid":len(valid),
 "same_sign_r15_count":sum(r["same_sign_r15"] for r in valid),
 "same_sign_r15_rate":sum(r["same_sign_r15"] for r in valid)/len(valid) if valid else None,
 "median_abs_gap_r15":statistics.median([r["abs_gap_r15"] for r in valid]) if valid else None,
 "act_bitget_r15":next((r["bitget"]["r15"] for r in valid if r["ticker"]=="ACT"),None),
 "act_kucoin_r15":next((r["kucoin"]["r15"] for r in valid if r["ticker"]=="ACT"),None)
}
p=Path("research/binance_listing_information_cascade/audits");p.mkdir(exist_ok=True)
(p/"V02_CROSSVENUE_INTEGRITY_AUDIT.json").write_text(json.dumps({"summary":summary,"rows":rows},indent=2))
print("AUDIT_SUMMARY",json.dumps(summary,indent=2))
print("AUDIT_ROWS",json.dumps(rows,indent=2))
