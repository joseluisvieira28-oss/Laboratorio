#!/usr/bin/env python3
import hashlib,json,os,time
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
from urllib.request import Request,urlopen

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts"); os.makedirs(OUTDIR,exist_ok=True)
COMET="0xc3d688b66703497daa19211eedff47f25384cdc3"
BUY="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
BASE="https://eth.blockscout.com"; START_TS=1735689600; END_TS=1767225599
MAP={
 "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2":"ETHUSDT",
 "0x514910771af9ca656af840dff83e8264ecf986ca":"LINKUSDT",
 "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984":"UNIUSDT",
 "0xc00e94cb662c3520282e6f5717214004a7f26888":"COMPUSDT",
}

def sh(b):return hashlib.sha256(b).hexdigest()
def iv(v):
 s=str(v or "0");return int(s,16) if s.startswith("0x") else int(s)
def ad(v):
 s=str(v or "").lower();return "0x"+s[-40:] if len(s)>=40 else None
def words(d):
 s=str(d or "");s=s[2:] if s.startswith("0x") else s
 if len(s)%64:raise ValueError("malformed event data")
 return [int(s[i:i+64],16) for i in range(0,len(s),64)]
def fetch(u):
 q=Request(u,headers={"User-Agent":"CryptoLab-Compound30mReadiness-V0.1","Accept":"application/json"})
 with urlopen(q,timeout=120) as r:raw=r.read()
 return json.loads(raw.decode()),sh(raw)
def block_by_time(ts,closest):
 o,h=fetch(f"{BASE}/api?module=block&action=getblocknobytime&timestamp={ts}&closest={closest}")
 r=o.get("result")
 if isinstance(r,dict):
  for k in ("blockNumber","block_number","block"):
   if r.get(k) is not None:return iv(r[k]),h
 return iv(r),h
def logs(b0,b1):
 out=[];seen=set();pages=[];a=b0
 while a<=b1:
  b=min(b1,a+1_999_999)
  o,h=fetch(f"{BASE}/api/?module=logs&action=getLogs&fromBlock={a}&toBlock={b}&address={COMET}&topic0={BUY}")
  xs=o.get("result")
  if not isinstance(xs,list) or len(xs)>=1000:raise RuntimeError(f"bad/truncated page {a}-{b}")
  pages.append({"from":a,"to":b,"count":len(xs),"sha256":h})
  for x in xs:
   k=(str(x.get("blockNumber")),str(x.get("transactionHash")).lower(),str(x.get("logIndex")))
   if k not in seen:seen.add(k);out.append(x)
  a=b+1
 return out,pages

receipt={"program":"COMPOUND_REALIZED_DISPOSAL_CANONICAL_30M_READINESS_V0.1",
"lab_id":"COMPOUND-REALIZED-DISPOSAL-FLOW-001",
"generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
"canonical_freeze_commit":"2191bbf741ced5f801d8ae4034bd126c3b91cbc8",
"firewall":{"source_only":True,"market_prices_opened":False,"returns_computed":False,"pnl_computed":False,
"protected_2025_market_outcomes_opened":False,"five_minute_draft_used":False}}
try:
 b0,h0=block_by_time(START_TS,"after");b1,h1=block_by_time(END_TS,"before")
 raw,pages=logs(b0,b1)
 grouped=defaultdict(lambda:{"base_raw":0,"coll_raw":0,"timestamp":None,"block":None})
 raw_counts=Counter()
 for x in raw:
  t=x.get("topics") or [];w=words(x.get("data"))
  asset=ad(t[2]) if len(t)>=3 else None;proxy=MAP.get(asset)
  if not proxy:continue
  tx=str(x.get("transactionHash")).lower();ts=iv(x.get("timeStamp"));block=iv(x.get("blockNumber"))
  k=(asset,tx)
  g=grouped[k];g["base_raw"]+=w[0];g["coll_raw"]+=w[1];g["timestamp"]=ts;g["block"]=block
  raw_counts[proxy]+=1
 events=[]
 for (asset,tx),g in grouped.items():
  proxy=MAP[asset];dt=datetime.fromtimestamp(g["timestamp"],timezone.utc)
  events.append({"asset":asset,"proxy":proxy,"tx":tx,"timestamp":g["timestamp"],"dt":dt,
                 "block":g["block"],"base_raw":g["base_raw"],"coll_raw":g["coll_raw"]})
 events.sort(key=lambda e:(e["proxy"],e["timestamp"],e["tx"]))
 kept=[];suppressed=[];last_exit={}
 for e in events:
  cutoff=last_exit.get(e["proxy"])
  if cutoff is not None and e["dt"]<cutoff:
   suppressed.append(e);continue
  kept.append(e);last_exit[e["proxy"]]=e["dt"]+timedelta(minutes=30)
 weeks=Counter();by_proxy=Counter()
 for e in kept:
  iso=e["dt"].isocalendar();weeks[f"{iso.year}-W{iso.week:02d}"]+=1;by_proxy[e["proxy"]]+=1
 gates={
  "n_ge_100":len(kept)>=100,
  "iso_weeks_ge_20":len(weeks)>=20,
  "all_four_assets_ge_10":all(by_proxy[p]>=10 for p in ["ETHUSDT","LINKUSDT","UNIUSDT","COMPUSDT"])
 }
 status="CANONICAL_30M_PREDICTOR_READY" if all(gates.values()) else "CANONICAL_30M_PREDICTOR_WEAK"
 receipt.update({"status":status,"window":{"start_block":b0,"end_block":b1,"start_lookup_sha256":h0,"end_lookup_sha256":h1},
 "source_pages":pages,
 "readiness":{"eligible_raw_logs":sum(raw_counts.values()),"aggregated_tx_asset_events":len(events),
 "kept_events_after_30m_overlap":len(kept),"suppressed_overlap_events":len(suppressed),
 "unique_iso_weeks":len(weeks),"kept_by_proxy":dict(by_proxy),"raw_logs_by_proxy":dict(raw_counts),
 "kept_by_iso_week":dict(sorted(weeks.items()))},
 "gate":gates,
 "interpretation":{"edge_claim":False,"economic_test_run":False,"canonical_contract_changed":False}})
except Exception as e:
 receipt.update({"status":"TECHNICAL_FAILURE","error":repr(e),"interpretation":{"edge_claim":False,"economic_test_run":False}})
pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode();receipt["receipt_sha256_pre_self_field"]=sh(pre)
p=os.path.join(OUTDIR,"COMPOUND_REALIZED_DISPOSAL_FLOW_001_CANONICAL_30M_READINESS_RECEIPT_V0.1.json")
with open(p,"w") as f:json.dump(receipt,f,sort_keys=True,indent=2);f.write("\n")
print(json.dumps(receipt,sort_keys=True,indent=2));print("receipt="+p)
