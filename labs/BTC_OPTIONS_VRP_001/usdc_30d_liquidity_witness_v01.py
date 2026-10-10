#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, hashlib, json, math, pathlib, re, urllib.parse, urllib.request

BASE="https://history.deribit.com/api/v2/public"
OUT=pathlib.Path("artifacts/btc_options_vrp_usdc_30d_liquidity_witness_v01")
MIN_AMOUNT=0.01
OPT_RE=re.compile(r"^BTC_USDC-(\d{1,2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{2})-(\d+(?:\.\d+)?)-(C|P)$")
MON={m:i+1 for i,m in enumerate(["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"])}

def ms(x): return int(x.timestamp()*1000)
def get(endpoint,params):
    url=BASE+endpoint+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-VRP-USDC-LiquidityWitness/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    obj=json.loads(raw.decode())
    if "error" in obj: raise RuntimeError(str(obj["error"]))
    return obj["result"],hashlib.sha256(raw).hexdigest()
def unpack(x):
    if isinstance(x,dict) and isinstance(x.get("trades"),list): return x["trades"],bool(x.get("has_more",False))
    if isinstance(x,list): return x,False
    raise RuntimeError("unexpected response")
def fetch(start,end):
    rows=[]; hashes=[]; seen=set(); cursor=start
    for _ in range(10):
        p,h=get("/get_last_trades_by_currency_and_time",{"currency":"USDC","kind":"option","start_timestamp":cursor,"end_timestamp":end,"count":1000,"sorting":"asc","include_old":"true"})
        hashes.append(h); page,more=unpack(p); last=None; new=0
        for t in page:
            ts=int(t.get("timestamp",-1)); key=(ts,str(t.get("trade_id","")),str(t.get("instrument_name","")),str(t.get("amount","")))
            if key not in seen: seen.add(key); rows.append(t); new+=1
            last=ts if last is None or ts>last else last
        if not more or not page or last is None or last>=end: break
        cursor=last+1
    else: raise RuntimeError("pagination limit")
    return rows,hashes
def parse(name):
    m=OPT_RE.match(name or "")
    if not m:return None
    d,mo,y,k,s=m.groups()
    return dt.datetime(2000+int(y),MON[mo],int(d),8,0,tzinfo=dt.timezone.utc),float(k),s
def thursdays():
    d=dt.date(2025,1,1)
    while d.weekday()!=3:d+=dt.timedelta(days=1)
    while d.year==2025:
        yield d; d+=dt.timedelta(days=7)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    receipts=[]; selected=[]
    for day in thursdays():
        anchor=dt.datetime.combine(day,dt.time(8,0),tzinfo=dt.timezone.utc); end=anchor+dt.timedelta(hours=4)-dt.timedelta(milliseconds=1)
        rows,hashes=fetch(ms(anchor),ms(end))
        first={}
        for t in sorted(rows,key=lambda z:(int(z.get("timestamp",-1)),str(z.get("trade_id","")))):
            name=str(t.get("instrument_name",""))
            if not name.startswith("BTC_USDC-"):continue
            try: amt=float(t.get("amount",0))
            except: continue
            if amt<MIN_AMOUNT:continue
            q=parse(name)
            if not q or t.get("index_price") is None:continue
            exp,k,side=q; dte=(exp-anchor).total_seconds()/86400
            if not (25<=dte<=35):continue
            first.setdefault(name,t)
        pairs={}
        for name,t in first.items():
            exp,k,side=parse(name); pairs.setdefault((exp,k),{})[side]=(name,t)
        cands=[]
        for (exp,k),legs in pairs.items():
            if "C" not in legs or "P" not in legs:continue
            cn,c=legs["C"]; pn,p=legs["P"]
            try: idx=(float(c["index_price"])+float(p["index_price"]))/2
            except: continue
            if idx<=0:continue
            dte=(exp-anchor).total_seconds()/86400
            cands.append((abs(dte-30),exp,abs(math.log(k/idx)),k,dte,cn,c,pn,p))
        cands.sort(key=lambda z:(z[0],z[1],z[2],z[3]))
        if cands:
            _,exp,_,k,dte,cn,c,pn,p=cands[0]
            selected.append({"anchor":anchor.isoformat(),"expiration_timestamp":int(exp.timestamp()*1000),"dte_days":dte,"strike":k,
              "call_instrument":cn,"put_instrument":pn,"call_trade_timestamp":int(c["timestamp"]),"put_trade_timestamp":int(p["timestamp"]),
              "call_direction":c.get("direction"),"put_direction":p.get("direction"),"call_amount":float(c["amount"]),"put_amount":float(p["amount"]),
              "call_trade_id":c.get("trade_id"),"put_trade_id":p.get("trade_id"),"prices_retained":False,"pnl_computed":False})
        receipts.append({"anchor":anchor.isoformat(),"real_btc_usdc_trades":sum(str(t.get("instrument_name","")).startswith("BTC_USDC-") for t in rows),
                         "eligible_instruments":len(first),"two_leg_candidates":len(cands),"selected":bool(cands),"raw_hashes":hashes})
    n=len(selected)
    result={"classification":"LIQUIDITY_WITNESS_PRESENT" if n>=24 else "LIQUIDITY_WITNESS_SPARSE","calendar_anchors":len(receipts),
            "two_leg_witness_anchors":n,"coverage":n/len(receipts),"required_floor":24,"prices_retained":False,"returns_computed":False,"pnl_computed":False,
            "authenticated":False,"orders":False}
    (OUT/"selected_pairs.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in selected)+"\n")
    (OUT/"anchor_receipts.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in receipts)+"\n")
    (OUT/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
