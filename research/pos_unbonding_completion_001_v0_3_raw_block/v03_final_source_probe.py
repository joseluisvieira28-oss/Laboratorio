#!/usr/bin/env python3
import hashlib, json, os, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_3_raw_block/FINAL_SOURCE_CAPABILITY_PROBE_V03.json"
UA="CryptoLab-Unbonding-V03-FinalSourceProbe/1.0"

REST_PROBES=[
  {"chain":"cosmoshub","lo":19950000,"hi":20050000,"bases":[
    ["cryptocrew_archive","https://rest.cosmoshub-main.ccvalidators.com"],
    ["lavenderfive","https://rest.lavenderfive.com/cosmoshub"],
    ["staketab","https://cosmos-rest.staketab.org"]]},
  {"chain":"osmosis","lo":14950000,"hi":15050000,"bases":[
    ["foundation","https://lcd.osmosis.zone"],
    ["polkachu","https://osmosis-api.polkachu.com"],
    ["publicnode","https://osmosis-rest.publicnode.com"]]},
  {"chain":"kava","lo":9450000,"hi":9550000,"bases":[
    ["kava_labs","https://api.data.kava.io"],
    ["polkachu","https://kava-api.polkachu.com"],
    ["publicnode","https://kava-rest.publicnode.com"]]},
  {"chain":"celestia","lo":2450000,"hi":2550000,"bases":[
    ["numia","https://public-celestia-lcd.numia.xyz"],
    ["lavenderfive","https://rest.lavenderfive.com/celestia"],
    ["publicnode","https://celestia-rest.publicnode.com"]]},
  {"chain":"dydx","lo":14950000,"hi":15050000,"bases":[
    ["kingnodes","https://dydx-rest.kingnodes.com"],
    ["lavenderfive","https://rest.lavenderfive.com/dydx"],
    ["polkachu","https://dydx-api.polkachu.com"]]}
]

KAVA_CANON={"name":"kava_labs","base":"https://rpc.data.kava.io","height":9500000}
KAVA_CANDIDATES=[
  ["publicnode","https://kava-rpc.publicnode.com"],
  ["polkachu","https://kava-rpc.polkachu.com"],
  ["pocket","https://kava.api.pocket.network"],
  ["jjozzie","https://rpc.jjozzietech.com.au:9443/kava/tendermint/"],
  ["nodies_public_archive","https://kava-archival-public.nodies.app"],
  ["nodies_listed","https://lb.nodies.app/v1/ec5ba839f2704606bda278e32892894a"]
]

def errbody(e):
  try:return e.read().decode("utf-8","replace")[:1600]
  except:return ""

def http(req,timeout=35):
  try:
    with urllib.request.urlopen(req,timeout=timeout) as r:
      return getattr(r,"status",200),r.read()
  except urllib.error.HTTPError as e:
    raise RuntimeError(f"HTTP {e.code}: {errbody(e)}")

