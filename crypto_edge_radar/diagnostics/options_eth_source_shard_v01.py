from __future__ import annotations
import argparse,datetime as dt,gzip,hashlib,json,math,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path

UTC=dt.timezone.utc; HOST="history.deribit.com"; PATH="/api/v2/public/get_last_trades_by_currency_and_time"
COUNT=1000; MIN_WINDOW_MS=1000; MAX_RETRIES=5

class TransportBlocked(RuntimeError): pass

def req(a,b):
    q=urllib.parse.urlencode({"currency":"ETH","kind":"option","include_old":"true","start_timestamp":a,"end_timestamp":b,"count":COUNT,"sorting":"asc"})
    url=f"https://{HOST}{PATH}?{q}"; r=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-ETH-SourceShard/0.1"})
    last=None; transport=False
    for n in range(1,MAX_RETRIES+1):
        try:
            with urllib.request.urlopen(r,timeout=90) as z: body=z.read()
            o=json.loads(body.decode()); 
            if not isinstance(o,dict) or o.get("error"): raise RuntimeError(str(o.get("error") if isinstance(o,dict) else "non-object"))
            return body,o
        except urllib.error.HTTPError as e: last=e; transport=False
        except (urllib.error.URLError,TimeoutError,OSError) as e: last=e; transport=True
        except (json.JSONDecodeError,RuntimeError) as e: last=e; transport=False
        if n<MAX_RETRIES: time.sleep(min(8,1.5*n))
    if transport: raise TransportBlocked(str(last))
    raise RuntimeError(str(last))

def fetch(a,b,pages):
    body,o=req(a,b); rr=o.get("result") or {}; rows=rr.get("trades")
    if not isinstance(rows,list): raise RuntimeError("missing trades")
    if rr.get("has_more"):
        if b-a<=MIN_WINDOW_MS: raise RuntimeError("unsplittable")
        m=a+(b-a)//2
        return fetch(a,m,pages)+fetch(m+1,b,pages)
    pages.append({"start_ms":a,"end_ms":b,"count":len(rows),"sha256":hashlib.sha256(body).hexdigest()})
    return [x for x in rows if isinstance(x,dict)]

def parse_name(name):
    p=name.split("-")
    if len(p)!=4 or p[0]!="ETH" or p[3] not in {"C","P"}: raise ValueError(name)
    dt.datetime.strptime(p[1].upper(),"%d%b%y")
    s=float(p[2])
    if not math.isfinite(s) or s<=0: raise ValueError(name)

def bounds(month):
    y,m=map(int,month.split("-")); a=dt.datetime(y,m,1,tzinfo=UTC)
    b=dt.datetime(y+1,1,1,tzinfo=UTC) if m==12 else dt.datetime(y,m+1,1,tzinfo=UTC)
    if y!=2024: raise ValueError("only 2024 authorized")
    return a,b

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--month",required=True); ap.add_argument("--out-dir",required=True); x=ap.parse_args()
    a,b=bounds(x.month); amin=int(a.timestamp()*1000); bmax=int(b.timestamp()*1000)
    pages=[]; seen=set(); ids=[]; totals={"rows":0,"duplicates_within_shard":0,"timestamp_violations":0,"missing_structural":0,"instrument_parse_failures":0,"invalid_iv":0,"invalid_index_price":0}
    error=None; transport=None
    try:
        d=a
        while d<b:
            e=min(d+dt.timedelta(days=1),b); rows=fetch(int(d.timestamp()*1000),int(e.timestamp()*1000)-1,pages)
            for row in rows:
                totals["rows"]+=1
                tid=str(row.get("trade_id") or "")
                if not tid: totals["missing_structural"]+=1
                elif tid in seen: totals["duplicates_within_shard"]+=1
                else: seen.add(tid); ids.append(tid)
                try: ts=int(row["timestamp"])
                except Exception: totals["missing_structural"]+=1; continue
                if ts<amin or ts>=bmax: totals["timestamp_violations"]+=1; continue
                name=str(row.get("instrument_name") or "")
                if not name: totals["missing_structural"]+=1; continue
                try: parse_name(name)
                except Exception: totals["instrument_parse_failures"]+=1
                try:
                    v=float(row.get("iv"))
                    if not math.isfinite(v) or v<=0: raise ValueError
                except Exception: totals["invalid_iv"]+=1
                try:
                    v=float(row.get("index_price"))
                    if not math.isfinite(v) or v<=0: raise ValueError
                except Exception: totals["invalid_index_price"]+=1
            d=e
    except TransportBlocked as ex: transport=f"{type(ex).__name__}:{ex}"
    except Exception as ex: error=f"{type(ex).__name__}:{ex}"
    out=Path(x.out_dir); out.mkdir(parents=True,exist_ok=True)
    complete=error is None and transport is None
    receipt={"asset":"ETH","month":x.month,"complete":complete,**totals,"unique_trade_ids":len(seen),"source_error":error,"transport_error":transport,
             "skew_computed":False,"signal_computed":False,"forward_return_computed":False,"pnl_computed":False,"outcome_source_contacted":False,"year_2025_accessed":False}
    (out/f"eth_{x.month}_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    (out/f"eth_{x.month}_pages.json").write_text(json.dumps({"month":x.month,"pages":pages},indent=2,sort_keys=True)+"\n")
    with gzip.open(out/f"eth_{x.month}_trade_ids.txt.gz","wt",encoding="utf-8") as f:
        for tid in sorted(seen): f.write(tid+"\n")
    print(json.dumps(receipt,indent=2))
    return 0 if complete else (12 if transport else 2)
if __name__=="__main__": raise SystemExit(main())
