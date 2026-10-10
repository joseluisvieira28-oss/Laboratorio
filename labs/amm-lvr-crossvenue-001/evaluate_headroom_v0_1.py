from __future__ import annotations

import json
import pathlib
import statistics
import urllib.request
from decimal import Decimal, getcontext

getcontext().prec = 60

ROOT = pathlib.Path(__file__).resolve().parent
IN = ROOT / "evidence" / "forward_protocol_capture_v0_1.json"
OUT = ROOT / "evidence"
RPC_PRIMARY = "https://ethereum-rpc.publicnode.com"
RPC_FALLBACK = "https://eth.drpc.org"
QUOTER = "0x61ffe014ba17989e743c5f6cb21bf9697530b21e"
NOTIONALS = [500, 1000, 5000]
LATENCIES = ["0","250","1000","3000"]
GAS_UNITS = 300_000
TAKER = Decimal("0.001")

TOKENS = {
    "WETH": {"address":"0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2","decimals":18,"cex":"ETHUSDT"},
    "USDC": {"address":"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48","decimals":6,"cex":"USDCUSDT"},
    "USDT": {"address":"0xdac17f958d2ee523a2206206994597c13d831ec7","decimals":6,"cex":None},
    "WBTC": {"address":"0x2260fac5e5542a773aa44fbcfedf7c193bc2c599","decimals":8,"cex":"BTCUSDT"},
    "LINK": {"address":"0x514910771af9ca656af840dff83e8264ecf986ca","decimals":18,"cex":"LINKUSDT"},
    "PEPE": {"address":"0x6982508145454ce325ddbe47a25d4ec3d2311933","decimals":18,"cex":"PEPEUSDT"},
    "SHIB": {"address":"0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce","decimals":18,"cex":"SHIBUSDT"},
}
ADDR_TO_TOKEN={v["address"].lower():k for k,v in TOKENS.items()}

