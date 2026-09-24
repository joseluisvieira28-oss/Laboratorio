#!/usr/bin/env python3
import json,math,re,statistics,urllib.request
from datetime import datetime,timezone
from pathlib import Path

URL="https://mcp.aave.com/"
ROOT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/aave_hf_crowding_001_calibration")
ROOT.mkdir(parents=True,exist_ok=True)
TODAY=datetime.now(timezone.utc).date().isoformat()
SNAP=ROOT/f"{TODAY}.json"
ROLL=ROOT/"ROLLUP.json"

def rpc(method,params):
    req=urllib.request.Request(URL,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AAVE-HFC-001/1.3"},method="POST")
    with urllib.request.urlopen(req,timeout=45) as r:
        x=json.loads(r.read().decode())
    if x.get("error"): raise RuntimeError(x["error"])
    return x.get("result")

def unwrap(x):
    if isinstance(x,dict) and x.get("structuredContent") is not None:return x["structuredContent"]
    if isinstance(x,dict) and "content" in x:
        for c in x["content"]:
            if isinstance(c,dict) and c.get("type")=="text":
                try:return json.loads(c.get("text",""))
                except: pass
    return x

def call(name,args):
    return unwrap(rpc("tools/call",{"name":name,"arguments":args}))

def dicts(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from dicts(v)
    elif isinstance(x,list):
        for v in x: yield from dicts(v)

def addresses(x):
    out=[]
    for d in dicts(x):
        for k in ("user","address","wallet"):
            v=d.get(k)
            if isinstance(v,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",v):
                out.append(v.lower()); break
    return out

def hf_values(x):
    vals=[]
    def walk(v):
        if isinstance(v,dict):
            for k,z in v.items():
                nk=re.sub(r"[^a-z0-9]","",str(k).lower())
                if "healthfactor" in nk:
                    try:
                        q=float(z)
                        if math.isfinite(q) and q>0: vals.append(q)
                    except: pass
                walk(z)
        elif isinstance(v,list):
            for z in v: walk(z)
    walk(x)
    return vals

if SNAP.exists():
    print(json.dumps({"status":"IDEMPOTENT_ALREADY_CAPTURED","date":TODAY}))
    raise SystemExit(0)

markets=call("get_markets",{"version":"v4"})
reserves=sorted({str(d.get("reserveId") or d.get("reserve_id")) for d in dicts(markets) if (d.get("reserveId") or d.get("reserve_id")) is not None})
wallets=set(); holder_errors=0
for rid in reserves:
    try:
        h=call("get_reserve_holders",{"reserveId":rid,"side":"borrow","limit":10,"version":"v4"})
        wallets.update(addresses(h))
    except Exception:
        holder_errors+=1

hfs=[]; summary_errors=0
for w in sorted(wallets):
    try:
        s=call("get_user_summary",{"user":w,"version":"v4"})
        vals=hf_values(s)
        if vals: hfs.append(min(vals))
    except Exception:
        summary_errors+=1

n=len(wallets); valid=len(hfs)
coverage=(valid/n) if n else 0.0
primary=(sum(x<1.10 for x in hfs)/valid) if valid else None
snapshot={
 "lab_id":"AAVE-HF-CROWDING-001",
 "stage":"OUTCOME_BLIND_CALIBRATION",
 "utc_date":TODAY,
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "reserve_count":len(reserves),
 "borrower_wallet_count":n,
 "valid_health_factor_count":valid,
 "valid_hf_coverage":coverage,
 "primary_fraction_hf_lt_1_10":primary,
 "diagnostic_fraction_hf_lt_1_05":(sum(x<1.05 for x in hfs)/valid) if valid else None,
 "diagnostic_fraction_hf_lt_1_25":(sum(x<1.25 for x in hfs)/valid) if valid else None,
 "diagnostic_median_hf":statistics.median(hfs) if hfs else None,
 "holder_query_error_count":holder_errors,
 "summary_query_error_count":summary_errors,
 "wallet_addresses_retained":False,
 "individual_hf_values_retained":False,
 "liquidation_outcomes_opened":False,
 "market_prices_opened":False,
 "returns_opened":False,
 "pnl_opened":False,
 "action_tool_called":False,
 "mutation":False
}
SNAP.write_text(json.dumps(snapshot,indent=2,sort_keys=True)+"\n")

snaps=[]
for p in sorted(ROOT.glob("20??-??-??.json")):
    try: snaps.append(json.loads(p.read_text()))
    except: pass
valid_snaps=[x for x in snaps if x.get("valid_health_factor_count",0)>=20 and x.get("primary_fraction_hf_lt_1_10") is not None]
coverages=[x["valid_hf_coverage"] for x in valid_snaps]
ready=len(valid_snaps)>=30 and (statistics.median(coverages)>=0.80 if coverages else False)
roll={
 "lab_id":"AAVE-HF-CROWDING-001",
 "stage":"OUTCOME_BLIND_CALIBRATION",
 "distinct_valid_utc_days":len(valid_snaps),
 "median_valid_hf_coverage":statistics.median(coverages) if coverages else None,
 "classification":"HF_CROWDING_Q90_READY_TO_FREEZE" if ready else "HF_CROWDING_CALIBRATION_COLLECTING",
 "q90_not_computed_until_ready":not ready,
 "outcomes_opened":False
}
ROLL.write_text(json.dumps(roll,indent=2,sort_keys=True)+"\n")
print(json.dumps({"snapshot":snapshot,"rollup":roll},indent=2))
