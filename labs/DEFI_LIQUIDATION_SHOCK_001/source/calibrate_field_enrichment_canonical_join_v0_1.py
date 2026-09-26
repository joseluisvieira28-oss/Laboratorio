#!/usr/bin/env python3
import datetime as dt, json, time, urllib.request, urllib.error
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
TSROOT="https://portal.sqd.dev/datasets/solana-mainnet/timestamps"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/FIELD_ENRICHMENT_CANONICAL_JOIN_CALIBRATION_RECEIPT_V0.1.json")
CASES=[
 {"family":"kamino_save11","label":"kamino","start":"2023-11-17T14:48:24Z","end":"2023-11-18T00:00:00Z",
  "program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
  "classes":{"kamino":"b1479abce2854a37"}},
 {"family":"marginfi_save0c","label":"marginfi","start":"2023-02-13T00:00:00Z","end":"2023-02-14T00:00:00Z",
  "program":"MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA",
  "classes":{"marginfi":"d6a997d5fba756db"}},
 {"family":"drift","label":"drift","start":"2022-11-07T00:00:00Z","end":"2022-11-08T00:00:00Z",
  "program":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH",
  "classes":{"liquidate_perp":"4b2377f7bf128b02","liquidate_spot":"6b00802923e5fb12",
             "liquidate_borrow_for_perp_pnl":"a911205acf94d11b",
             "liquidate_perp_pnl_for_deposit":"ed4bc6ebe9ba4b23"}}
]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}
def b58(s):
    n=0
    for c in s:
        if c not in MAP: raise ValueError("base58")
        n=n*58+MAP[c]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\0"*(len(s)-len(s.lstrip("1")))+raw
def iso(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def norm(v):
    if isinstance(v,str): return v
    if isinstance(v,(int,float)): return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None
def req(url,body=None,retries=10):
    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    headers={"Accept":"application/x-ndjson,application/json","User-Agent":"crypto-lab-field-join-cal/0.1"}
    if data is not None: headers["Content-Type"]="application/json"
    rq=urllib.request.Request(url,data=data,headers=headers,method="GET" if data is None else "POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(rq,timeout=120) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:last={"http":e.code};time.sleep(min(45,2**i));continue
            return int(e.code),raw
        except Exception as e:last={"error":type(e).__name__};time.sleep(min(45,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")
def slot_for(ts):
    st,raw=req(f"{TSROOT}/{int(iso(ts).timestamp())}/block")
    if st!=200: raise RuntimeError(f"resolver_{st}")
    o=json.loads(raw)
    if isinstance(o,int):return o
    for k in ("block","block_number","number","slot"):
        if isinstance(o.get(k),int):return o[k]
    raise RuntimeError("resolver_schema")
def collect(c,with_accounts):
    lo,hi=iso(c["start"]),iso(c["end"]); lo_u,hi_u=int(lo.timestamp()),int(hi.timestamp())
    current=slot_for(c["start"]); to=slot_for(c["end"])+16
    successful={}; anomalies=[]; requests=0
    while current<=to:
        ixfields={"programId":True,"data":True,"transactionIndex":True,"instructionAddress":True,"isCommitted":True,"error":True}
        if with_accounts: ixfields["accounts"]=True
        body={"type":"solana","fromBlock":current,"toBlock":to,
              "fields":{"block":{"number":True,"timestamp":True},
                        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
                        "instruction":ixfields},
              "instructions":[{"programId":[c["program"]],"transaction":True}]}
        st,raw=req(STREAM,body);requests+=1
        if st==204: break
        if st!=200: raise RuntimeError(f"stream_{st}")
        lines=[x for x in raw.decode("utf-8","replace").splitlines() if x.strip()]
        if not lines: break
        last=None
        for line in lines:
            b=json.loads(line); h=b.get("header") or {}; slot=h.get("number"); ts=norm(h.get("timestamp"))
            if isinstance(slot,int):last=slot if last is None else max(last,slot)
            if ts is None or not (lo_u<=int(iso(ts).timestamp())<hi_u):continue
            txs={}
            for pos,tx in enumerate(b.get("transactions") or []):
                txs[tx.get("transactionIndex",tx.get("index",pos))]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=c["program"]:continue
                try:d=b58(ix.get("data") or "")
                except Exception:continue
                cls=None
                for name,pref in c["classes"].items():
                    if d.startswith(bytes.fromhex(pref)):cls=name;break
                if cls is None:continue
                tx=txs.get(ix.get("transactionIndex"))
                if not isinstance(tx,dict):
                    anomalies.append({"reason":"missing_parent_tx","slot":slot});continue
                sigs=tx.get("signatures") or [];sig=sigs[0] if sigs and isinstance(sigs[0],str) else None
                addr=ix.get("instructionAddress")
                if not sig or not isinstance(addr,list):
                    anomalies.append({"reason":"bad_identity","slot":slot});continue
                if tx.get("err") is None and ix.get("isCommitted") is True and ix.get("error") is None:
                    key=cls+"|"+sig+"|"+json.dumps(addr,separators=(",",":"))
                    successful[key]={"class":cls,"signature":sig,"instructionAddress":addr,
                                     "accounts":ix.get("accounts") if with_accounts else None}
        if last is None: raise RuntimeError("non_advancing_no_slot")
        if last<current: raise RuntimeError("non_advancing")
        current=last+1
    return successful,anomalies,requests

results=[];all_pass=True
for c in CASES:
    base,ba,br=collect(c,False); enr,ea,er=collect(c,True)
    bk=set(base);ek=set(enr)
    missing=sorted(bk-ek);extra=sorted(ek-bk)
    empty=[k for k,v in enr.items() if not v.get("accounts")]
    ok=bool(bk) and not ba and not ea and not missing and not extra and not empty
    all_pass=all_pass and ok
    results.append({"family":c["family"],"start":c["start"],"end":c["end"],
                    "baseline_success_count":len(bk),"enriched_success_count":len(ek),
                    "missing_count":len(missing),"extra_count":len(extra),
                    "baseline_anomaly_count":len(ba),"enriched_anomaly_count":len(ea),
                    "empty_accounts_count":len(empty),"baseline_requests":br,"enriched_requests":er,
                    "pass":ok})
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"FIELD_ENRICHMENT_CANONICAL_JOIN_3_OF_3_FAMILY_PASS" if all_pass else "FIELD_ENRICHMENT_CANONICAL_JOIN_CALIBRATION_FAIL_CLOSED",
 "results":results,
 "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
             "balances":False,"token_amounts":False,"token_decimals":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
             "post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if not all_pass: raise SystemExit(2)
