#!/usr/bin/env python3
import hashlib, json, math, re, statistics, urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL="https://mcp.aave.com/"
OUT=Path("artifacts/lcod_hf_reconciliation_v02.json")
TARGET_BORROWERS=35
MIN_COMPLETE_POSITIONS=25

def rpc(method,params):
    req=urllib.request.Request(URL,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),headers={"Content-Type":"application/json","User-Agent":"CryptoLab-LCOD-001-Recon/0.2"},method="POST")
    with urllib.request.urlopen(req,timeout=45) as r:x=json.loads(r.read().decode())
    if x.get("error"):raise RuntimeError(x["error"])
    return x.get("result")

def unwrap(x):
    if isinstance(x,dict) and x.get("structuredContent") is not None:
        y=x["structuredContent"]
        return y.get("data") if isinstance(y,dict) and "data" in y else y
    if isinstance(x,dict) and "content" in x:
        for c in x["content"]:
            if isinstance(c,dict) and c.get("type")=="text":
                try:
                    y=json.loads(c.get("text",""))
                    return y.get("data") if isinstance(y,dict) and "data" in y else y
                except Exception:pass
    return x.get("data") if isinstance(x,dict) and "data" in x else x

def call(name,args):return unwrap(rpc("tools/call",{"name":name,"arguments":args}))

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
            if isinstance(v,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",v):out.append(v.lower());break
    return out

def num(v):
    if isinstance(v,bool) or v is None:return None
    if isinstance(v,(int,float)):
        q=float(v);return q if math.isfinite(q) else None
    if isinstance(v,str):
        try:
            q=float(v);return q if math.isfinite(q) else None
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

markets=call("get_markets",{"version":"v4"})
reserve_ids=[]
for d in walk(markets):
    if isinstance(d.get("reserveId"),str):reserve_ids.append(d["reserveId"])
reserve_ids=list(dict.fromkeys(reserve_ids))

wallets=[]
for rid in reserve_ids:
    if len(set(wallets))>=TARGET_BORROWERS:break
    try:wallets.extend(addresses(call("get_reserve_holders",{"reserveId":rid,"side":"borrow","limit":50,"version":"v4"})))
    except Exception:pass
wallets=list(dict.fromkeys(wallets))[:TARGET_BORROWERS]

detail_cache={}
def detail(rid):
    if rid not in detail_cache:detail_cache[rid]=call("get_reserve_details",{"reserveId":rid,"version":"v4"})
    return detail_cache[rid]

rows=[];excluded={};errors=[]
for w in wallets:
    wh=hashlib.sha256(w.encode()).hexdigest()
    try:ps=positions(call("get_user_positions",{"user":w,"version":"v4"}))
    except Exception as e:
        errors.append(f"positions:{type(e).__name__}:{str(e)[:140]}");continue
    for p in ps:
        spoke=p.get("spokeId");official=num(p.get("healthFactor"));td=num(p.get("totalDebtUsd"))
        if not isinstance(spoke,str) or official is None or td is None or td<=0:
            excluded["POSITION_REQUIRED_FIELD_MISSING"]=excluded.get("POSITION_REQUIRED_FIELD_MISSING",0)+1;continue
        try:
            ss=items(call("get_position_items",{"user":w,"spokeId":spoke,"side":"supply","version":"v4"}))
            bs=items(call("get_position_items",{"user":w,"spokeId":spoke,"side":"borrow","version":"v4"}))
        except Exception as e:
            excluded["ITEM_READ_ERROR"]=excluded.get("ITEM_READ_ERROR",0)+1;errors.append(f"items:{type(e).__name__}:{str(e)[:140]}");continue

        cap=0.0;debt=0.0;complete=True;legs=[];balance_identity_errors=[]
        collateral_legs=0;borrow_legs=0
        for it in ss:
            if not bool(it.get("isCollateral")):continue
            rid=it.get("reserveId");amount=num(it.get("balance"))
            if not isinstance(rid,str) or amount is None:complete=False;break
            try:rd=detail(rid)
            except Exception as e:complete=False;errors.append(f"reserve:{type(e).__name__}:{str(e)[:140]}");break
            price=num(rd.get("priceUsd")) if isinstance(rd,dict) else None
            cf=num(rd.get("collateralFactorPct")) if isinstance(rd,dict) else None
            if price is None or cf is None:complete=False;break
            usd=amount*price;cap+=usd*(cf/100.0);collateral_legs+=1
            legs.append({"reserve_id":rid,"side":"supply","amount_main":amount,"price_usd":price,"collateral_factor_pct":cf,"computed_usd":usd})

        if not complete:
            excluded["SUPPLY_RAW_COMPONENT_INCOMPLETE"]=excluded.get("SUPPLY_RAW_COMPONENT_INCOMPLETE",0)+1;continue

        for it in bs:
            rid=it.get("reserveId");principal=num(it.get("principal"));interest=num(it.get("interest"));bal=num(it.get("balance"))
            if not isinstance(rid,str) or principal is None or interest is None:complete=False;break
            try:rd=detail(rid)
            except Exception as e:complete=False;errors.append(f"reserve:{type(e).__name__}:{str(e)[:140]}");break
            price=num(rd.get("priceUsd")) if isinstance(rd,dict) else None
            if price is None:complete=False;break
            amount=principal+interest;usd=amount*price;debt+=usd;borrow_legs+=1
            identity=None if bal is None else abs(bal-amount)
            if identity is not None:balance_identity_errors.append(identity)
            legs.append({"reserve_id":rid,"side":"borrow","principal_main":principal,"interest_main":interest,"balance_main":bal,"balance_identity_abs_error":identity,"price_usd":price,"computed_usd":usd})

        if not complete or cap<=0 or debt<=0 or collateral_legs==0 or borrow_legs==0:
            excluded["DEBT_RAW_COMPONENT_INCOMPLETE"]=excluded.get("DEBT_RAW_COMPONENT_INCOMPLETE",0)+1;continue

        hf=cap/debt;rel=abs(hf-official)/official if official>0 else None
        rows.append({"borrower_sha256":wh,"spoke_id_sha256":hashlib.sha256(spoke.encode()).hexdigest(),"official_health_factor":official,"raw_component_health_factor":hf,"raw_component_relative_error":rel,"collateral_capacity_usd":cap,"debt_usd":debt,"collateral_leg_count":collateral_legs,"borrow_leg_count":borrow_legs,"max_balance_vs_principal_interest_abs_error":max(balance_identity_errors) if balance_identity_errors else None,"legs":legs})

errs=sorted(r["raw_component_relative_error"] for r in rows if r["raw_component_relative_error"] is not None)
def stat(xs):
    if not xs:return None
    def q(p):return xs[min(len(xs)-1,max(0,round((len(xs)-1)*p)))]
    return {"n":len(xs),"median":statistics.median(xs),"p90_nearest":q(.90),"p95_nearest":q(.95),"p99_nearest":q(.99),"max":max(xs)}

receipt={"lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001","stage":"HF_RAW_COMPONENT_RECONCILIATION_SOURCE_CALIBRATION_V0.2","captured_at_utc":datetime.now(timezone.utc).isoformat(),"borrowers_sampled":len(wallets),"complete_debt_positions":len(rows),"minimum_complete_positions":MIN_COMPLETE_POSITIONS,"complete_position_gate_pass":len(rows)>=MIN_COMPLETE_POSITIONS,"raw_component_relative_error_stats":stat(errs),"exclusions":excluded,"errors":errors[:30],"rows":rows,"tolerance_frozen":False,"market_returns_opened":False,"liquidation_outcomes_opened":False,"pnl_opened":False,"mutation":False}
receipt["classification"]="HF_RAW_RECONCILIATION_MEASURED__TOLERANCE_NOT_FROZEN" if len(rows)>=MIN_COMPLETE_POSITIONS and errs else "HF_RAW_RECONCILIATION_INSUFFICIENT"

OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":receipt["classification"],"complete_debt_positions":len(rows),"raw_component_relative_error_stats":receipt["raw_component_relative_error_stats"],"exclusions":excluded},indent=2))
