#!/usr/bin/env python3
import datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
PREFIX="a911205acf94d11b"
EXPECTED={
  "signature":"5kYZPtPTFhvdBZfaFMPXtWh2A9tQYHt8bbzKJazopc7pWWmpwdcn1DeT4yLjxaidn387VMK6g6rYX4KMMh7NPka6",
  "slot":195239739,
  "timestamp":"2023-05-22T00:48:06Z",
  "instructionAddress":[1],
}
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_FOURTH_CLASS_FIRST_CANDIDATE_RAW_RECEIPT_V0.1.json")
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
    req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-drift-fourth-raw/0.1"})
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
    for i,ix in enumerate(msg.get("instructions") or []): yield [i],ix
    for g in (res.get("meta") or {}).get("innerInstructions") or []:
        outer=g.get("index")
        for j,ix in enumerate(g.get("instructions") or []): yield [outer,j],ix

obj=rpc(EXPECTED["signature"]); res=obj.get("result")
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","class":"liquidate_borrow_for_perp_pnl",
         "expected":EXPECTED,"classification":"DRIFT_FOURTH_CLASS_FIRST_CANDIDATE_RAW_FAIL_CLOSED",
         "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
         "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
         "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
if isinstance(res,dict):
    meta=res.get("meta") or {}; slot=res.get("slot"); bt=res.get("blockTime")
    timestamp=dt.datetime.fromtimestamp(int(bt),dt.timezone.utc).isoformat().replace("+00:00","Z") if bt is not None else None
    matches=[]
    for addr,ix in iter_ix(res):
        if ix.get("programId")!=PROGRAM: continue
        try: dec=b58(ix.get("data",""))
        except Exception: continue
        if dec.startswith(bytes.fromhex(PREFIX)):
            matches.append({"instructionAddress":addr,"path_class":"inner" if len(addr)>1 else "outer","decoded_prefix_hex":dec[:8].hex()})
    exp_class="inner" if len(EXPECTED["instructionAddress"])>1 else "outer"
    passed=(meta.get("err") is None and slot==EXPECTED["slot"] and timestamp==EXPECTED["timestamp"]
            and any(m["instructionAddress"]==EXPECTED["instructionAddress"] for m in matches)
            and any(m["path_class"]==exp_class for m in matches))
    receipt.update({"slot":slot,"timestamp":timestamp,"meta_err":meta.get("err"),"matches":matches,
                    "classification":"DRIFT_FOURTH_CLASS_FIRST_CANDIDATE_RAW_PASS" if passed else "DRIFT_FOURTH_CLASS_FIRST_CANDIDATE_RAW_FAIL_CLOSED"})
else:
    receipt["reason"]="null_transaction"
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if receipt["classification"]!="DRIFT_FOURTH_CLASS_FIRST_CANDIDATE_RAW_PASS": raise SystemExit(2)
