#!/usr/bin/env python3
import datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
IN=BASE/"MARGINFI_SAVE0C_SQD_FIRST_SUCCESS_CANDIDATES_V0.1.json"
OUT=BASE/"MARGINFI_SAVE0C_SQD_FIRST_SUCCESS_RAW_RECEIPT_V0.1.json"
CFG={
 "marginfi":{"program":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA","prefix":"d6a997d5fba756db",
             "pass":"MARGINFI_FIRST_SUCCESS_BOUNDARY_SQD_PASS"},
 "save0c":{"program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo","prefix":"0c",
            "pass":"SAVE0C_FIRST_SUCCESS_BOUNDARY_SQD_PASS"}
}
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}
def b58(s):
    n=0
    for c in s:
        if c not in MAP: raise ValueError("base58")
        n=n*58+MAP[c]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\0"*(len(s)-len(s.lstrip("1")))+raw
def rpc(sig):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","commitment":"finalized","maxSupportedTransactionVersion":0}]},separators=(",",":")).encode()
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-first-success-raw/0.1"})
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
def ts(v): return dt.datetime.fromtimestamp(int(v),dt.timezone.utc).isoformat().replace("+00:00","Z")

src=json.loads(IN.read_text())
results={}; combined=True
for protocol,cfg in CFG.items():
    cand=((src.get("protocols") or {}).get(protocol) or {}).get("candidate")
    if not cand:
        results[protocol]={"classification":"RAW_NOT_RUN_NO_SQD_CANDIDATE"};combined=False;continue
    obj=rpc(cand["signature"]); res=obj.get("result")
    rec={"signature":cand["signature"],"expected_slot":cand.get("slot"),"expected_timestamp":cand.get("timestamp"),
         "expected_instructionAddress":cand.get("instructionAddress")}
    if not isinstance(res,dict):
        rec["classification"]="RAW_RECONCILIATION_FAIL_CLOSED";rec["reason"]="null_transaction";results[protocol]=rec;combined=False;continue
    meta=res.get("meta") or {}; slot=res.get("slot"); block_ts=ts(res.get("blockTime")) if res.get("blockTime") is not None else None
    pref=bytes.fromhex(cfg["prefix"]); matches=[]
    for addr,ix in iter_ix(res):
        if ix.get("programId")!=cfg["program"]:continue
        try:dec=b58(ix.get("data",""))
        except Exception:continue
        if dec.startswith(pref):matches.append({"instructionAddress":addr,"prefix":dec[:len(pref)].hex()})
    exp_addr=cand.get("instructionAddress") or []
    exp_class="inner" if len(exp_addr)>1 else "outer"
    got_classes={"inner" if len(m["instructionAddress"])>1 else "outer" for m in matches}
    passed=(meta.get("err") is None and slot==cand.get("slot") and block_ts==cand.get("timestamp") and bool(matches) and exp_class in got_classes)
    rec.update({"classification":cfg["pass"] if passed else "RAW_RECONCILIATION_FAIL_CLOSED",
                "slot":slot,"timestamp":block_ts,"meta_err":meta.get("err"),"matches":matches,
                "path_class_expected":exp_class,"path_classes_observed":sorted(got_classes)})
    if not passed:combined=False
    results[protocol]=rec;time.sleep(0.2)
out={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
     "classification":"MARGINFI_SAVE0C_SQD_FIRST_SUCCESS_SOURCE_PASS" if combined else "MARGINFI_SAVE0C_SQD_FIRST_SUCCESS_SOURCE_NOT_PASS",
     "protocols":results,
     "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
     "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
     "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))
if not combined:raise SystemExit(2)
