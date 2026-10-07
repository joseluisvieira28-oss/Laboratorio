#!/usr/bin/env python3
import datetime, hashlib, json, os, urllib.error, urllib.request

TARGET="2023-12-07T02:54:58.930543213Z"
TARGET_TS=datetime.datetime.fromisoformat(TARGET.replace("Z","+00:00")).timestamp()
OUT="research/cosmos_native_emission_param_shock_001_v0_2/SCRT287_EXPLORERS_GURU_EXACT_V40.json"
UA={"User-Agent":"CryptoLab-source-only-explorers-guru-v40/1.0","Accept":"application/json,text/plain,*/*"}

BASES=[
 "https://secret.api.explorers.guru",
 "https://secretnetwork.api.explorers.guru",
 "https://scrt.api.explorers.guru"
]
PATHS=["/api/blocks/{h}","/api/v1/blocks/{h}"]

def get(url,timeout=15):
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

def pts(v):
    s=str(v)
    try:return datetime.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()
    except Exception:
        try:
            x=float(s)
            if x>1e12:x/=1000
            return x
        except Exception:return None

def parse(resp,h):
    try:d=json.loads(resp.get("body",""))
    except Exception:return None
    for x in walk(d):
        if not isinstance(x,dict):continue
        hv=next((x.get(k) for k in ("height","block_height","blockHeight") if x.get(k) is not None),None)
        tv=next((x.get(k) for k in ("time","timestamp","block_time","blockTime","created_at","createdAt") if x.get(k) is not None),None)
        if hv is None or tv is None:continue
        try:hi=int(str(hv).replace(",",""))
        except Exception:continue
        if hi!=h or pts(tv) is None:continue
        hs=next((x.get(k) for k in ("hash","block_hash","blockHash") if x.get(k) is not None),None)
        return {"height":hi,"time":str(tv),"hash":hs}
    return None

seed=11885000
routes=[]
for b in BASES:
    for p in PATHS:
        u=b+p.format(h=seed)
        r=get(u)
        routes.append({"base":b,"path":p,"url":u,"ok":r.get("ok"),"status":r.get("status"),
                       "parsed":parse(r,seed),"sha256":r.get("sha256"),"error":r.get("error"),
                       "body_excerpt":r.get("body","")[:2500]})
winners=[x for x in routes if x.get("parsed")]

broad=[11752974,11800000,11840000,11860000,11870000,11875000,11880000,11885000,11890000,11900000,11920000]
resolutions={}
cert=None
for w in winners:
    b,p=w["base"],w["path"]
    points=[]
    for h in broad:
        r=get(b+p.format(h=h)); z=parse(r,h)
        if z: points.append((h,pts(z["time"]),z["time"]))
    points=sorted(points)
    bracket=None
    for a,c in zip(points,points[1:]):
        if a[1]<TARGET_TS<=c[1]: bracket=(a,c);break
    rec={"points":points,"bracket":bracket}
    if bracket:
        L,R=bracket[0][0],bracket[1][0];err=None
        while L<R:
            m=(L+R)//2;r=get(b+p.format(h=m));z=parse(r,m)
            if not z:
                err={"height":m,"status":r.get("status"),"error":r.get("error"),"body_excerpt":r.get("body","")[:1000]};break
            if pts(z["time"])<TARGET_TS:L=m+1
            else:R=m
        rec["error"]=err
        if err is None:
            H=L;ns=[]
            for h in (H-1,H,H+1):
                r=get(b+p.format(h=h));z=parse(r,h)
                ns.append({"height":h,"parsed":z,"url":r.get("url"),"status":r.get("status"),
                           "sha256":r.get("sha256"),"body":r.get("body","")[:12000]})
            rec["H"]=H;rec["neighbors"]=ns
            if all(x["parsed"] for x in ns) and pts(ns[0]["parsed"]["time"])<TARGET_TS<=pts(ns[1]["parsed"]["time"])<pts(ns[2]["parsed"]["time"]):
                cert={"source":b+p,"H":H,"H_minus_1":ns[0]["parsed"],"H_block":ns[1]["parsed"],
                      "H_plus_1":ns[2]["parsed"],"canonical_T0_height":H+1,
                      "canonical_T0_time":ns[2]["parsed"]["time"]}
    resolutions[b+p]=rec

out={"scope":"SOURCE_ONLY_NO_MARKET_DATA","scientific_rules_changed":False,
     "target_voting_end":TARGET,"routes":routes,"winners":winners,
     "resolutions":resolutions,"certified_candidate":cert,
     "verdict":"H_BOUNDARY_RECOVERED" if cert else "EXPLORERS_GURU_NOT_RESOLVED",
     "tested_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
os.makedirs(os.path.dirname(OUT),exist_ok=True)
with open(OUT,"w",encoding="utf-8") as f:json.dump(out,f,indent=2,ensure_ascii=False)
print(json.dumps({"routes":[(x["url"],x["status"],bool(x["parsed"])) for x in routes],
                  "certified_candidate":cert,"verdict":out["verdict"]},indent=2))