def rpc(url, method, params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(
        url,data=payload,
        headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-headroom/0.1"}
    )
    with urllib.request.urlopen(req,timeout=30) as r:
        body=json.loads(r.read().decode())
    if body.get("error"):
        raise RuntimeError(str(body["error"]))
    return body.get("result")

def resilient_rpc(method, params):
    err=None
    for url in [RPC_PRIMARY,RPC_FALLBACK]:
        try:
            return rpc(url,method,params)
        except Exception as e:
            err=e
    raise err if err else RuntimeError("RPC failure")

def selector(sig):
    return resilient_rpc("web3_sha3",["0x"+sig.encode().hex()])[2:10]

QUOTE_SEL=selector("quoteExactInputSingle((address,address,uint256,uint24,uint160))")
TOKEN0_SEL="0x0dfe1681"
TOKEN1_SEL="0xd21220a7"
RESERVES_SEL="0x0902f1ac"

def waddr(a): return a[2:].lower().rjust(64,"0")
def wuint(v): return hex(int(v))[2:].rjust(64,"0")
def dec_addr(out):
    if not out or out=="0x": return None
    return "0x"+out[-40:].lower()

def eth_call(to,data,block_num):
    return resilient_rpc("eth_call",[{"to":to,"data":data},hex(int(block_num))])

def token_order(pool,block_num):
    t0=dec_addr(eth_call(pool,TOKEN0_SEL,block_num))
    t1=dec_addr(eth_call(pool,TOKEN1_SEL,block_num))
    return ADDR_TO_TOKEN.get((t0 or "").lower()),ADDR_TO_TOKEN.get((t1 or "").lower())

def v3_quote(token_in,token_out,amount_in_raw,fee,block_num):
    data=("0x"+QUOTE_SEL+waddr(TOKENS[token_in]["address"])+waddr(TOKENS[token_out]["address"])
          +wuint(amount_in_raw)+wuint(fee)+wuint(0))
    out=eth_call(QUOTER,data,block_num)
    if not out or out=="0x": return None
    h=out[2:]
    if len(h)<64: return None
    return int(h[0:64],16)

def v2_reserves(pool,block_num):
    out=eth_call(pool,RESERVES_SEL,block_num)
    h=out[2:]
    if len(h)<128: raise RuntimeError("short reserves")
    return int(h[0:64],16),int(h[64:128],16)

def v2_quote(amount_in_raw,reserve_in,reserve_out):
    if amount_in_raw<=0 or reserve_in<=0 or reserve_out<=0: return None
    ai=amount_in_raw*997
    return (ai*reserve_out)//(reserve_in*1000+ai)

def to_qty(token,raw):
    return Decimal(raw)/(Decimal(10)**TOKENS[token]["decimals"])

def to_raw(token,qty):
    return int((Decimal(qty)*(Decimal(10)**TOKENS[token]["decimals"])).to_integral_value(rounding="ROUND_FLOOR"))

def parse_book(snap):
    if not snap: return None
    return {
        "bids":[(Decimal(p),Decimal(q)) for p,q in snap.get("bids",[])],
        "asks":[(Decimal(p),Decimal(q)) for p,q in snap.get("asks",[])],
    }

def buy_with_budget(book,budget):
    if book is None:return None
    left=Decimal(budget); qty=Decimal(0); spent=Decimal(0)
    for p,q in book["asks"]:
        cap=p*q
        use=min(left,cap)
        if use>0:
            qty+=use/p;spent+=use;left-=use
        if left<=Decimal("0.00000001"):break
    if left>Decimal("0.0001"):return None
    return qty,spent

def buy_qty(book,qty):
    if book is None:return None
    left=Decimal(qty);cost=Decimal(0)
    for p,q in book["asks"]:
        take=min(left,q);cost+=take*p;left-=take
        if left<=Decimal("0.000000000001"):break
    if left>Decimal("0.00000001"):return None
    return cost

def sell_qty(book,qty):
    if book is None:return None
    left=Decimal(qty);proceeds=Decimal(0)
    for p,q in book["bids"]:
        take=min(left,q);proceeds+=take*p;left-=take
        if left<=Decimal("0.000000000001"):break
    if left>Decimal("0.00000001"):return None
    return proceeds

def eth_ask_from(event):
    snap=event["hedge_depth_by_latency_ms"]["0"].get("ETHUSDT")
    b=parse_book(snap)
    return b["asks"][0][0] if b and b["asks"] else None

def size_input(event,token_in,notional):
    if token_in=="USDT": return Decimal(notional)
    sym=TOKENS[token_in]["cex"]
    snap=event["hedge_depth_by_latency_ms"]["0"].get(sym)
    got=buy_with_budget(parse_book(snap),Decimal(notional))
    return None if got is None else got[0]

def quote_direction(state,event,token_in,token_out,notional):
    qty_in=size_input(event,token_in,notional)
    if qty_in is None:return None
    raw_in=to_raw(token_in,qty_in)
    qty_in=to_qty(token_in,raw_in)
    if raw_in<=0:return None
    if state["dex"]=="UNISWAP_V3":
        raw_out=v3_quote(token_in,token_out,raw_in,int(state["fee"]),state["block_number"])
    else:
        r0,r1=state["reserves"]
        if state["token0"]==token_in and state["token1"]==token_out:
            raw_out=v2_quote(raw_in,r0,r1)
        elif state["token1"]==token_in and state["token0"]==token_out:
            raw_out=v2_quote(raw_in,r1,r0)
        else:
            return None
    if not raw_out:return None
    return {"token_in":token_in,"token_out":token_out,"qty_in":qty_in,"qty_out":to_qty(token_out,raw_out)}

def econ(event,quote,latency,base_gas_usdt):
    token_in=quote["token_in"];token_out=quote["token_out"]
    snaps=event["hedge_depth_by_latency_ms"][latency]
    legs=0
    if token_in=="USDT":
        cost=quote["qty_in"]
    else:
        b=parse_book(snaps.get(TOKENS[token_in]["cex"]))
        cost=buy_qty(b,quote["qty_in"])
        if cost is None:return None
        legs+=1
    if token_out=="USDT":
        proceeds=quote["qty_out"]
    else:
        b=parse_book(snaps.get(TOKENS[token_out]["cex"]))
        proceeds=sell_qty(b,quote["qty_out"])
        if proceeds is None:return None
        legs+=1
    gross=proceeds-cost
    cex_fee=TAKER*((cost if token_in!="USDT" else Decimal(0))+(proceeds if token_out!="USDT" else Decimal(0)))
    headroom=gross-cex_fee-base_gas_usdt
    return {
        "gross_usdt":gross,
        "cex_fee_usdt":cex_fee,
        "base_fee_gas_usdt":base_gas_usdt,
        "pre_inclusion_headroom_usdt":headroom,
        "legs":legs,
    }

events=json.loads(IN.read_text(encoding="utf-8"))
# First captured tx anchors each reproducible end-of-block pool state.
states={}
for ev in events:
    for sw in ev.get("swaps",[]):
        key=(int(ev["block_number"]),sw["pool"].lower())
        if key not in states:
            states[key]={"event":ev,"swap":sw}

rows=[]
errors=[]
for (block,pool),obj in sorted(states.items()):
    ev=obj["event"];sw=obj["swap"]
    try:
        t0,t1=token_order(pool,block)
        if not t0 or not t1:
            raise RuntimeError("pool token mapping failed")
        state={
            "block_number":block,"pool":pool,"dex":sw["dex"],"fee":sw["fee"],
            "token0":t0,"token1":t1,
        }
        if state["dex"]=="UNISWAP_V2":
            state["reserves"]=v2_reserves(pool,block)
        ethask=eth_ask_from(ev)
        if ethask is None: raise RuntimeError("missing T0 ETH ask")
        basefee=int(ev["builder_cost"].get("base_fee_per_gas_wei",0))
        base_gas=Decimal(GAS_UNITS)*Decimal(basefee)/Decimal(10**18)*ethask

        for notional in NOTIONALS:
            q01=quote_direction(state,ev,t0,t1,notional)
            q10=quote_direction(state,ev,t1,t0,notional)
            e01=econ(ev,q01,"0",base_gas) if q01 else None
            e10=econ(ev,q10,"0",base_gas) if q10 else None
            choices=[]
            if e01:choices.append((e01["gross_usdt"],q01))
            if e10:choices.append((e10["gross_usdt"],q10))
            if not choices:
                rows.append({
                    "block_number":block,"pool":pool,"pair":sw["pair"],"dex":sw["dex"],
                    "anchor_tx_hash":ev["tx_hash"],"notional_usdt":notional,"status":"INFEASIBLE"
                })
                continue
            _,chosen=max(choices,key=lambda x:x[0])
            rec={
                "block_number":block,"pool":pool,"pair":sw["pair"],"dex":sw["dex"],
                "anchor_tx_hash":ev["tx_hash"],"notional_usdt":notional,"status":"EXECUTABLE",
                "frozen_direction":f'{chosen["token_in"]}->{chosen["token_out"]}',
                "dex_input_qty":str(chosen["qty_in"]),"dex_output_qty":str(chosen["qty_out"]),
                "base_fee_per_gas_wei":basefee,"gas_units_frozen":GAS_UNITS,
                "priority_fee_bound":False,"direct_builder_payment_bound_for_hypothetical":False,
                "failed_inclusion_risk_bound":False,"full_cost_pnl_computed":False,
            }
            for lat in LATENCIES:
                ee=econ(ev,chosen,lat,base_gas)
                if ee is None:
                    rec[f"latency_{lat}ms"]={"status":"DATA_INSUFFICIENT"}
                else:
                    rec[f"latency_{lat}ms"]={
                        "status":"OK",
                        "gross_usdt":str(ee["gross_usdt"]),
                        "gross_bps":str(ee["gross_usdt"]/Decimal(notional)*Decimal(10000)),
                        "cex_fee_usdt":str(ee["cex_fee_usdt"]),
                        "base_fee_gas_usdt":str(ee["base_fee_gas_usdt"]),
                        "pre_inclusion_headroom_usdt":str(ee["pre_inclusion_headroom_usdt"]),
                        "pre_inclusion_headroom_bps":str(ee["pre_inclusion_headroom_usdt"]/Decimal(notional)*Decimal(10000)),
                        "positive_headroom":ee["pre_inclusion_headroom_usdt"]>0,
                    }
            rows.append(rec)
    except Exception as e:
        errors.append({"block":block,"pool":pool,"error":type(e).__name__+":"+str(e)[:500]})

summary_by={}
for n in NOTIONALS:
    summary_by[str(n)]={}
    relevant=[r for r in rows if r.get("notional_usdt")==n and r.get("status")=="EXECUTABLE"]
    for lat in LATENCIES:
        vals=[]
        for r in relevant:
            x=r.get(f"latency_{lat}ms",{})
            if x.get("status")=="OK":
                vals.append(Decimal(x["pre_inclusion_headroom_usdt"]))
        pos=[v for v in vals if v>0]
        summary_by[str(n)][lat]={
            "evaluable_states":len(vals),
            "positive_headroom_states":len(pos),
            "positive_share":(len(pos)/len(vals) if vals else None),
            "median_headroom_usdt":(str(statistics.median(vals)) if vals else None),
            "mean_headroom_usdt":(str(sum(vals)/len(vals)) if vals else None),
            "max_headroom_usdt":(str(max(vals)) if vals else None),
            "total_positive_headroom_usdt":(str(sum(pos)) if pos else "0"),
        }

summary={
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "phase":"INTERIM_PRE_INCLUSION_HEADROOM_V0.1",
    "raw_transaction_events":len(events),
    "unique_block_pool_states":len(states),
    "row_count":len(rows),
    "error_count":len(errors),
    "by_notional_latency":summary_by,
    "full_cost_pnl_computed":False,
    "scientific_verdict":"NOT_OPEN",
    "discovery_event_credit":0,
    "minimum_scientific_events":500,
    "minimum_scientific_days":14,
    "missing_cost_layers":["priority_fee_for_hypothetical","direct_or_private_builder_payment_for_hypothetical","failed_inclusion_probability"],
    "note":"Positive pre-inclusion headroom is only budget available to the still-unbound competitive inclusion stack. It is not net edge."
}
(OUT/"headroom_evaluation_v0_1.json").write_text(json.dumps(rows,indent=2,sort_keys=True),encoding="utf-8")
(OUT/"headroom_evaluation_v0_1_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
(OUT/"headroom_evaluation_v0_1_errors.json").write_text(json.dumps(errors,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(summary,indent=2,sort_keys=True))

# Outcome sign does not control workflow success. Fail only if implementation produced no evaluable rows.
if not any(r.get("status")=="EXECUTABLE" for r in rows):
    raise SystemExit(2)
