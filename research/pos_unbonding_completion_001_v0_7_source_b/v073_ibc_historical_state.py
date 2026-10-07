#!/usr/bin/env python3
import base64,json,urllib.request,urllib.parse,os
from datetime import datetime,timezone

OUT="research/pos_unbonding_completion_001_v0_7_source_b/IBC_OSMOSIS_HISTORICAL_STATE_V073.json"
RPC="https://rpc.archive.osmosis.validatus.com"
COREUM_A="https://archive.rpc.mainnet-1.tx.org"
CLIENT="07-tendermint-2929"
RESTS=[
 ("validatus","https://api.osmosis.validatus.com"),
 ("osmosis","https://lcd.osmosis.zone"),
 ("lavenderfive","https://rest.lavenderfive.com/osmosis")
]
HOST_TARGETS=["2023-08-11T00:00:00+00:00","2024-01-02T00:00:00+00:00"]
UA="CryptoLab-Unbonding-V073/1.0"

def get(url,headers=None,t=30):
 h={"User-Agent":UA,"Accept":"application/json"}
 if headers:h.update(headers)
 req=urllib.request.Request(url,headers=h)
 with urllib.request.urlopen(req,timeout=t) as r:return json.loads(r.read().decode("utf-8"))

def rpc(path,params=None):
 u=RPC.rstrip("/")+"/"+path
 if params:u+="?"+urllib.parse.urlencode(params)
 o=get(u)
 if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
 return o.get("result") or {}

def btime(h):
 r=rpc("block",{"height":str(h)});hd=((r.get("block") or {}).get("header") or {})
 return {"height":int(hd["height"]),"time":hd["time"],"app_hash":hd.get("app_hash"),"hash":((r.get("block_id") or {}).get("hash"))}

def latest():
 return int(((rpc("status").get("sync_info") or {}).get("latest_block_height")))

def dt(s):return datetime.fromisoformat(s.replace("Z","+00:00"))

def first_at(target):
 t=dt(target);lo,hi=1,latest()
 while lo<hi:
  m=(lo+hi)//2
  try:x=btime(m)
  except Exception:lo=m+1;continue
  if dt(x["time"])<t:lo=m+1
  else:hi=m
 return lo

def hist_get(rest,path,h):
 return get(rest.rstrip("/")+path,{"x-cosmos-block-height":str(h)},30)

def decode_root(s):
 return base64.b64decode(s).hex().upper()

def coreum(h):
 o=get(COREUM_A.rstrip("/")+"/block?height="+str(h))
 r=o.get("result") or {};hd=((r.get("block") or {}).get("header") or {})
 return {"height":int(hd["height"]),"time":hd["time"],"app_hash":hd.get("app_hash"),"hash":((r.get("block_id") or {}).get("hash"))}

def norm(s):return dt(s).isoformat()

def main():
 rec={"amendment_commit":"f7bc1e49f95c95765299f92137be434357f3cc81","event_counts_opened":False,"client_id":CLIENT,"generated_utc":datetime.now(timezone.utc).isoformat(),"checkpoints":[]}
 for target in HOST_TARGETS:
  cp={"host_target":target}
  try:
   h=first_at(target);hb=btime(h);cp["host_height"]=h;cp["host_block"]=hb
   attempts=[];good=None
   for name,rest in RESTS:
    a={"provider":name,"rest":rest}
    try:
     cs=hist_get(rest,f"/ibc/core/client/v1/client_states/{CLIENT}",h)
     state=cs.get("client_state") or {}
     a["client_chain_id"]=state.get("chain_id")
     allcs=hist_get(rest,f"/ibc/core/client/v1/consensus_states/{CLIENT}?pagination.limit=1000",h)
     vals=allcs.get("consensus_states") or []
     a["consensus_state_count"]=len(vals)
     eligible=[]
     for row in vals:
      st=row.get("consensus_state") or {}
      ts=st.get("timestamp");ht=row.get("height") or {}
      root=((st.get("root") or {}).get("hash"))
      if ts and root and dt(ts)<=dt(hb["time"]):
       eligible.append((dt(ts),row))
     if state.get("chain_id")!="coreum-mainnet-1":raise RuntimeError("historical client does not track coreum-mainnet-1")
     if not eligible:raise RuntimeError("no eligible historical consensus state")
     eligible.sort(key=lambda z:z[0])
     row=eligible[-1][1];st=row["consensus_state"];rh=int((row.get("height") or {}).get("revision_height"));rev=int((row.get("height") or {}).get("revision_number") or 0)
     roothex=decode_root(st["root"]["hash"]);cb=coreum(rh)
     a["selected"]={"revision_number":rev,"revision_height":rh,"timestamp":st["timestamp"],"root_b64":st["root"]["hash"],"root_hex":roothex}
     a["coreum_source_a"]=cb
     a["app_hash_match"]=roothex==str(cb.get("app_hash","")).upper()
     a["timestamp_match"]=norm(st["timestamp"])==norm(cb["time"])
     a["pass"]=bool(a["app_hash_match"] and a["timestamp_match"])
     if a["pass"] and good is None:good=a
    except Exception as e:a["pass"]=False;a["error"]=type(e).__name__+": "+str(e)[:900]
    attempts.append(a)
   cp["attempts"]=attempts;cp["pass"]=good is not None;cp["passing"]=good
  except Exception as e:cp["pass"]=False;cp["error"]=type(e).__name__+": "+str(e)[:1000]
  rec["checkpoints"].append(cp)
 rec["passing_checkpoints"]=sum(1 for x in rec["checkpoints"] if x.get("pass"))
 hs=[(x.get("passing") or {}).get("selected",{}).get("revision_height") for x in rec["checkpoints"] if x.get("pass")]
 rec["distinct_coreum_heights"]=len(set(h for h in hs if h is not None))
 rec["cross_chain_source_b_pass"]=rec["passing_checkpoints"]==2 and rec["distinct_coreum_heights"]==2
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()
