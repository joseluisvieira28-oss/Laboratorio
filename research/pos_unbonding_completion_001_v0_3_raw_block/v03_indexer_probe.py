#!/usr/bin/env python3
import hashlib, json, os, urllib.parse, urllib.request
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_3_raw_block/INDEXER_AND_SECOND_SOURCE_PROBE_V03.json"
UA="CryptoLab-Unbonding-V03-IndexerProbe/1.0"

CHAINS=[
  {
    "chain":"cosmoshub","lo":19950000,"hi":20050000,
    "indexers":[
      ["publicnode","https://cosmos-rpc.publicnode.com"],
      ["lavenderfive","https://rpc.lavenderfive.com/cosmoshub"],
      ["uquad","https://cosmos.rpc.uquad.org"],
      ["polkachu","https://cosmos-rpc.polkachu.com"]
    ]
  },
  {
    "chain":"osmosis","lo":14950000,"hi":15050000,
    "indexers":[
      ["foundation","https://rpc.osmosis.zone"],
      ["publicnode","https://osmosis-rpc.publicnode.com"],
      ["lavenderfive","https://rpc.lavenderfive.com/osmosis"],
      ["polkachu","https://osmosis-rpc.polkachu.com"]
    ]
  },
  {
    "chain":"kava","lo":9450000,"hi":9550000,
    "indexers":[
      ["publicnode","https://kava-rpc.publicnode.com"],
      ["nodestake","https://rpc.kava.nodestake.org"],
      ["polkachu","https://kava-rpc.polkachu.com"]
    ]
  },
  {
    "chain":"celestia","lo":2450000,"hi":2550000,
    "indexers":[
      ["numia","https://public-celestia-rpc.numia.xyz"],
      ["publicnode","https://celestia-rpc.publicnode.com"],
      ["lavenderfive","https://rpc.lavenderfive.com/celestia"],
      ["kjnodes","https://celestia.rpc.kjnodes.com"],
      ["nodestake","https://rpc.celestia.nodestake.org"]
    ]
  },
  {
    "chain":"dydx","lo":14950000,"hi":15050000,
    "indexers":[
      ["kingnodes","https://dydx-rpc.kingnodes.com"],
      ["publicnode","https://dydx-rpc.publicnode.com"],
      ["lavenderfive","https://rpc.lavenderfive.com/dydx"],
      ["polkachu","https://dydx-rpc.polkachu.com"]
    ]
  }
]

SECOND_SOURCE=[
  {
    "chain":"kava","height":9500000,
    "canonical":["kava_labs","https://rpc.data.kava.io"],
    "candidates":[
      ["nodies_public_archive","https://kava-archival-public.nodies.app"],
      ["nodies_listed","https://lb.nodies.app/v1/ec5ba839f2704606bda278e32892894a"],
      ["autostake","https://kava-mainnet-rpc.autostake.com"],
      ["nodestake","https://rpc.kava.nodestake.org"]
    ]
  },
  {
    "chain":"celestia","height":2500000,
    "canonical":["kjnodes_raw","http://136.243.94.113:26667"],
    "candidates":[
      ["numia","https://public-celestia-rpc.numia.xyz"],
      ["publicnode","https://celestia-rpc.publicnode.com"],
      ["lavenderfive","https://rpc.lavenderfive.com/celestia"],
      ["kjnodes_dns","https://celestia.rpc.kjnodes.com"],
      ["nodestake","https://rpc.celestia.nodestake.org"],
      ["lunar_oasis","https://rpc.lunaroasis.net"]
    ]
  }
]

def get(url,timeout=25):
  req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=timeout) as r:
    raw=r.read()
    return getattr(r,"status",200),raw

def sha(b): return hashlib.sha256(b).hexdigest()
def j(raw): return json.loads(raw.decode("utf-8"))

def tx_search(base,lo,hi,action):
  q=f"message.action='{action}' AND tx.height >= {lo} AND tx.height <= {hi}"
  url=base.rstrip("/")+"/tx_search?"+urllib.parse.urlencode({
    "query":q,"prove":"false","page":"1","per_page":"10","order_by":"asc"
  })
  try:
    st,raw=get(url,35)
    obj=j(raw)
    rr=obj.get("result",{})
    txs=[]
    for x in rr.get("txs") or []:
      txs.append({
        "hash":x.get("hash"),
        "height":x.get("height"),
        "code":((x.get("tx_result") or {}).get("code",0)),
        "event_types":[e.get("type") for e in ((x.get("tx_result") or {}).get("events") or [])]
      })
    return {"http":st,"sha256":sha(raw),"query":q,"total_count":rr.get("total_count"),"txs":txs}
  except Exception as e:
    return {"query":q,"error":type(e).__name__+": "+str(e)}

def block_pair(base,h):
  out={"base":base}
  try:
    bs,braw=get(base.rstrip("/")+f"/block?height={h}")
    rs,rraw=get(base.rstrip("/")+f"/block_results?height={h}")
    bo=j(braw).get("result",{})
    header=((bo.get("block") or {}).get("header") or {})
    rr=j(rraw).get("result",{})
    out.update({
      "block_http":bs,"block_results_http":rs,
      "block_sha256":sha(braw),"block_results_sha256":sha(rraw),
      "height":header.get("height"),"time":header.get("time"),"chain_id":header.get("chain_id"),
      "block_hash":((bo.get("block_id") or {}).get("hash")),"app_hash":header.get("app_hash"),
      "returned_results_height":rr.get("height")
    })
  except Exception as e:
    out["error"]=type(e).__name__+": "+str(e)
  return out

def main():
  receipt={
    "freeze_commit":"93e0c6abff72d1d645c709382d8f06ccc558a34e",
    "scope":"source-only; all tx_search ranges explicitly historical; no market endpoints/outcomes/current-state reads",
    "generated_utc":datetime.now(timezone.utc).isoformat(),
    "indexer_probes":[],
    "second_source_probes":[]
  }

  actions=[
    "/cosmos.staking.v1beta1.MsgUndelegate",
    "undelegate"
  ]
  for spec in CHAINS:
    ce={"chain":spec["chain"],"height_window":[spec["lo"],spec["hi"]],"providers":[]}
    for name,base in spec["indexers"]:
      pe={"provider":name,"base":base,"queries":[]}
      for action in actions:
        pe["queries"].append(tx_search(base,spec["lo"],spec["hi"],action))
      ce["providers"].append(pe)
    receipt["indexer_probes"].append(ce)

  for spec in SECOND_SOURCE:
    cname,cbase=spec["canonical"]
    canon=block_pair(cbase,spec["height"])
    se={"chain":spec["chain"],"height":spec["height"],"canonical_name":cname,"canonical":canon,"candidates":[]}
    for name,base in spec["candidates"]:
      c=block_pair(base,spec["height"])
      c["provider"]=name
      if c.get("block_hash") and canon.get("block_hash"):
        c["block_hash_match"]=c["block_hash"]==canon["block_hash"]
        c["time_match"]=c.get("time")==canon.get("time")
        c["app_hash_match"]=c.get("app_hash")==canon.get("app_hash")
      se["candidates"].append(c)
    receipt["second_source_probes"].append(se)

  os.makedirs(os.path.dirname(OUT),exist_ok=True)
  with open(OUT,"w",encoding="utf-8") as f:
    json.dump(receipt,f,indent=2,sort_keys=True); f.write("\n")
  print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":
  main()
