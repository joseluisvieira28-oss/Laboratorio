#!/usr/bin/env python3
import hashlib, json, os, time
from collections import Counter
from datetime import datetime, timezone
from urllib.request import Request, urlopen

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts"); os.makedirs(OUTDIR,exist_ok=True)
LAB_ID="COMPOUND-REALIZED-DISPOSAL-FLOW-001"
COMET="0xc3d688b66703497daa19211eedff47f25384cdc3"
BUY="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
BASE="https://eth.blockscout.com"
START_TS=1735689600
END_TS=1767225599

def sh(b): return hashlib.sha256(b).hexdigest()
def iv(v):
    if isinstance(v,int): return v
    s=str(v or "0"); return int(s,16) if s.startswith("0x") else int(s)
def ad(v):
    s=str(v or "").lower(); return "0x"+s[-40:] if len(s)>=40 else None
def wd(d):
    s=str(d or ""); s=s[2:] if s.startswith("0x") else s
    if len(s)%64: raise ValueError("bad event data")
    return [int(s[i:i+64],16) for i in range(0,len(s),64)]
def fetch(url,timeout=120):
    req=Request(url,headers={"User-Agent":"CryptoLab-Compound2025PredictorCensus-V0.1","Accept":"application/json"})
    with urlopen(req,timeout=timeout) as r: raw=r.read()
    return json.loads(raw.decode()),sh(raw)
def block_by_time(ts,closest):
    url=f"{BASE}/api?module=block&action=getblocknobytime&timestamp={ts}&closest={closest}"
    o,h=fetch(url)
    r=o.get("result") if isinstance(o,dict) else None
    if isinstance(r,dict):
        for k in ("blockNumber","block_number","block"):
            if r.get(k) is not None: return iv(r[k]),h,o
    if r is not None and not isinstance(r,(list,dict)): return iv(r),h,o
    raise RuntimeError(f"block_by_time failed: {o!r}")
def get_logs(b0,b1):
    out=[]; seen=set(); pages=[]; cur=b0
    while cur<=b1:
        stop=min(b1,cur+1_999_999)
        u=(f"{BASE}/api/?module=logs&action=getLogs&fromBlock={cur}&toBlock={stop}"
           f"&address={COMET}&topic0={BUY}")
        time.sleep(1.1); o,h=fetch(u)
        rows=o.get("result") if isinstance(o,dict) else None
        if not isinstance(rows,list): raise RuntimeError(f"invalid logs response {cur}-{stop}: {o!r}")
        if len(rows)>=1000: raise RuntimeError(f"possible truncation {cur}-{stop}: {len(rows)}")
        pages.append({"from":cur,"to":stop,"count":len(rows),"sha256":h})
        for x in rows:
            k=(str(x.get("blockNumber","")).lower(),str(x.get("transactionHash","")).lower(),str(x.get("logIndex","")).lower())
            if k not in seen: seen.add(k); out.append(x)
        cur=stop+1
    return out,pages
def decode(x):
    t=x.get("topics") or []; w=wd(x.get("data"))
    if len(t)<3 or len(w)<2: raise ValueError("malformed BuyCollateral")
    ts=iv(x.get("timeStamp"))
    dt=datetime.fromtimestamp(ts,timezone.utc)
    return {"block":iv(x.get("blockNumber")),"tx":str(x.get("transactionHash","")).lower(),
            "logi":iv(x.get("logIndex")),"buyer":ad(t[1]),"asset":ad(t[2]),
            "base":w[0],"coll":w[1],"timestamp":ts,
            "month":dt.strftime("%Y-%m"),"iso_week":f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"}

receipt={"program":"COMPOUND_REALIZED_DISPOSAL_FLOW_2025_PREDICTOR_CENSUS_V0.1","lab_id":LAB_ID,
"generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
"firewall":{"source_only":True,"market_prices_opened":False,"returns_computed":False,"pnl_computed":False,
"protected_2025_market_outcomes_opened":False,"direction_selected_from_outcomes":False,"horizon_selected_from_outcomes":False,
"live_trading":False,"orders":False,"exchange_mutation":False,"capital":False,"paid_data":False,"main_merge":False}}

try:
    b0,h0,o0=block_by_time(START_TS,"after")
    b1,h1,o1=block_by_time(END_TS,"before")
    raw,pages=get_logs(b0,b1)
    xs=[decode(x) for x in raw]
    buyers=Counter(x["buyer"] for x in xs if x["buyer"])
    assets=Counter(x["asset"] for x in xs if x["asset"])
    months=Counter(x["month"] for x in xs)
    weeks=Counter(x["iso_week"] for x in xs)
    txs={x["tx"] for x in xs}
    n=len(xs)
    top_n=buyers.most_common(1)[0][1] if buyers else 0
    top_share=(top_n/n) if n else 1.0
    gate={
      "events_ge_30":n>=30,
      "unique_transactions_ge_30":len(txs)>=30,
      "unique_assets_ge_3":len(assets)>=3,
      "unique_iso_weeks_ge_12":len(weeks)>=12,
      "top_buyer_share_lt_80pct":top_share<0.80,
    }
    status="PREDICTOR_SAMPLE_VIABLE" if all(gate.values()) else "PREDICTOR_SAMPLE_WEAK"
    receipt.update({"status":status,
      "window":{"start_utc":"2025-01-01T00:00:00Z","end_utc":"2025-12-31T23:59:59Z",
                "start_block":b0,"end_block":b1,"start_block_lookup_sha256":h0,"end_block_lookup_sha256":h1},
      "source_pages":pages,
      "census":{"buy_collateral_events":n,"unique_transactions":len(txs),"unique_buyers":len(buyers),
                "unique_assets":len(assets),"unique_iso_weeks":len(weeks),
                "top_buyer":buyers.most_common(1)[0][0] if buyers else None,
                "top_buyer_events":top_n,"top_buyer_share_pct":round(top_share*100,4) if n else None,
                "by_asset":dict(sorted(assets.items())),"by_month":dict(sorted(months.items())),
                "by_iso_week":dict(sorted(weeks.items()))},
      "gate":gate,
      "interpretation":{"edge_claim":False,"economic_test_run":False,"protected_market_outcomes_opened":False}})
except Exception as e:
    receipt.update({"status":"TECHNICAL_FAILURE","error":repr(e),
      "interpretation":{"edge_claim":False,"economic_test_run":False,"protected_market_outcomes_opened":False}})

pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
receipt["receipt_sha256_pre_self_field"]=sh(pre)
out=os.path.join(OUTDIR,"COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_PREDICTOR_CENSUS_RECEIPT_V0.1.json")
with open(out,"w",encoding="utf-8") as f: json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps(receipt,sort_keys=True,indent=2)); print("receipt="+out)
