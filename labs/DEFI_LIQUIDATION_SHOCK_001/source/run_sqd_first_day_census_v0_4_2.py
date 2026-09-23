#!/usr/bin/env python3
import json,time,urllib.request,urllib.error,datetime as dt,hashlib
from pathlib import Path

ENDPOINT="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSBASE="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_SQD_FIRST_DAY_CENSUS_RECEIPT_V0.4.2.json")
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}
def b58(s):
 n=0
 for c in s:
  if c not in MAP: raise ValueError("base58")
  n=n*58+MAP[c]
 raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+raw
def unix(s): return int(dt.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def iso(v):
 if isinstance(v,str): return v
 return dt.datetime.fromtimestamp(int(v),dt.timezone.utc).isoformat().replace("+00:00","Z")
def get_seed(ts):
 url=f"{TSBASE}/{ts}/block"; last=None
 for i in range(10):
  try:
   req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"crypto-lab-dls-census/0.4.2"})
   with urllib.request.urlopen(req,timeout=30) as resp:
    o=json.loads(resp.read()); b=o.get("block_number")
    if not isinstance(b,int): raise RuntimeError(f"bad block_number {o}")
    return b
  except urllib.error.HTTPError as e:
   body=e.read(500).decode("utf-8","replace"); last=(e.code,body)
   if e.code in (429,529) or 500<=e.code<600: time.sleep(min(60,2**i)); continue
   raise
  except Exception as e:
   last=repr(e); time.sleep(min(60,2**i))
 raise RuntimeError(f"timestamp_seed_exhausted:{last}")
def post(body):
 raw=json.dumps(body,separators=(",",":")).encode(); last=None
 for i in range(10):
  try:
   req=urllib.request.Request(ENDPOINT,data=raw,method="POST",headers={"Content-Type":"application/json","Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-dls-census/0.4.2"})
   with urllib.request.urlopen(req,timeout=90) as resp: return int(resp.status),dict(resp.headers),resp.read().decode("utf-8","replace")
  except urllib.error.HTTPError as e:
   txt=e.read().decode("utf-8","replace"); last=(e.code,txt[:500])
   if e.code in (429,529) or 500<=e.code<600: time.sleep(min(60,2**i)); continue
   return e.code,dict(e.headers),txt
  except Exception as e: last=repr(e); time.sleep(min(60,2**i))
 raise RuntimeError(f"stream_exhausted:{last}")

