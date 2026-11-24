#!/usr/bin/env python3
import hashlib,json,os,time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from urllib.request import Request,urlopen

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts"); os.makedirs(OUTDIR,exist_ok=True)
COMET="0xc3d688b66703497daa19211eedff47f25384cdc3"
BUY="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
BASE="https://eth.blockscout.com"
START_TS=1735689600; END_TS=1767225599
MAP={
 "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2":"ETHUSDT",
 "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0":"ETHUSDT",
 "0x514910771af9ca656af840dff83e8264ecf986ca":"LINKUSDT",
 "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984":"UNIUSDT",
 "0xc00e94cb662c3520282e6f5717214004a7f26888":"COMPUSDT",
}

def sh(b):return hashlib.sha256(b).hexdigest()
def iv(v):
 s=str(v or "0"); return int(s,16) if s.startswith("0x") else int(s)
def ad(v):
 s=str(v or "").lower(); return "0x"+s[-40:] if len(s)>=40 else None
def words(d):
 s=str(d or ""); s=s[2:] if s.startswith("0x") else s
 return [int(s[i:i+64],16) for i in range(0,len(s),64)]
def fetch(u):
 q=Request(u,headers={"User-Agent":"CryptoLab-CompoundPrimaryReadiness-V0.1","Accept":"application/json"})
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

receipt={"program":"COMPOUND_REALIZED_DISPOSAL_PRIMARY_READINESS_V0.1",
"lab_id":"COMPOUND-REALIZED-DISPOSAL-FLOW-001",
"generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
"firewall":{"source_only":True,"market_prices_opened":False,"returns_computed":False,"pnl_computed":False,
"protected_2025_market_outcomes_opened":False,"protected_2026_market_outcomes_opened":False}}
try:
 b0,h0=block_by_time(START_TS,"after"); b1,h1=block_by_time(END_TS,"before")
 raw,pages=logs(b0,b1)
 events=[]; block_ts={}
 for x in raw:
  t=x.get("topics") or []; w=words(x.get("data"))
  asset=ad(t[2]) if len(t)>=3 else None
  proxy=MAP.get(asset)
  if not proxy:continue
  events.append({"block":iv(x.get("blockNumber")),"asset":asset,"proxy":proxy,"base_raw":w[0]})
 # Resolve one timestamp per unique eligible block using Blockscout v2.
 for n,b in enumerate(sorted({x["block"] for x in events}),1):
  if n%4==0:time.sleep(.15)
  o,_=fetch(f"{BASE}/api/v2/blocks/{b}")
  ts=o.get("timestamp")
  if isinstance(ts,str):
   dt=datetime.fromisoformat(ts.replace("Z","+00:00"))
  elif isinstance(ts,(int,float)):
   dt=datetime.fromtimestamp(ts,timezone.utc)
  else:raise RuntimeError(f"missing timestamp for block {b}")
  block_ts[b]=dt
 clusters=defaultdict(lambda:{"flow_usdc":0.0,"events":0})
 for e in events:
  k=(e["proxy"],e["block"])
  clusters[k]["flow_usdc"]+=e["base_raw"]/1e6
  clusters[k]["events"]+=1
 weeks=Counter(); by_proxy_clusters=Counter(); by_proxy_events=Counter()
 flows=[]
 for (proxy,b),v in clusters.items():
  dt=block_ts[b]; iso=dt.isocalendar(); wk=f"{iso.year}-W{iso.week:02d}"
  weeks[wk]+=1; by_proxy_clusters[proxy]+=1; flows.append(v["flow_usdc"])
 for e in events:by_proxy_events[e["proxy"]]+=1
 flows.sort()
 def q(p):
  if not flows:return None
  idx=min(len(flows)-1,max(0,int(round((len(flows)-1)*p))))
  return round(flows[idx],6)
 status="PRIMARY_PREDICTOR_READY" if len(clusters)>=100 and len(weeks)>=12 else "PRIMARY_PREDICTOR_WEAK"
 receipt.update({"status":status,"window":{"start_block":b0,"end_block":b1,"start_lookup_sha256":h0,"end_lookup_sha256":h1},
 "source_pages":pages,
 "readiness":{"eligible_raw_events":len(events),"proxy_block_clusters":len(clusters),"unique_iso_weeks":len(weeks),
 "events_by_proxy":dict(by_proxy_events),"clusters_by_proxy":dict(by_proxy_clusters),"clusters_by_iso_week":dict(sorted(weeks.items())),
 "flow_usdc":{"min":round(flows[0],6) if flows else None,"p50":q(.5),"p90":q(.9),"p95":q(.95),"p99":q(.99),"max":round(flows[-1],6) if flows else None}},
 "gate":{"clusters_ge_100":len(clusters)>=100,"weeks_ge_12":len(weeks)>=12},
 "interpretation":{"edge_claim":False,"economic_test_run":False}})
except Exception as e:
 receipt.update({"status":"TECHNICAL_FAILURE","error":repr(e),"interpretation":{"edge_claim":False,"economic_test_run":False}})
pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode();receipt["receipt_sha256_pre_self_field"]=sh(pre)
p=os.path.join(OUTDIR,"COMPOUND_REALIZED_DISPOSAL_FLOW_001_PRIMARY_READINESS_RECEIPT_V0.1.json")
with open(p,"w") as f:json.dump(receipt,f,sort_keys=True,indent=2);f.write("\n")
print(json.dumps(receipt,sort_keys=True,indent=2));print("receipt="+p)
