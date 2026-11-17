#!/usr/bin/env python3
"""LP-NET-002: bounded, read-only, evidence-only Ethereum Uniswap v3 event probe.
No wallet, trading, API key, or profit promotion. Single declared burn block
per historical NFT; this is NOT a complete position-lifecycle reconstruction.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from decimal import Decimal
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

MANAGER="0xc36442b4a4522e871399cd717abdd847ab11fe88"
POOL="0x6c6bc977e13df9b0de53b251522280bb72383700"
FACTORY="0x1f98431c8ad98523631ae4a59f267346ea31f984"
DAI="0x6b175474e89094c44da98b954eedeac495271d0f"
USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
POSITION_SELECTOR="0x99fbab88"
GET_POOL_SELECTOR="0x1698ee82"
INCREASE="0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f"
DECREASE="0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4"
COLLECT="0x40d0efd1a53d60ecbf40971b9daf7dc90178c3aadc7aab1765632738fa8b8f01"
TYPES={INCREASE:"IncreaseLiquidity",DECREASE:"DecreaseLiquidity",COLLECT:"Collect"}
TARGETS=[
 {"token_id":102244,"block":12964997,"source_event_timestamp":1628166792,"source_id":"102244#12964997","source_fee_usd":0.06938},
 {"token_id":107633,"block":15092225,"source_event_timestamp":1657153859,"source_id":"107633#15092225","source_fee_usd":4.412673},
 {"token_id":106475,"block":17948957,"source_event_timestamp":1692449783,"source_id":"106475#17948957","source_fee_usd":4849.255522},
]
PUBLIC_RPC=("https://ethereum.publicnode.com","https://eth.llamarpc.com","https://1rpc.io/eth")

def topicid(x:int)->str:return "0x"+format(x,"064x")
def words(s:str)->list[int]:
 if not s.startswith("0x") or (len(s)-2)%64:raise ValueError("Invalid ABI word layout")
 return [int(s[i:i+64],16) for i in range(2,len(s),64)]

def decode_event(item:dict,token_id:int)->dict|None:
 topics=item.get("topics",[])
 if item.get("address","").lower()!=MANAGER or len(topics)!=2:return None
 event=TYPES.get(topics[0].lower())
 if event is None or int(topics[1],16)!=token_id:return None
 w=words(item["data"])
 if len(w)!=3:raise ValueError("Unexpected ABI fields")
 out={"type":event,"amount0_raw":w[1],"amount1_raw":w[2]}
 if event=="Collect":
  out["recipient"]="0x"+format(w[0],"064x")[-40:]
  out["fee_attribution"]="UNKNOWN_COLLECT_INCLUDES_WITHDRAWN_PRINCIPAL"
 else:out["liquidity_raw"]=w[0]
 return out

def get_rpc(url:str,method:str,params:list)->object:
 u=urlsplit(url)
 if u.scheme!="https" or not u.netloc or u.username or u.password or u.query or u.fragment:
  raise ValueError("RPC URL must be HTTPS without credentials or query")
 request=Request(url,method="POST",headers={"Content-Type":"application/json","User-Agent":"LP-NET-002/0.1"},
                 data=json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":1}).encode())
 with urlopen(request,timeout=12) as reply:
  out=json.loads(reply.read(2_000_000))
 if out.get("error"):raise RuntimeError(str(out["error"])[:150])
 if "result" not in out:raise RuntimeError("Missing JSON-RPC result")
 return out["result"]

def gas_eth(receipt:dict)->str|None:
 if "gasUsed" not in receipt or "effectiveGasPrice" not in receipt:return None
 return str(Decimal(int(receipt["gasUsed"],16))*Decimal(int(receipt["effectiveGasPrice"],16))/Decimal(10**18))

def probe_one(url:str,target:dict)->dict:
 block=target["block"];tid=target["token_id"]
 logs=get_rpc(url,"eth_getLogs",[{"address":MANAGER,"fromBlock":hex(block),"toBlock":hex(block),
                "topics":[list(TYPES.keys()),topicid(tid)]}])
 if not isinstance(logs,list):raise RuntimeError("eth_getLogs not array")
 items=[];receipts={}
 for log in logs:
  val=decode_event(log,tid)
  if val is None:continue
  if int(log["blockNumber"],16)!=block:raise RuntimeError("Log wrong block")
  txhash=log["transactionHash"].lower()
  if txhash not in receipts:
   rc=get_rpc(url,"eth_getTransactionReceipt",[txhash])
   if rc is None or int(rc.get("status","0x0"),16)!=1 or int(rc["blockNumber"],16)!=block:
    raise RuntimeError("Missing or failed receipt")
   receipt_indexes={int(x["logIndex"],16) for x in rc.get("logs",[])
                    if x.get("address","").lower()==MANAGER}
   if int(log["logIndex"],16) not in receipt_indexes:raise RuntimeError("Log absent in receipt")
   receipts[txhash]={"receipt_sha256":hashlib.sha256(json.dumps(rc,sort_keys=True).encode()).hexdigest(),
                     "gas_used":int(rc["gasUsed"],16),"gas_price_wei":int(rc.get("effectiveGasPrice","0x0"),16),
                     "total_tx_fee_eth":gas_eth(rc),"receipt_block_hash":rc["blockHash"],
                     "gas_allocation_to_one_position":"UNKNOWN_IF_SHARED_TRANSACTION"}
  val.update({"tx_hash":txhash,"log_index":int(log["logIndex"],16),"tx_index":int(log["transactionIndex"],16)})
  items.append(val)
 blockinfo=get_rpc(url,"eth_getBlockByNumber",[hex(block),False])
 if blockinfo is None or int(blockinfo["number"],16)!=block:raise RuntimeError("Missing block")
 ts=int(blockinfo["timestamp"],16)
 same=ts==target["source_event_timestamp"]
 identity={"state":"ARCHIVE_NFT_POSITION_NOT_CHECKED"}
 try:
  # Use pre-withdrawal block to avoid a potentially burned NFT in the target block.
  state=get_rpc(url,"eth_call",[{"to":MANAGER,"data":POSITION_SELECTOR+format(tid,"064x")},hex(block-1)])
  state_words=words(state)
  if len(state_words)!=12:raise ValueError("Unexpected positions() output")
  token0="0x"+format(state_words[2],"064x")[-40:]
  token1="0x"+format(state_words[3],"064x")[-40:]
  tier=state_words[4]
  if (token0,token1,tier)!=(DAI,USDC,500):raise ValueError("NFT token pair or tier mismatch")
  pool_call=GET_POOL_SELECTOR+format(int(DAI,16),"064x")+format(int(USDC,16),"064x")+format(500,"064x")
  returned_pool=words(get_rpc(url,"eth_call",[{"to":FACTORY,"data":pool_call},hex(block-1)]))
  if len(returned_pool)!=1:raise ValueError("Unexpected factory getPool() output")
  factory_pool="0x"+format(returned_pool[0],"064x")[-40:]
  if factory_pool!=POOL:raise ValueError("Factory pool identity mismatch")
  identity={"state":"NFT_PAIR_AND_FACTORY_POOL_VERIFIED","token0":token0,"token1":token1,
            "fee_tier":tier,"factory_pool":factory_pool}
 except (OSError,RuntimeError,ValueError,KeyError,TypeError,OverflowError) as exc:
  identity={"state":"NFT_POOL_IDENTITY_NOT_VERIFIED",
            "reason_type":type(exc).__name__,"reason":str(exc)[:150]}
 return {**target,"state":("TIMESTAMP_MISMATCH" if not same else
                            "SOURCE_EVENTS_PRESENT" if items else "NO_LOGS_AT_DECLARED_BLOCK"),
         "timestamp_matches_csv":same,"block_hash":blockinfo["hash"],"observed_timestamp":ts,
         "manager_address_verified_as_log_emitter":bool(items),
         "pool_identity_verified_from_nft_position":identity["state"]=="NFT_PAIR_AND_FACTORY_POOL_VERIFIED",
         "position_pool_identity":identity,
         "events":sorted(items,key=lambda x:(x["tx_index"],x["log_index"])),
         "receipts":receipts,"raw_collect_fee_is_separable":False,"net_profit_usd":None}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--output",type=Path,default=Path("lp_net_002_onchain_receipt.json"))
 p.add_argument("--rpc",action="append",default=[])
 p.add_argument("--offline",action="store_true",help="No network; record source blocker")
 args=p.parse_args()
 out={"study":"LP-NET-002","mode":"SINGLE_BLOCK_READ_ONLY","eth_chain_id_required":1,
      "no_trades":True,"no_wallet":True,"capital_used_chf":0,"targets":TARGETS,
      "economic_verdict":"NO_LIVE_GO","pnl_usd":None,"results":[],"errors":[]}
 if args.offline:out["state"]="SOURCE_BLOCKED_OFFLINE_MODE"
 else:
  for t in TARGETS:
   ok=False
   for url in (args.rpc or list(PUBLIC_RPC)):
    try:
     chain=get_rpc(url,"eth_chainId",[])
     if int(chain,16)!=1:raise RuntimeError("RPC is not Ethereum mainnet")
     r=probe_one(url,t);r["rpc_source"]=url;out["results"].append(r);ok=True;break
    except (OSError,ValueError,RuntimeError,TypeError,KeyError,OverflowError) as exc:
     out["errors"].append({"token_id":t["token_id"],"rpc":url,
                           "error_type":type(exc).__name__,"detail":str(exc)[:150]})
   if not ok:out["results"].append({**t,"state":"SOURCE_BLOCKED_RPC","pnl_usd":None})
  out["state"]=("SOURCE_PARTIALLY_OBSERVED_NOT_RECONSTRUCTED" if any(
    x["state"]=="SOURCE_EVENTS_PRESENT" for x in out["results"]) else "SOURCE_BLOCKED")
 out["next_gate"]="Complete tokenId lifecycle including minted liquidity, decreases, collect fees, NFT/pool validation, gas by position, prices, chronological OOS."
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
 print(json.dumps({"state":out["state"],"events":sum(len(x.get("events",[])) for x in out["results"]),
                   "economic_verdict":out["economic_verdict"]}))
if __name__=="__main__":main()
