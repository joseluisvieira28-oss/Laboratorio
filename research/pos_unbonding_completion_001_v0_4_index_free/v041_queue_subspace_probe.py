#!/usr/bin/env python3
import base64, hashlib, json, os, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone

OUT="research/pos_unbonding_completion_001_v0_4_index_free/QUEUE_SUBSPACE_PROBE_V041.json"
UA="CryptoLab-Unbonding-V041-QueueProbe/1.0"

PROBES=[
  {"chain":"cosmoshub","height":20000000,"sources":[
    ["citizenweb3","https://rpc.cosmoshub-4-archive.citizenweb3.com"],
    ["cryptocrew","https://rpc.cosmoshub-main.ccvalidators.com"]]},
  {"chain":"osmosis","height":15000000,"sources":[
    ["osmosis","https://rpc.osmosis.zone"],
    ["validatus","https://rpc.archive.osmosis.validatus.com"]]},
  {"chain":"kava","height":9500000,"sources":[
    ["kava_labs","https://rpc.data.kava.io"],
    ["chainstack","https://rpc.data.kava.chainstacklabs.com"]]},
  {"chain":"celestia","height":2500000,"sources":[
    ["kjnodes","http://136.243.94.113:26667"],
    ["numia","https://public-celestia-rpc.numia.xyz"]]},
  {"chain":"dydx","height":15000000,"sources":[
    ["kingnodes","https://dydx-ops-archive-rpc.kingnodes.com"],
    ["polkachu","https://dydx-dao-archive-rpc.polkachu.com"]]}
]

def read_varint(buf,i):
  out=shift=0
  while True:
    if i>=len(buf): raise ValueError("truncated varint")
    b=buf[i];i+=1;out|=(b&0x7f)<<shift
    if not b&0x80:return out,i
    shift+=7
    if shift>70:raise ValueError("varint overflow")

def fields(buf):
  i=0
  while i<len(buf):
    key,i=read_varint(buf,i);n=key>>3;w=key&7
    if w==0:v,i=read_varint(buf,i);yield n,w,v
    elif w==2:
      ln,i=read_varint(buf,i);v=buf[i:i+ln];i+=ln;yield n,w,v
    elif w==1:v=buf[i:i+8];i+=8;yield n,w,v
    elif w==5:v=buf[i:i+4];i+=4;yield n,w,v
    else:raise ValueError("unsupported wire")

def decode_pairs(buf):
  out=[]
  for n,w,p in fields(buf):
    if n!=1 or w!=2:continue
    k=v=None
    for fn,fw,fv in fields(p):
      if fn==1 and fw==2:k=fv
      elif fn==2 and fw==2:v=fv
    out.append({
      "key_hex":k.hex() if k else None,
      "value_len":len(v) if v is not None else None,
      "value_sha256":hashlib.sha256(v).hexdigest() if v is not None else None
    })
  return out

def get(url,timeout=25):
  req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
  try:
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
  except urllib.error.HTTPError as e:
    body=e.read().decode("utf-8","replace")[:1200]
    raise RuntimeError(f"HTTP {e.code}: {body}")

def abci(base,height):
  variants=[
    {"path":json.dumps("/store/staking/subspace"),"data":"0x41","height":str(height),"prove":"false"},
    {"path":json.dumps("/store/staking/subspace"),"data":"41","height":str(height),"prove":"false"}
  ]
  attempts=[]
  for params in variants:
    url=base.rstrip("/")+"/abci_query?"+urllib.parse.urlencode(params)
    try:
      raw=get(url);obj=json.loads(raw.decode())
      resp=((obj.get("result") or {}).get("response") or {})
      code=resp.get("code",0);val=resp.get("value")
      att={"url":url,"http_payload_sha256":hashlib.sha256(raw).hexdigest(),"code":code,
           "height":resp.get("height"),"log":resp.get("log"),"value_present":bool(val)}
      if code in (0,None) and val:
        bz=base64.b64decode(val)
        pairs=decode_pairs(bz)
        att.update({
          "value_sha256":hashlib.sha256(bz).hexdigest(),
          "value_len":len(bz),"pair_count":len(pairs),
          "all_keys_prefix_41":bool(pairs) and all((p.get("key_hex") or "").startswith("41") for p in pairs),
          "pairs":pairs[:200]
        })
        attempts.append(att)
        return {"status":"PASS","selected":att,"attempts":attempts}
      attempts.append(att)
    except Exception as e:
      attempts.append({"url":url,"error":type(e).__name__+": "+str(e)})
  return {"status":"FAIL","attempts":attempts}

def main():
  receipt={"amendment_commit":"023ceb3c26e603282ebf48fac150c3f4141e0881",
           "generated_utc":datetime.now(timezone.utc).isoformat(),"probes":[]}
  for spec in PROBES:
    e={"chain":spec["chain"],"height":spec["height"],"sources":{}}
    for name,base in spec["sources"]:
      r=abci(base,spec["height"]);r["base"]=base;e["sources"][name]=r
    good=[(n,r["selected"]) for n,r in e["sources"].items() if r.get("status")=="PASS"]
    e["reconciliation"]={"successful_sources":len(good),"exact_value_match":False}
    if len(good)>=2:
      e["reconciliation"]["exact_value_match"]=len({x[1]["value_sha256"] for x in good})==1
      e["reconciliation"]["pair_count_match"]=len({x[1]["pair_count"] for x in good})==1
    receipt["probes"].append(e)
  os.makedirs(os.path.dirname(OUT),exist_ok=True)
  with open(OUT,"w",encoding="utf-8") as f:
    json.dump(receipt,f,indent=2,sort_keys=True);f.write("\n")
  print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":main()
