#!/usr/bin/env python3
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE="https://api-v2.pendle.finance/core"
OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def fetch_json(url, timeout=120):
    req=Request(url,headers={
        "User-Agent":"CryptoLab-Pendle-SourceCompleteness-V0.1",
        "Accept":"application/json",
    })
    with urlopen(req,timeout=timeout) as r:
        raw=r.read()
        return json.loads(raw.decode("utf-8")), sha256_bytes(raw), r.status

def norm_expiry(v):
    if isinstance(v,(int,float)):
        return int(v/1000) if v>10_000_000_000 else int(v)
    if isinstance(v,str):
        try:
            if v.isdigit():
                return norm_expiry(int(v))
            return int(datetime.fromisoformat(v.replace("Z","+00:00")).timestamp())
        except Exception:
            return None
    return None

def nonempty(v):
    return v not in (None,False,[],{},"")

def identity_value(v):
    if isinstance(v,str):
        return v if v else None
    if isinstance(v,dict):
        for k in ("address","id","symbol","name"):
            x=v.get(k)
            if isinstance(x,str) and x:
                return x
    return None

def nested_keys(v):
    out=set()
    if isinstance(v,dict):
        out.update(v.keys())
        for x in v.values():
            if isinstance(x,dict):
                out.update(x.keys())
    elif isinstance(v,list):
        for x in v[:3]:
            if isinstance(x,dict):
                out.update(x.keys())
    return sorted(out)

cutoff=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp())
all_markets=[]
page_hashes=[]
skip=0
for _ in range(20):
    url=f"{BASE}/v2/markets/all?limit=100&skip={skip}"
    obj,h,status=fetch_json(url)
    rows=obj.get("results") if isinstance(obj,dict) else None
    if not isinstance(rows,list):
        raise RuntimeError("markets/all results is not a list")
    all_markets.extend(rows)
    page_hashes.append({"skip":skip,"count":len(rows),"sha256":h,"http_status":status})
    if len(rows)<100:
        break
    skip+=100

eth_expired=[]
for m in all_markets:
    if not isinstance(m,dict):
        continue
    chain=m.get("chain")
    cid=m.get("chainId") or m.get("chain_id") or (chain.get("id") if isinstance(chain,dict) else None)
    if str(cid)!="1":
        continue
    exp=norm_expiry(m.get("expiry") or m.get("expiryTimestamp") or m.get("expiration"))
    if exp is None or exp>=cutoff:
        continue
    eth_expired.append((m,exp))

records=[]
for m,exp in eth_expired:
    addr=m.get("address")
    aa=identity_value(m.get("accountingAsset"))
    pt=identity_value(m.get("pt") or m.get("PT") or m.get("principalToken"))
    yt=identity_value(m.get("yt") or m.get("YT") or m.get("yieldToken"))
    points_contaminated=nonempty(m.get("points"))
    rewards_present=nonempty(m.get("rewardTokens"))
    records.append({
        "address":addr if isinstance(addr,str) else None,
        "expiry_ts":exp,
        "protocol":identity_value(m.get("protocol")),
        "accounting_asset":aa,
        "pt_identity_present":bool(pt),
        "yt_identity_present":bool(yt),
        "points_contaminated":points_contaminated,
        "reward_tokens_metadata_present":rewards_present,
        "metadata_keys":sorted(m.keys()),
    })

points_free=[
    x for x in records
    if x["address"] and x["accounting_asset"] and not x["points_contaminated"]
]
points_free.sort(key=lambda x:x["address"].lower())

