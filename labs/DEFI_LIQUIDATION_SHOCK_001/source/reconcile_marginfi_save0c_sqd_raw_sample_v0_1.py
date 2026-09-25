#!/usr/bin/env python3
import datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
QUEUE=BASE/"MARGINFI_SAVE0C_RAW_SAMPLE_QUEUE_V0.1.json"
OUT=BASE/"MARGINFI_SAVE0C_RAW_SAMPLE_RECONCILIATION_RECEIPT_V0.1.json"
CFG={
 "marginfi":("MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA","d6a997d5fba756db"),
 "save0c":("So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","0c")
}
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}
def b58(s):
    n=0
    for c in s:
        if c not in MAP: raise ValueError("base58")
        n=n*58+MAP[c]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\0"*(len(s)-len(s.lstrip("1")))+raw
def iso(v): return dt.datetime.fromtimestamp(int(v),dt.timezone.utc).isoformat().replace("+00:00","Z")
def rpc(sig):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":0}]},separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-ms-raw/0.1"})
    last=None
    for i in range(10):
        try:
            with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last={"http":e.code,"body":e.read(300).decode("utf-8","replace")}
            if e.code in (429,500,502,503,504):time.sleep(min(45,2*(i+1)));continue
            raise
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]};time.sleep(min(45,2*(i+1)))
    raise RuntimeError(f"rpc_exhausted:{last}")
def iter_ix(res):
    msg=((res.get("transaction") or {}).get("message") or {})
    for i,ix in enumerate(msg.get("instructions") or []):yield [i],ix
    for g in (res.get("meta") or {}).get("innerInstructions") or []:
        outer=g.get("index")
        for j,ix in enumerate(g.get("instructions") or []):yield [outer,j],ix

q=json.loads(QUEUE.read_text());results=[];ok=True
for protocol,item in (q.get("protocols") or {}).items():
    program,phex=CFG[protocol];pref=bytes.fromhex(phex)
    for ent in item.get("entries",[]):
        sig=ent["signature"];obj=rpc(sig);res=obj.get("result")
        rec={"protocol":protocol,"signature":sig,"expected_slot":ent.get("slot"),
             "expected_timestamp":ent.get("timestamp"),"expected_path_classes":ent.get("expected_path_classes")}
        if not isinstance(res,dict):
            rec.update(pass_=False,reason="null_transaction");ok=False;results.append(rec);continue
        meta=res.get("meta") or {}
        if meta.get("err") is not None:
            rec.update(pass_=False,reason="raw_not_success",meta_err=meta.get("err"));ok=False;results.append(rec);continue
        slot=res.get("slot");bt=res.get("blockTime");timestamp=iso(bt) if bt is not None else None
        matches=[]
        for addr,ix in iter_ix(res):
            if ix.get("programId")!=program:continue
            try:dec=b58(ix.get("data",""))
            except Exception:continue
            if dec.startswith(pref):
                matches.append({"instructionAddress":addr,"location":"inner" if len(addr)>1 else "outer",
                                "data_prefix_hex":dec[:len(pref)].hex()})
        got=sorted(set(m["location"] for m in matches))
        passed=(slot==ent.get("slot") and timestamp==ent.get("timestamp") and bool(matches)
                and set(ent.get("expected_path_classes") or []).issubset(set(got)))
        if not passed:ok=False
        rec.update(pass_=passed,slot=slot,timestamp=timestamp,matches=matches,observed_path_classes=got,
                   reason=None if passed else "raw_reconciliation_mismatch")
        results.append(rec);time.sleep(0.15)

receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
         "classification":"MARGINFI_SAVE0C_RAW_SAMPLE_RECONCILIATION_PASS" if ok else "MARGINFI_SAVE0C_RAW_SAMPLE_RECONCILIATION_FAIL_CLOSED",
         "sample_count":len(results),"pass_count":sum(1 for r in results if r.get("pass_")),"results":results,
         "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
         "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
         "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":receipt["classification"],"sample_count":receipt["sample_count"],"pass_count":receipt["pass_count"]},indent=2))
if not ok:raise SystemExit(2)
