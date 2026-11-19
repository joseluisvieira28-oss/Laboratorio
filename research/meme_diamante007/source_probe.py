#!/usr/bin/env python3
"""No-key public source feasibility. NEVER calls transaction execution endpoints."""
import datetime as dt
import hashlib
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA="CryptoLab-MEME007-ReadOnly-SourceFeasibility/0.1"
SEED_SHA="39ee74fb7521ca699b7e3bbbb83b37fcd133ac05fe8ee2349c79c360043889e4"

def utc():return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")

def get(url,timeout=28):
    start=utc();t0=time.monotonic();status=None;err=None;body=None;data=None
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"},method="GET")
        with urllib.request.urlopen(req,timeout=timeout) as r:
            status=r.status
            body=r.read(1_500_000)
        data=json.loads(body)
    except urllib.error.HTTPError as exc:
        status=exc.code;err="HTTP_"+str(exc.code)
    except (OSError,TimeoutError,UnicodeError,ValueError) as exc:
        err=type(exc).__name__+":"+str(exc)[:160]
    return data,dict(url=url,requested_at=start,received_at=utc(),
        http_status=status,error=err,response_bytes=len(body) if body is not None else None,
        response_sha256=hashlib.sha256(body).hexdigest() if body is not None else None,
        elapsed_ms=round(1000*(time.monotonic()-t0)))

def cohort(path):
    raw=pathlib.Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SEED_SHA:
        raise RuntimeError("SOURCE_INTEGRITY_BLOCKED")
    snapshot=json.loads(raw)
    rows=[x for x in snapshot.get("selection",[]) if (x.get("screen") or {}).get("status")=="SCREEN_PASS_ONLY"]
    if len(rows)!=6:raise RuntimeError("NOT_EXACT_SIX")
    return [dict(id=x["coingecko_id"],mint=x["mint"],pool=x["pair"]["pair_address"]) for x in rows]

def trades_schema(data):
    rows=data.get("data") if isinstance(data,dict) else None
    if not isinstance(rows,list):return dict(is_trade_array=False)
    dates=[];keycounts={};missing=0
    for x in rows:
        a=x.get("attributes") or {}
        if not isinstance(a,dict):missing+=1;continue
        for k in a:keycounts[k]=keycounts.get(k,0)+1
        for field in ("block_timestamp","timestamp","block_time"):
            if a.get(field):
                dates.append(str(a[field]))
                break
    dates.sort()
    return dict(is_trade_array=True,count=len(rows),
        oldest_trade_time=dates[0] if dates else None,
        newest_trade_time=dates[-1] if dates else None,
        detected_attribute_fields=keycounts,
        missing_attributes=missing,
        max_trades_limited_to_recent_24h=True,
        full_2026_october_history_available=False)

def index_schema(data):
    if not isinstance(data,(dict,list)):return dict(valid_json=False)
    d={"valid_json":True,"json_type":type(data).__name__}
    if isinstance(data,list):
        d["items"]=len(data)
        d["keys_first_row"]=sorted(data[0]) if data and isinstance(data[0],dict) else []
    else:
        d["top_keys"]=sorted(data)
        for k,v in data.items():
            if isinstance(v,list):d["list_"+k+"_count"]=len(v)
    return d

def main(seed):
    coins=cohort(seed)
    sources=[]
    indexes=[
        ("solarchive_oct23","https://data.solarchive.org/txs/2026-10-23/index.json"),
        ("solarchive_nov14","https://data.solarchive.org/txs/2026-11-14/index.json"),
        ("solarchive_dataset_root","https://data.solarchive.org/txs/index.json"),
        ("huggingface_solarchive_oct23","https://huggingface.co/api/datasets/solarchive/solarchive/tree/main/txs/2026-10-23"),
        ("dune_public_no_key","https://api.dune.com/api/v1/query/9130074/results")
    ]
    for name,url in indexes:
        d,r=get(url)
        sources.append(dict(source=name,receipt=r,shape=index_schema(d)))
        time.sleep(.7)
    for coin in coins:
        url="https://api.geckoterminal.com/api/v2/networks/solana/pools/"+urllib.parse.quote(coin["pool"],safe="")+"/trades"
        d,r=get(url)
        sources.append(dict(source="geckoterminal_recent_trades",
            coin_id=coin["id"],mint=coin["mint"],pool=coin["pool"],
            receipt=r,shape=trades_schema(d)))
        time.sleep(2)
    out=dict(protocol="MEME007-v0.1",tested_at=utc(),
        six_mints=[dict(id=x["id"],mint=x["mint"],pool=x["pool"]) for x in coins],
        sources=sources,actual_october_swaps_reconstructed=0,
        full_original_historical_signals_settled=0,
        note="Schema/source availability probe only; trade reads are current, not October historical; no trading")
    path=pathlib.Path("meme007-source-evidence")
    path.mkdir(exist_ok=True)
    blob=json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True).encode()
    (path/"source_probe.json").write_bytes(blob)
    (path/"source_probe.sha256").write_text(hashlib.sha256(blob).hexdigest()+"  source_probe.json\n")
    compact=dict(probe_sha256=hashlib.sha256(blob).hexdigest(),
                 sources=[dict(source=x["source"],coin_id=x.get("coin_id"),
                    http_status=x["receipt"]["http_status"],error=x["receipt"]["error"],
                    shape=x["shape"]) for x in sources],orders=0)
    print("MEME007_SOURCE_RESULT="+json.dumps(compact,sort_keys=True))
    return out

if __name__=="__main__":main(sys.argv[1])
