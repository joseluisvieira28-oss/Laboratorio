#!/usr/bin/env python3
"""LP-NET-004: independent block-pinned 24h GLOBAL fee growth from Arbitrum V3.

This is a backward historical per-unit-liquidity diagnostic, NOT real fees
for our (nonexistent) position. Global growth only, cannot substitute for
feeGrowthInside at ticks; virtual deposit would dilute other LPs.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from decimal import Decimal,getcontext
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
getcontext().prec=58
RPC="https://arb1.arbitrum.io/rpc"
POOL="0xbe3ad6a5669dc0b8b12febc03608860c31e2eef6"
SEL={"global0":"0xf3058399","global1":"0x46141319",
     "slot0":"0x3850c7bd","L":"0x1a686502"}
UINT256=1<<256
Q128=1<<128
def post(method,params):
    req=Request(RPC,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),
         method="POST",headers={"Content-Type":"application/json","User-Agent":"LP-NET-004-24h-FEEGROWTH-RESEARCH/1.0"})
    with urlopen(req,timeout=12) as resp:raw=resp.read(1_000_000)
    obj=json.loads(raw)
    if not isinstance(obj,dict) or obj.get("error") or "result" not in obj:
         raise RuntimeError("RPC unavailable: "+str(obj.get("error") if isinstance(obj,dict) else obj)[:110])
    return obj["result"],hashlib.sha256(raw).hexdigest()
def block_info(number):
    val,sha=post("eth_getBlockByNumber",[hex(number),False])
    if not isinstance(val,dict) or int(val.get("number","0x0"),16)!=number:
        raise ValueError("missing block")
    return {"block_number":number,"block_timestamp":int(val["timestamp"],16),
            "block_hash":val["hash"],"rpc_sha256":sha}
def block_at_or_before(latest,seek_timestamp):
    low=max(0,latest-800000);high=latest
    first=block_info(low)
    if first["block_timestamp"]>seek_timestamp:raise ValueError("lookback exceeds fixed block range")
    count=0
    while low<high:
        if count>27:raise RuntimeError("block timestamp binary search unbounded")
        mid=(low+high+1)//2
        candidate=block_info(mid)
        if candidate["block_timestamp"]<=seek_timestamp:low=mid
        else:high=mid-1
        count+=1
    info=block_info(low);info["binary_search_queries"]=count
    if not 0<=seek_timestamp-info["block_timestamp"]<=600:raise ValueError("timestamp predecessor farther than 10 minutes")
    return info
def u256(s):
    if not isinstance(s,str) or not s.startswith("0x"):raise ValueError("bad u256")
    v=int(s,16)
    if v<0 or v>=UINT256:raise ValueError("u256 out of range")
    return v
def state(block):
    tag=hex(block)
    proof={}
    d={}
    for k,selector in SEL.items():
        raw,sha=post("eth_call",[{"to":POOL,"data":selector},tag])
        if not isinstance(raw,str) or len(raw)<66 or (len(raw)-2)%64:
            raise ValueError("historical archive state not available")
        chunks=[int(raw[i:i+64],16) for i in range(2,len(raw),64)]
        if k in ("global0","global1","L") and len(chunks)!=1:raise ValueError("ABI width")
        if k=="slot0" and len(chunks)!=7:raise ValueError("slot0 ABI width")
        proof[k]=sha
        if k=="slot0":
            tick=chunks[1]-(1<<256) if chunks[1]>=(1<<255) else chunks[1]
            d["tick"]=tick;d["sqrtPriceX96"]=str(chunks[0]);d["feeProtocol"]=chunks[5]
        else:d[k]=chunks[0]
    d["proof_sha256"]=proof
    return d
def collect(f):
    value,sha=post("eth_chainId",[])
    if int(value,16)!=42161:raise ValueError("wrong chain")
    n,_=post("eth_blockNumber",[])
    latest=int(n,16)
    end=block_info(latest)
    target=end["block_timestamp"]-86400
    start=block_at_or_before(latest,target)
    if not 86000<=end["block_timestamp"]-start["block_timestamp"]<=87000:
        raise ValueError("not a roughly 24-hour interval")
    s=state(start["block_number"]);e=state(end["block_number"])
    if s["feeProtocol"]!=68 or e["feeProtocol"]!=68:
        raise ValueError("feeProtocol no longer matches original 0x44 at endpoints")
    raw0=(e["global0"]-s["global0"])%UINT256
    raw1=(e["global1"]-s["global1"])%UINT256
    if raw0>=Q128*10**20 or raw1>=Q128*10**20:
        raise ValueError("unrealistic or wrapped fee growth")
    # Diff in pool global fee growth per raw L: active at all swaps only.
    growth0=Decimal(raw0)/Decimal(Q128)
    growth1=Decimal(raw1)/Decimal(Q128)
    p0=Decimal(f["price0_usd"]);p1=Decimal(f["price1_usd"])
    out=[]
    from arbitrum_static_fee_share_scenario import fee_scenarios
    for rec in fee_scenarios(f):
        lu=Decimal(rec["hypothetical_added_raw_liquidity_L"])
        token0=lu*growth0/Decimal(10**6)
        token1=lu*growth1/Decimal(10**6)
        usd=token0*p0+token1*p1
        out.append({"notional_usd":rec["notional_usd"],"half_width_frac":rec["half_width_frac"],
          "virtual_liquidity_L_T0":rec["hypothetical_added_raw_liquidity_L"],
          "raw_global_fee_growth_token0_per_rawL_Q128":str(raw0),
          "raw_global_fee_growth_token1_per_rawL_Q128":str(raw1),
          "historical_24h_global_if_always_active_token0_units":str(token0),
          "historical_24h_global_if_always_active_token1_units":str(token1),
          "historical_24h_global_if_always_active_USD_using_T0_prices":str(usd),
          "static_24h_volume_based_model_USD":rec["static_position_fees_per_day_usd"],
          "growth_not_fee_growth_inside":True,
          "actual_position_fee":None})
    return {"block_start":start,"block_end":end,
      "states_at_same_exact_blocks":{"start":s,"end":e},
      "raw_growth_delta_0":str(raw0),"raw_growth_delta_1":str(raw1),
      "fee_growth_global_historical":out,
      "crossed_ticks_and_fee_growth_inside":"NOT_RECONSTRUCTED",
      "virtual_addition_dilution":"NOT_APPLIED",
      "usd_marks":"T0 market prices not original hourly exchange rate; USD diagnostic only",
      "source_endpoint":RPC,
      "chain_id_proof_sha256":sha}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    raw=a.fixture.read_bytes();f=json.loads(raw)
    if f.get("raw_artifact_json_sha256")!="8c28d45226600e65a63a8bdd42b6155c77f83e5392b9ea49cd68fe13bd606f7b":
        raise ValueError("source fixture changed")
    output={"study":"LP-NET-004-ARBITRUM-24H-GLOBAL-FEEGROWTH",
       "source_fixture_sha256":hashlib.sha256(raw).hexdigest(),
       "no_trades":True,"capital_chf":0,"economic_verdict":"NO_LIVE_GO",
       "status":"SOURCE_BLOCKED","analysis":None}
    try:output["analysis"]=collect(f);output["status"]="BLOCK_PINNED_POOL_GLOBAL_FEEGROWTH_OBSERVED"
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as e:
        output["source_blocker"]=type(e).__name__+":"+str(e)[:180]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"status":output["status"],"cases":len(output["analysis"]["fee_growth_global_historical"]) if output["analysis"] else 0,
                      "economic_verdict":output["economic_verdict"]}))
if __name__=="__main__":main()
