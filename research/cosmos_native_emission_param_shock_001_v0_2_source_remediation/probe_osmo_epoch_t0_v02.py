#!/usr/bin/env python3
import json,urllib.request,ssl,concurrent.futures,hashlib
RPC="https://rpc.archive.osmosis.zone"
START=10189799
END=START+6000
UA={"User-Agent":"CryptoLab-OSMO-T0/0.2"}
def get(h):
  url=f"{RPC}/block_results?height={h}"
  try:
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=12,context=ssl.create_default_context()) as r:
      j=json.loads(r.read().decode())
    res=j.get("result") or {}
    evs=(res.get("finalize_block_events") or [])+(res.get("end_block_events") or [])+(res.get("begin_block_events") or [])
    hits=[]
    for e in evs:
      if e.get("type") in ("epoch_start","epoch_end"):
        a={x.get("key"):x.get("value") for x in e.get("attributes") or []}
        hits.append({"type":e.get("type"),"attrs":a})
    return h,hits,None
  except Exception as e:return h,[],f"{type(e).__name__}: {e}"
found=[]
errors=0
for base in range(START,END+1,200):
  hs=list(range(base,min(base+200,END+1)))
  with concurrent.futures.ThreadPoolExecutor(max_workers=32) as ex:
    rows=list(ex.map(get,hs))
  for h,hits,e in rows:
    if e: errors+=1
    for ev in hits:
      if ev["type"]=="epoch_start":
        found.append({"height":h,"event":ev})
  if found: break
receipt={"start":START,"end":END,"errors":errors,"epoch_starts":found[:10]}
if found:
  h=min(x["height"] for x in found)
  def block(k):
    req=urllib.request.Request(f"{RPC}/block?height={k}",headers=UA)
    with urllib.request.urlopen(req,timeout=12,context=ssl.create_default_context()) as r:return json.loads(r.read().decode())["result"]
  receipt["canonical_block"]={k:v for k,v in {
    "height":h,
    "time":block(h)["block"]["header"]["time"],
    "hash":block(h)["block_id"]["hash"],
    "prev_time":block(h-1)["block"]["header"]["time"],
    "prev_hash":block(h-1)["block_id"]["hash"]
  }.items()}
print(json.dumps(receipt,indent=2,sort_keys=True))
open("osmo_epoch_t0_v02.json","w").write(json.dumps(receipt,indent=2,sort_keys=True))
