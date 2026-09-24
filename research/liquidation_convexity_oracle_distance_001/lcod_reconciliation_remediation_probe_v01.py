#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,math,re,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from eth_utils import keccak

URL="https://mcp.aave.com/"
CHAIN_RPCS={
  1:"https://eth-mainnet.public.blastapi.io",
  43114:"https://api.avax.network/ext/bc/C/rpc",
}
OUT=Path("artifacts/lcod_reconciliation_remediation_probe_v01.json")
GROUP=set("4567")
TOL=5e-5
TARGET=24

SEL_GET_USER_POSITION=keccak(text="getUserPosition(uint256,address)")[:4]
SEL_GET_DYNAMIC_CONFIG=keccak(text="getDynamicReserveConfig(uint256,uint32)")[:4]

def http_post(url,obj,timeout=45):
    raw=json.dumps(obj).encode();last=None
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,data=raw,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-LCOD-001-Remediation/0.1"},method="POST")
            with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
            last=e
            if attempt==3:raise
            time.sleep(1.5*(attempt+1))
    raise last

def mcp_rpc(method,params):
    x=http_post(URL,{"jsonrpc":"2.0","id":1,"method":method,"params":params})
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

def call(name,args):return unwrap(mcp_rpc("tools/call",{"name":name,"arguments":args}))

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)

def addresses(x):
    out=[]
    for d in walk(x):
        for k in ("user","address","wallet"):
            v=d.get(k)
            if isinstance(v,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",v):
                out.append(v.lower());break
    return out

def next_cursor(x):
    vals=[]
    for d in walk(x):
        for k in ("nextCursor","next_cursor"):
            v=d.get(k)
            if isinstance(v,str) and v.strip():vals.append(v.strip())
    vals=list(dict.fromkeys(vals))
    if len(vals)>1:raise RuntimeError("AMBIGUOUS_NEXT_CURSOR")
    return vals[0] if vals else None

def num(v):
    if isinstance(v,bool) or v is None:return None
    if isinstance(v,(int,float)):
        q=float(v);return q if math.isfinite(q) else None
    if isinstance(v,str):
        try:q=float(v);return q if math.isfinite(q) else None
        except Exception:return None
    if isinstance(v,dict):
        for k in ("value","normalized","amount","usd"):
            if k in v:
                q=num(v[k])
                if q is not None:return q
    return None

def positions(x):
    return x.get("v4",{}).get("positions",[]) if isinstance(x,dict) and isinstance(x.get("v4"),dict) else []

def items(x):
    if isinstance(x,list):return [z for z in x if isinstance(z,dict)]
    if isinstance(x,dict):
        for k in ("items","data","positions"):
            if isinstance(x.get(k),list):return [z for z in x[k] if isinstance(z,dict)]
    return []

def decode_reserve_id(rid):
    raw=base64.b64decode(rid).decode()
    chain,spoke,numeric=raw.split("::")
    return int(chain),spoke.lower(),int(numeric)

def chain_call(chain_id,to,data):
    url=CHAIN_RPCS.get(chain_id)
    if not url:raise RuntimeError(f"UNSUPPORTED_CHAIN:{chain_id}")
    x=http_post(url,{"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":to,"data":"0x"+data.hex()},"latest"]})
    if x.get("error"):raise RuntimeError(x["error"])
    v=x.get("result")
    if not isinstance(v,str) or not v.startswith("0x"):raise RuntimeError("INVALID_ETH_CALL")
    return bytes.fromhex(v[2:])

def dynamic_cf_bps(chain_id,spoke,rid_num,user):
    addr=bytes.fromhex(user[2:])
    d1=SEL_GET_USER_POSITION + rid_num.to_bytes(32,"big") + b"\x00"*12 + addr
    raw=chain_call(chain_id,spoke,d1)
    if len(raw)<160:raise RuntimeError("SHORT_USER_POSITION_RETURN")
    key=int.from_bytes(raw[128:160],"big")
    d2=SEL_GET_DYNAMIC_CONFIG + rid_num.to_bytes(32,"big") + key.to_bytes(32,"big")
    cfg=chain_call(chain_id,spoke,d2)
    if len(cfg)<96:raise RuntimeError("SHORT_DYNAMIC_CONFIG_RETURN")
    return key,int.from_bytes(cfg[0:32],"big")

