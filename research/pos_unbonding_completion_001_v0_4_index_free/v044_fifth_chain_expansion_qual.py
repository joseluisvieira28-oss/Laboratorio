#!/usr/bin/env python3
import json, hashlib, os, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_4_index_free/FIFTH_CHAIN_EXPANSION_QUALIFICATION_V044.json"
UA="CryptoLab-Unbonding-V044/1.0"
T0=datetime(2023,1,1,tzinfo=timezone.utc)
T1=datetime(2024,12,31,23,59,59,tzinfo=timezone.utc)

CANDIDATES=[
 {"chain":"terra2","chain_id":"phoenix-1","symbol":"LUNA","sources":[
   ["delight_archive","http://15.204.43.42:26657"],
   ["blockpane_archive","https://pho1-rpc.blockpane.com"],
   ["polkachu","https://terra-rpc.polkachu.com"],
   ["lavenderfive","https://rpc.lavenderfive.com/terra2"]]},
 {"chain":"archway","chain_id":"archway-1","symbol":"ARCH","sources":[
   ["allthatnode_archive","https://archway-mainnet-archive.allthatnode.com:26657"],
   ["foundation","https://rpc.mainnet.archway.io"],
   ["validatrium","https://rpc-archway.mainnet.validatrium.club"],
   ["kjnodes","https://archway.rpc.kjnodes.com"]]},
 {"chain":"coreum","chain_id":"coreum-mainnet-1","symbol":"CORE","sources":[
   ["foundation_archive","https://archive.rpc.mainnet-1.tx.org"],
   ["ecostake","https://rpc-coreum.ecostake.com"],
   ["publicnode","https://coreum-rpc.publicnode.com"],
   ["chainroot","https://coreum-rpc.chainroot.io"]]},
 {"chain":"axelar","chain_id":"axelar-dojo-1","symbol":"AXL","sources":[
   ["imperator","https://rpc-axelar.imperator.co"],
   ["pops","https://axelar-rpc.pops.one"],
   ["lavenderfive","https://rpc.lavenderfive.com/axelar"],
   ["polkachu","https://axelar-rpc.polkachu.com"]]}
]

def get(url, timeout=12):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8","replace")[:800]
        raise RuntimeError(f"HTTP {e.code}: {body}")

def parse_time(s):
    if not s: return None
    return datetime.fromisoformat(s.replace("Z","+00:00"))

def block(base,h=None):
    url=base.rstrip("/")+"/block"+(f"?height={h}" if h is not None else "")
    raw=get(url)
    obj=json.loads(raw.decode())
    if obj.get("error"): raise RuntimeError(json.dumps(obj["error"]))
    r=obj.get("result") or {}
    b=r.get("block") or {}
    hd=b.get("header") or {}
    if not hd.get("height"): raise RuntimeError("no block header")
    return {
      "height":int(hd["height"]),"time":hd.get("time"),"chain_id":hd.get("chain_id"),
      "block_hash":((r.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash"),
      "sha256":hashlib.sha256(raw).hexdigest()
    }

def block_results(base,h):
    url=base.rstrip("/") + f"/block_results?height={h}"
    raw=get(url)
    obj=json.loads(raw.decode())
    if obj.get("error"): raise RuntimeError(json.dumps(obj["error"]))
    r=obj.get("result") or {}
    if int(r.get("height") or 0)!=int(h): raise RuntimeError("wrong results height")
    return {"height":int(h),"sha256":hashlib.sha256(raw).hexdigest()}

def locate_height(base,target):
    latest=block(base)
    lo=1; hi=latest["height"]
    first=block(base,1)
    if parse_time(first["time"]) >= target:
        return first
    if parse_time(latest["time"]) < target:
        return latest
    # archive source must make every probed historical block available.
    while lo < hi:
        mid=(lo+hi)//2
        bm=block(base,mid)
        if parse_time(bm["time"]) < target:
            lo=mid+1
        else:
            hi=mid
    return block(base,lo)

def source_probe(base,anchors,expected_chain):
    out={"base":base,"anchors":{}}
    try:
        for label,h in anchors.items():
            b=block(base,h)
            if b["chain_id"]!=expected_chain: raise RuntimeError(f"wrong chain_id {b['chain_id']}")
            br=block_results(base,h)
            out["anchors"][label]={"block":b,"block_results":br}
        out["status"]="PASS"
    except Exception as e:
        out["status"]="FAIL"; out["error"]=type(e).__name__+": "+str(e)[:1000]
    return out

def reconcile(probes,anchors):
    names=[n for n,p in probes.items() if p.get("status")=="PASS"]
    pairs=[]
    for i in range(len(names)):
      for j in range(i+1,len(names)):
        a,b=names[i],names[j]
        ok=True; details={}
        for label in anchors:
          A=probes[a]["anchors"][label]["block"]; B=probes[b]["anchors"][label]["block"]
          same=(A["height"]==B["height"] and A["time"]==B["time"] and
                A["block_hash"]==B["block_hash"] and A["app_hash"]==B["app_hash"])
          details[label]=same; ok=ok and same
        pairs.append({"a":a,"b":b,"match":ok,"anchors":details})
    return {"successful_sources":len(names),"pairs":pairs,
            "two_source_pass":any(x["match"] for x in pairs)}

def main():
    rec={"amendment_commit":"18b742ed57c3f7f85616ceb2f2744ae64e97aa73",
         "generated_utc":datetime.now(timezone.utc).isoformat(),
         "scope":"source-only; no market values/outcomes; ordered fifth-chain qualification",
         "order":[x["chain"] for x in CANDIDATES],"results":[],"selected":None}
    for spec in CANDIDATES:
        ce={"chain":spec["chain"],"chain_id":spec["chain_id"],"symbol":spec["symbol"],"sources":{}}
        primary_name,primary=spec["sources"][0]
        try:
            start=locate_height(primary,T0)
            end=locate_height(primary,T1)
            # target window can begin at genesis if chain launched after 2023-01-01.
            anchors={"start":start["height"],"end":end["height"]}
            ce["primary_bounds"]={"start":start,"end":end}
            # Require end anchor to be inside 2024, and at least ~365 days of eligible history.
            st=parse_time(start["time"]); et=parse_time(end["time"])
            ce["eligible_days"]=(et-max(st,T0)).total_seconds()/86400.0
            ce["interval_capable"]=bool(et.year==2024 and ce["eligible_days"]>=365)
            for name,base in spec["sources"]:
                ce["sources"][name]=source_probe(base,anchors,spec["chain_id"])
            ce["reconciliation"]=reconcile(ce["sources"],anchors)
            ce["historical_two_source_pass"]=bool(ce["interval_capable"] and ce["reconciliation"]["two_source_pass"])
        except Exception as e:
            ce["primary_error"]=type(e).__name__+": "+str(e)[:1200]
            ce["historical_two_source_pass"]=False
        rec["results"].append(ce)
        if ce["historical_two_source_pass"]:
            rec["selected"]=spec["chain"]
            break
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:
        json.dump(rec,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps(rec,indent=2,sort_keys=True))

if __name__=="__main__": main()
