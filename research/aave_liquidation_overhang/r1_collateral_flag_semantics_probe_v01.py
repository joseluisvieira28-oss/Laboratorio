#!/usr/bin/env python3
from __future__ import annotations
import json,sys,time
from pathlib import Path
from collections import Counter
import requests
from eth_hash.auto import keccak

POOL="0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
BLOCK=21525890
PROVIDERS=[
 "https://eth-mainnet.public.blastapi.io",
 "https://rpc.mevblocker.io",
 "https://ethereum.blinklabs.xyz/",
]
PAIRS=[
 {"reserve":"0x514910771af9ca656af840dff83e8264ecf986ca","aToken":"0x5e8c8a7243651db1384c0ddfdbe39761e8e7e51a","user":"0xd43607346490e89f7e2e0b8ac0fa730790e5c154"},
 {"reserve":"0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2","aToken":"0x4d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e8","user":"0xa9c39d49be0511fb4698f1452e267dbdda2f5b1e"},
 {"reserve":"0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0","aToken":"0x0b925ed163218f6662a35e0f0371ac234f9e9371","user":"0xd814e1b7cc203ff6ca4358bf4aa3ce9771fedc68"},
 {"reserve":"0xae78736cd615f374d3085123a210448e74fc6393","aToken":"0xcc9ee9483f662091a1de4795249e24ac0ac2630f","user":"0xb5b29320d2dde5ba5bafa1ebcd270052070483ec"},
 {"reserve":"0x2260fac5e5542a773aa44fbcfedf7c193bc2c599","aToken":"0x5ee5bf7ae06d1be5997a1a72006fe6c607ec6de8","user":"0x6f260d8dbde1ea4e1411f375cc1b0d0438ffa35e"},
]
def sel(sig): return keccak(sig.encode())[:4].hex()
GET_RESERVE=sel("getReserveData(address)")
GET_USER=sel("getUserConfiguration(address)")
SCALED=sel("scaledBalanceOf(address)")
def calldata(selector,addr): return "0x"+selector+"0"*24+addr[2:]
def call(ep,to,data):
    payload={"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":to,"data":data},hex(BLOCK)]}
    last=None
    for k in range(3):
        try:
            r=requests.post(ep,json=payload,timeout=(10,45),headers={"Content-Type":"application/json","User-Agent":"AAVE-R1-flag-semantics-v0.1"})
            r.raise_for_status(); o=r.json(); r.close()
            if o.get("error") is not None: raise RuntimeError(str(o["error"]))
            x=o.get("result")
            if not isinstance(x,str) or not x.startswith("0x"): raise RuntimeError("invalid result")
            return x
        except Exception as e:
            last=e; time.sleep(1.5*(k+1))
    raise RuntimeError(str(last))
def qint(vals):
    xs=[int(x,16) for x in vals]
    if len(xs)<2: raise RuntimeError("quorum<2")
    if len(set(xs))!=1: raise RuntimeError(f"provider disagreement {xs}")
    return xs[0]
def main():
    rows=[]; technical=[]
    for p in PAIRS:
        per={"reserveData":[],"userConfig":[],"scaledBalance":[]}
        for ep in PROVIDERS:
            try:
                per["reserveData"].append(call(ep,POOL,calldata(GET_RESERVE,p["reserve"])))
                per["userConfig"].append(call(ep,POOL,calldata(GET_USER,p["user"])))
                per["scaledBalance"].append(call(ep,p["aToken"],calldata(SCALED,p["user"])))
            except Exception as e:
                technical.append({"provider":ep,"pair":p,"error":str(e)[:300]})
        try:
            rd=per["reserveData"]
            if len(rd)<2: raise RuntimeError("reserveData quorum<2")
            if len(set(rd))!=1: raise RuntimeError("reserveData disagreement")
            h=rd[0][2:]
            words=[int(h[i:i+64],16) for i in range(0,len(h),64)]
            if len(words)<8: raise RuntimeError("reserveData too short")
            reserve_id=words[7]
            uc=qint(per["userConfig"]); sb=qint(per["scaledBalance"])
            flag=((uc>>((reserve_id<<1)+1))&1)==1
            rows.append({**p,"reserve_id":reserve_id,"scaled_balance":str(sb),"collateral_flag":flag,"stale_flag_zero_scaled":bool(flag and sb==0)})
        except Exception as e:
            technical.append({"pair":p,"error":str(e)[:300]})
    observed=[r for r in rows if r["stale_flag_zero_scaled"]]
    if observed:
        classification="STALE_COLLATERAL_FLAG_ZERO_SCALED_STATE_OBSERVED"
    elif len(rows)==len(PAIRS):
        classification="NO_TERMINAL_STALE_FLAG_OBSERVED"
    else:
        classification="TECHNICAL_INCONCLUSIVE"
    out={
      "lab_id":"AAVE-LIQUIDATION-OVERHANG-001",
      "probe_id":"R1-COLLATERAL-FLAG-SEMANTICS-PROBE-V0.1",
      "classification":classification,
      "block":BLOCK,
      "pairs":rows,
      "observed_count":len(observed),
      "technical_errors":technical,
      "provider_set":PROVIDERS,
      "quorum_required":2,
      "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcomes_opened":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
    }
    Path("out/aave_flag_semantics").mkdir(parents=True,exist_ok=True)
    Path("out/aave_flag_semantics/AAVE_R1_COLLATERAL_FLAG_SEMANTICS_PROBE_V0_1.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"observed_count":len(observed),"rows":len(rows)},sort_keys=True))
    return 0 if classification!="TECHNICAL_INCONCLUSIVE" else 2
if __name__=="__main__": sys.exit(main())
