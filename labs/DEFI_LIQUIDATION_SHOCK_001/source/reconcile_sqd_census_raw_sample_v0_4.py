#!/usr/bin/env python3
import hashlib,json,time,urllib.request,urllib.error
from pathlib import Path
RPC="https://api.mainnet-beta.solana.com"
QUEUE=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_RAW_SAMPLE_QUEUE_V0.4.json")
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_RAW_SAMPLE_RECONCILIATION_RECEIPT_V0.4.json")
CFG={
 "kamino":("KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD","b1479abce2854a37"),
 "save11":("So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","11")
}
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}
def b58(s):
 n=0
 for c in s:
  if c not in MAP: raise ValueError("base58")
  n=n*58+MAP[c]
 raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\x00"*(len(s)-len(s.lstrip("1")))+raw
def rpc(sig):
 body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":0}]},separators=(",",":")).encode()
 req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-raw-sample/0.4"})
 last=None
 for i in range(10):
  try:
   with urllib.request.urlopen(req,timeout=60) as r: return r.read()
  except urllib.error.HTTPError as e:
   if e.code in (429,500,502,503,504): last=e.code; time.sleep(min(45,2*(i+1))); continue
   raise
  except Exception as e: last=repr(e); time.sleep(min(45,2*(i+1)))
 raise RuntimeError(f"rpc_exhausted:{last}")
def ixs(res):
 tx=res.get("transaction") or {}; msg=tx.get("message") or {}
 for ix in msg.get("instructions") or []: yield "outer",ix
 for g in (res.get("meta") or {}).get("innerInstructions") or []:
  for ix in g.get("instructions") or []: yield "inner",ix
q=json.loads(QUEUE.read_text()); results=[]; ok=True
for protocol,item in q.items():
 program,phex=CFG[protocol]; pref=bytes.fromhex(phex)
 for sig in item["selected_signatures"]:
  raw=rpc(sig); obj=json.loads(raw); res=obj.get("result")
  rec={"protocol":protocol,"signature":sig,"raw_sha256":hashlib.sha256(raw).hexdigest()}
  if not isinstance(res,dict):
   rec.update(pass_=False,reason="null_transaction"); ok=False; results.append(rec); continue
  meta=res.get("meta")
  if not isinstance(meta,dict) or meta.get("err") is not None:
   rec.update(pass_=False,reason="raw_not_success"); ok=False; results.append(rec); continue
  matches=[]
  for loc,ix in ixs(res):
   if ix.get("programId")!=program: continue
   try: dec=b58(ix.get("data",""))
   except: continue
   if dec.startswith(pref): matches.append({"location":loc,"data_prefix_hex":dec[:len(pref)].hex()})
  passed=len(matches)>=1
  if not passed: ok=False
  rec.update(pass_=passed,slot=res.get("slot"),blockTime=res.get("blockTime"),matches=matches,match_count=len(matches),
             reason=None if passed else "exact_instruction_not_found")
  results.append(rec); time.sleep(0.15)
receipt={"schema_version":"0.4","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"RAW_SAMPLE_RECONCILIATION_PASS" if ok else "RAW_SAMPLE_RECONCILIATION_FAIL_CLOSED",
 "sample_count":len(results),"pass_count":sum(1 for r in results if r.get("pass_")),
 "results":results,
 "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
 "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
 "exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":receipt["classification"],"sample_count":len(results),"pass_count":receipt["pass_count"]},indent=2))
if not ok: raise SystemExit(2)
