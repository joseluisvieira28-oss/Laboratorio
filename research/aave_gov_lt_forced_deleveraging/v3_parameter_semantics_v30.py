#!/usr/bin/env python3
"""V30 SOURCE-ONLY exact V3 LT parameter semantics for the frozen 10-proposal set.

Nine proposals are verified against the pinned Seatbelt payload state diffs.
Proposal 19 is verified directly from Optimism effect receipt + signal-1 Pool state
because its pinned Seatbelt payload simulation is explicitly failed.

No borrower behaviour, economic outcomes, Development, 2026 data, trading or accounts.
"""
import gzip,hashlib,json,os,re,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

ROOT=Path(os.environ["SEATBELT_ROOT"])
OUT=Path("out/aave_v3_parameter_semantics_v30");OUT.mkdir(parents=True,exist_ok=True)
SEATBELT_COMMIT=os.environ["SEATBELT_COMMIT"]

ROWS={
 2:("reports/payloads/43114/0x1140CB7CAfAcC745771C2Ea31e7B5C653c5d0B80/11.md","0xce6ac8064744d211867be08855d0e66860a55875afe185ef79cd511d4f476d59",[(7500,7000)]),
 13:("reports/payloads/43114/0x1140CB7CAfAcC745771C2Ea31e7B5C653c5d0B80/13.md","0xa384379aea3b70bf3f56c3bafc01d8c0fa0464207367fd21135352ba65b320d7",[(8100,8000)]),
 55:("reports/payloads/43114/0x1140CB7CAfAcC745771C2Ea31e7B5C653c5d0B80/17.md","0xa3c46c26959c03b46a0937a91c6650cb9e12ee7ca05119786ae2216db4b721c5",[(7000,6700),(8000,7700)]),
 71:("reports/payloads/10/0x0E1a3Af1f9cC76A62eD31eDedca291E63632e7c4/24.md","0xa8ecf8b94a86aac1e68db482e01282cc4e66a051cc7c97d816ed293443db9538",[(8000,7900),(8500,8400),(8300,8000)]),
 87:("reports/payloads/10/0x0E1a3Af1f9cC76A62eD31eDedca291E63632e7c4/28.md","0x32d60434b74e59c69ecf7a06d38b67527245aff9c2e5eef7e3bc5da3e30fbac9",[(8000,7700)]),
 100:("reports/payloads/10/0x0E1a3Af1f9cC76A62eD31eDedca291E63632e7c4/30.md","0x6d6f4750a7109b7322de3782ffdd6f7e6a99a079242a7929481802f7094a026f",[(7900,7800),(8400,8000)]),
 114:("reports/payloads/10/0x0E1a3Af1f9cC76A62eD31eDedca291E63632e7c4/33.md","0x99af268f6b4145c78bc2239bb21e84e196638704ad9a3a15dd808742535bd485",[(9500,9300),(7500,7000)]),
 173:("reports/payloads/10/0x0E1a3Af1f9cC76A62eD31eDedca291E63632e7c4/50.md","0xf646ec46e06384edbed76231bbb0fb92ea4d5de33f083079721684ca14047a50",[(8000,7900),(7500,7100),(8000,7850)]),
 260:("reports/payloads/137/0x401B5D0294E23637c18fcc38b1Bca814CDa2637C/102.md","0xd99064b3668c92d453973ffa84cb56fd52fcc8720aae853f247fb00a853371ae",[(9500,9425)]),
}
PROPOSALS=[2,13,19,55,71,87,100,114,173,260]

def sha(b):return hashlib.sha256(b).hexdigest()
def parse_num(s):
 m=re.search(r"\[(\d+)\]",s)
 if m:return int(m.group(1))
 m=re.search(r"(?<![A-Za-z0-9])(\d{2,5})(?![A-Za-z0-9])",s)
 return int(m.group(1)) if m else None
def lt_pairs(text):
 ls=text.splitlines();out=[]
 for i,line in enumerate(ls[:-2]):
  if ("liquidationThreshold" in line) and line.startswith("@@"):
   old=parse_num(ls[i+1]);new=parse_num(ls[i+2])
   if old is not None and new is not None and new<old:
    out.append({"key_line":line,"old_lt_bps":old,"new_lt_bps":new})
 return out
def queue_line(pid):
 p=ROOT/"reports"/"proposals"/f"{pid}.md";raw=p.read_bytes();s=raw.decode(errors="replace")
 line=next((x for x in s.splitlines() if x.startswith("- queuedAt:")),None)
 if not line:raise RuntimeError(f"NO_QUEUE_LINE_{pid}")
 txm=re.search(r"/tx/(0x[0-9a-fA-F]{64})",line)
 if not txm:raise RuntimeError(f"NO_QUEUE_TX_{pid}")
 return {"proposal_report":str(p.relative_to(ROOT)),"proposal_report_sha256":sha(raw),"queue_line":line,"queue_tx":txm.group(1).lower()}

rows=[]
for pid,(path,effect,required) in ROWS.items():
 raw=(ROOT/path).read_bytes();s=raw.decode(errors="replace")
 if effect.lower() not in s.lower():raise RuntimeError(f"EFFECT_TX_NOT_IN_PINNED_REPORT_{pid}")
 found=lt_pairs(s);pairs={(x["old_lt_bps"],x["new_lt_bps"]) for x in found}
 missing=[x for x in required if x not in pairs]
 q=queue_line(pid)
 rows.append({"proposal_id":pid,"status":"PASS" if not missing else "SOURCE_BLOCKED",
              "proof_mode":"PINNED_SEATBELT_STATE_DIFF","payload_report":path,
              "payload_report_sha256":sha(raw),"effect_tx":effect,
              "lt_decrease_pairs":found,"required_pairs":required,"missing_required_pairs":missing,**q})

