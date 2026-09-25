#!/usr/bin/env python3
import base64,hashlib,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from web3 import Web3

MCP="https://mcp.aave.com/"
RPC="https://eth-mainnet.public.blastapi.io"
OUT=Path("artifacts/lcod_multi_borrower_block_pin_v01.json")
TOL=5e-5
TARGET=16
RAY=10**27
BPS_TO_WAD=10**14

SPOKE_ABI=[
 {"type":"function","name":"getReserveCount","stateMutability":"view","inputs":[],"outputs":[{"type":"uint256"}]},
 {"type":"function","name":"getReserve","stateMutability":"view","inputs":[{"type":"uint256"}],"outputs":[{"type":"tuple","components":[
  {"name":"underlying","type":"address"},{"name":"hub","type":"address"},{"name":"assetId","type":"uint16"},
  {"name":"decimals","type":"uint8"},{"name":"collateralRisk","type":"uint24"},{"name":"flags","type":"uint8"},{"name":"dynamicConfigKey","type":"uint32"}]}]},
 {"type":"function","name":"getUserReserveStatus","stateMutability":"view","inputs":[{"type":"uint256"},{"type":"address"}],"outputs":[{"type":"bool"},{"type":"bool"}]},
 {"type":"function","name":"getUserSuppliedAssets","stateMutability":"view","inputs":[{"type":"uint256"},{"type":"address"}],"outputs":[{"type":"uint256"}]},
 {"type":"function","name":"getUserPosition","stateMutability":"view","inputs":[{"type":"uint256"},{"type":"address"}],"outputs":[{"type":"tuple","components":[
  {"name":"drawnShares","type":"uint120"},{"name":"premiumShares","type":"uint120"},{"name":"premiumOffsetRay","type":"int200"},
  {"name":"suppliedShares","type":"uint120"},{"name":"dynamicConfigKey","type":"uint32"}]}]},
 {"type":"function","name":"getDynamicReserveConfig","stateMutability":"view","inputs":[{"type":"uint256"},{"type":"uint32"}],"outputs":[{"type":"tuple","components":[
  {"name":"collateralFactor","type":"uint16"},{"name":"maxLiquidationBonus","type":"uint32"},{"name":"liquidationFee","type":"uint16"}]}]},
 {"type":"function","name":"getUserPremiumDebtRay","stateMutability":"view","inputs":[{"type":"uint256"},{"type":"address"}],"outputs":[{"type":"uint256"}]},
 {"type":"function","name":"getUserAccountData","stateMutability":"view","inputs":[{"type":"address"}],"outputs":[{"type":"tuple","components":[
  {"name":"riskPremium","type":"uint256"},{"name":"avgCollateralFactor","type":"uint256"},{"name":"healthFactor","type":"uint256"},
  {"name":"totalCollateralValue","type":"uint256"},{"name":"totalDebtValueRay","type":"uint256"},
  {"name":"activeCollateralCount","type":"uint256"},{"name":"borrowCount","type":"uint256"}]}]},
 {"type":"function","name":"ORACLE","stateMutability":"view","inputs":[],"outputs":[{"type":"address"}]}
]
ORACLE_ABI=[{"type":"function","name":"getReservePrice","stateMutability":"view","inputs":[{"type":"uint256"}],"outputs":[{"type":"uint256"}]}]
HUB_ABI=[{"type":"function","name":"getAssetDrawnIndex","stateMutability":"view","inputs":[{"type":"uint256"}],"outputs":[{"type":"uint256"}]}]

def mcp_rpc(method,params):
    data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(MCP,data=data,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-LCOD-MultiBlockPin/0.1"},method="POST")
    with urllib.request.urlopen(req,timeout=45) as r:x=json.loads(r.read().decode())
    if x.get("error"):raise RuntimeError(x["error"])
    return x.get("result")

def unwrap(x):
    if isinstance(x,dict) and x.get("structuredContent") is not None:
        y=x["structuredContent"];return y.get("data") if isinstance(y,dict) and "data" in y else y
    if isinstance(x,dict) and "content" in x:
        for c in x["content"]:
            if isinstance(c,dict) and c.get("type")=="text":
                try:
                    y=json.loads(c.get("text",""));return y.get("data") if isinstance(y,dict) and "data" in y else y
                except Exception:pass
    return x.get("data") if isinstance(x,dict) and "data" in x else x

def tool(name,args):return unwrap(mcp_rpc("tools/call",{"name":name,"arguments":args}))

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)

def decode_reserve_id(s):
    try:
        raw=base64.b64decode(s+"="*((-len(s))%4)).decode()
        chain,spoke,rid=raw.split("::")
        if chain!="1" or not re.fullmatch(r"0x[a-fA-F0-9]{40}",spoke):return None
        return spoke.lower(),int(rid),s
    except Exception:return None

