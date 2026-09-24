#!/usr/bin/env python3
import hashlib, json, math, re, statistics, urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL="https://mcp.aave.com/"
OUT=Path("artifacts/lcod_hf_reconciliation_v01.json")
UA="CryptoLab-LCOD-001-Reconciliation/0.1"
TARGET_BORROWERS=35
MIN_COMPLETE_POSITIONS=25

def rpc(method,params):
    req=urllib.request.Request(
        URL,
        data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),
        headers={"Content-Type":"application/json","User-Agent":UA},
        method="POST",
    )
    with urllib.request.urlopen(req,timeout=45) as r:
        x=json.loads(r.read().decode())
    if x.get("error"):
        raise RuntimeError(x["error"])
    return x.get("result")

def unwrap(x):
    if isinstance(x,dict) and x.get("structuredContent") is not None:
        sc=x["structuredContent"]
        if isinstance(sc,dict) and "data" in sc:return sc["data"]
        return sc
    if isinstance(x,dict) and "content" in x:
        for c in x["content"]:
            if isinstance(c,dict) and c.get("type")=="text":
                try:
                    z=json.loads(c.get("text",""))
                    if isinstance(z,dict) and "data" in z:return z["data"]
                    return z
                except Exception:pass
    if isinstance(x,dict) and "data" in x:return x["data"]
    return x

def call(name,args):
    return unwrap(rpc("tools/call",{"name":name,"arguments":args}))

