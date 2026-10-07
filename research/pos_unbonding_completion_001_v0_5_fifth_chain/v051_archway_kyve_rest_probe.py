#!/usr/bin/env python3
import json, hashlib, gzip, urllib.request, urllib.error, os
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_5_fifth_chain/ARCHWAY_KYVE_REST_QUALIFICATION_V051.json"
UA="CryptoLab-Unbonding-V051-KYVE/1.0"
H=3554500
KYVE="https://api.kyve.network"
POOL=2

REST_SOURCES=[
 ("cosmowiz_archive_rest","http://148.251.124.58:1317"),
 ("allthatnode_archive_rest","https://archway-mainnet-archive.allthatnode.com:1317"),
 ("foundation_rest","https://api.mainnet.archway.io"),
]
RPC_SOURCES=[
 ("cosmowiz_archive_rpc_guess","http://148.251.124.58:26657"),
 ("allthatnode_archive_rpc","https://archway-mainnet-archive.allthatnode.com:26657")
]

def get(url,timeout=30):
  req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
  try:
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
  except urllib.error.HTTPError as e:
    body=e.read().decode("utf-8","replace")[:1200]
    raise RuntimeError(f"HTTP {e.code}: {body}")

def storage_url(pid,sid):
  if pid in ("1","2","4"):return "https://arweave.net/"+sid
  if pid=="3":return "https://storage.kyve.network/"+sid
  raise RuntimeError("unknown storage provider "+pid)

def canonical_header(hd):
  keys=["chain_id","height","time","last_block_id","last_commit_hash","data_hash","validators_hash",
        "next_validators_hash","consensus_hash","app_hash","last_results_hash","evidence_hash","proposer_address"]
  return {k:hd.get(k) for k in keys}

def kyve_block():
  pool=json.loads(get(f"{KYVE}/kyve/query/v1beta1/pool/{POOL}").decode())
  p=pool["pool"]["data"]; start=int(p["start_key"]); current=int(p["current_key"])
  if not (start<=H<=current):raise RuntimeError(f"height outside KYVE pool [{start},{current}]")
  index=H-start
  meta_raw=get(f"{KYVE}/kyve/v1/bundles/{POOL}?index={index}")
  meta=json.loads(meta_raw.decode()); bundles=meta.get("finalized_bundles") or []
  if len(bundles)!=1:raise RuntimeError(f"expected 1 bundle, got {len(bundles)}")
  b=bundles[0]; raw=get(storage_url(str(b["storage_provider_id"]),b["storage_id"]),90)
  found=hashlib.sha256(raw).hexdigest()
  if found.lower()!=str(b["data_hash"]).lower():raise RuntimeError(f"bundle checksum mismatch expected={b['data_hash']} found={found}")
  data=gzip.decompress(raw) if str(b.get("compression_id"))=="1" else raw
  items=json.loads(data.decode())
  item=next((x for x in items if int(x["key"])==H),None)
  if item is None:raise RuntimeError("height not found in verified bundle")
  v=item["value"]
  # Tendermint runtime historically nests block response under value.block.block.
  candidates=[]
  if isinstance(v,dict):
    candidates.append(v)
    if isinstance(v.get("block"),dict):
      candidates.append(v["block"])
      if isinstance(v["block"].get("block"),dict):candidates.append(v["block"]["block"])
  block=None
  for c in candidates:
    if isinstance(c,dict) and isinstance(c.get("header"),dict) and str(c["header"].get("height"))==str(H):
      block=c;break
  if block is None:
    raise RuntimeError("verified bundle item found but block header nesting not recognized: keys="+str(list(v.keys()) if isinstance(v,dict) else type(v)))
  return {
    "pool":{"runtime":p.get("runtime"),"start_key":start,"current_key":current,"total_bundles":p.get("total_bundles")},
    "bundle":{"id":b.get("id"),"from_key":b.get("from_key"),"to_key":b.get("to_key"),"storage_id":b.get("storage_id"),
              "storage_provider_id":b.get("storage_provider_id"),"compression_id":b.get("compression_id"),
              "data_hash":b.get("data_hash"),"download_sha256":found,"metadata_sha256":hashlib.sha256(meta_raw).hexdigest(),
              "compressed_bytes":len(raw),"decompressed_bytes":len(data)},
    "header":canonical_header(block["header"]),
    "header_json_sha256":hashlib.sha256(json.dumps(block["header"],sort_keys=True,separators=(",",":")).encode()).hexdigest()
  }

def rest_block(name,base):
  out={"provider":name,"base":base,"transport":"REST"}
  try:
    raw=get(base.rstrip("/")+f"/cosmos/base/tendermint/v1beta1/blocks/{H}")
    o=json.loads(raw.decode())
    block=o.get("block") or {}; hd=block.get("header") or {}
    if str(hd.get("height"))!=str(H):raise RuntimeError("no expected historical block")
    out.update({"status":"PASS","block_id_hash":((o.get("block_id") or {}).get("hash")),
                "header":canonical_header(hd),"response_sha256":hashlib.sha256(raw).hexdigest()})
  except Exception as e:out.update({"status":"FAIL","error":type(e).__name__+": "+str(e)})
  return out

def rpc_block(name,base):
  out={"provider":name,"base":base,"transport":"RPC"}
  try:
    raw=get(base.rstrip("/")+f"/block?height={H}")
    o=json.loads(raw.decode())
    if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
    r=o.get("result") or {}; hd=((r.get("block") or {}).get("header") or {})
    if str(hd.get("height"))!=str(H):raise RuntimeError("no expected historical block")
    out.update({"status":"PASS","block_id_hash":((r.get("block_id") or {}).get("hash")),
                "header":canonical_header(hd),"response_sha256":hashlib.sha256(raw).hexdigest()})
  except Exception as e:out.update({"status":"FAIL","error":type(e).__name__+": "+str(e)})
  return out

def main():
  rec={"amendment_commit":"c5e4529f5ca32b5987583992c358bc3f08fc8522","height":H,
       "generated_utc":datetime.now(timezone.utc).isoformat(),"kyve":{},"independent_sources":[]}
  try:
    rec["kyve"]=kyve_block();rec["kyve"]["status"]="PASS"
  except Exception as e:
    rec["kyve"]={"status":"FAIL","error":type(e).__name__+": "+str(e)}
  for n,b in REST_SOURCES:rec["independent_sources"].append(rest_block(n,b))
  for n,b in RPC_SOURCES:rec["independent_sources"].append(rpc_block(n,b))
  kh=(rec.get("kyve") or {}).get("header")
  matches=[]
  if kh:
    for s in rec["independent_sources"]:
      if s.get("status")!="PASS":continue
      sh=s.get("header") or {}
      # exact canonical header field equality across all populated frozen fields.
      common={k for k,v in kh.items() if v is not None and sh.get(k) is not None}
      ok=bool(common) and all(kh[k]==sh[k] for k in common) and kh.get("chain_id")=="archway-1"
      s["header_match_to_kyve"]=ok;s["common_fields"]=sorted(common)
      if ok:matches.append(s["provider"])
  rec["reconciliation"]={"kyve_pass":rec.get("kyve",{}).get("status")=="PASS",
                          "matching_independent_sources":matches,
                          "two_path_pass":rec.get("kyve",{}).get("status")=="PASS" and len(matches)>=1}
  os.makedirs(os.path.dirname(OUT),exist_ok=True)
  with open(OUT,"w",encoding="utf-8") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
  print(json.dumps(rec,indent=2,sort_keys=True))

if __name__=="__main__":main()
