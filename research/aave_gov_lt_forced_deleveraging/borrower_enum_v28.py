#!/usr/bin/env python3
"""V28 PRE-SIGNAL borrower enumeration proof: Optimism sUSD, Proposal 114.

Source-only. Enumerates every address ever appearing in the affected aToken's
Transfer history through signal-1, then historical-balance filters at snapshot.
No post-signal behavior or economic outcomes.
"""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

OUT=Path("out/aave_borrower_enum_v28");OUT.mkdir(parents=True,exist_ok=True)
URL="https://mainnet.optimism.io"
POOL="0x794a61358d6845594f94dc1db02a252b5b4814ad"
ASSET="0x8c6f28f2f1a3c87f0f938b96d27520d9751ec8d" # sUSD
SIGNAL_TS=1717599515 # Proposal 114 core queuedAt
last_request=0.0
def sig(s):
 k=keccak.new(digest_bits=256);k.update(s.encode());return "0x"+k.hexdigest()
TRANSFER=sig("Transfer(address,address,uint256)")
def sha(b):return hashlib.sha256(b).hexdigest()
def post(body):
 global last_request
 time.sleep(max(0,.10-(time.monotonic()-last_request)));last_request=time.monotonic()
 raw=json.dumps(body,sort_keys=True).encode();rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time()}
 try:
  req=urllib.request.Request(URL,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
  with urllib.request.urlopen(req,timeout=45) as res:data=res.read();status=res.status;headers=dict(res.headers)
 except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
 except Exception as e:data=str(e).encode();status=0;headers={}
 h=sha(data);(OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0));rec.update(http_status=status,response_sha256=h,headers=headers)
 with (OUT/"requests.jsonl").open("a") as f:f.write(json.dumps(rec)+"\n")
 try:d=json.loads(data)
 except Exception:d={"transport_body":data.decode(errors="replace")}
 return d,status,h
def rpc(method,params):
 last=None
 for a in range(16):
  d,status,h=post({"jsonrpc":"2.0","id":1,"method":method,"params":params});last=(d,status,h)
  if status==200 and isinstance(d,dict) and d.get("result") is not None:return d["result"],h
  time.sleep(min(8,.4*(a+1)))
 raise RuntimeError("RPC_EXHAUSTED_"+method+"_"+json.dumps(last))
def word(data,i):return int(data[2+i*64:2+(i+1)*64],16)
def call(to,selector,arg,block):
 d,h=rpc("eth_call",[{"to":to,"data":selector+arg},hex(block)]);return d,h
# snapshot = greatest Optimism block strictly before core queue timestamp
latest=int(rpc("eth_blockNumber",[])[0],16);lo,hi=0,latest
while lo<hi:
 m=(lo+hi+1)//2;b=rpc("eth_getBlockByNumber",[hex(m),False])[0];ts=int(b["timestamp"],16)
 if ts<SIGNAL_TS:lo=m
 else:hi=m-1
SNAP=lo; sh=rpc("eth_getBlockByNumber",[hex(SNAP),False])[0]
assert int(sh["timestamp"],16)<SIGNAL_TS
# reserve data at signal-1
rd,_=call(POOL,sig("getReserveData(address)")[:10],ASSET[2:].zfill(64),SNAP)
assert len(rd)>=962
ATOKEN="0x"+format(word(rd,8),"040x")
STABLE="0x"+format(word(rd,9),"040x")
VARIABLE="0x"+format(word(rd,10),"040x")
for x in [ATOKEN,VARIABLE]:
 code,_=rpc("eth_getCode",[x,hex(SNAP)]);assert code!="0x"
# find aToken first code block
lo,hi=0,SNAP
while lo<hi:
 m=(lo+hi)//2;code,_=rpc("eth_getCode",[ATOKEN,hex(m)])
 if code=="0x":lo=m+1
 else:hi=m
DEPLOY=lo
addresses=set();coverage=[];transfer_logs=0
def getlogs(a,b):
 body={"jsonrpc":"2.0","id":a,"method":"eth_getLogs","params":[{"address":ATOKEN,"fromBlock":hex(a),"toBlock":hex(b),"topics":[TRANSFER]}]}
 d,status,h=post(body)
 if status==200 and isinstance(d,dict) and isinstance(d.get("result"),list):return d["result"],h
 return None,h
