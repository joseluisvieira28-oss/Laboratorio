#!/usr/bin/env python3
"""LP-NET-004: immutable 9-L2-pool, no-key, read-only state and market probe.

This sources pool-level FACTS, not a replicable individual LP APR.
Never transacts or creates wallets. Failure of a provider => SOURCE_BLOCKED.
"""
from __future__ import annotations
import argparse,hashlib,json,time,math
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation,getcontext
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
getcontext().prec=55
RPC={
 "base":("https://mainnet.base.org","https://base.publicnode.com"),
 "arbitrum":("https://arb1.arbitrum.io/rpc","https://arbitrum-one.publicnode.com"),
 "optimism":("https://mainnet.optimism.io","https://optimism.publicnode.com")}
SEL={"token0":"0x0dfe1681","token1":"0xd21220a7","fee":"0xddca3f43",
    "slot0":"0x3850c7bd","liquidity":"0x1a686502",
    "tickSpacing":"0xd0c93a7c","decimals":"0x313ce567"}
CHAIN_DEX={"base":"base","arbitrum":"arbitrum","optimism":"optimism"}
RPC_TIMEOUT=9
FEE_PRICE="https://coins.llama.fi/prices/current/coingecko:ethereum"
LIMIT_URLS=("https://api.geckoterminal.com/api/v2/networks/",
            "https://api.dexscreener.com/latest/dex/pairs/",
            "https://coins.llama.fi/prices/current/")
def fetch(url,method="GET",payload=None):
    req=Request(url,method=method,data=(json.dumps(payload).encode() if payload is not None else None),
        headers={"Accept":"application/json","Content-Type":"application/json",
                 "User-Agent":"CryptoLab-LP-NET-004-READONLY/1.0"})
    with urlopen(req,timeout=RPC_TIMEOUT) as resp:raw=resp.read(1_000_000)
    return json.loads(raw),hashlib.sha256(raw).hexdigest()
def decimal_positive(v):
    d=Decimal(str(v))
    if not d.is_finite() or d<=0:raise ValueError("non-positive or nonfinite")
    return d
def words(raw,number=None):
    if not isinstance(raw,str) or not raw.startswith("0x") or (len(raw)-2)%64:
        raise ValueError("invalid ABI encoding")
    out=[int(raw[i:i+64],16) for i in range(2,len(raw),64)]
    if number is not None and len(out)!=number:raise ValueError("unexpected ABI width")
    return out
def addr(w):
    return "0x"+format(w,"064x")[-40:]
def signed256(v):
    return v-(1<<256) if v>=(1<<255) else v
def rpc_direct(url,method,params):
    out,sha=fetch(url,method="POST",payload={"jsonrpc":"2.0","id":1,"method":method,"params":params})
    if not isinstance(out,dict) or out.get("error") or "result" not in out:
        raise RuntimeError("invalid JSON RPC: "+str(out.get("error") if isinstance(out,dict) else out)[:100])
    return out["result"],sha
def routescan(chain_id,method,params):
    api=f"https://api.routescan.io/v2/network/mainnet/evm/{chain_id}/etherscan/api"
    if method=="eth_call":
        call,tag=params
        query={"module":"proxy","action":"eth_call","to":call["to"],
               "data":call["data"],"tag":tag}
    elif method=="eth_gasPrice":
        query={"module":"proxy","action":"eth_gasPrice"}
    else:raise ValueError("unsupported archive proxy method")
    out,sha=fetch(api+"?"+urlencode(query))
    if not isinstance(out,dict) or not isinstance(out.get("result"),str):
        raise RuntimeError("Routescan public proxy unavailable: "+str(out.get("message") if isinstance(out,dict) else out)[:100])
    return out["result"],sha
class Source:
    def __init__(self,chain,chain_id):
        self.chain=chain;self.chain_id=chain_id
        self.kind=None;self.endpoint=None;self.errors=[]
        for url in RPC[chain]:
            try:
                value,proof=rpc_direct(url,"eth_chainId",[])
                if int(value,16)!=chain_id:raise ValueError("wrong chainId")
                self.kind="RPC_CHAIN_VERIFIED";self.endpoint=url;self.chain_sha=proof
                break
            except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
                self.errors.append({"endpoint":url,"failure":type(exc).__name__+":"+str(exc)[:95]})
        if self.kind is None:
            # Chain is constrained by routescan's network URL, not independently eth_chainId.
            self.kind="ROUTESCAN_CHAIN_SPECIFIC_PROXY"
            self.endpoint=f"routescan:eip155:{chain_id}"
    def call(self,to,selector):
        request={"to":to,"data":selector}
        if self.kind=="RPC_CHAIN_VERIFIED":
            return rpc_direct(self.endpoint,"eth_call",[request,"latest"])
        return routescan(self.chain_id,"eth_call",[request,"latest"])
    def gas_price(self):
        if self.kind=="RPC_CHAIN_VERIFIED":
            return rpc_direct(self.endpoint,"eth_gasPrice",[])
        return routescan(self.chain_id,"eth_gasPrice",[])
