#!/usr/bin/env python3
import hashlib, json, math, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL="https://mcp.aave.com/"
OUT=Path("artifacts/lcod_source_probe_v01.json")
UA="CryptoLab-LCOD-001/0.1"

def rpc(method, params):
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
        if isinstance(sc,dict) and "data" in sc:
            return sc["data"]
        return sc
    if isinstance(x,dict) and "content" in x:
        for c in x["content"]:
            if isinstance(c,dict) and c.get("type")=="text":
                try:
                    z=json.loads(c.get("text",""))
                    if isinstance(z,dict) and "data" in z:
                        return z["data"]
                    return z
                except Exception:
                    pass
    if isinstance(x,dict) and "data" in x:
        return x["data"]
    return x

def call(name,args):
    return unwrap(rpc("tools/call",{"name":name,"arguments":args}))

def dicts(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            yield from dicts(v)
    elif isinstance(x,list):
        for v in x:
            yield from dicts(v)

def field_paths(x,prefix="",depth=0,max_depth=7):
    out=set()
    if depth>max_depth:return out
    if isinstance(x,dict):
        for k,v in x.items():
            p=f"{prefix}.{k}" if prefix else str(k)
            out.add(p)
            out |= field_paths(v,p,depth+1,max_depth)
    elif isinstance(x,list) and x:
        out |= field_paths(x[0],prefix+"[]",depth+1,max_depth)
    return out

def address_list(x):
    out=[]
    for d in dicts(x):
        for k in ("user","address","wallet"):
            v=d.get(k)
            if isinstance(v,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",v):
                out.append(v.lower());break
    return out

def extract_ids(x, keys):
    out=[]
    for d in dicts(x):
        for k in keys:
            v=d.get(k)
            if isinstance(v,str) and len(v)>=8:
                out.append(v)
    return out

catalog=rpc("tools/list",{})
tool_rows=(catalog or {}).get("tools",[])
toolmap={t.get("name"):t for t in tool_rows}
required=["get_markets","get_reserve_holders","get_user_positions","get_position_items","get_user_summary","get_reserve_details"]
missing=[x for x in required if x not in toolmap]

receipt={
  "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
  "stage":"LIVE_SOURCE_COMPONENT_CAPABILITY_PROBE",
  "captured_at_utc":datetime.now(timezone.utc).isoformat(),
  "endpoint":URL,
  "required_tools":required,
  "missing_tools":missing,
  "tool_input_schemas":{k:toolmap.get(k,{}).get("inputSchema") for k in required if k in toolmap},
  "market_returns_opened":False,
  "pnl_opened":False,
  "mutation":False,
  "action_tools_called":False,
}

if missing:
    receipt["classification"]="SOURCE_BLOCKED_REQUIRED_TOOLS_MISSING"
else:
    markets=call("get_markets",{"version":"v4"})
    reserve_ids=[]
    for d in dicts(markets):
        v=d.get("reserveId") or d.get("reserve_id")
        if isinstance(v,str):
            reserve_ids.append(v)
    reserve_ids=list(dict.fromkeys(reserve_ids))
    receipt["v4_reserve_ids_found"]=len(reserve_ids)
    receipt["markets_field_paths"]=sorted(field_paths(markets))[:1200]

    wallets=[]
    holder_queries=0
    holder_errors=[]
    for rid in reserve_ids[:20]:
        if len(set(wallets))>=6:break
        try:
            h=call("get_reserve_holders",{"reserveId":rid,"side":"borrow","limit":10,"version":"v4"})
            holder_queries+=1
            wallets.extend(address_list(h))
        except Exception as e:
            holder_errors.append(f"{type(e).__name__}:{str(e)[:240]}")
    wallets=list(dict.fromkeys(wallets))[:6]
    receipt["holder_queries"]=holder_queries
    receipt["holder_query_error_types"]=holder_errors
    receipt["sample_borrowers"]=len(wallets)
    receipt["sample_borrower_sha256"]=[hashlib.sha256(w.encode()).hexdigest() for w in wallets]

    samples=[]
    for w in wallets:
        row={"borrower_sha256":hashlib.sha256(w.encode()).hexdigest()}
        try:
            pos=call("get_user_positions",{"user":w,"version":"v4"})
            row["positions_field_paths"]=sorted(field_paths(pos))
            pos_ids=extract_ids(pos,("positionId","position_id","userPositionId","id"))
            reserve_from_pos=extract_ids(pos,("reserveId","reserve_id"))
            row["position_ids_found"]=len(set(pos_ids))
            row["reserve_ids_in_positions"]=len(set(reserve_from_pos))
        except Exception as e:
            row["positions_error"]=f"{type(e).__name__}:{str(e)[:160]}"
            pos=None;pos_ids=[];reserve_from_pos=[]

        try:
            summ=call("get_user_summary",{"user":w,"version":"v4"})
            row["summary_field_paths"]=sorted(field_paths(summ))
            # preserve numeric health candidates only, no wallet address
            hfs=[]
            for d in dicts(summ):
                for k,v in d.items():
                    nk=re.sub(r"[^a-z0-9]","",str(k).lower())
                    if "healthfactor" in nk:
                        try:
                            q=float(v)
                            if math.isfinite(q):hfs.append(q)
                        except Exception:pass
            row["summary_health_candidates"]=hfs[:10]
        except Exception as e:
            row["summary_error"]=f"{type(e).__name__}:{str(e)[:160]}"

        items=None
        spoke_ids=extract_ids(pos,("spokeId","spoke_id")) if pos is not None else []
        row["spoke_ids_found"]=len(set(spoke_ids))
        for spoke_id in list(dict.fromkeys(spoke_ids))[:2]:
            for side in ("supply","borrow"):
                args={"user":w,"spokeId":spoke_id,"side":side,"version":"v4"}
                try:
                    got=call("get_position_items",args)
                    row.setdefault("position_items_field_paths",[])
                    row["position_items_field_paths"]=sorted(set(row["position_items_field_paths"]) | field_paths(got))
                    row.setdefault("position_items_argument_shapes_used",[]).append({"spokeId_sha256":hashlib.sha256(spoke_id.encode()).hexdigest(),"side":side})
                    reserve_from_pos.extend(extract_ids(got,("reserveId","reserve_id")))
                    items=got
                except Exception:
                    continue

        row["reserve_ids_in_positions"]=len(set(reserve_from_pos))
        # reserve details on reserves actually referenced by component items
        reserve_detail_paths=set()
        for rid in list(dict.fromkeys(reserve_from_pos))[:3]:
            try:
                rd=call("get_reserve_details",{"reserveId":rid,"version":"v4"})
                reserve_detail_paths |= field_paths(rd)
                row["reserve_details_field_paths"]=sorted(reserve_detail_paths)
            except Exception as e:
                row["reserve_details_error"]=f"{type(e).__name__}:{str(e)[:160]}"
        samples.append(row)

    receipt["samples"]=samples
    all_paths=set()
    for s in samples:
        for k in ("positions_field_paths","position_items_field_paths","summary_field_paths","reserve_details_field_paths"):
            all_paths.update(s.get(k,[]))
    keywords=("collateral","borrow","debt","supply","principal","interest","price","usd","liquidation","threshold","health","ltv","reserve","emode")
    receipt["relevant_field_paths"]=sorted(p for p in all_paths if any(k in p.lower() for k in keywords))
    component_markers=[p for p in receipt["relevant_field_paths"] if any(k in p.lower() for k in ("principal","interest","debt","borrow","collateral","supply"))]
    valuation_markers=[p for p in receipt["relevant_field_paths"] if any(k in p.lower() for k in ("price","usd","liquidation","threshold","ltv"))]
    receipt["component_marker_count"]=len(component_markers)
    receipt["valuation_marker_count"]=len(valuation_markers)
    if wallets and component_markers and valuation_markers:
        receipt["classification"]="SOURCE_COMPONENT_FIELDS_PRESENT_RECONCILIATION_REQUIRED"
    elif wallets and component_markers:
        receipt["classification"]="SOURCE_COMPONENT_FIELDS_PRESENT_VALUATION_INCOMPLETE"
    else:
        receipt["classification"]="SOURCE_COMPONENT_FIELDS_INSUFFICIENT"

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":receipt.get("classification"),
 "missing_tools":missing,
 "v4_reserve_ids_found":receipt.get("v4_reserve_ids_found"),
 "sample_borrowers":receipt.get("sample_borrowers"),
 "component_marker_count":receipt.get("component_marker_count"),
 "valuation_marker_count":receipt.get("valuation_marker_count"),
},indent=2))
