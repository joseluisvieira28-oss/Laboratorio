#!/usr/bin/env python3
import json, hashlib, math, os, urllib.parse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_4_index_free/BLOCK_INDEX_CAPABILITY_V042_FAST.json"
UA="CryptoLab-Unbonding-V042-BlockIndex-Fast/1.0"

CHAINS=[
  {"chain":"cosmoshub","anchor":20000000,"sources":[
    ["citizenweb3","https://rpc.cosmoshub-4-archive.citizenweb3.com"],
    ["cryptocrew","https://rpc.cosmoshub-main.ccvalidators.com"]]},
  {"chain":"osmosis","anchor":15000000,"sources":[
    ["osmosis","https://rpc.osmosis.zone"],
    ["validatus","https://rpc.archive.osmosis.validatus.com"]]},
  {"chain":"celestia","anchor":2500000,"sources":[
    ["kjnodes","http://136.243.94.113:26667"],
    ["numia","https://public-celestia-rpc.numia.xyz"]]},
  {"chain":"dydx","anchor":15000000,"sources":[
    ["kingnodes","https://dydx-ops-archive-rpc.kingnodes.com"],
    ["polkachu","https://dydx-dao-archive-rpc.polkachu.com"]]}
]

def get(url,timeout=15):
  req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
  try:
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
  except urllib.error.HTTPError as e:
    body=e.read().decode("utf-8","replace")[:1200]
    raise RuntimeError(f"HTTP {e.code}: {body}")

def qurl(base,path,params):
  return base.rstrip("/") + path + "?" + urllib.parse.urlencode(params)

def block_search(base,query,page=1,per_page=100):
  params={"query":json.dumps(query),"page":str(page),"per_page":str(per_page),"order_by":json.dumps("asc")}
  url=qurl(base,"/block_search",params)
  raw=get(url,20); obj=json.loads(raw.decode())
  if obj.get("error"): raise RuntimeError(json.dumps(obj["error"]))
  rr=obj.get("result") or {}
  blocks=[]
  for x in rr.get("blocks") or []:
    h=((x.get("block") or {}).get("header") or {})
    blocks.append({"height":int(h["height"]),"time":h.get("time"),"hash":((x.get("block_id") or {}).get("hash"))})
  return {"url":url,"sha256":hashlib.sha256(raw).hexdigest(),"total_count":int(rr.get("total_count") or 0),"blocks":blocks}

def paginate(base,query):
  first=block_search(base,query,1,100)
  total=first["total_count"]; out=list(first["blocks"]); pages=[{"page":1,"sha256":first["sha256"],"returned":len(first["blocks"])}]
  npages=math.ceil(total/100)
  if npages>1:
    def one(p):
      r=block_search(base,query,p,100)
      return p,r
    with ThreadPoolExecutor(max_workers=min(12,npages-1)) as ex:
      futs=[ex.submit(one,p) for p in range(2,npages+1)]
      tmp=[]
      for fut in as_completed(futs):
        p,r=fut.result(); tmp.append((p,r))
    for p,r in sorted(tmp):
      out.extend(r["blocks"]); pages.append({"page":p,"sha256":r["sha256"],"returned":len(r["blocks"])})
  return {"query":query,"total_count":total,"blocks":out,"pages":pages}

def block_results(base,h):
  url=base.rstrip("/") + f"/block_results?height={h}"
  raw=get(url,15); obj=json.loads(raw.decode())
  if obj.get("error"): raise RuntimeError(json.dumps(obj["error"]))
  rr=obj.get("result") or {}
  ev=[]
  for phase in ("begin_block_events","end_block_events","finalize_block_events"):
    for e in rr.get(phase) or []:
      if e.get("type")=="complete_unbonding":
        ev.append({"phase":phase,"attributes":e.get("attributes") or []})
  return {"height":h,"events":ev,"sha256":hashlib.sha256(raw).hexdigest()}

def audit512(base,anchor):
  raw_events=[]; failures=[]
  def one(h):
    try:
      return ("ok",block_results(base,h))
    except Exception as e:
      return ("err",{"height":h,"error":type(e).__name__+": "+str(e)})
  with ThreadPoolExecutor(max_workers=32) as ex:
    futs={ex.submit(one,h):h for h in range(anchor,anchor+512)}
    for fut in as_completed(futs):
      kind,val=fut.result()
      if kind=="ok":
        if val["events"]: raw_events.append({"height":val["height"],"events":val["events"],"sha256":val["sha256"]})
      else: failures.append(val)
  raw_events.sort(key=lambda x:x["height"]); failures.sort(key=lambda x:x["height"])
  return raw_events,failures

def main():
  rec={"amendment_commit":"6b7debcd7797cbbc1005c44c3762fc7202a4b6a2",
       "execution_note":"same frozen queries/windows as V0.4.2; HTTP concurrency only",
       "generated_utc":datetime.now(timezone.utc).isoformat(),"chains":[]}
  for spec in CHAINS:
    lo=spec["anchor"]-250000; hi=spec["anchor"]+250000
    ce={"chain":spec["chain"],"anchor":spec["anchor"],"window":[lo,hi],"sources":{}}
    for name,base in spec["sources"]:
      se={"base":base}
      try: se["exact_anchor"]=paginate(base,f"block.height = {spec['anchor']}")
      except Exception as e: se["exact_anchor_error"]=type(e).__name__+": "+str(e)
      try: se["completion_index"]=paginate(base,f"complete_unbonding.amount EXISTS AND block.height >= {lo} AND block.height <= {hi}")
      except Exception as e: se["completion_index_error"]=type(e).__name__+": "+str(e)
      ce["sources"][name]=se
    pname,pbase=spec["sources"][0]
    raw_events,failures=audit512(pbase,spec["anchor"])
    ce["raw_audit"]={"provider":pname,"range":[spec["anchor"],spec["anchor"]+511],"event_blocks":raw_events,"failures":failures}
    good=[]
    for n,s in ce["sources"].items():
      ci=s.get("completion_index")
      if ci is not None: good.append((n,[b["height"] for b in ci["blocks"]]))
    ce["reconciliation"]={"successful_indexes":len(good),"exact_height_set_match":False}
    if len(good)>=2:
      ce["reconciliation"]["exact_height_set_match"]=good[0][1]==good[1][1]
      ce["reconciliation"]["counts"]={n:len(v) for n,v in good}
    indexed=set(good[0][1]) if good else set()
    ce["raw_audit"]["all_raw_event_heights_in_primary_index"]=all(x["height"] in indexed for x in raw_events)
    rec["chains"].append(ce)
  os.makedirs(os.path.dirname(OUT),exist_ok=True)
  with open(OUT,"w",encoding="utf-8") as f:
    json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
  print(json.dumps(rec,indent=2,sort_keys=True))

if __name__=="__main__": main()