# full borrower index
markets=call("get_markets",{"version":"v4"})
reserve_ids=list(dict.fromkeys(d["reserveId"] for d in walk(markets) if isinstance(d.get("reserveId"),str)))
wallets=set();census_errors=[]
for rid in reserve_ids:
    cursor=None;seen=set()
    for _ in range(1000):
        args={"reserveId":rid,"side":"borrow","limit":50,"version":"v4"}
        if cursor:args["cursor"]=cursor
        try:r=call("get_reserve_holders",args)
        except Exception as e:census_errors.append(f"{type(e).__name__}:{str(e)[:160]}");break
        wallets.update(addresses(r))
        nxt=next_cursor(r)
        if not nxt:break
        if nxt in seen:census_errors.append("CURSOR_LOOP");break
        seen.add(nxt);cursor=nxt

selected=sorted(w for w in wallets if hashlib.sha256(w.encode()).hexdigest()[0] in GROUP)
cached={}
def cached_detail(rid):
    if rid not in cached:cached[rid]=call("get_reserve_details",{"reserveId":rid,"version":"v4"})
    return cached[rid]

rows=[];technical=[]
for w in selected:
    if len(rows)>=TARGET:break
    wh=hashlib.sha256(w.encode()).hexdigest()
    try:ps=positions(call("get_user_positions",{"user":w,"version":"v4"}))
    except Exception as e:technical.append(f"positions:{type(e).__name__}:{str(e)[:120]}");continue
    for p in ps:
        if len(rows)>=TARGET:break
        official=num(p.get("healthFactor"));debt_total=num(p.get("totalDebtUsd"))
        spoke_id=p.get("spokeId");spoke_addr=str(p.get("spokeAddress") or "").lower()
        chain_id=int(p.get("chainId") or 0)
        if official is None or official<=0 or not debt_total or debt_total<=0 or not isinstance(spoke_id,str):continue
        try:
            ss=items(call("get_position_items",{"user":w,"spokeId":spoke_id,"side":"supply","version":"v4"}))
            bs=items(call("get_position_items",{"user":w,"spokeId":spoke_id,"side":"borrow","version":"v4"}))
        except Exception as e:technical.append(f"items:{type(e).__name__}:{str(e)[:120]}");continue

        # baseline cached/current
        cap0=0.0;debt0=0.0;complete=True
        for it in ss:
            if not bool(it.get("isCollateral")):continue
            rid=it.get("reserveId");amount=num(it.get("balance"))
            if not isinstance(rid,str) or amount is None:complete=False;break
            rd=cached_detail(rid);price=num(rd.get("priceUsd"));cf=num(rd.get("collateralFactorPct"))
            if price is None or cf is None:complete=False;break
            cap0+=amount*price*(cf/100.0)
        for it in bs:
            rid=it.get("reserveId");pr=num(it.get("principal"));intr=num(it.get("interest"))
            if not isinstance(rid,str) or pr is None or intr is None:complete=False;break
            rd=cached_detail(rid);price=num(rd.get("priceUsd"))
            if price is None:complete=False;break
            debt0+=(pr+intr)*price
        if not complete or cap0<=0 or debt0<=0:continue
        r0=cap0/debt0;err0=abs(r0-official)/official
        if err0<=TOL:continue

        # fresh current + dynamic
        try:
            fresh={rid:call("get_reserve_details",{"reserveId":rid,"version":"v4"})
                   for rid in dict.fromkeys([x.get("reserveId") for x in ss+bs if isinstance(x.get("reserveId"),str)])}
            cap1=0.0;cap2=0.0;debt1=0.0;changed=0;dyn_legs=0
            for it in ss:
                if not bool(it.get("isCollateral")):continue
                rid=it["reserveId"];amount=num(it.get("balance"));rd=fresh[rid]
                price=num(rd.get("priceUsd"));cf=num(rd.get("collateralFactorPct"))
                if amount is None or price is None or cf is None:raise RuntimeError("FRESH_SUPPLY_FIELD_MISSING")
                cap1+=amount*price*(cf/100.0)
                ch,spoke_from_rid,rn=decode_reserve_id(rid)
                if ch!=chain_id:raise RuntimeError(f"CHAIN_ID_MISMATCH:{ch}:{chain_id}")
                if ch not in CHAIN_RPCS:raise RuntimeError(f"UNSUPPORTED_CHAIN:{ch}")
                if spoke_addr and spoke_from_rid!=spoke_addr:raise RuntimeError("SPOKE_ADDRESS_MISMATCH")
                key,dyn_cf=dynamic_cf_bps(ch,spoke_from_rid,rn,w)
                cap2+=amount*price*(dyn_cf/10000.0);dyn_legs+=1
                if abs(dyn_cf/100.0-cf)>1e-12:changed+=1
            for it in bs:
                rid=it["reserveId"];pr=num(it.get("principal"));intr=num(it.get("interest"));rd=fresh[rid]
                price=num(rd.get("priceUsd"))
                if pr is None or intr is None or price is None:raise RuntimeError("FRESH_DEBT_FIELD_MISSING")
                debt1+=(pr+intr)*price
            if cap1<=0 or cap2<=0 or debt1<=0:raise RuntimeError("NONPOSITIVE_RECON")
            r1=cap1/debt1;r2=cap2/debt1
            e1=abs(r1-official)/official;e2=abs(r2-official)/official
            rows.append({
              "borrower_sha256":wh,"official_hf":official,
              "baseline_cached_current_rel_error":err0,
              "fresh_current_rel_error":e1,
              "fresh_dynamic_rel_error":e2,
              "fresh_current_pass":e1<=TOL,
              "fresh_dynamic_pass":e2<=TOL,
              "dynamic_collateral_legs":dyn_legs,
              "legs_with_dynamic_factor_different_from_current":changed,
            })
        except Exception as e:
            technical.append(f"diagnostic:{wh[:12]}:{type(e).__name__}:{str(e)[:180]}")

