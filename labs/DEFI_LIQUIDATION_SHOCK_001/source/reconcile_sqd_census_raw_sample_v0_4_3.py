#!/usr/bin/env python3
import datetime as dt, hashlib, json, time, urllib.request, urllib.error
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
QUEUE=BASE/"KAMINO_SAVE11_RAW_SAMPLE_QUEUE_V0.4.3.json"
OUT=BASE/"KAMINO_SAVE11_RAW_SAMPLE_RECONCILIATION_RECEIPT_V0.4.3.json"
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
 return b"\0"*(len(s)-len(s.lstrip("1")))+raw
def iso(v):
 return dt.datetime.fromtimestamp(int(v),dt.timezone.utc).isoformat().replace("+00:00","Z")
def rpc(sig):
 body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":0}]},separators=(",",":")).encode()
 req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-raw-sample/0.4.3"})
 last=None
 for i in range(10):
  try:
   with urllib.request.urlopen(req,timeout=60) as r: return r.read()
  except urllib.error.HTTPError as e:
   body=e.read(500).decode("utf-8","replace"); last={"http":e.code,"body":body}
   if e.code in (429,500,502,503,504): time.sleep(min(45,2*(i+1))); continue
   raise
  except Exception as e:
   last={"error":type(e).__name__,"detail":str(e)[:300]}; time.sleep(min(45,2*(i+1)))
 raise RuntimeError(f"rpc_exhausted:{last}")
def ixs(res):
 tx=res.get("transaction") or {}; msg=tx.get("message") or {}
 for ix in msg.get("instructions") or []: yield "outer",ix
 for g in (res.get("meta") or {}).get("innerInstructions") or []:
  for ix in g.get("instructions") or []: yield "inner",ix

q=json.loads(QUEUE.read_text()); results=[]; ok=True
for protocol,item in q.items():
 program,phex=CFG[protocol]; pref=bytes.fromhex(phex)
 for ent in item.get("entries",[]):
  sig=ent["signature"]; raw=rpc(sig); obj=json.loads(raw); res=obj.get("result")
  rec={"protocol":protocol,"signature":sig,"expected_slot":ent.get("slot"),
       "expected_timestamp":ent.get("timestamp"),"expected_path_classes":ent.get("expected_path_classes"),
       "raw_sha256":hashlib.sha256(raw).hexdigest()}
  if not isinstance(res,dict):
   rec.update(pass_=False,reason="null_transaction"); ok=False; results.append(rec); continue
  meta=res.get("meta")
  if not isinstance(meta,dict) or meta.get("err") is not None:
   rec.update(pass_=False,reason="raw_not_success"); ok=False; results.append(rec); continue
  slot=res.get("slot"); bt=res.get("blockTime"); ts=iso(bt) if bt is not None else None
  matches=[]
  for loc,ix in ixs(res):
   if ix.get("programId")!=program: continue
   try: dec=b58(ix.get("data",""))
   except Exception: continue
   if dec.startswith(pref):
    matches.append({"location":loc,"data_prefix_hex":dec[:len(pref)].hex()})
  got_classes=sorted(set(m["location"] for m in matches))
  slot_ok=(slot==ent.get("slot"))
  time_ok=(ts==ent.get("timestamp"))
  path_ok=set(ent.get("expected_path_classes") or []).issubset(set(got_classes))
  ix_ok=bool(matches)
  passed=slot_ok and time_ok and path_ok and ix_ok
  if not passed: ok=False
  rec.update(pass_=passed,slot=slot,blockTime=bt,timestamp=ts,matches=matches,
             observed_path_classes=got_classes,slot_ok=slot_ok,time_ok=time_ok,path_ok=path_ok,
             exact_instruction_found=ix_ok,
             reason=None if passed else "raw_reconciliation_mismatch")
  results.append(rec); time.sleep(0.15)

receipt={"schema_version":"0.4.3","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"RAW_SAMPLE_RECONCILIATION_PASS" if ok else "RAW_SAMPLE_RECONCILIATION_FAIL_CLOSED",
 "sample_count":len(results),"pass_count":sum(1 for r in results if r.get("pass_")),
 "results":results,
 "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
 "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
 "exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":receipt["classification"],"sample_count":len(results),"pass_count":receipt["pass_count"]},indent=2))
if not ok: raise SystemExit(2)