probes=[]
for rec in points_free[:10]:
    addr=rec["address"]
    query=urlencode({"time_frame":"day","includeApyBreakdown":"true"})
    url=f"{BASE}/v3/1/markets/{addr}/historical-data?{query}"
    try:
        obj,h,status=fetch_json(url)
        rows=obj.get("results") if isinstance(obj,dict) else None
        first=rows[0] if isinstance(rows,list) and rows and isinstance(rows[0],dict) else {}
        # Source/schema only: do not copy any APY or price values.
        probes.append({
            "address":addr,
            "expiry_ts":rec["expiry_ts"],
            "http_status":status,
            "payload_sha256":h,
            "historical_total":obj.get("total") if isinstance(obj,dict) else None,
            "timestamp_start":obj.get("timestamp_start") if isinstance(obj,dict) else None,
            "timestamp_end":obj.get("timestamp_end") if isinstance(obj,dict) else None,
            "row_keys":sorted(first.keys()),
            "yt_apy_breakdown_keys":nested_keys(first.get("ytApyBreakdown")),
            "lp_apy_breakdown_keys":nested_keys(first.get("lpApyBreakdown")),
            "breakdown_schema_present":(
                "ytApyBreakdown" in first or "lpApyBreakdown" in first
            ),
        })
    except Exception as e:
        probes.append({
            "address":addr,
            "expiry_ts":rec["expiry_ts"],
            "error":repr(e),
            "breakdown_schema_present":False,
        })
    time.sleep(0.2)

probe_pass=sum(
    1 for p in probes
    if "error" not in p and isinstance(p.get("historical_total"),int) and p["historical_total"]>0
)
breakdown_pass=sum(1 for p in probes if p.get("breakdown_schema_present"))
identity_complete=sum(1 for x in points_free if x["pt_identity_present"] and x["yt_identity_present"])
points_contaminated=sum(1 for x in records if x["points_contaminated"])
points_free_count=len(points_free)

status="SOURCE_COMPLETENESS_PASS"
if points_free_count==0:
    status="INSUFFICIENT_POINTS_FREE_POPULATION"
elif probe_pass==0:
    status="SOURCE_COMPLETENESS_PARTIAL"
elif breakdown_pass==0:
    status="SOURCE_COMPLETENESS_PARTIAL"

receipt={
    "lab_id":"PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001",
    "protocol":"PENDLE_FIXED_VARIABLE_YIELD_PREMIUM_001_SOURCE_COMPLETENESS_PROTOCOL_V0.1",
    "status":status,
    "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
    "population_rule":{
        "chain_id":1,
        "expiry_before_utc":"2025-01-01T00:00:00Z",
        "points_rule":"non-empty points metadata => POINTS_CONTAMINATED; excluded from future economic population unless separately valued prospectively",
        "selection_uses_market_outcomes":False,
    },
    "counts":{
        "markets_enumerated":len(all_markets),
        "ethereum_expired_pre2025":len(records),
        "points_contaminated":points_contaminated,
        "points_free_source_candidates":points_free_count,
        "points_free_with_pt_yt_identity":identity_complete,
        "points_free_with_reward_token_metadata":sum(1 for x in points_free if x["reward_tokens_metadata_present"]),
        "deterministic_history_probes":len(probes),
        "history_probe_pass":probe_pass,
        "apy_breakdown_schema_pass":breakdown_pass,
    },
    "market_page_receipts":page_hashes,
    "points_free_metadata_records":points_free,
    "historical_schema_probes":probes,
    "firewall":{
        "source_only":True,
        "implied_apy_values_emitted":False,
        "underlying_apy_values_emitted":False,
        "yield_premium_computed":False,
        "returns_computed":False,
        "pnl_computed":False,
        "protected_2025_opened":False,
        "live_trading":False,
        "orders":False,
        "exchange_mutation":False,
        "capital":False,
        "paid_data":False,
    },
}
pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
receipt["receipt_sha256_pre_self_field"]=sha256_bytes(pre)

out=os.path.join(OUTDIR,"PENDLE_SOURCE_COMPLETENESS_RECEIPT_V0.1.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,indent=2)
    f.write("\n")

print(json.dumps({
    "status":status,
    "counts":receipt["counts"],
    "receipt_sha256_pre_self_field":receipt["receipt_sha256_pre_self_field"],
},sort_keys=True,indent=2))
print(f"receipt={out}")