def read_chain(candidate,src:Source):
    address=candidate["addr"]
    proof={}
    raw={}
    for method in ("token0","token1","fee","slot0","liquidity","tickSpacing"):
        value,sha=src.call(address,SEL[method])
        raw[method]=value;proof[method]=sha
    token0,token1=(addr(words(raw[k],1)[0]) for k in ("token0","token1"))
    fee=words(raw["fee"],1)[0]
    if fee !=candidate["fee_bps"]*100:raise ValueError("claimed pool fee tier differs from onchain")
    slot=words(raw["slot0"],7)
    active=words(raw["liquidity"],1)[0]
    spacing=signed256(words(raw["tickSpacing"],1)[0])
    if not (token0!=token1 and 0<active and spacing>0 and 0<slot[0]<2**160):
        raise ValueError("abnormal onchain pool parameters")
    fp=int(slot[5])
    cuts=[Decimal(0) if x==0 else Decimal(1)/Decimal(x)
          for x in (fp&0xf,fp>>4&0xf)]
    if any((x!=0 and not (4<=x<=10)) for x in (fp&0xf,fp>>4&0xf)):
        raise ValueError("nonstandard protocolFee nibble")
    token_decimals={}
    for t in (token0,token1):
        value,sha=src.call(t,SEL["decimals"])
        dec=words(value,1)[0]
        if dec not in (6,8,18):raise ValueError("unexpected decimals for stablecoin")
        token_decimals[t]={"decimals":dec,"sha256":sha}
    gas,gsha=src.gas_price()
    gas_wei=int(gas,16)
    if gas_wei<=0:raise ValueError("invalid gas price")
    tick=signed256(slot[1])
    if not (-887272<=tick<=887272):raise ValueError("tick out of bounds")
    dec0,dec1=(token_decimals[t]["decimals"] for t in (token0,token1))
    price_ratio=(Decimal(slot[0])/Decimal(2**96))**2 * Decimal(10)**(dec0-dec1)
    if not price_ratio.is_finite() or price_ratio<=0:raise ValueError("invalid onchain spot ratio")
    return {"status":"POOL_STATE_ONCHAIN_OBSERVED","rpc_kind":src.kind,
       "chain_id":candidate["chain_id"],"pool":address,"chain_verification":src.kind,
       "token0":token0,"token1":token1,"token_decimals":token_decimals,
       "fee_tier_raw":fee,"tick_spacing":spacing,"slot0_tick":tick,
       "sqrtPriceX96":str(slot[0]),"token1_per_token0_spot":str(price_ratio),
       "active_liquidity_raw_L":str(active),
       "IMPORTANT_active_L_is_not_dollar_TVL":True,
       "slot0_fee_protocol_byte":fp,
       "fee_protocol_token0_cut":str(cuts[0]),
       "fee_protocol_token1_cut":str(cuts[1]),
       "nominal_swap_fee_fraction":str(Decimal(fee)/Decimal(1_000_000)),
       "lp_effective_swap_fee_by_direction":[str(Decimal(fee)/Decimal(1_000_000)*(1-x)) for x in cuts],
       "gas_price_wei":gas_wei,"gas_price_proof_sha256":gsha,
       "proof_sha256_each_call":proof}