cfgs=[
 {"name":"kamino","program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","prefix":"b1479abce2854a37",
  "start":"2023-11-17T14:48:24Z","end":"2023-11-18T00:00:00Z","start_slot":230572965,
  "known":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv","server_filter":True},
 {"name":"save11","program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"11",
  "start":"2024-07-19T19:30:52Z","end":"2024-07-20T00:00:00Z","start_slot":278496102,
  "known":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L","server_filter":False}
]
results=[]
for c in cfgs:
 t0,t1=unix(c["start"]),unix(c["end"]); s0=get_seed(t0); s1=get_seed(t1)
 current=s0; endslot=s1+16; blocks=[]; requests=0; statuses=[]; sources=[]
 while current<=endslot:
  filt={"programId":[c["program"]],"transaction":True}
  if c["server_filter"]: filt["d8"]=["0x"+c["prefix"]]
  body={"type":"solana","fromBlock":current,"toBlock":endslot,
   "fields":{"block":{"number":True,"timestamp":True},"transaction":{"transactionIndex":True,"signatures":True,"err":True},
             "instruction":{"programId":True,"data":True,"transactionIndex":True,"instructionAddress":True,"isCommitted":True,"error":True}},
   "instructions":[filt]}
  st,h,txt=post(body); requests+=1; statuses.append(st); sources.append(h.get("x-sqd-data-source"))
  if st==204: break
  if st!=200: raise RuntimeError(f"{c['name']} http {st} {txt[:500]}")
  batch=[json.loads(x) for x in txt.splitlines() if x.strip()]
  if not batch: raise RuntimeError(f"{c['name']} empty200")
  blocks.extend(batch)
  nums=[(b.get("header") or {}).get("number") for b in batch]; nums=[x for x in nums if isinstance(x,int)]
  if not nums: raise RuntimeError(f"{c['name']} no block number")
  last=max(nums)
  if last<current: raise RuntimeError(f"{c['name']} nonadvancing")
  current=last+1
 cand=[]; anomalies=[]
 for b in blocks:
  h=b.get("header") or {}; slot=h.get("number"); ts=h.get("timestamp")
  tsu=unix(ts) if isinstance(ts,str) else int(ts) if isinstance(ts,(int,float)) else None
  if tsu is None or not(t0<=tsu<t1) or slot<c["start_slot"]: continue
  txs=b.get("transactions") or []; txmap={}
  for pos,tx in enumerate(txs): txmap[tx.get("transactionIndex",tx.get("index",pos))]=tx
  for ix in b.get("instructions") or []:
   if ix.get("programId")!=c["program"]: continue
   try: dec=b58(ix.get("data")) if isinstance(ix.get("data"),str) else b""
   except Exception: dec=b""
   pref=bytes.fromhex(c["prefix"])
   if not dec.startswith(pref): continue
   ti=ix.get("transactionIndex"); tx=txmap.get(ti); addr=ix.get("instructionAddress")
   if not isinstance(tx,dict) or not (tx.get("signatures") or []) or not isinstance(addr,list) or not addr:
    anomalies.append({"slot":slot,"reason":"linkage_or_path_missing"}); continue
   terr=tx.get("err"); committed=ix.get("isCommitted"); ierr=ix.get("error")
   success=(terr is None and committed is True and ierr is None)
   failed=(terr is not None or committed is False or ierr is not None)
   if success: cls="SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_RAW_SAMPLE_RECONCILIATION"
   elif failed: cls="LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED"
   else:
    anomalies.append({"slot":slot,"signature":tx["signatures"][0],"reason":"execution_state_inconsistent"}); continue
   cand.append({"protocol":c["name"],"slot":slot,"timestamp":iso(tsu),"signature":tx["signatures"][0],
                "instructionAddress":addr,"classification":cls,"transactionErr":terr,"instructionError":ierr,
                "isCommitted":committed,"decoded_prefix_hex":dec[:len(pref)].hex()})
 keys=[x["protocol"]+":"+x["signature"]+":"+json.dumps(x["instructionAddress"],separators=(",",":")) for x in cand]
 if len(keys)!=len(set(keys)): anomalies.append({"reason":"duplicate_instruction_key"})
 known=any(x["signature"]==c["known"] and x["classification"].startswith("SUCCESSFUL") for x in cand)
 results.append({"name":c["name"],"start":c["start"],"end":c["end"],"seed_start":s0,"seed_end":s1,
                 "request_count":requests,"http_statuses":statuses,"source_headers":sources,
                 "candidate_count":len(cand),"successful_count":sum(x["classification"].startswith("SUCCESSFUL") for x in cand),
                 "failed_attempt_count":sum(x["classification"].startswith("LIQUIDATION_ATTEMPT") for x in cand),
                 "known_first_success_recovered":known,"anomalies":anomalies,"candidates":cand})
ok=all(r["known_first_success_recovered"] and not r["anomalies"] for r in results)
rec={"schema_version":"0.4.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
     "classification":"SQD_FIRST_DAY_CENSUS_PASS" if ok else "SOURCE_ANOMALY_FAIL_CLOSED",
     "results":results,
     "firewall":{"prices":False,"balances":False,"token_balances":False,"amounts":False,"returns":False,"pnl":False,
      "direction":False,"economic_outcomes":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,
      "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}}
OUT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":rec["classification"],"results":[{k:v for k,v in r.items() if k!="candidates"} for r in results]},indent=2))
if not ok: raise SystemExit(2)