def dicts(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from dicts(v)
    elif isinstance(x,list):
        for v in x:yield from dicts(v)

def addresses(x):
    out=[]
    for d in dicts(x):
        for k in ("user","address","wallet"):
            v=d.get(k)
            if isinstance(v,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",v):
                out.append(v.lower());break
    return out

def n(v):
    if isinstance(v,bool) or v is None:return None
    if isinstance(v,(int,float)):
        q=float(v);return q if math.isfinite(q) else None
    if isinstance(v,str):
        try:
            q=float(v);return q if math.isfinite(q) else None
        except Exception:return None
    if isinstance(v,dict):
        for k in ("usd","value","normalized","amount","formatted"):
            if k in v:
                q=n(v[k])
                if q is not None:return q
    return None

def v4_positions(x):
    if isinstance(x,dict):
        v4=x.get("v4")
        if isinstance(v4,dict) and isinstance(v4.get("positions"),list):
            return [p for p in v4["positions"] if isinstance(p,dict)]
    return []

def item_list(x):
    if isinstance(x,list):return [z for z in x if isinstance(z,dict)]
    if isinstance(x,dict):
        for k in ("items","positions","data"):
            if isinstance(x.get(k),list):return [z for z in x[k] if isinstance(z,dict)]
    return []

markets=call("get_markets",{"version":"v4"})
reserve_ids=[]
for d in dicts(markets):
    rid=d.get("reserveId")
    if isinstance(rid,str):reserve_ids.append(rid)
reserve_ids=list(dict.fromkeys(reserve_ids))

wallets=[]
holder_errors=[]
holder_queries=0
for rid in reserve_ids:
    if len(set(wallets))>=TARGET_BORROWERS:break
    try:
        h=call("get_reserve_holders",{"reserveId":rid,"side":"borrow","limit":50,"version":"v4"})
        holder_queries+=1
        wallets.extend(addresses(h))
    except Exception as e:
        holder_errors.append(f"{type(e).__name__}:{str(e)[:180]}")
wallets=list(dict.fromkeys(wallets))[:TARGET_BORROWERS]

detail_cache={}
def reserve_detail(rid):
    if rid not in detail_cache:
        detail_cache[rid]=call("get_reserve_details",{"reserveId":rid,"version":"v4"})
    return detail_cache[rid]

rows=[]
excluded={}
call_errors=[]
for w in wallets:
    wh=hashlib.sha256(w.encode()).hexdigest()
    try:
        pos_response=call("get_user_positions",{"user":w,"version":"v4"})
    except Exception as e:
        excluded["POSITIONS_READ_ERROR"]=excluded.get("POSITIONS_READ_ERROR",0)+1
        call_errors.append(f"positions:{type(e).__name__}:{str(e)[:160]}")
        continue

    for p in v4_positions(pos_response):
        spoke=p.get("spokeId")
        official=n(p.get("healthFactor"))
        total_coll=n(p.get("totalCollateralUsd"))
        total_debt=n(p.get("totalDebtUsd"))
        avg_cf=n(p.get("averageCollateralFactorPct"))
        if not isinstance(spoke,str) or official is None or total_debt is None or total_debt<=0:
            excluded["POSITION_REQUIRED_FIELD_MISSING"]=excluded.get("POSITION_REQUIRED_FIELD_MISSING",0)+1
            continue

        aggregate_hf=None
        if total_coll is not None and avg_cf is not None and total_debt>0:
            aggregate_hf=(total_coll*(avg_cf/100.0))/total_debt

        try:
            supplies=item_list(call("get_position_items",{"user":w,"spokeId":spoke,"side":"supply","version":"v4"}))
            borrows=item_list(call("get_position_items",{"user":w,"spokeId":spoke,"side":"borrow","version":"v4"}))
        except Exception as e:
            excluded["POSITION_ITEMS_READ_ERROR"]=excluded.get("POSITION_ITEMS_READ_ERROR",0)+1
            call_errors.append(f"items:{type(e).__name__}:{str(e)[:160]}")
            continue

        collateral_capacity=0.0
        debt_usd=0.0
        complete=True
        supply_count=0
        borrow_count=0
        reserve_evidence=[]

        for item in supplies:
            if not bool(item.get("isCollateral")):
                continue
            rid=item.get("reserveId")
            bal_usd=n(item.get("balanceUsd"))
            if not isinstance(rid,str) or bal_usd is None:
                complete=False;break
            try:
                rd=reserve_detail(rid)
            except Exception as e:
                complete=False
                call_errors.append(f"reserve:{type(e).__name__}:{str(e)[:160]}")
                break
            cf=n(rd.get("collateralFactorPct") if isinstance(rd,dict) else None)
            price=n(rd.get("priceUsd") if isinstance(rd,dict) else None)
            if cf is None or price is None:
                complete=False;break
            collateral_capacity += bal_usd*(cf/100.0)
            supply_count += 1
            reserve_evidence.append({
                "reserve_id":rid,
                "side":"supply",
                "balance_usd":bal_usd,
                "collateral_factor_pct":cf,
                "price_usd":price,
            })

        if not complete:
            excluded["SUPPLY_COMPONENT_INCOMPLETE"]=excluded.get("SUPPLY_COMPONENT_INCOMPLETE",0)+1
            continue

        for item in borrows:
            rid=item.get("reserveId")
            bal_usd=n(item.get("balanceUsd"))
            principal=n(item.get("principal"))
            interest=n(item.get("interest"))
            if not isinstance(rid,str) or bal_usd is None:
                complete=False;break
            try:
                rd=reserve_detail(rid)
            except Exception as e:
                complete=False
                call_errors.append(f"reserve:{type(e).__name__}:{str(e)[:160]}")
                break
            price=n(rd.get("priceUsd") if isinstance(rd,dict) else None)
            if price is None:
                complete=False;break
            debt_usd += bal_usd
            borrow_count += 1
            reserve_evidence.append({
                "reserve_id":rid,
                "side":"borrow",
                "balance_usd":bal_usd,
                "principal_present":principal is not None,
                "interest_present":interest is not None,
                "price_usd":price,
            })

        if not complete or debt_usd<=0 or supply_count==0 or borrow_count==0:
            excluded["DEBT_COMPONENT_INCOMPLETE"]=excluded.get("DEBT_COMPONENT_INCOMPLETE",0)+1
            continue

        component_hf=collateral_capacity/debt_usd
        comp_rel=abs(component_hf-official)/official if official>0 else None
        agg_rel=abs(aggregate_hf-official)/official if official>0 and aggregate_hf is not None else None
        rows.append({
            "borrower_sha256":wh,
            "spoke_id_sha256":hashlib.sha256(spoke.encode()).hexdigest(),
            "official_health_factor":official,
            "aggregate_reconstructed_health_factor":aggregate_hf,
            "aggregate_relative_error":agg_rel,
            "component_reconstructed_health_factor":component_hf,
            "component_relative_error":comp_rel,
            "collateral_capacity_usd":collateral_capacity,
            "debt_usd":debt_usd,
            "collateral_leg_count":supply_count,
            "borrow_leg_count":borrow_count,
            "reserve_evidence":reserve_evidence,
        })

comp_errors=[r["component_relative_error"] for r in rows if r["component_relative_error"] is not None]
agg_errors=[r["aggregate_relative_error"] for r in rows if r["aggregate_relative_error"] is not None]

def stats(xs):
    if not xs:return None
    ys=sorted(xs)
    def q(p):
        i=min(len(ys)-1,max(0,round((len(ys)-1)*p)))
        return ys[i]
    return {
      "n":len(ys),
      "median":statistics.median(ys),
      "p90_nearest":q(0.90),
      "p95_nearest":q(0.95),
      "max":max(ys),
    }

receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"HF_COMPONENT_RECONCILIATION_SOURCE_CALIBRATION",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "borrower_target":TARGET_BORROWERS,
 "borrowers_sampled":len(wallets),
 "holder_queries":holder_queries,
 "holder_errors":holder_errors,
 "complete_debt_positions":len(rows),
 "minimum_complete_positions":MIN_COMPLETE_POSITIONS,
 "complete_position_gate_pass":len(rows)>=MIN_COMPLETE_POSITIONS,
 "component_relative_error_stats":stats(comp_errors),
 "aggregate_relative_error_stats":stats(agg_errors),
 "exclusions":excluded,
 "call_errors":call_errors[:30],
 "rows":rows,
 "tolerance_frozen":False,
 "market_returns_opened":False,
 "liquidation_outcomes_opened":False,
 "pnl_opened":False,
 "mutation":False,
}
if len(rows)<MIN_COMPLETE_POSITIONS:
    receipt["classification"]="HF_RECONCILIATION_INSUFFICIENT_COMPLETE_POSITIONS"
elif not comp_errors:
    receipt["classification"]="HF_RECONCILIATION_COMPONENT_ERROR_UNAVAILABLE"
else:
    receipt["classification"]="HF_RECONCILIATION_MEASURED__TOLERANCE_NOT_FROZEN"

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":receipt["classification"],
 "borrowers_sampled":len(wallets),
 "complete_debt_positions":len(rows),
 "component_relative_error_stats":receipt["component_relative_error_stats"],
 "aggregate_relative_error_stats":receipt["aggregate_relative_error_stats"],
 "exclusions":excluded,
},indent=2))
