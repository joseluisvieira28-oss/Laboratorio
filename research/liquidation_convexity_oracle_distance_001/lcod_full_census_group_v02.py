#!/usr/bin/env python3
import hashlib,json,math,re,time,urllib.request,urllib.error,os
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

URL="https://mcp.aave.com/"
GROUP=os.environ.get("LCOD_GROUP","0123").lower()
if not GROUP or any(ch not in "0123456789abcdef" for ch in GROUP):
    raise SystemExit("INVALID_LCOD_GROUP")
OUT=Path(f"artifacts/lcod_full_census_group_{GROUP}_v02.json")
TOL=5e-5

def rpc(method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for attempt in range(4):
        try:
            req=urllib.request.Request(URL,data=payload,headers={"Content-Type":"application/json","User-Agent":f"CryptoLab-LCOD-001-Group-{GROUP}/0.1"},method="POST")
            with urllib.request.urlopen(req,timeout=45) as r:x=json.loads(r.read().decode())
            if x.get("error"):raise RuntimeError(x["error"])
            return x.get("result")
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,RuntimeError) as e:
            last=e
            if attempt==3:raise
            time.sleep(1.5*(attempt+1))
    raise last

def unwrap(x):
    if isinstance(x,dict) and x.get("structuredContent") is not None:
        y=x["structuredContent"]; return y.get("data") if isinstance(y,dict) and "data" in y else y
    if isinstance(x,dict) and "content" in x:
        for c in x["content"]:
            if isinstance(c,dict) and c.get("type")=="text":
                try:
                    y=json.loads(c.get("text","")); return y.get("data") if isinstance(y,dict) and "data" in y else y
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

# Enumerate full index in-memory.
markets=call("get_markets",{"version":"v4"})
reserve_ids=list(dict.fromkeys(d["reserveId"] for d in walk(markets) if isinstance(d.get("reserveId"),str)))
all_wallets=set(); census_errors=[]
for rid in reserve_ids:
    cursor=None; seen=set()
    for page in range(1000):
        args={"reserveId":rid,"side":"borrow","limit":50,"version":"v4"}
        if cursor:args["cursor"]=cursor
        try:r=call("get_reserve_holders",args)
        except Exception as e:
            census_errors.append(f"{type(e).__name__}:{str(e)[:180]}");break
        all_wallets.update(addresses(r))
        nxt=next_cursor(r)
        if not nxt:break
        if nxt in seen:
            census_errors.append("CURSOR_LOOP");break
        seen.add(nxt);cursor=nxt
    else:census_errors.append("MAX_PAGES")

selected=sorted(w for w in all_wallets if hashlib.sha256(w.encode()).hexdigest()[0] in set(GROUP))
eligible=0; debt_borrowers=0; no_debt=0
reasons=Counter(); rel_errors=[]; read_errors=[]
borrower_receipts=[]