def market(candidate):
    net=candidate["network"];address=candidate["addr"]
    g,gh=fetch(f"https://api.geckoterminal.com/api/v2/networks/{net}/pools/{address}")
    d,dh=fetch(f"https://api.dexscreener.com/latest/dex/pairs/{CHAIN_DEX[net]}/{address}")
    data=g.get("data") or {}
    attrs=data.get("attributes") or {}
    relation=data.get("relationships") or {}
    base_id=(relation.get("base_token") or {}).get("data",{}).get("id")
    quote_id=(relation.get("quote_token") or {}).get("data",{}).get("id")
    if attrs.get("address","").lower()!=address:
        raise ValueError("Gecko pool address mismatch or missing")
    gvol=Decimal(str(attrs.get("volume_usd",{}).get("h24",0)))
    gtvl=Decimal(str(attrs.get("reserve_in_usd",0)))
    if not (gvol.is_finite() and gvol>=0 and gtvl.is_finite() and gtvl>=0):
        raise ValueError("bad market values")
    pair=next((x for x in (d.get("pairs") or [])
       if x.get("pairAddress","").lower()==address and
          x.get("chainId","").lower()==net),None)
    out={"status":"MARKET_RECEIVED","gecko_sha256":gh,"dex_sha256":dh,
       "gecko_address":attrs.get("address"),"gecko_dex_id":(relation.get("dex") or {}).get("data",{}).get("id"),
       "gecko_token_ids":[base_id,quote_id],"gecko_price_usd":[attrs.get("base_token_price_usd"),attrs.get("quote_token_price_usd")],
       "gecko_tvl_usd":str(gtvl),"gecko_vol24_usd":str(gvol),
       "dex_pair_found":pair is not None}
    if pair:
        dv=Decimal(str(pair.get("volume",{}).get("h24",0)))
        dl=Decimal(str(pair.get("liquidity",{}).get("usd",0)))
        out["dex_volume24_usd"]=str(dv);out["dex_liquidity_usd"]=str(dl)
        out["dex_token_addresses"]=[pair.get("baseToken",{}).get("address"),
               pair.get("quoteToken",{}).get("address")]
        if gtvl>0 and dl>0 and gvol>0 and dv>0:
            out["volume_diff_frac"]=str(abs(gvol-dv)/max(gvol,dv))
            out["reserve_diff_frac"]=str(abs(gtvl-dl)/max(gtvl,dl))
            out["two_source_consistent"]=(abs(gvol-dv)/max(gvol,dv)<=Decimal("0.35") and
                abs(gtvl-dl)/max(gtvl,dl)<=Decimal("0.35"))
        else:out["two_source_consistent"]=False
    else:out["two_source_consistent"]=False
    return out
def native_price(now):
    try:
        body,sha=fetch(FEE_PRICE)
        value=(body.get("coins") or {}).get("coingecko:ethereum")
        if not isinstance(value,dict):raise ValueError("no ETH quote")
        usd=decimal_positive(value["price"]);ts=int(value["timestamp"])
        if not 0<=now-ts<=900:raise ValueError("ETH USD quote stale/future")
        if value.get("confidence") is not None and Decimal(str(value["confidence"]))<Decimal(".9"):
            raise ValueError("weak ETH USD source confidence")
        return {"source":"DefiLlama ETH current","sha256":sha,"eth_usd":str(usd),"timestamp":ts,"status":"PASS"}
    except (OSError,ValueError,TypeError,KeyError) as e:
        return {"status":"PRICE_SOURCE_BLOCKED","error":type(e).__name__+":"+str(e)[:150]}
