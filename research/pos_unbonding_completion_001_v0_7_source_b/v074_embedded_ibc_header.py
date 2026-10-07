#!/usr/bin/env python3
import hashlib,json,os,urllib.request,urllib.parse,base64
from datetime import datetime,timezone

INP="research/pos_unbonding_completion_001_v0_7_source_b/IBC_OSMOSIS_COREUM_SOURCE_B_V072.json"
OUT="research/pos_unbonding_completion_001_v0_7_source_b/EMBEDDED_IBC_HEADER_PROOF_V074.json"
OSMO_RPC="https://rpc.archive.osmosis.validatus.com"
COREUM_A="https://archive.rpc.mainnet-1.tx.org"
CLIENT="07-tendermint-2929"
UA="CryptoLab-Unbonding-V074/1.0"

def get_json(url,t=30):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=t) as r:return json.loads(r.read().decode("utf-8"))

def read_varint(buf,i):
 out=0;shift=0
 while True:
  if i>=len(buf):raise ValueError("truncated varint")
  b=buf[i];i+=1;out|=(b&0x7f)<<shift
  if not b&0x80:return out,i
  shift+=7
  if shift>70:raise ValueError("varint overflow")

def fields(buf):
 i=0
 while i<len(buf):
  k,i=read_varint(buf,i);n=k>>3;w=k&7
  if w==0:v,i=read_varint(buf,i)
  elif w==1:v=buf[i:i+8];i+=8
  elif w==2:
   ln,i=read_varint(buf,i);v=buf[i:i+ln];i+=ln
  elif w==5:v=buf[i:i+4];i+=4
  else:raise ValueError("unsupported wire "+str(w))
  yield n,w,v

def one_len(buf,n):
 for fn,w,v in fields(buf):
  if fn==n and w==2:return v
 return None

def one_varint(buf,n):
 for fn,w,v in fields(buf):
  if fn==n and w==0:return v
 return None

def text_field(buf,n):
 v=one_len(buf,n)
 return v.decode("utf-8","strict") if v is not None else None

def maybe_text(s):
 if not isinstance(s,str):return s
 if s==CLIENT or s=="update_client" or s.startswith("1-"):return s
 try:
  b=base64.b64decode(s,validate=True);t=b.decode("utf-8")
  if t and all(31<ord(c)<127 for c in t):return t
 except Exception:pass
 return s