def holder_addresses(x):
    out=set()
    for d in walk(x):
        for k in ("user","address","wallet"):
            v=d.get(k)
            if isinstance(v,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",v):
                out.add(v.lower())
    return out

def h(v):return hashlib.sha256(json.dumps(v,sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()

w3=Web3(Web3.HTTPProvider(RPC,request_kwargs={"timeout":45}))
final=w3.eth.get_block("finalized")
N=int(final["number"]);block_hash=final["hash"].hex()

markets=tool("get_markets",{"version":"v4","chainId":1})
opaque=sorted({str(d.get("reserveId")) for d in walk(markets) if isinstance(d.get("reserveId"),str)})
decoded=sorted(x for x in (decode_reserve_id(s) for s in opaque) if x is not None)

candidate_pairs=set();selection_errors=[]
for spoke_l,rid,opaque_id in decoded:
    try:
        cursor=None;seen=set()
        for _ in range(100):
            args={"reserveId":opaque_id,"side":"borrow","limit":50,"version":"v4"}
            if cursor:args["cursor"]=cursor
            page=tool("get_reserve_holders",args)
            for u in holder_addresses(page): candidate_pairs.add((spoke_l,u))
            curs=[]
            for d in walk(page):
                v=d.get("nextCursor") or d.get("next_cursor")
                if isinstance(v,str) and v.strip():curs.append(v.strip())
            curs=list(dict.fromkeys(curs))
            if not curs:break
            if len(curs)!=1 or curs[0] in seen:
                selection_errors.append("CURSOR_AMBIGUOUS_OR_LOOP");break
            seen.add(curs[0]);cursor=curs[0]
    except Exception as e:
        selection_errors.append(f"holders:{spoke_l}:{rid}:{type(e).__name__}")

ordered=sorted(candidate_pairs,key=lambda p:(p[0],hashlib.sha256(p[1].encode()).hexdigest()))
selected=[]
for spoke_l,user_l in ordered:
    spoke=Web3.to_checksum_address(spoke_l)
    user=Web3.to_checksum_address(user_l)
    contract=w3.eth.contract(address=spoke,abi=SPOKE_ABI)
    try:uad=contract.functions.getUserAccountData(user).call(block_identifier=N)
    except Exception as e:
        selection_errors.append(f"uad:{spoke_l}:{type(e).__name__}");continue
    if int(uad[4])>0:
        selected.append((spoke_l,user_l,uad))
        if len(selected)==TARGET:break

rows=[];recon_errors=[]
for spoke_l,user_l,uad in selected:
    spoke=Web3.to_checksum_address(spoke_l);user=Web3.to_checksum_address(user_l)
    contract=w3.eth.contract(address=spoke,abi=SPOKE_ABI)
    try:
        oracle_addr=contract.functions.ORACLE().call(block_identifier=N)
        oracle=w3.eth.contract(address=oracle_addr,abi=ORACLE_ABI)
        count=int(contract.functions.getReserveCount().call(block_identifier=N))
        weighted=0;debt_value_ray=0;active=0
        for rid in range(count):
            status=contract.functions.getUserReserveStatus(rid,user).call(block_identifier=N)
            collateral,borrowing=bool(status[0]),bool(status[1])
            if not collateral and not borrowing:continue
            active+=1
            reserve=contract.functions.getReserve(rid).call(block_identifier=N)
            underlying,hub_addr,asset_id,decimals,collateral_risk,flags,reserve_key=reserve
            pos=contract.functions.getUserPosition(rid,user).call(block_identifier=N)
            drawn_shares,premium_shares,premium_offset,supplied_shares,user_key=map(int,pos)
            price=int(oracle.functions.getReservePrice(rid).call(block_identifier=N))
            scale=10**(18-int(decimals))
            if collateral:
                cf=int(contract.functions.getDynamicReserveConfig(rid,user_key).call(block_identifier=N)[0])
                supplied=int(contract.functions.getUserSuppliedAssets(rid,user).call(block_identifier=N))
                if cf>0 and supplied>0: weighted+=supplied*price*scale*cf
            if borrowing:
                premium_ray=int(contract.functions.getUserPremiumDebtRay(rid,user).call(block_identifier=N))
                hub=w3.eth.contract(address=Web3.to_checksum_address(hub_addr),abi=HUB_ABI)
                drawn_index=int(hub.functions.getAssetDrawnIndex(int(asset_id)).call(block_identifier=N))
                debt_ray=drawn_shares*drawn_index+premium_ray
                debt_value_ray+=debt_ray*price*scale
        if debt_value_ray<=0: raise RuntimeError("ZERO_DEBT_AT_BLOCK")
        reconstructed=(weighted*BPS_TO_WAD*RAY)//debt_value_ray
        official=int(uad[2])
        rel=abs(reconstructed-official)/official if official>0 else None
        rows.append({
          "pair_sha256":hashlib.sha256((spoke_l+"::"+user_l).encode()).hexdigest(),
          "spoke_address":spoke_l,
          "active_leg_count":active,
          "official_hf_wad_sha256":h(official),
          "reconstructed_hf_wad_sha256":h(reconstructed),
          "relative_hf_error":rel,
          "pass":rel is not None and rel<=TOL
        })
    except Exception as e:
        recon_errors.append(f"{hashlib.sha256((spoke_l+'::'+user_l).encode()).hexdigest()}:{type(e).__name__}:{str(e)[:180]}")

passed=(len(selected)==TARGET and len(rows)==TARGET and all(x["pass"] for x in rows) and not recon_errors)
receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"MULTI_BORROWER_SAME_BLOCK_SCALE_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"MULTI_BORROWER_BLOCK_PIN_PASS" if passed else "MULTI_BORROWER_BLOCK_PIN_BLOCKED",
 "ethereum_block_number":N,"ethereum_block_hash":block_hash,"block_tag_policy":"finalized",
 "candidate_pair_count":len(candidate_pairs),"selected_debt_pair_count":len(selected),
 "target_pair_count":TARGET,"passing_pair_count":sum(1 for x in rows if x.get("pass")),
 "max_relative_hf_error":max((x["relative_hf_error"] for x in rows if x["relative_hf_error"] is not None),default=None),
 "frozen_tolerance":TOL,"rows":rows,"selection_errors":selection_errors[:100],"reconstruction_errors":recon_errors[:100],
 "all_scientific_eth_calls_block_pinned":True,"raw_wallet_retained":False,
 "curve_computed":False,"market_returns_opened":False,"liquidation_outcomes_opened":False,
 "pnl_opened":False,"mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k!="rows"},indent=2))
if not passed:raise SystemExit(2)
