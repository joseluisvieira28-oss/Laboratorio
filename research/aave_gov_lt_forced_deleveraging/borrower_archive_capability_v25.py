#!/usr/bin/env python3
"""PRE-SIGNAL SOURCE CAPABILITY matrix: public historical eth_call only.

Does not enumerate borrowers or inspect behavioral outcomes. It proves whether
protocol state can be read at representative historical blocks on candidate
chains using unauthenticated public RPC.
"""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

OUT=Path("out/aave_borrower_archive_capability_v25");OUT.mkdir(parents=True,exist_ok=True)
POOL="0x794a61358d6845594f94dc1db02a252b5b4814ad"
# Representative effect-adjacent historical blocks, never post-outcome values.
CHAINS={
 "optimism":{"block":118500000,"urls":["https://mainnet.optimism.io","https://optimism-rpc.publicnode.com","https://optimism.drpc.org"]},
 "avalanche":{"block":43400000,"urls":["https://api.avax.network/ext/bc/C/rpc","https://avalanche-c-chain-rpc.publicnode.com","https://avalanche.drpc.org"]},
 "polygon":{"block":55100000,"urls":["https://polygon-bor-rpc.publicnode.com","https://polygon.drpc.org","https://1rpc.io/matic"]},
 "base":{"block":13000000,"pool":"0xA238Dd80C259a72e81d7e4664a9801593F98d1c5","urls":["https://base-rpc.publicnode.com","https://mainnet.base.org","https://base.drpc.org"]},
}
def sig(s):
 k=keccak.new(digest_bits=256);k.update(s.encode());return "0x"+k.hexdigest()
SEL=sig("getUserAccountData(address)")[:10]+"0"*64
def sha(b):return hashlib.sha256(b).hexdigest()
def post(url,body):
 raw=json.dumps(body,sort_keys=True).encode();rec={"url":url,"request":body,"request_sha256":sha(raw),"observed_at":time.time()}
 try:
  req=urllib.request.Request(url,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
  with urllib.request.urlopen(req,timeout=30) as res:data=res.read();status=res.status
 except urllib.error.HTTPError as e:data=e.read();status=e.code
 except Exception as e:data=str(e).encode();status=0
 h=sha(data);(OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0));rec.update(http_status=status,response_sha256=h)
 with (OUT/"requests.jsonl").open("a") as f:f.write(json.dumps(rec)+"\n")
 try:d=json.loads(data)
 except Exception:d={"transport_body":data.decode(errors="replace")}
 return d,status,h
rows=[]
for chain,cfg in CHAINS.items():
 block=cfg["block"];pool=cfg.get("pool",POOL);attempts=[]
 for url in cfg["urls"]:
  body={"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":pool,"data":SEL},hex(block)]}
  d,status,h=post(url,body)
  ok=status==200 and isinstance(d,dict) and isinstance(d.get("result"),str) and d["result"].startswith("0x") and len(d["result"])>=64
  attempts.append({"url":url,"ok":ok,"http_status":status,"response_sha256":h,"error":None if ok else d.get("error",d)})
 row={"chain":chain,"block":block,"pool":pool,"historical_protocol_eth_call_pass":any(a["ok"] for a in attempts),"attempts":attempts}
 rows.append(row);print(json.dumps(row),flush=True)
receipt={"lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001","phase":"PRE_SIGNAL_PUBLIC_ARCHIVE_CAPABILITY_ONLY","rows":rows,"chains_pass":sum(r["historical_protocol_eth_call_pass"] for r in rows),"source_gate_pass":False,"hypothesis_status":"NOT_TESTED","economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