def ts_from_proto(buf):
 sec=one_varint(buf,1) or 0;nanos=one_varint(buf,2) or 0
 main=datetime.fromtimestamp(sec,timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
 frac=f"{nanos:09d}".rstrip("0")
 return main+("." + frac if frac else "")+"Z"

def canon_ts(s):
 if s.endswith("Z"):s=s[:-1]
 if "+" in s:s=s.split("+",1)[0]
 if "." in s:
  main,frac=s.split(".",1);frac=frac[:9].ljust(9,"0").rstrip("0")
  return main+("." + frac if frac else "")+"Z"
 return s+"Z"

def decode_ibc_any(hexstr):
 raw=bytes.fromhex(hexstr)
 type_url=text_field(raw,1);value=one_len(raw,2)
 if not value:raise ValueError("Any.value missing")
 ibc_signed=one_len(value,1)
 if not ibc_signed:raise ValueError("IBC Header.signed_header missing")
 tm_header=one_len(ibc_signed,1);commit=one_len(ibc_signed,2)
 if not tm_header or not commit:raise ValueError("SignedHeader incomplete")
 chain_id=text_field(tm_header,2)
 height=one_varint(tm_header,3)
 tmsg=one_len(tm_header,4)
 app_hash=one_len(tm_header,11)
 block_id=one_len(commit,3)
 commit_hash=one_len(block_id,1) if block_id else None
 return {
  "any_type_url":type_url,
  "raw_any_sha256":hashlib.sha256(raw).hexdigest(),
  "chain_id":chain_id,
  "height":height,
  "time":ts_from_proto(tmsg) if tmsg else None,
  "app_hash":app_hash.hex().upper() if app_hash else None,
  "commit_block_id_hash":commit_hash.hex().upper() if commit_hash else None,
 }

def osmo_results(h):
 u=OSMO_RPC+f"/block_results?height={h}";o=get_json(u)
 if o.get("error"):raise RuntimeError(json.dumps(o["error"]))
 return o.get("result") or {}

def osmo_block(h):
 o=get_json(OSMO_RPC+f"/block?height={h}");r=o.get("result") or {};hd=((r.get("block") or {}).get("header") or {})
 return {"height":int(hd["height"]),"time":hd["time"],"hash":((r.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash")}

def coreum_block(h):
 o=get_json(COREUM_A+f"/block?height={h}");r=o.get("result") or {};hd=((r.get("block") or {}).get("header") or {})
 return {"height":int(hd["height"]),"time":hd["time"],"hash":((r.get("block_id") or {}).get("hash")),"app_hash":hd.get("app_hash")}

def find_event_and_code(host_h,consensus_height):
 r=osmo_results(host_h)
 target="1-"+str(consensus_height)
 matches=[]
 for idx,tr in enumerate(r.get("txs_results") or []):
  for e in tr.get("events") or []:
   if e.get("type")!="update_client":continue
   attrs={}
   for a in e.get("attributes") or []:attrs[maybe_text(a.get("key"))]=maybe_text(a.get("value"))
   if attrs.get("client_id")==CLIENT and attrs.get("consensus_height")==target:
    matches.append({"tx_index":idx,"code":int(tr.get("code") or 0),"attrs":attrs})
 if len(matches)!=1:raise RuntimeError(f"expected one matching update event, got {len(matches)}")
 return matches[0]

def main():
 with open(INP,encoding="utf-8") as f:parent=json.load(f)
 rec={"freeze_commit":"09b88a46131798fba2740db098fd53d8b3b1ab73","generated_utc":datetime.now(timezone.utc).isoformat(),"event_counts_opened":False,"checkpoints":[]}
 for p in parent["checkpoints"]:
  host=int(p["update_search"]["host_height"]);ch=int(p["consensus_height_event"]["revision_height"])
  cp={"target":p["target_utc"],"osmosis_host_height":host,"coreum_consensus_height":ch}
  try:
   ev=find_event_and_code(host,ch);cp["tx_index"]=ev["tx_index"];cp["tx_code"]=ev["code"]
   header_hex=ev["attrs"].get("header")
   if not header_hex:raise RuntimeError("embedded header attribute missing")
   dec=decode_ibc_any(header_hex);cp["decoded"]=dec
   ob=osmo_block(host);cb=coreum_block(ch);cp["osmosis_host_block"]=ob;cp["coreum_source_a"]=cb
   cp["checks"]={
    "tx_success":ev["code"]==0,
    "client_id":ev["attrs"].get("client_id")==CLIENT,
    "event_height_equals_decoded":dec["height"]==ch,
    "chain_id":dec["chain_id"]=="coreum-mainnet-1",
    "timestamp":canon_ts(dec["time"])==canon_ts(cb["time"]),
    "app_hash":dec["app_hash"]==str(cb["app_hash"]).upper(),
    "block_hash":dec["commit_block_id_hash"]==str(cb["hash"]).upper(),
    "type_url":dec["any_type_url"]=="/ibc.lightclients.tendermint.v1.Header",
   }
   cp["pass"]=all(cp["checks"].values())
  except Exception as e:
   cp["pass"]=False;cp["error"]=type(e).__name__+": "+str(e)[:1000]
  rec["checkpoints"].append(cp)
 rec["passing_checkpoints"]=sum(1 for x in rec["checkpoints"] if x.get("pass"))
 rec["coreum_cryptographic_source_b_pass"]=rec["passing_checkpoints"]==2
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 with open(OUT,"w",encoding="utf-8") as f:json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(rec,indent=2))
if __name__=="__main__":main()