def combine(c,mc,chain,eth):
    out={"id":c["id"],"network":c["network"],"chain_id":c["chain_id"],
       "pair":c["token_pair"],"fee_bps":c["fee_bps"],"address":c["addr"],"market":mc,"onchain":chain,
       "source_screen":"BLOCKED","economic_verdict":"NO_LIVE_GO"}
    if mc.get("status")!="MARKET_RECEIVED" or chain.get("status")!="POOL_STATE_ONCHAIN_OBSERVED":
        out["reason"]="MISSING_MARKET_OR_ONCHAIN";return out
    gecko=[str(v or "").lower().split("_")[-1] for v in mc.get("gecko_token_ids",[])]
    if not (len(gecko)==2 and set(gecko)=={chain["token0"],chain["token1"]}):
        out["reason"]="GECKO_TOKEN_CONTRACT_IDENTITY_UNVERIFIED";return out
    if mc.get("dex_pair_found"):
        pair=[str(x or "").lower() for x in mc.get("dex_token_addresses",[])]
        if set(pair)!={chain["token0"],chain["token1"]}:
            out["reason"]="DEX_TOKEN_CONTRACT_IDENTITY_UNVERIFIED";return out
    try:
        prices=[decimal_positive(v) for v in mc["gecko_price_usd"]]
        if any(not Decimal(".995")<=v<=Decimal("1.005") for v in prices):
            out["reason"]="STABLECOIN_PRICE_OUTSIDE_FROZEN_SAFE_RANGE";return out
        vol=Decimal(mc["gecko_vol24_usd"])
        reserve=Decimal(mc["gecko_tvl_usd"])
        if vol<100000 or reserve<500000:
            out["source_screen"]="FAIL_VOLUME_OR_RESERVE";return out
        if not mc["two_source_consistent"]:
            out["reason"]="DUAL_PROVIDER_INCONSISTENT_OR_MISSING";return out
        out["source_screen"]="MARKET_AND_POOL_STATE_PASS_WATCH_ONLY"
        efee=[Decimal(v) for v in chain["lp_effective_swap_fee_by_direction"]]
        gross_revenues=[vol*v for v in efee]
        out["lp_pool_total_fee_dollars_day_direction_bounds"]=[str(v) for v in gross_revenues]
        out["critical_note"]="TOTAL pool fees only. No single-LP income inferred."
        # Not future returns: assumes exact current 24h volume repeats 7/30 days.
        if eth["status"]=="PASS":
            gas_weiprice=Decimal(chain["gas_price_wei"])
            for units,label in ((450000,"gas_450k_scenario"),(1350000,"gas_3x_stress")):
                d=Decimal(units)*gas_weiprice/Decimal(10**18)*Decimal(eth["eth_usd"])
                out[label+"_usd_excluding_l1_data_fee"]=str(d)
            out["l1_data_fee_usd"]="UNBOUND_NOT_INCLUDED"
            out["minimum_pool_fee_share_to_cover_gas_450k_in_7days"]=[
                str((Decimal(out["gas_450k_scenario_usd_excluding_l1_data_fee"])/(v*7)) if v>0 else None)
                for v in gross_revenues]
            out["minimum_pool_fee_share_to_cover_gas_450k_in_30days"]=[
                str((Decimal(out["gas_450k_scenario_usd_excluding_l1_data_fee"])/(v*30)) if v>0 else None)
                for v in gross_revenues]
        out["economic_verdict"]="NO_LIVE_GO_INDIVIDUAL_ACTIVE_RANGE_SHARE_UNBOUND"
        return out
    except (InvalidOperation,ValueError,TypeError,KeyError) as e:
        out["reason"]="SCREEN_COMPUTATION_FAILED:"+type(e).__name__;return out
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--universe",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    raw=args.universe.read_bytes();source=json.loads(raw)
    fixed=source["candidates"]
    if source.get("study")!="LP-NET-004" or len(fixed)!=9:
        raise ValueError("not frozen 9-pool source")
    if len(set((x["network"],x["addr"]) for x in fixed))!=9:
        raise ValueError("duplicate frozen addresses")
    asof=int(time.time())
    out={"study":"LP-NET-004","captured_start_utc":datetime.fromtimestamp(asof,timezone.utc).isoformat(),
        "universe_sha256":hashlib.sha256(raw).hexdigest(),
        "source_universe_preserved":True,"capital_chf":0,"orders":0,"wallets":0,
        "funding_costs":"UNBOUND","fee_growth_inside":"UNBOUND","capital_allocation":"NONE",
        "economic_verdict":"NO_LIVE_GO","results":[]}
    eth=native_price(asof);out["eth_quote"]=eth
    rpc_sources={}
    for network,chain_id in source["chain_ids"].items():
        rpc_sources[network]=Source(network,chain_id)
    out["chain_endpoint_discovery"]={k:{"kind":v.kind,"endpoint":v.endpoint,"attempts":v.errors}
                                     for k,v in rpc_sources.items()}
    for c in fixed:
        try:mc=market(c)
        except (OSError,ValueError,TypeError,KeyError) as e:
            mc={"status":"MARKET_SOURCE_BLOCKED","error":type(e).__name__+":"+str(e)[:130]}
        try:state=read_chain(c,rpc_sources[c["network"]])
        except (OSError,ValueError,TypeError,KeyError,RuntimeError) as e:
            state={"status":"ONCHAIN_SOURCE_BLOCKED","error":type(e).__name__+":"+str(e)[:130]}
        out["results"].append(combine(c,mc,state,eth))
        time.sleep(.35)
    out["captured_end_utc"]=datetime.now(timezone.utc).isoformat()
    out["n_market_and_pool_state_pass"]=sum(x["source_screen"]=="MARKET_AND_POOL_STATE_PASS_WATCH_ONLY" for x in out["results"])
    out["next_gate"]="Verify active liquidity for chosen LP price tick range, feeGrowthInside/historical swap crossing, L2 posting gas, forward 7/30 day net performance vs inventory HODL; zero trades until economic proof."
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"market_and_pool_state_pass":out["n_market_and_pool_state_pass"],
        "screen":{x["id"]:x["source_screen"] for x in out["results"]},
        "onchain":{x["id"]:x["onchain"]["status"] for x in out["results"]},
        "economic_verdict":out["economic_verdict"]},ensure_ascii=False))
if __name__=="__main__":main()