def scan(a,b):
 logs,h=getlogs(a,b)
 if logs is not None:return [(a,b,logs,h)]
 if a==b:raise RuntimeError("UNRESOLVED_SINGLE_BLOCK_"+str(a))
 m=(a+b)//2
 return scan(a,m)+scan(m+1,b)
cursor=DEPLOY
while cursor<=SNAP:
 target=min(cursor+499999,SNAP)
 parts=scan(cursor,target)
 for a,b,logs,h in parts:
  assert a==cursor
  coverage.append({"from":a,"to":b,"response_sha256":h})
  for l in logs:
   assert l["topics"][0].lower()==TRANSFER
   for t in l["topics"][1:3]:
    addr="0x"+t[-40:].lower()
    if addr!="0x"+"0"*40:addresses.add(addr)
  transfer_logs+=len(logs);cursor=b+1
 if len(coverage)%50==0:
  (OUT/"checkpoint.json").write_text(json.dumps({"snapshot":SNAP,"aToken":ATOKEN,"deploy":DEPLOY,"frontier":cursor-1,"coverage":coverage,"addresses_sorted":sorted(addresses),"transfer_logs":transfer_logs},indent=2)+"\n")
# historical snapshot filtering
positive=[];borrowers=[]
SEL_BAL=sig("balanceOf(address)")[:10]
SEL_ACC=sig("getUserAccountData(address)")[:10]
SEL_CFG=sig("getUserConfiguration(address)")[:10]
SEL_EM=sig("getUserEMode(address)")[:10]
for i,u in enumerate(sorted(addresses)):
 arg=u[2:].zfill(64)
 bal,_=call(ATOKEN,SEL_BAL,arg,SNAP)
 b=word(bal,0)
 if b==0:continue
 positive.append({"user":u,"aToken_balance_raw":str(b)})
 acc,_=call(POOL,SEL_ACC,arg,SNAP);vals=[word(acc,j) for j in range(6)]
 if vals[1]==0:continue
 cfg,_=call(POOL,SEL_CFG,arg,SNAP);em,_=call(POOL,SEL_EM,arg,SNAP)
 debt={}
 for name,tok in [("stableDebt",STABLE),("variableDebt",VARIABLE)]:
  if tok=="0x"+"0"*40:debt[name]="0"
  else:
   d,_=call(tok,SEL_BAL,arg,SNAP);debt[name]=str(word(d,0))
 borrowers.append({"user":u,"aToken_balance_raw":str(b),"account_data_raw":[str(v) for v in vals],"user_configuration_raw":str(word(cfg,0)),"emode_category":word(em,0),"affected_asset_debt":debt})
 if i%100==0:
  (OUT/"borrower_progress.json").write_text(json.dumps({"processed":i+1,"candidate_addresses":len(addresses),"positive_holders":len(positive),"borrowers":borrowers},indent=2)+"\n")
receipt={"lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001","phase":"PRE_SIGNAL_BORROWER_ENUMERATION_SOURCE_ONLY","shock":"V3_PROPOSAL_114","chain":"optimism","signal_timestamp":SIGNAL_TS,"snapshot_block":SNAP,"snapshot_timestamp":int(sh["timestamp"],16),"asset":ASSET,"aToken":ATOKEN,"aToken_deployment_block":DEPLOY,"coverage_complete":coverage[0]["from"]==DEPLOY and coverage[-1]["to"]==SNAP and all(coverage[i]["to"]+1==coverage[i+1]["from"] for i in range(len(coverage)-1)),"transfer_intervals":len(coverage),"transfer_logs":transfer_logs,"candidate_addresses":len(addresses),"positive_aToken_holders":len(positive),"positive_holders":positive,"borrowers_with_any_pool_debt":borrowers,"borrower_count":len(borrowers),"reserve_data_abi_sha256":sha(rd.encode()),"source_gate_pass":False,"hypothesis_status":"NOT_TESTED","economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k not in {"positive_holders","borrowers_with_any_pool_debt"}},flush=True))
