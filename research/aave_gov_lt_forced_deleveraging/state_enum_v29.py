#!/usr/bin/env python3
"""V29 authoritative Pool-state-event enumeration, Proposal 114 on Optimism.

Reconstructs collateral-enabled users for sUSD and current eMode category-1
users from Pool events from deployment through signal-1. Confirms the state
using historical getters. PRE-SIGNAL SOURCE ONLY; no outcomes.
"""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak
OUT=Path("out/aave_state_enum_v29");OUT.mkdir(parents=True,exist_ok=True)
URL="https://mainnet.optimism.io"
POOL="0x794a61358d6845594f94dc1db02a252b5b4814ad"
ASSET="0x8c6f28f2f1a3c87f0f938b96d27520d9751ec8d9"
SIGNAL_TS=1717599515
last=0.0
def sig(s):
 k=keccak.new(digest_bits=256);k.update(s.encode());return "0x"+k.hexdigest()
EN=sig("ReserveUsedAsCollateralEnabled(address,address)")
DIS=sig("ReserveUsedAsCollateralDisabled(address,address)")
EM=sig("UserEModeSet(address,uint8)")
def sha(b):return hashlib.sha256(b).hexdigest()
def post(body):
 global last
 time.sleep(max(0,.10-(time.monotonic()-last)));last=time.monotonic()
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
 lastv=None
 for a in range(16):
  d,status,h=post({"jsonrpc":"2.0","id":1,"method":method,"params":params});lastv=(d,status,h)
  if status==200 and isinstance(d,dict) and d.get("result") is not None:return d["result"],h
  time.sleep(min(8,.4*(a+1)))
 raise RuntimeError("RPC_EXHAUSTED_"+method+"_"+json.dumps(lastv))
def word(d,i):return int(d[2+i*64:2+(i+1)*64],16)
def call(to,sel,arg,block):return rpc("eth_call",[{"to":to,"data":sel+arg},hex(block)])[0]
# snapshot last block strictly before signal
latest=int(rpc("eth_blockNumber",[])[0],16);lo,hi=0,latest
while lo<hi:
 m=(lo+hi+1)//2;b=rpc("eth_getBlockByNumber",[hex(m),False])[0]
 if int(b["timestamp"],16)<SIGNAL_TS:lo=m
 else:hi=m-1
SNAP=lo;SH=rpc("eth_getBlockByNumber",[hex(SNAP),False])[0]
# pool deployment block
lo,hi=0,SNAP
while lo<hi:
 m=(lo+hi)//2;code=rpc("eth_getCode",[POOL,hex(m)])[0]
 if code=="0x":lo=m+1
 else:hi=m
DEPLOY=lo
asset_topic="0x"+"0"*24+ASSET[2:]
coverage=[]
def getlogs(a,b,topics):
 d,status,h=post({"jsonrpc":"2.0","id":a,"method":"eth_getLogs","params":[{"address":POOL,"fromBlock":hex(a),"toBlock":hex(b),"topics":topics}]})
 if status==200 and isinstance(d,dict) and isinstance(d.get("result"),list):return d["result"],h
 return None,h
def scan(a,b,topics):
 logs,h=getlogs(a,b,topics)
 if logs is not None:return [(a,b,logs,h)]
 if a==b:raise RuntimeError("UNRESOLVED_SINGLE_BLOCK_"+str(a))
 m=(a+b)//2
 return scan(a,m,topics)+scan(m+1,b,topics)
def acquire(label,topics):
 cursor=DEPLOY;out=[];cov=[]
 while cursor<=SNAP:
  target=min(cursor+999999,SNAP)
  for a,b,logs,h in scan(cursor,target,topics):
   assert a==cursor;cov.append({"from":a,"to":b,"response_sha256":h});out.extend(logs);cursor=b+1
  if len(cov)%50==0:
   (OUT/(label+"_checkpoint.json")).write_text(json.dumps({"frontier":cursor-1,"coverage":cov,"rows":out},indent=2)+"\n")
 return out,cov
collogs,colcov=acquire("collateral",[[EN,DIS],asset_topic])
emlogs,emcov=acquire("emode",[EM])
# canonical sort and state transitions
collogs.sort(key=lambda l:(int(l["blockNumber"],16),int(l["transactionIndex"],16),int(l["logIndex"],16)))
emlogs.sort(key=lambda l:(int(l["blockNumber"],16),int(l["transactionIndex"],16),int(l["logIndex"],16)))
coll={}
for l in collogs:
 u="0x"+l["topics"][2][-40:].lower();coll[u]=(l["topics"][0].lower()==EN)
