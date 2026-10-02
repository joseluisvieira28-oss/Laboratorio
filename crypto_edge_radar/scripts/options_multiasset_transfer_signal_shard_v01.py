#!/usr/bin/env python3
"""Frozen source-only monthly signal builder for OPTIONS multi-asset transfer V0.1."""

from __future__ import annotations
import argparse, datetime as dt, hashlib, json, math, statistics, time
import urllib.error, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

UTC=dt.timezone.utc
HOST="history.deribit.com"
PATH="/api/v2/public/get_last_trades_by_currency_and_time"
COUNT=1000
MIN_WINDOW_MS=1000
MAX_RETRIES=5
MIN_DTE=30
MAX_DTE=120
CALL_MIN=1.05
CALL_MAX=1.20
PUT_MIN=0.80
PUT_MAX=0.95
MIN_SIDE=5
ROUTE={"ETH":"ETH","SOL":"USDC","XRP":"USDC"}
PREFIX={"ETH":"ETH-","SOL":"SOL_USDC-","XRP":"XRP_USDC-"}

class TransportBlocked(RuntimeError): pass

def month_bounds(month:str):
    y,m=map(int,month.split("-"))
    a=dt.datetime(y,m,1,tzinfo=UTC)
    b=dt.datetime(y+1,1,1,tzinfo=UTC) if m==12 else dt.datetime(y,m+1,1,tzinfo=UTC)
    return a,b

def parse_name(asset:str,name:str):
    p=name.split("-")
    if len(p)!=4 or p[3] not in {"C","P"}: raise ValueError(name)
    if asset=="ETH" and p[0]!="ETH": raise ValueError(name)
    if asset in {"SOL","XRP"} and p[0]!=f"{asset}_USDC": raise ValueError(name)
    expiry=dt.datetime.strptime(p[1].upper(),"%d%b%y").date()
    tok=p[2]
    if asset=="XRP" and tok.count("d")==1: tok=tok.replace("d",".")
    strike=float(tok)
    if not math.isfinite(strike) or strike<=0: raise ValueError(name)
    return expiry,strike,p[3]

def request_json(url:str):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Options-MultiAsset-Transfer/0.1"})
    last=None; transport=False
    for n in range(1,MAX_RETRIES+1):
        try:
            with urllib.request.urlopen(req,timeout=90) as r: body=r.read()
            obj=json.loads(body.decode("utf-8"))
            if not isinstance(obj,dict) or obj.get("error"):
                raise RuntimeError(str(obj.get("error") if isinstance(obj,dict) else "non-object"))
            return body,obj
        except urllib.error.HTTPError as e:
            last=e; transport=False
        except (urllib.error.URLError,TimeoutError,OSError) as e:
            last=e; transport=True
        except (json.JSONDecodeError,RuntimeError) as e:
            last=e; transport=False
        if n<MAX_RETRIES: time.sleep(min(8.0,1.5*n))
    if transport: raise TransportBlocked(str(last))
    raise RuntimeError(str(last))

def url(asset:str,a:int,b:int):
    q=urllib.parse.urlencode({
      "currency":ROUTE[asset],"kind":"option","include_old":"true",
      "start_timestamp":a,"end_timestamp":b,"count":COUNT,"sorting":"asc"})
    return f"https://{HOST}{PATH}?{q}"

def fetch(asset:str,a:int,b:int,pages:list[dict[str,Any]]):
    body,obj=request_json(url(asset,a,b))
    result=obj.get("result")
    if not isinstance(result,dict) or not isinstance(result.get("trades"),list):
        raise RuntimeError("invalid Deribit result")
    rows=result["trades"]
    if result.get("has_more"):
        if b-a<=MIN_WINDOW_MS: raise RuntimeError("unsplittable source window")
        m=a+(b-a)//2
        return fetch(asset,a,m,pages)+fetch(asset,m+1,b,pages)
    pages.append({"start_ms":a,"end_ms":b,"count":len(rows),"sha256":hashlib.sha256(body).hexdigest()})
    return [r for r in rows if isinstance(r,dict)]