for w in selected:
    # Fresh-price remediation: reserve details are cached only inside this borrower
    # so official HF and reserve price/factor reads are temporally close.
    borrower_detail_cache={}
    def detail(rid):
        if rid not in borrower_detail_cache:
            borrower_detail_cache[rid]=call("get_reserve_details",{"reserveId":rid,"version":"v4"})
        return borrower_detail_cache[rid]
    wh=hashlib.sha256(w.encode()).hexdigest()
    row={"borrower_sha256":wh,"status":"UNKNOWN","debt_positions":0}
    try:ps=positions(call("get_user_positions",{"user":w,"version":"v4"}))
    except Exception as e:
        reasons["USER_POSITIONS_READ_ERROR"]+=1;read_errors.append(f"positions:{type(e).__name__}:{str(e)[:160]}");row["status"]="USER_POSITIONS_READ_ERROR";borrower_receipts.append(row);continue
    debt_ps=[p for p in ps if (num(p.get("totalDebtUsd")) or 0)>0]
    row["debt_positions"]=len(debt_ps)
    if not debt_ps:
        no_debt+=1;row["status"]="NO_CURRENT_DEBT_POSITION";borrower_receipts.append(row);continue
    debt_borrowers+=1
    borrower_ok=True; max_rel=0.0

    for p in debt_ps:
        spoke=p.get("spokeId");official=num(p.get("healthFactor"))
        if not isinstance(spoke,str) or official is None or official<=0:
            borrower_ok=False;reasons["POSITION_REQUIRED_FIELD_MISSING"]+=1;break
        try:
            ss=items(call("get_position_items",{"user":w,"spokeId":spoke,"side":"supply","version":"v4"}))
            bs=items(call("get_position_items",{"user":w,"spokeId":spoke,"side":"borrow","version":"v4"}))
        except Exception as e:
            borrower_ok=False;reasons["ITEM_READ_ERROR"]+=1;read_errors.append(f"items:{type(e).__name__}:{str(e)[:160]}");break
        cap=0.0; debt=0.0; collateral_legs=0; borrow_legs=0; complete=True
        for it in ss:
            if not bool(it.get("isCollateral")):continue
            rid=it.get("reserveId");amount=num(it.get("balance"))
            if not isinstance(rid,str) or amount is None:complete=False;break
            try:rd=detail(rid)
            except Exception as e:
                complete=False;read_errors.append(f"reserve:{type(e).__name__}:{str(e)[:160]}");break
            price=num(rd.get("priceUsd")) if isinstance(rd,dict) else None
            cf=num(rd.get("collateralFactorPct")) if isinstance(rd,dict) else None
            if price is None or cf is None:complete=False;break
            cap+=amount*price*(cf/100.0);collateral_legs+=1
        if not complete:
            borrower_ok=False;reasons["SUPPLY_COMPONENT_INCOMPLETE"]+=1;break
        for it in bs:
            rid=it.get("reserveId");principal=num(it.get("principal"));interest=num(it.get("interest"));bal=num(it.get("balance"))
            if not isinstance(rid,str) or principal is None or interest is None:complete=False;break
            try:rd=detail(rid)
            except Exception as e:
                complete=False;read_errors.append(f"reserve:{type(e).__name__}:{str(e)[:160]}");break
            price=num(rd.get("priceUsd")) if isinstance(rd,dict) else None
            if price is None:complete=False;break
            amount=principal+interest
            if bal is not None and abs(bal-amount)>1e-9:
                complete=False;reasons["DEBT_BALANCE_IDENTITY_FAIL"]+=1;break
            debt+=amount*price;borrow_legs+=1
        if not complete or cap<=0 or debt<=0 or collateral_legs==0 or borrow_legs==0:
            borrower_ok=False;reasons["DEBT_COMPONENT_INCOMPLETE"]+=1;break
        reconstructed=cap/debt
        rel=abs(reconstructed-official)/official
        rel_errors.append(rel);max_rel=max(max_rel,rel)
        if rel>TOL:
            borrower_ok=False;reasons["HF_RECONCILIATION_FAIL"]+=1;break

    if borrower_ok:
        eligible+=1;row["status"]="ELIGIBLE";row["max_relative_hf_error"]=max_rel
    else:
        row["status"]="INELIGIBLE"
    borrower_receipts.append(row)

coverage=eligible/debt_borrowers if debt_borrowers else 0.0
passed=(not census_errors and debt_borrowers>0 and coverage>=0.90 and not read_errors)
finished_at=datetime.now(timezone.utc)
receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"FULL_CENSUS_GROUP_FRESH_PRICE_RECON_V0.2",
 "captured_at_utc":finished_at.isoformat(),
 "price_read_policy":"fresh get_reserve_details cache scoped to one borrower only",
 "canonical_snapshot_claim":False,
 "group_prefixes":GROUP,
 "selection_rule":"sha256(lowercase_wallet)[0] in group_prefixes",
 "full_index_borrowers":len(all_wallets),
 "group_indexed_borrowers":len(selected),
 "debt_bearing_borrowers":debt_borrowers,
 "no_current_debt_position":no_debt,
 "eligible_borrowers":eligible,
 "eligible_coverage":coverage,
 "frozen_min_coverage":0.90,
 "hf_relative_error_tolerance":TOL,
 "max_observed_relative_hf_error":max(rel_errors) if rel_errors else None,
 "exclusion_reasons":dict(reasons),
 "census_errors":census_errors,
 "read_errors":read_errors[:50],
 "borrower_receipts":borrower_receipts,
 "classification":"GROUP_FRESH_PRICE_RECON_PASS" if passed else "GROUP_FRESH_PRICE_RECON_BLOCKED",
 "curve_computed":False,
 "market_returns_opened":False,"liquidation_outcomes_opened":False,"pnl_opened":False,"mutation":False,
 "raw_wallet_addresses_retained":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ("classification","full_index_borrowers","group_indexed_borrowers","debt_bearing_borrowers","eligible_borrowers","eligible_coverage","max_observed_relative_hf_error","exclusion_reasons","census_errors","read_errors")},indent=2))