n=len(rows)
r1pass=sum(x["fresh_current_pass"] for x in rows);r2pass=sum(x["fresh_dynamic_pass"] for x in rows)
r1rate=r1pass/n if n else 0.0;r2rate=r2pass/n if n else 0.0
if n>=20 and r1rate>=0.90:
    classification="PRICE_STALENESS_CONFIRMED"
elif n>=20 and r2rate>=0.90:
    classification="DYNAMIC_CONFIG_CONFIRMED"
elif n>=20 and r2rate>=0.75:
    classification="MIXED_SOURCE_REMEDIATION"
else:
    classification="SOURCE_RECONCILIATION_UNRESOLVED"

receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"FULL_CENSUS_RECONCILIATION_REMEDIATION_PROBE_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "frozen_group":"4567","target_failures":TARGET,"diagnosed_failures":n,
 "hf_relative_error_tolerance":TOL,
 "fresh_current_pass_count":r1pass,"fresh_current_pass_rate":r1rate,
 "fresh_dynamic_pass_count":r2pass,"fresh_dynamic_pass_rate":r2rate,
 "dynamic_factor_changed_cases":sum(x["legs_with_dynamic_factor_different_from_current"]>0 for x in rows),
 "classification":classification,
 "rows":rows,"technical_errors":technical[:50],"census_errors":census_errors,
 "market_returns_opened":False,"liquidation_outcomes_opened":False,"pnl_opened":False,"mutation":False,
 "raw_wallet_addresses_retained":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ("classification","diagnosed_failures","fresh_current_pass_count","fresh_current_pass_rate","fresh_dynamic_pass_count","fresh_dynamic_pass_rate","dynamic_factor_changed_cases","technical_errors","census_errors")},indent=2))