def day_windows(a:dt.datetime,b:dt.datetime):
    cur=a
    while cur<b:
        nxt=min(cur+dt.timedelta(days=1),b)
        yield int(cur.timestamp()*1000),int(nxt.timestamp()*1000)-1
        cur=nxt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--asset",required=True,choices=["ETH","SOL","XRP"])
    ap.add_argument("--month",required=True)
    ap.add_argument("--out-dir",required=True)
    x=ap.parse_args()
    asset=x.asset; a,b=month_bounds(x.month)
    if a.year not in {2024,2025}: raise RuntimeError("only frozen 2024/2025 windows supported")
    if b>dt.datetime(2026,1,1,tzinfo=UTC): raise RuntimeError("2026 access blocked")

    inst=defaultdict(lambda: defaultdict(list))
    sides={}
    seen=set()
    pages=[]
    totals=defaultdict(int)
    transport_error=None; source_error=None
    try:
        for wa,wb in day_windows(a,b):
            for row in fetch(asset,wa,wb,pages):
                totals["source_rows"]+=1
                name=str(row.get("instrument_name") or "")
                if not name.startswith(PREFIX[asset]):
                    totals["non_target_rows_filtered"]+=1
                    continue
                totals["target_rows"]+=1
                tid=str(row.get("trade_id") or "")
                if not tid:
                    totals["missing_structural"]+=1
                elif tid in seen:
                    totals["duplicate_trade_ids"]+=1
                else:
                    seen.add(tid)
                try: ts=int(row["timestamp"])
                except Exception:
                    totals["missing_structural"]+=1; continue
                t=dt.datetime.fromtimestamp(ts/1000,tz=UTC)
                if not (a<=t<b):
                    totals["timestamp_violations"]+=1; continue
                try: expiry,strike,side=parse_name(asset,name)
                except Exception:
                    totals["parse_failures"]+=1; continue
                try:
                    iv=float(row.get("iv"))
                    if not math.isfinite(iv) or iv<=0: raise ValueError
                except Exception:
                    totals["invalid_iv"]+=1; continue
                try:
                    index=float(row.get("index_price"))
                    if not math.isfinite(index) or index<=0: raise ValueError
                except Exception:
                    totals["invalid_index"]+=1; continue
                dte=(expiry-t.date()).days
                if not (MIN_DTE<=dte<=MAX_DTE):
                    totals["dte_rejected"]+=1; continue
                moneyness=strike/index
                ok=(side=="C" and CALL_MIN<=moneyness<=CALL_MAX) or (side=="P" and PUT_MIN<=moneyness<=PUT_MAX)
                if not ok:
                    totals["moneyness_rejected"]+=1; continue
                day=t.date().isoformat()
                inst[day][name].append(iv)
                sides[name]=side
                totals["eligible_rows"]+=1
    except TransportBlocked as e:
        transport_error=f"{type(e).__name__}:{e}"
    except Exception as e:
        source_error=f"{type(e).__name__}:{e}"

    signals=[]
    cur=a.date()
    while cur<b.date():
        calls=[]; puts=[]
        for name,vals in inst.get(cur.isoformat(),{}).items():
            med=float(statistics.median(vals))
            (calls if sides[name]=="C" else puts).append(med)
        valid=len(calls)>=MIN_SIDE and len(puts)>=MIN_SIDE
        signals.append({
          "date":cur.isoformat(),"distinct_calls":len(calls),"distinct_puts":len(puts),"valid":valid,
          "call_iv":float(statistics.median(calls)) if valid else None,
          "put_iv":float(statistics.median(puts)) if valid else None,
          "skew":float(statistics.median(calls)-statistics.median(puts)) if valid else None})
        cur+=dt.timedelta(days=1)

    complete=transport_error is None and source_error is None
    structural_ok=(totals["missing_structural"]==0 and totals["duplicate_trade_ids"]==0 and totals["timestamp_violations"]==0 and totals["parse_failures"]==0)
    status="PASS" if complete and structural_ok else ("BLOCKED_TRANSPORT" if transport_error else "FAIL_DATA")
    out=Path(x.out_dir); out.mkdir(parents=True,exist_ok=True)
    receipt={
      "asset":asset,"month":x.month,"status":status,"request_currency":ROUTE[asset],"target_prefix":PREFIX[asset],
      "source_complete":complete,"structural_ok":structural_ok,"unique_trade_ids":len(seen),
      **dict(totals),"transport_error":transport_error,"source_error":source_error,
      "valid_signal_days":sum(1 for r in signals if r["valid"]),
      "skew_values_computed":True,"forward_returns_computed":False,"pnl_computed":False,"outcome_source_contacted":False,
      "year_2026_accessed":False}
    (out/f"{asset.lower()}_{x.month}_signal.json").write_text(json.dumps({"asset":asset,"month":x.month,"signals":signals},indent=2,sort_keys=True)+"\n")
    (out/f"{asset.lower()}_{x.month}_source_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    (out/f"{asset.lower()}_{x.month}_page_hash_manifest.json").write_text(json.dumps({"asset":asset,"month":x.month,"pages":pages},indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if status=="PASS" else (12 if status=="BLOCKED_TRANSPORT" else 2)

if __name__=="__main__": raise SystemExit(main())