def get(url,timeout=35):
  return http(urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"}),timeout)

def post(base,method,params,timeout=35):
  raw=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
  req=urllib.request.Request(base,data=raw,method="POST",headers={"User-Agent":UA,"Accept":"application/json","Content-Type":"application/json"})
  return http(req,timeout)

def sha(b):return hashlib.sha256(b).hexdigest()
def parse(b):return json.loads(b.decode("utf-8"))

def rest_txs(base,lo,hi):
  # Cosmos gRPC-gateway transaction endpoint. Keep all event filters explicitly historical.
  params=[
    ("events","message.action='begin_unbonding'"),
    ("events",f"tx.height>={lo}"),
    ("events",f"tx.height<={hi}"),
    ("pagination.limit","5"),
    ("order_by","ORDER_BY_ASC")
  ]
  url=base.rstrip("/")+"/cosmos/tx/v1beta1/txs?"+urllib.parse.urlencode(params)
  out={"url":url}
  try:
    st,raw=get(url,45); obj=parse(raw)
    txrs=obj.get("tx_responses") or []
    out.update({
      "http":st,"sha256":sha(raw),
      "tx_count":len(txrs),
      "pagination_total":((obj.get("pagination") or {}).get("total")),
      "sample":[{"height":x.get("height"),"txhash":x.get("txhash"),"code":x.get("code"),"timestamp":x.get("timestamp")} for x in txrs[:5]]
    })
  except Exception as e:
    out["error"]=type(e).__name__+": "+str(e)
  return out

def block_summary(raw):
  obj=parse(raw); r=obj.get("result",{})
  # If a provider returned an error envelope, preserve it explicitly.
  if obj.get("error"):
    return {"rpc_error":obj.get("error")}
  b=r.get("block") or {}; h=b.get("header") or {}
  return {"height":h.get("height"),"time":h.get("time"),"chain_id":h.get("chain_id"),
          "block_hash":((r.get("block_id") or {}).get("hash")),"app_hash":h.get("app_hash")}

def results_summary(raw):
  obj=parse(raw)
  if obj.get("error"): return {"rpc_error":obj.get("error")}
  r=obj.get("result") or {}
  return {"height":r.get("height")}

def pair_get(base,h):
  st1,b=get(base.rstrip("/") + f"/block?height={h}")
  st2,r=get(base.rstrip("/") + f"/block_results?height={h}")
  out=block_summary(b); out.update({"transport":"GET","block_http":st1,"results_http":st2,
    "block_sha256":sha(b),"results_sha256":sha(r),"results":results_summary(r)})
  return out

def pair_post(base,h):
  st1,b=post(base,"block",{"height":str(h)})
  st2,r=post(base,"block_results",{"height":str(h)})
  out=block_summary(b); out.update({"transport":"JSON_RPC_POST","block_http":st1,"results_http":st2,
    "block_sha256":sha(b),"results_sha256":sha(r),"results":results_summary(r)})
  return out

def pair(base,h):
  out={"base":base,"attempts":[]}
  for mode in ("GET","POST"):
    try:
      got=pair_get(base,h) if mode=="GET" else pair_post(base,h)
      if got.get("block_hash") and got.get("height"):
        out.update(got); return out
      out["attempts"].append({"transport":mode,"noncanonical_response":got})
    except Exception as e:
      out["attempts"].append({"transport":mode,"error":type(e).__name__+": "+str(e)})
  out["error"]="no canonical historical block response"
  return out

def main():
  receipt={"freeze_commit":"93e0c6abff72d1d645c709382d8f06ccc558a34e",
    "scope":"source only; bounded historical tx enumeration and fixed historical block-store tests; no market data/current state",
    "generated_utc":datetime.now(timezone.utc).isoformat(),
    "rest_tx_enumeration":[],"kava_second_source":{}}

  for c in REST_PROBES:
    ce={"chain":c["chain"],"height_window":[c["lo"],c["hi"]],"providers":[]}
    for name,base in c["bases"]:
      ce["providers"].append({"provider":name,"base":base,"result":rest_txs(base,c["lo"],c["hi"])})
    receipt["rest_tx_enumeration"].append(ce)

  canon=pair(KAVA_CANON["base"],KAVA_CANON["height"])
  k={"height":KAVA_CANON["height"],"canonical":{"provider":KAVA_CANON["name"],**canon},"candidates":[]}
  for name,base in KAVA_CANDIDATES:
    c=pair(base,KAVA_CANON["height"]); c["provider"]=name
    if c.get("block_hash") and canon.get("block_hash"):
      c["block_hash_match"]=c["block_hash"]==canon["block_hash"]
      c["time_match"]=c.get("time")==canon.get("time")
      c["app_hash_match"]=c.get("app_hash")==canon.get("app_hash")
      c["canonical_match"]=bool(c["block_hash_match"] and c["time_match"] and c["app_hash_match"])
    k["candidates"].append(c)
  receipt["kava_second_source"]=k

  os.makedirs(os.path.dirname(OUT),exist_ok=True)
  with open(OUT,"w",encoding="utf-8") as f:
    json.dump(receipt,f,indent=2,sort_keys=True);f.write("\n")
  print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":main()
