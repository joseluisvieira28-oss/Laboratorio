#!/usr/bin/env python3
import base64,json,urllib.request,urllib.parse,hashlib,os
from datetime import datetime,timezone

OUT="research/pos_unbonding_completion_001_v0_7_source_b/IBC_OSMOSIS_COREUM_SOURCE_B_V072.json"
RPC="https://rpc.archive.osmosis.validatus.com"
COREUM_A="https://archive.rpc.mainnet-1.tx.org"
CLIENT="07-tendermint-2929"
RESTS=[
 ("validatus","https://api.osmosis.validatus.com"),
 ("osmosis","https://lcd.osmosis.zone"),
 ("lavenderfive","https://rest.lavenderfive.com/osmosis")
]
TARGETS=["2023-07-01T00:00:00+00:00","2024-01-01T00:00:00+00:00"]
UA="CryptoLab-Unbonding-V072/1.0"

def req(url,headers=None,t=30):
 h={"User-Agent":UA,"Accept":"application/json"}
 if headers:h.update(headers)
 r=urllib.request.Request(url,headers=h)
 with urllib.request.urlopen(r,timeout=t) as x:return x.read()

def js(url,headers=None,t=30):return json.loads(req(url,headers,t).decode("utf-8"))

def rpc(path,params=None,t=30):
 url=RPC.rstrip("/")+"/"+path.lstrip("/")
 if params:url+="?"+urllib.parse.urlencode(params)
 o=js(url,t=t)
 if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
 return o.get("result") or {}

def block(h):
 r=rpc("block",{"height":str(h)})
 hd=((r.get("block") or {}).get("header") or {})
 return {"height":int(hd["height"]),"time":hd["time"],"hash":((r.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash")}

def latest_height():
 r=rpc("status")
 return int((((r.get("sync_info") or {}).get("latest_block_height"))))

def parse_time(s):
 return datetime.fromisoformat(s.replace("Z","+00:00"))

def first_block_at_or_after(target):
 target=parse_time(target);lo,hi=1,latest_height()
 while lo<hi:
  mid=(lo+hi)//2
  try:b=block(mid)
  except Exception:
   lo=mid+1;continue
  if parse_time(b["time"])<target:lo=mid+1
  else:hi=mid
 return lo

def maybe_text(s):
 if not isinstance(s,str):return s
 # CometBFT modern APIs expose plain strings. Older APIs may expose base64.
 if s in (CLIENT,"update_client") or s.startswith("1-"):return s
 try:
  b=base64.b64decode(s,validate=True)
  t=b.decode("utf-8")
  if all(31<ord(c)<127 for c in t):return t
 except Exception:pass
 return s

def find_update(lo):
 # deterministic: first matching indexed block after target, searched in fixed 100k chunks up to 2m blocks.
 for start in range(lo,lo+2000000,100000):
  end=start+99999
  q=f"update_client.client_id='{CLIENT}' AND block.height >= {start} AND block.height <= {end}"
  p={"query":json.dumps(q),"page":"1","per_page":"100","order_by":json.dumps("asc")}
  try:r=rpc("block_search",p,45)
  except Exception as e:continue
  bs=r.get("blocks") or []
  if bs:
   h=min(int(((x.get("block") or {}).get("header") or {}).get("height")) for x in bs)
   return {"host_height":h,"query":q,"total_count":int(r.get("total_count") or 0)}
 return None

def consensus_height_from_results(h):
 r=rpc("block_results",{"height":str(h)})
 phases=[]
 for k in ("begin_block_events","end_block_events","finalize_block_events"):
  phases += r.get(k) or []
 for txr in r.get("txs_results") or []:
  phases += txr.get("events") or []
 hits=[]
 for e in phases:
  if e.get("type")!="update_client":continue
  attrs={}
  for a in e.get("attributes") or []:
   attrs[maybe_text(a.get("key"))]=maybe_text(a.get("value"))
  if attrs.get("client_id")==CLIENT:
   hits.append(attrs)
 if not hits:return None
 # First event in canonical block for this client.
 ch=hits[0].get("consensus_height")
 if not ch:return {"attrs":hits[0]}
 rev,height=ch.split("-",1)
 return {"revision_number":int(rev),"revision_height":int(height),"attrs":hits[0]}

def query_consensus(rest,host_height,rev,rh):
 url=rest.rstrip("/")+f"/ibc/core/client/v1/consensus_states/{CLIENT}/revision/{rev}/height/{rh}"
 headers={"x-cosmos-block-height":str(host_height)}
 o=js(url,headers,30)
 cs=o.get("consensus_state") or {}
 root=((cs.get("root") or {}).get("hash"))
 ts=cs.get("timestamp")
 if not root or not ts:raise RuntimeError("missing consensus_state root/timestamp")
 root_hex=base64.b64decode(root).hex().upper()
 return {"url":url,"root_b64":root,"root_hex":root_hex,"timestamp":ts,"type":cs.get("@type"),"proof_height":o.get("proof_height")}

def coreum_block(h):
 o=js(COREUM_A.rstrip("/")+"/block?height="+str(h),t=30)
 r=o.get("result") or {};hd=((r.get("block") or {}).get("header") or {})
 return {"height":int(hd["height"]),"time":hd.get("time"),"hash":((r.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash")}

def norm_ts(s):
 return parse_time(s).isoformat()

def main():
 rec={"amendment_commit":"2857e56e85555fcd6356e2264f4687f6cd81b416","event_counts_opened":False,"client_id":CLIENT,"counterparty":"osmosis-1","generated_utc":datetime.now(timezone.utc).isoformat(),"checkpoints":[]}
 for target in TARGETS:
  cp={"target_utc":target}
  try:
   lo=first_block_at_or_after(target);cp["first_osmosis_height_at_target"]=lo;cp["first_osmosis_block"]=block(lo)
   u=find_update(lo);cp["update_search"]=u
   if not u:raise RuntimeError("no indexed Coreum update_client within 2m blocks")
   ch=consensus_height_from_results(u["host_height"]);cp["consensus_height_event"]=ch
   if not ch or "revision_height" not in ch:raise RuntimeError("consensus_height not found in update_client event")
   cb=coreum_block(ch["revision_height"]);cp["coreum_source_a"]=cb
   cp["rest_attempts"]=[]
   good=None
   for name,rest in RESTS:
    try:
     cs=query_consensus(rest,u["host_height"],ch["revision_number"],ch["revision_height"])
     cs["provider"]=name
     cs["app_hash_match"]=cs["root_hex"]==str(cb.get("app_hash","")).upper()
     cs["timestamp_match"]=norm_ts(cs["timestamp"])==norm_ts(cb["time"])
     cs["pass"]=bool(cs["app_hash_match"] and cs["timestamp_match"])
     cp["rest_attempts"].append(cs)
     if cs["pass"] and good is None:good=cs
    except Exception as e:
     cp["rest_attempts"].append({"provider":name,"pass":False,"error":type(e).__name__+": "+str(e)[:700]})
   cp["pass"]=good is not None
   cp["passing_consensus_source"]=good
  except Exception as e:
   cp["pass"]=False;cp["error"]=type(e).__name__+": "+str(e)[:1000]
  rec["checkpoints"].append(cp)
 rec["passing_checkpoints"]=sum(1 for x in rec["checkpoints"] if x.get("pass"))
 rec["cross_chain_source_b_pass"]=rec["passing_checkpoints"]==2
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w",encoding="utf-8") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()
