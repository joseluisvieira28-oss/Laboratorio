#!/usr/bin/env python3
import datetime, hashlib, json, os, urllib.error, urllib.parse, urllib.request

TARGET="2023-12-07T02:54:58.930543213Z"
TARGET_TS=datetime.datetime.fromisoformat(TARGET.replace("Z","+00:00")).timestamp()
OUT="research/cosmos_native_emission_param_shock_001_v0_2/SCRT287_SECRETAPI_CHAINOFSECRETS_V41.json"
UA={"User-Agent":"CryptoLab-source-only-secretapi-v41/1.0","Accept":"application/json,text/plain,*/*"}

ROUTES=[
 ("legacy_rest","https://api.secretapi.io/blocks/{h}"),
 ("legacy_rpc","https://rpc.secretapi.io/block?height={h}"),
 ("legacy_rpc_https_quoted","https://rpc.secretapi.io/block?height=%22{h}%22"),
]

def get(url, timeout=18):
    req=urllib.request.Request(url,headers=UA)
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read()
            return {"ok":True,"status":getattr(r,"status",200),"url":url,
                    "content_type":r.headers.get("content-type",""),
                    "sha256":hashlib.sha256(raw).hexdigest(),
                    "body":raw.decode("utf-8","replace")}
    except urllib.error.HTTPError as e:
        try: raw=e.read()
        except Exception: raw=b""
        return {"ok":False,"status":e.code,"url":url,"error":str(e),
                "content_type":e.headers.get("content-type","") if e.headers else "",
                "sha256":hashlib.sha256(raw).hexdigest() if raw else None,
                "body":raw.decode("utf-8","replace")}
    except Exception as e:
        return {"ok":False,"url":url,"error":repr(e),"body":""}

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def ts(v):
    s=str(v)
    try:return datetime.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()
    except Exception:
        try:
            n=float(s)
            if n>1e12:n/=1000
            return n
        except Exception:return None

def parse(resp,h):
    try:d=json.loads(resp.get("body",""))
    except Exception:return None
    for x in walk(d):
        if not isinstance(x,dict):continue
        # Tendermint / legacy LCD shapes
        header=None
        if isinstance(x.get("header"),dict): header=x["header"]
        elif isinstance(x.get("block"),dict) and isinstance(x["block"].get("header"),dict): header=x["block"]["header"]
        if header:
            hv=header.get("height"); tv=header.get("time")
            try:hi=int(hv)
            except Exception:hi=None
            if hi==h and tv and ts(tv) is not None:
                hs=x.get("hash") or (x.get("block_id") or {}).get("hash")
                return {"height":hi,"time":str(tv),"hash":hs}
        hv=next((x.get(k) for k in ("height","block_height","blockHeight") if x.get(k) is not None),None)
        tv=next((x.get(k) for k in ("time","timestamp","block_time","blockTime") if x.get(k) is not None),None)
        if hv is not None and tv is not None:
            try:hi=int(str(hv).replace(",",""))
            except Exception:continue
            if hi==h and ts(tv) is not None:
                hs=next((x.get(k) for k in ("hash","block_hash","blockHash") if x.get(k) is not None),None)
                return {"height":hi,"time":str(tv),"hash":hs}
    return None

grid_heights=[11752974,11800000,11840000,11880000,11900000,11920000,11950000,12000000]
rows=[]
for name,tpl in ROUTES:
    for h in grid_heights:
        r=get(tpl.format(h=h))
        rows.append({"source":name,"height":h,"url":r.get("url"),"ok":r.get("ok"),"status":r.get("status"),
                     "parsed":parse(r,h),"content_type":r.get("content_type"),"sha256":r.get("sha256"),
                     "error":r.get("error"),"body_excerpt":r.get("body","")[:1800]})

winners={}
for row in rows:
    if row.get("parsed"):
        winners.setdefault(row["source"],[]).append(row)

exact={}
for name,ptsrows in winners.items():
    tpl=dict(ROUTES)[name]
    pts=sorted((r["height"],ts(r["parsed"]["time"]),r["parsed"]["time"]) for r in ptsrows)
    bracket=None
    for a,b in zip(pts,pts[1:]):
        if a[1] < TARGET_TS <= b[1]:
            bracket=(a,b);break
    rec={"points":pts,"bracket":bracket}
    if bracket:
        L,R=bracket[0][0],bracket[1][0];err=None
        while L<R:
            m=(L+R)//2
            rr=get(tpl.format(h=m)); z=parse(rr,m)
            if not z:
                err={"height":m,"status":rr.get("status"),"error":rr.get("error"),"body_excerpt":rr.get("body","")[:800]};break
            if ts(z["time"]) < TARGET_TS:L=m+1
            else:R=m
        rec["error"]=err
        if err is None:
            H=L;ns=[]
            for h in (H-1,H,H+1):
                rr=get(tpl.format(h=h));z=parse(rr,h)
                ns.append({"height":h,"parsed":z,"url":rr.get("url"),"status":rr.get("status"),
                           "sha256":rr.get("sha256"),"body":rr.get("body","")[:10000]})
            rec["H"]=H;rec["neighbors"]=ns
    exact[name]=rec

cert=None
for name,rec in exact.items():
    H=rec.get("H"); ns=rec.get("neighbors") or []
    if H is not None and len(ns)==3 and all(x.get("parsed") for x in ns):
        if ts(ns[0]["parsed"]["time"]) < TARGET_TS <= ts(ns[1]["parsed"]["time"]) < ts(ns[2]["parsed"]["time"]):
            cert={"source":name,"H":H,"H_minus_1":ns[0]["parsed"],"H_block":ns[1]["parsed"],
                  "H_plus_1":ns[2]["parsed"],"canonical_T0_height":H+1,
                  "canonical_T0_time":ns[2]["parsed"]["time"]}
            break

# Wayback CDX: passive historical records only.
cdx=[]
for pattern in [
    "api.secretapi.io/blocks/*",
    "rpc.secretapi.io/block*",
]:
    u="https://web.archive.org/cdx/search/cdx?url="+urllib.parse.quote(pattern,safe="")+"&from=20231201&to=20231215&output=json&filter=statuscode:200&collapse=urlkey&limit=1000"
    r=get(u,25)
    cdx.append({"pattern":pattern,"url":u,"ok":r.get("ok"),"status":r.get("status"),
                "sha256":r.get("sha256"),"error":r.get("error"),"body_excerpt":r.get("body","")[:20000]})

out={"scope":"SOURCE_ONLY_NO_MARKET_DATA","scientific_rules_changed":False,
     "target_voting_end":TARGET,"documented_authority":"Chain of Secrets Secret API legacy REST/RPC",
     "grid":rows,"winners":winners,"exact":exact,"wayback_cdx":cdx,
     "certified_candidate":cert,
     "verdict":"H_BOUNDARY_RECOVERED" if cert else "SECRETAPI_NOT_RESOLVED",
     "tested_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
os.makedirs(os.path.dirname(OUT),exist_ok=True)
with open(OUT,"w",encoding="utf-8") as f:json.dump(out,f,indent=2,ensure_ascii=False)
print(json.dumps({"winner_sources":list(winners.keys()),"certified_candidate":cert,"verdict":out["verdict"]},indent=2))
