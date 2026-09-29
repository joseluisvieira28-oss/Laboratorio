#!/usr/bin/env python3
import datetime as dt,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
SRC=Path("drift_source/drift-202301.json")
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/POST_LIQUIDATOR_HEDGE_DRIFT_ROUTE_PROBE_RECEIPT_V0.1.json")

def iso(s):return dt.datetime.fromisoformat(str(s).replace("Z","+00:00"))
def addr_key(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def rank(r):return hashlib.sha256((r["signature"]+"|"+addr_key(r["instructionAddress"])).encode()).hexdigest()
def req(url,body=None,retries=8):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    h={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-post-liquidator-hedge/0.1"}
    if data is not None:h["Content-Type"]="application/json"
    q=urllib.request.Request(url,data=data,headers=h,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:last={"http":e.code};time.sleep(min(45,2**i));continue
            return int(e.code),raw
        except Exception as e:last={"error":type(e).__name__,"detail":str(e)[:220]};time.sleep(min(45,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")
def ts_slot(t):
    st,raw=req(f"{TSROOT}/{int(t.timestamp())}/block")
    if st!=200:raise RuntimeError(f"timestamp_resolver_http_{st}")
    o=json.loads(raw)
    if isinstance(o,int):return o
    for k in ("block","block_number","number","slot"):
        if isinstance(o.get(k),int):return o[k]
    raise RuntimeError("timestamp_resolver_schema")

src=json.loads(SRC.read_text())
assert src["classification"]=="FIELD_ENRICHMENT_PARTITION_PASS"
lp=[r for r in src["enriched_rows"] if r.get("class")=="liquidate_perp"]
seeds=sorted(lp,key=lambda r:(rank(r),r["signature"],addr_key(r["instructionAddress"])))[:3]
results=[];conflicts=0
for i,e in enumerate(seeds,1):
    authority=(e.get("semantic_accounts") or {}).get("authority")
    liquidator=(e.get("semantic_accounts") or {}).get("liquidator")
    t0=iso(e["timestamp"]);end=t0+dt.timedelta(seconds=60)
    to_slot=ts_slot(end)+4
    body={"type":"solana","fromBlock":int(e["slot"]),"toBlock":to_slot,
      "fields":{"block":{"number":True,"timestamp":True},
                "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                "instruction":{"programId":True,"accounts":True,"data":True,"transactionIndex":True,
                               "instructionAddress":True,"isCommitted":True,"error":True}},
      "instructions":[{"transaction":True}]}
    st,raw=req(STREAM,body)
    rr={"sample_index":i,"seed_signature":e["signature"],"seed_slot":e["slot"],"seed_timestamp":e["timestamp"],
        "authority":authority,"liquidator":liquidator,"window_end":end.isoformat().replace("+00:00","Z"),
        "http_status":st,"classification":"SOURCE_EVIDENCE_INCOMPLETE","post_transactions":[]}
    if st!=200:
        rr["transport_error"]=raw[:600].decode("utf-8","replace");results.append(rr);continue
    txmeta={};instructions=[]
    for line in raw.decode("utf-8","replace").splitlines():
        if not line.strip():continue
        b=json.loads(line);hdr=b.get("header") or {};slot=hdr.get("number");bt=hdr.get("timestamp")
        if isinstance(bt,(int,float)):bt=dt.datetime.fromtimestamp(bt,dt.timezone.utc).isoformat().replace("+00:00","Z")
        for pos,tx in enumerate(b.get("transactions") or []):
            ti=tx.get("transactionIndex",tx.get("index",pos));sigs=tx.get("signatures") or []
            sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
            if sig:txmeta[(slot,ti)]={"signature":sig,"err":tx.get("err"),"timestamp":bt,"slot":slot}
        for ix in b.get("instructions") or []:
            instructions.append((slot,bt,ix))
    grouped={}
    for slot,bt,ix in instructions:
        meta=txmeta.get((slot,ix.get("transactionIndex")))
        if not meta or meta["err"] is not None:continue
        sig=meta["signature"]
        if sig==e["signature"]:continue
        try:t=iso(meta["timestamp"])
        except Exception:continue
        if not(t0<t<=end):continue
        accounts=ix.get("accounts") or []
        if authority not in accounts and liquidator not in accounts:continue
        key=sig
        g=grouped.setdefault(key,{"signature":sig,"slot":slot,"timestamp":meta["timestamp"],"programs":[],"authority_account_seen":False,"liquidator_account_seen":False})
        g["authority_account_seen"] = g["authority_account_seen"] or authority in accounts
        g["liquidator_account_seen"] = g["liquidator_account_seen"] or liquidator in accounts
        g["programs"].append({"programId":ix.get("programId"),"instructionAddress":ix.get("instructionAddress"),
                              "authority_in_accounts":authority in accounts,"liquidator_in_accounts":liquidator in accounts,
                              "isCommitted":ix.get("isCommitted"),"error":ix.get("error")})
    rr["post_transactions"]=sorted(grouped.values(),key=lambda x:(x["timestamp"],x["slot"],x["signature"]))
    rr["post_transaction_count"]=len(rr["post_transactions"])
    rr["classification"]="POST_LIQUIDATOR_HEDGE_ROUTE_PROBE_PASS"
    results.append(rr)

passed=sum(r["classification"]=="POST_LIQUIDATOR_HEDGE_ROUTE_PROBE_PASS" for r in results)
classification="POST_LIQUIDATOR_HEDGE_DRIFT_ROUTE_3_OF_3_PASS" if passed==3 and conflicts==0 else "POST_LIQUIDATOR_HEDGE_DRIFT_ROUTE_BLOCKED"
rec={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","mission":"POST-LIQUIDATOR-HEDGE-001",
 "classification":classification,"sample_count":3,"pass_count":passed,"identity_conflict_count":conflicts,
 "results":results,"direction_labeled":False,
 "firewall":{"prices":False,"returns":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"wallets_mutation":False,"exchange_mutation":False,"merge_main":False}}
OUT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"pass_count":passed,
 "post_transaction_counts":[r.get("post_transaction_count") for r in results],
 "programs":[sorted(set(p["programId"] for tx in r.get("post_transactions",[]) for p in tx["programs"] if p.get("programId"))) for r in results]},indent=2))
if classification!="POST_LIQUIDATOR_HEDGE_DRIFT_ROUTE_3_OF_3_PASS":raise SystemExit(2)
