#!/usr/bin/env python3
import hashlib,json,os,time
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
from urllib.request import Request,urlopen

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts");os.makedirs(OUTDIR,exist_ok=True)
COMET="0xc3d688b66703497daa19211eedff47f25384cdc3"
BUY="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
BASE="https://eth.blockscout.com"; START=1735689600; END=1767225599; Y2026=1767225600
MAP={
"0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2":"ETHUSDT",
"0x514910771af9ca656af840dff83e8264ecf986ca":"LINKUSDT",
"0x1f9840a85d5af5bf1d1762f925bdaddc4201f984":"UNIUSDT",
"0xc00e94cb662c3520282e6f5717214004a7f26888":"COMPUSDT"}

def sha(b):return hashlib.sha256(b).hexdigest()
def iv(v):
 s=str(v or "0");return int(s,16) if s.startswith("0x") else int(s)
def ad(v):
 s=str(v or "").lower();return "0x"+s[-40:] if len(s)>=40 else None
def words(d):
 s=str(d or "");s=s[2:] if s.startswith("0x") else s
 return [int(s[i:i+64],16) for i in range(0,len(s),64)]
def fetch(u):
 q=Request(u,headers={"User-Agent":"CryptoLab-Compound30m-BoundaryAudit-V0.1","Accept":"application/json"})
 with urlopen(q,timeout=120) as r:b=r.read()
 return json.loads(b.decode()),sha(b)
def btime(ts,closest):
 o,h=fetch(f"{BASE}/api?module=block&action=getblocknobytime&timestamp={ts}&closest={closest}");r=o.get("result")
 if isinstance(r,dict):
  for k in ("blockNumber","block_number","block"):
   if r.get(k) is not None:return iv(r[k]),h
 return iv(r),h
def logs(a,b):
 out=[];seen=set();pages=[]
 while a<=b:
  z=min(b,a+1_999_999)
  o,h=fetch(f"{BASE}/api/?module=logs&action=getLogs&fromBlock={a}&toBlock={z}&address={COMET}&topic0={BUY}")
  xs=o.get("result")
  if not isinstance(xs,list) or len(xs)>=1000:raise RuntimeError(f"bad/truncated {a}-{z}")
  pages.append({"from":a,"to":z,"count":len(xs),"sha256":h})
  for x in xs:
   k=(str(x.get("blockNumber")),str(x.get("transactionHash")).lower(),str(x.get("logIndex")))
   if k not in seen:seen.add(k);out.append(x)
  a=z+1
 return out,pages

receipt={"program":"COMPOUND_REALIZED_DISPOSAL_30M_BOUNDARY_AUDIT_V0.1","lab_id":"COMPOUND-REALIZED-DISPOSAL-FLOW-001",
"generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
"firewall":{"source_only":True,"market_prices_opened":False,"protected_2026_market_outcomes_opened":False}}
try:
 b0,h0=btime(START,"after");b1,h1=btime(END,"before");raw,pages=logs(b0,b1)
 g=defaultdict(lambda:{"ts":None,"base":0,"coll":0,"proxy":None,"asset":None})
 raw_n=0
 for x in raw:
  t=x.get("topics") or [];asset=ad(t[2]) if len(t)>=3 else None
  if asset not in MAP:continue
  raw_n+=1;w=words(x.get("data"));tx=str(x.get("transactionHash")).lower()
  k=(asset,tx);v=g[k];v["ts"]=iv(x.get("timeStamp"));v["base"]+=w[0];v["coll"]+=w[1];v["proxy"]=MAP[asset];v["asset"]=asset
 ev=[{"asset":a,"tx":tx,**v} for (a,tx),v in g.items()]
 ev.sort(key=lambda e:(e["asset"],e["ts"],e["tx"]))
 kept=[];supp=[];last_exit={}
 for e in ev:
  cut=last_exit.get(e["asset"])
  if cut is not None and e["ts"]<cut:supp.append(e);continue
  kept.append(e);last_exit[e["asset"]]=e["ts"]+1800
 boundary=[e for e in kept if e["ts"]+1800>=Y2026]
 final=[e for e in kept if e["ts"]+1800<Y2026]
 weeks=Counter();by=Counter()
 for e in final:
  dt=datetime.fromtimestamp(e["ts"],timezone.utc);iso=dt.isocalendar();weeks[f"{iso.year}-W{iso.week:02d}"]+=1;by[e["proxy"]]+=1
 fingerprint_match=(raw_n==1157 and len(ev)==1148 and len(kept)==373 and len(weeks)==35 and
                    dict(by)=={"COMPUSDT":35,"ETHUSDT":167,"LINKUSDT":93,"UNIUSDT":78})
 status="BOUNDARY_AUDIT_PASS" if fingerprint_match and len(boundary)==0 else ("BOUNDARY_AUDIT_PASS_WITH_EXCLUSIONS" if len(final)>=100 and len(weeks)>=20 and all(by[x]>=10 for x in MAP.values()) else "BOUNDARY_AUDIT_FAIL")
 receipt.update({"status":status,"window":{"start_block":b0,"end_block":b1,"start_lookup_sha256":h0,"end_lookup_sha256":h1},
 "source_pages":pages,"counts":{"eligible_raw_logs":raw_n,"aggregated_tx_asset_events":len(ev),"kept_pre_boundary":len(kept),
 "overlap_suppressed":len(supp),"protected_boundary_exclusions":len(boundary),"final_eligible":len(final),"unique_iso_weeks":len(weeks),
 "final_by_proxy":dict(sorted(by.items()))},
 "preoutcome_readiness_fingerprint_exact_match":fingerprint_match,
 "boundary_events":[{"asset":e["asset"],"proxy":e["proxy"],"tx":e["tx"],"timestamp":e["ts"]} for e in boundary]})
except Exception as e:receipt.update({"status":"TECHNICAL_FAILURE","error":repr(e)})
pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode();receipt["receipt_sha256_pre_self_field"]=sha(pre)
p=os.path.join(OUTDIR,"COMPOUND_REALIZED_DISPOSAL_FLOW_001_30M_BOUNDARY_AUDIT_RECEIPT_V0.1.json")
with open(p,"w") as f:json.dump(receipt,f,sort_keys=True,indent=2);f.write("\n")
print(json.dumps({k:v for k,v in receipt.items() if k not in ("source_pages","boundary_events")},sort_keys=True,indent=2))
print("receipt="+p)
