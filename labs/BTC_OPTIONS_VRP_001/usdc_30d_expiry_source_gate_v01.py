#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, hashlib, json, math, pathlib, re, urllib.parse, urllib.request

HISTORY="https://history.deribit.com/api/v2/public"
OUT=pathlib.Path("artifacts/btc_options_vrp_usdc_30d_source_v01")
MIN_AMOUNT=0.01
DTE_MIN=25.0
DTE_MAX=35.0
TARGET_DTE=30.0
OPT_RE=re.compile(r"^BTC_USDC-(\d{1,2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{2})-(\d+(?:\.\d+)?)-(C|P)$")
MON={m:i+1 for i,m in enumerate(["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"])}

def ms(x): return int(x.timestamp()*1000)

def get(endpoint,params):
    url=HISTORY+endpoint+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-VRP-USDC-30D-SourceOnly/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    obj=json.loads(raw.decode())
    if "error" in obj: raise RuntimeError(f"{endpoint}: {obj['error']}")
    return obj["result"],hashlib.sha256(raw).hexdigest()

def unpack(result):
    if isinstance(result,dict) and isinstance(result.get("trades"),list):
        return result["trades"],bool(result.get("has_more",False))
    if isinstance(result,list): return result,False
    raise RuntimeError("unexpected trade response")

def fetch_window(start_ms,end_ms,count=1000,max_pages=10):
    rows=[]; hashes=[]; seen=set(); cursor=start_ms
    for _ in range(max_pages):
        payload,h=get("/get_last_trades_by_currency_and_time",{
          "currency":"USDC","kind":"option","start_timestamp":cursor,
          "end_timestamp":end_ms,"count":count,"sorting":"asc","include_old":"true"
        })
        hashes.append(h); page,more=unpack(payload)
        last=None; new=0
        for t in page:
            ts=int(t.get("timestamp",-1))
            key=(ts,str(t.get("trade_id","")),str(t.get("instrument_name","")),str(t.get("amount","")))
            if key not in seen:
                seen.add(key); rows.append(t); new+=1
            last=ts if last is None or ts>last else last
        if not more or not page or last is None or last>=end_ms: break
        nxt=last+1
        if nxt<=cursor and new==0: raise RuntimeError("pagination stalled")
        cursor=nxt
    else:
        raise RuntimeError("pagination limit exceeded")
    return rows,hashes

def expiry_from_name(name):
    m=OPT_RE.match(name or "")
    if not m:return None
    day,mon,yy,strike,side=m.groups()
    return dt.datetime(2000+int(yy),MON[mon],int(day),8,0,tzinfo=dt.timezone.utc),float(strike),side

def thursdays_2025():
    d=dt.date(2025,1,1)
    while d.weekday()!=3:d+=dt.timedelta(days=1)
    while d.year==2025:
        yield d
        d+=dt.timedelta(days=7)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    receipts=[]; selected=[]
    for day in thursdays_2025():
        anchor=dt.datetime.combine(day,dt.time(8,0),tzinfo=dt.timezone.utc)
        end=anchor+dt.timedelta(hours=4)-dt.timedelta(milliseconds=1)
        rows,hashes=fetch_window(ms(anchor),ms(end))
        first_sell={}
        for t in sorted(rows,key=lambda x:(int(x.get("timestamp",-1)),str(x.get("trade_id","")))):
            name=str(t.get("instrument_name",""))
            if not name.startswith("BTC_USDC-"):continue
            if str(t.get("direction","")).lower()!="sell":continue
            try: amount=float(t.get("amount",0))
            except Exception: continue
            if amount<MIN_AMOUNT:continue
            parsed=expiry_from_name(name)
            if not parsed:continue
            exp,strike,side=parsed
            dte=(exp-anchor).total_seconds()/86400
            if not (DTE_MIN<=dte<=DTE_MAX):continue
            if t.get("index_price") is None:continue
            first_sell.setdefault(name,t)

        pairs={}
        for name,t in first_sell.items():
            exp,strike,side=expiry_from_name(name)
            pairs.setdefault((exp,strike),{})[side]=(name,t)

        cands=[]
        for (exp,strike),legs in pairs.items():
            if "C" not in legs or "P" not in legs:continue
            c_name,c=legs["C"]; p_name,p=legs["P"]
            try: idx=(float(c["index_price"])+float(p["index_price"]))/2
            except Exception: continue
            if idx<=0:continue
            dte=(exp-anchor).total_seconds()/86400
            cands.append((abs(dte-TARGET_DTE),exp,abs(math.log(strike/idx)),strike,dte,c_name,c,p_name,p))
        cands.sort(key=lambda z:(z[0],z[1],z[2],z[3]))
        if cands:
            _,exp,_,strike,dte,cname,c,pname,p=cands[0]
            # Metadata is source identity only; no prices retained.
            cm,ch=get("/get_instrument",{"instrument_name":cname})
            pm,ph=get("/get_instrument",{"instrument_name":pname})
            meta_ok=all([
              isinstance(cm,dict),isinstance(pm,dict),
              cm.get("kind")=="option",pm.get("kind")=="option",
              float(cm.get("min_trade_amount") or 0)<=MIN_AMOUNT,
              float(pm.get("min_trade_amount") or 0)<=MIN_AMOUNT,
            ])
            rec={
              "anchor":anchor.isoformat(),"status":"ENTRY_PAIR_FOUND" if meta_ok else "METADATA_FAIL",
              "expiration_timestamp":int(exp.timestamp()*1000),"dte_days":dte,"strike":strike,
              "call_instrument":cname,"put_instrument":pname,
              "call_trade_timestamp":int(c["timestamp"]),"put_trade_timestamp":int(p["timestamp"]),
              "call_amount":float(c["amount"]),"put_amount":float(p["amount"]),
              "call_trade_id":c.get("trade_id"),"put_trade_id":p.get("trade_id"),
              "call_min_trade_amount":cm.get("min_trade_amount"),"put_min_trade_amount":pm.get("min_trade_amount"),
              "trade_payload_sha256":hashes,"call_metadata_sha256":ch,"put_metadata_sha256":ph,
              "prices_retained":False,"pnl_computed":False
            }
            selected.append(rec)
        receipts.append({
          "anchor":anchor.isoformat(),"btc_usdc_rows_in_window":sum(str(t.get("instrument_name","")).startswith("BTC_USDC-") for t in rows),
          "eligible_first_sell_instruments":len(first_sell),"eligible_callput_candidates":len(cands),
          "selected":bool(cands),"raw_payload_sha256":hashes
        })

    valid=[x for x in selected if x["status"]=="ENTRY_PAIR_FOUND"]
    coverage=len(valid)/len(receipts)
    classification="SOURCE_ENTRY_PASS" if len(valid)>=24 else "SOURCE_ENTRY_INSUFFICIENT"
    result={
      "classification":classification,
      "calendar_anchors":len(receipts),"entry_pairs_found":len(valid),"anchor_coverage":coverage,
      "required_floor":24,
      "first_anchor":receipts[0]["anchor"],"last_anchor":receipts[-1]["anchor"],
      "prices_retained":False,"settlement_values_opened":False,"pnl_computed":False,
      "returns_computed":False,"authenticated":False,"orders":False,"wallets":False
    }
    (OUT/"anchor_receipts.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in receipts)+"\n")
    (OUT/"selected_pairs.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True,separators=(",",":")) for x in valid)+"\n")
    (OUT/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
