#!/usr/bin/env python3
import hashlib,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path

URL="https://mcp.aave.com/"
OUT=Path("artifacts/lcod_v4_borrower_census_v01.json")
MAX_PAGES=1000

def rpc(method,params):
    req=urllib.request.Request(URL,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),headers={"Content-Type":"application/json","User-Agent":"CryptoLab-LCOD-001-Census/0.1"},method="POST")
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
            if isinstance(v,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",v):
                out.append(v.lower());break
    return out

def next_cursor(x):
    found=[]
    for d in walk(x):
        for k in ("nextCursor","next_cursor"):
            v=d.get(k)
            if isinstance(v,str) and v.strip():found.append(v.strip())
    uniq=list(dict.fromkeys(found))
    if len(uniq)>1:raise RuntimeError("AMBIGUOUS_MULTIPLE_NEXT_CURSORS")
    return uniq[0] if uniq else None

catalog=rpc("tools/list",{})
names={t.get("name") for t in (catalog or {}).get("tools",[])}
if not {"get_markets","get_reserve_holders"}.issubset(names):
    raise SystemExit("required tools absent")

markets=call("get_markets",{"version":"v4"})
reserve_ids=[]
for d in walk(markets):
    rid=d.get("reserveId")
    if isinstance(rid,str):reserve_ids.append(rid)
reserve_ids=list(dict.fromkeys(reserve_ids))

all_wallets=set()
reserves=[]
errors=[]
for idx,rid in enumerate(reserve_ids):
    cursor=None
    seen_cursors=set()
    pages=0
    row_count=0
    reserve_wallets=set()
    status="PASS"
    error=None
    while True:
        if pages>=MAX_PAGES:
            status="FAIL";error="MAX_PAGES_EXCEEDED";break
        args={"reserveId":rid,"side":"borrow","limit":50,"version":"v4"}
        if cursor is not None:args["cursor"]=cursor
        try:
            result=call("get_reserve_holders",args)
        except Exception as e:
            status="FAIL";error=f"{type(e).__name__}:{str(e)[:300]}";break
        pages+=1
        addrs=addresses(result)
        row_count+=len(addrs)
        reserve_wallets.update(addrs)
        nxt=next_cursor(result)
        if not nxt:break
        if nxt in seen_cursors:
            status="FAIL";error="CURSOR_LOOP";break
        seen_cursors.add(nxt)
        cursor=nxt
    all_wallets.update(reserve_wallets)
    reserves.append({
      "reserve_id_sha256":hashlib.sha256(rid.encode()).hexdigest(),
      "status":status,
      "pages":pages,
      "raw_address_rows":row_count,
      "unique_borrowers":len(reserve_wallets),
      "error":error,
    })
    if status!="PASS":errors.append({"reserve_id_sha256":hashlib.sha256(rid.encode()).hexdigest(),"error":error})

passed=bool(reserve_ids) and not errors and len(reserves)==len(reserve_ids) and len(all_wallets)>0
receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"V4_BORROWER_INDEX_CENSUS_SOURCE_GATE",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"CENSUS_INDEX_SOURCE_PASS" if passed else "CENSUS_INDEX_SOURCE_BLOCKED",
 "reserve_count_initial":len(reserve_ids),
 "reserves_visited":len(reserves),
 "total_pages":sum(x["pages"] for x in reserves),
 "total_raw_address_rows":sum(x["raw_address_rows"] for x in reserves),
 "deduplicated_borrower_count":len(all_wallets),
 "borrower_sha256":sorted(hashlib.sha256(w.encode()).hexdigest() for w in all_wallets),
 "reserve_receipts":reserves,
 "errors":errors,
 "raw_wallet_addresses_retained":False,
 "health_factor_values_opened":False,
 "liquidation_outcomes_opened":False,
 "market_returns_opened":False,
 "pnl_opened":False,
 "mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ("classification","reserve_count_initial","reserves_visited","total_pages","total_raw_address_rows","deduplicated_borrower_count","errors")},indent=2))