emode={}
for l in emlogs:
 u="0x"+l["topics"][1][-40:].lower();emode[u]=word(l["data"],0)
# reserve id + all reserves/category1 at snapshot
rd=call(POOL,sig("getReserveData(address)")[:10],ASSET[2:].zfill(64),SNAP)
RID=word(rd,7)
res=call(POOL,sig("getReservesList()")[:10],"",SNAP)
off=word(res,0)//32;n=word(res,off);reserves=["0x"+format(word(res,off+1+i),"040x") for i in range(n)]
cat1=[]
for asset in reserves:
 d=call(POOL,sig("getReserveData(address)")[:10],asset[2:].zfill(64),SNAP)
 cfg=word(d,0);rid=word(d,7);cat=(cfg>>168)&255
 if cat==1:cat1.append({"asset":asset,"reserve_id":rid,"config_raw":str(cfg),"aToken":"0x"+format(word(d,8),"040x"),"liquidity_index":str(word(d,1)),"variable_borrow_index":str(word(d,3))})
BORROW_MASK=int("55"*32,16)
SEL_CFG=sig("getUserConfiguration(address)")[:10];SEL_ACC=sig("getUserAccountData(address)")[:10];SEL_EM=sig("getUserEMode(address)")[:10];SEL_BAL=sig("balanceOf(address)")[:10]
base_users=[];emode_users=[]
candidates=sorted(set([u for u,v in coll.items() if v]+[u for u,v in emode.items() if v==1]))
for i,u in enumerate(candidates):
 arg=u[2:].zfill(64);cfg=word(call(POOL,SEL_CFG,arg,SNAP),0);acc=call(POOL,SEL_ACC,arg,SNAP);av=[word(acc,j) for j in range(6)];em=word(call(POOL,SEL_EM,arg,SNAP),0)
 has_debt=(cfg&BORROW_MASK)!=0 and av[1]>0
 if coll.get(u,False):
  bit=1<<((RID<<1)+1)
  if cfg&bit and has_debt:
   bal=word(call("0x"+format(word(rd,8),"040x"),SEL_BAL,arg,SNAP),0)
   base_users.append({"user":u,"user_config_raw":str(cfg),"account_data_raw":[str(x) for x in av],"emode":em,"affected_aToken_balance_raw":str(bal)})
 if emode.get(u)==1 and em==1 and has_debt:
  assets=[]
  for a in cat1:
   bit=1<<((a["reserve_id"]<<1)+1)
   if cfg&bit:
    bal=word(call(a["aToken"],SEL_BAL,arg,SNAP),0)
    if bal>0:assets.append({"asset":a["asset"],"aToken_balance_raw":str(bal),"reserve_id":a["reserve_id"]})
  if assets:
   emode_users.append({"user":u,"user_config_raw":str(cfg),"account_data_raw":[str(x) for x in av],"emode":em,"category1_collateral":assets})
receipt={"lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001","phase":"PRE_SIGNAL_POOL_STATE_ENUMERATION_SOURCE_ONLY","shock":"V3_PROPOSAL_114","chain":"optimism","signal_timestamp":SIGNAL_TS,"snapshot_block":SNAP,"snapshot_timestamp":int(SH["timestamp"],16),"pool_deployment_block":DEPLOY,"asset":ASSET,"reserve_id":RID,"collateral_event_coverage_complete":colcov[0]["from"]==DEPLOY and colcov[-1]["to"]==SNAP and all(colcov[i]["to"]+1==colcov[i+1]["from"] for i in range(len(colcov)-1)),"emode_event_coverage_complete":emcov[0]["from"]==DEPLOY and emcov[-1]["to"]==SNAP and all(emcov[i]["to"]+1==emcov[i+1]["from"] for i in range(len(emcov)-1)),"collateral_transition_logs":len(collogs),"emode_transition_logs":len(emlogs),"collateral_active_state_users":sum(coll.values()),"emode1_active_state_users":sum(1 for x in emode.values() if x==1),"category1_reserves":cat1,"base_lt_borrowers":base_users,"base_lt_borrower_count":len(base_users),"emode_lt_borrowers":emode_users,"emode_lt_borrower_count":len(emode_users),"source_gate_pass":False,"hypothesis_status":"NOT_TESTED","economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k not in {"base_lt_borrowers","emode_lt_borrowers","category1_reserves"}},flush=True))