# Proposal 19: direct on-chain proof due failed Seatbelt simulation.
URL="https://mainnet.optimism.io"
POOL="0x794a61358d6845594f94dc1db02a252b5b4814ad"
CONFIG="0x8145edddf43f50276641b55bd3ad95944510021e"
EFFECT="0x22c2eb7b02ae215657fdccfc4d923b78dc035eefa85d23950c8074fc925d9444"
SIGNAL_TS=1707234251
last=0.0
def post(body):
 global last
 time.sleep(max(0,.12-(time.monotonic()-last)));last=time.monotonic()
 raw=json.dumps(body,sort_keys=True).encode()
 try:
  req=urllib.request.Request(URL,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
  with urllib.request.urlopen(req,timeout=45) as res:data=res.read();status=res.status;headers=dict(res.headers)
 except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
 except Exception as e:data=str(e).encode();status=0;headers={}
 h=sha(data);(OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0))
 with (OUT/"requests.jsonl").open("a") as f:f.write(json.dumps({"request":body,"http_status":status,"response_sha256":h,"headers":headers})+"\n")
 try:d=json.loads(data)
 except Exception:d={}
 return d,status,h
def rpc(method,params):
 lastv=None
 for a in range(16):
  d,status,h=post({"jsonrpc":"2.0","id":1,"method":method,"params":params});lastv=(d,status,h)
  if status==200 and isinstance(d,dict) and d.get("result") is not None:return d["result"],h
  time.sleep(min(8,.4*(a+1)))
 raise RuntimeError("RPC_EXHAUSTED_"+method+"_"+json.dumps(lastv))
def sig(s):
 k=keccak.new(digest_bits=256);k.update(s.encode());return "0x"+k.hexdigest()
T=sig("CollateralConfigurationChanged(address,uint256,uint256,uint256)")
SEL=sig("getConfiguration(address)")[:10]
# snapshot greatest block strictly before first Core queue timestamp
latest=int(rpc("eth_blockNumber",[])[0],16);lo,hi=0,latest
while lo<hi:
 m=(lo+hi+1)//2;b=rpc("eth_getBlockByNumber",[hex(m),False])[0];ts=int(b["timestamp"],16)
 if ts<SIGNAL_TS:lo=m
 else:hi=m-1
snap=lo;sh=rpc("eth_getBlockByNumber",[hex(snap),False])[0]
rcpt=rpc("eth_getTransactionReceipt",[EFFECT])[0]
if not rcpt or int(rcpt["status"],16)!=1:raise RuntimeError("P19_EFFECT_RECEIPT_BAD")
effect_block=int(rcpt["blockNumber"],16)
events=[]
for l in rcpt["logs"]:
 if l["address"].lower()!=CONFIG or not l.get("topics") or l["topics"][0].lower()!=T:continue
 if len(l["topics"])>=2:
  asset="0x"+l["topics"][1][-40:]
  words=[int(l["data"][2+i*64:2+(i+1)*64],16) for i in range((len(l["data"])-2)//64)]
  if len(words)<3:raise RuntimeError("P19_BAD_EVENT_DATA")
  new_ltv,new_lt,new_bonus=words[:3]
 else:
  words=[int(l["data"][2+i*64:2+(i+1)*64],16) for i in range((len(l["data"])-2)//64)]
  if len(words)<4:raise RuntimeError("P19_BAD_EVENT_DATA_UNINDEXED")
  asset="0x"+format(words[0],"040x");new_ltv,new_lt,new_bonus=words[1:4]
 cfg=rpc("eth_call",[{"to":POOL,"data":SEL+asset[2:].zfill(64)},hex(snap)])[0]
 old_raw=int(cfg,16);old_ltv=old_raw & 0xffff;old_lt=(old_raw>>16)&0xffff
 events.append({"asset":asset.lower(),"old_ltv_bps":old_ltv,"old_lt_bps":old_lt,
                "new_ltv_bps":new_ltv,"new_lt_bps":new_lt,"new_bonus_bps":new_bonus,
                "qualifying_lt_decrease":new_lt<old_lt})
q=queue_line(19)
rows.append({"proposal_id":19,"status":"PASS" if events and any(x["qualifying_lt_decrease"] for x in events) else "SOURCE_BLOCKED",
             "proof_mode":"DIRECT_OPTIMISM_SIGNAL_MINUS_ONE_AND_EFFECT_RECEIPT",
             "seatbelt_payload_report":"reports/payloads/10/0x0E1a3Af1f9cC76A62eD31eDedca291E63632e7c4/12.md",
             "seatbelt_simulation_failed":True,"signal_timestamp":SIGNAL_TS,"snapshot_block":snap,
             "snapshot_timestamp":int(sh["timestamp"],16),"effect_tx":EFFECT,"effect_block":effect_block,
             "events":events,**q})
rows.sort(key=lambda x:x["proposal_id"])
receipt={"lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001","phase":"V30_V3_PARAMETER_SEMANTICS_SOURCE_ONLY",
         "seatbelt_repo":"aave-dao/seatbelt-gov-v3","seatbelt_commit":SEATBELT_COMMIT,
         "proposal_count":len(rows),"pass_count":sum(x["status"]=="PASS" for x in rows),
         "all_v3_parameter_semantics_pass":all(x["status"]=="PASS" for x in rows),
         "rows":rows,"source_gate_pass":False,"hypothesis_status":"NOT_TESTED",
         "economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k!="rows"},indent=2),flush=True)
for r in rows:print(json.dumps({"proposal_id":r["proposal_id"],"status":r["status"],"proof_mode":r["proof_mode"]}),flush=True)
