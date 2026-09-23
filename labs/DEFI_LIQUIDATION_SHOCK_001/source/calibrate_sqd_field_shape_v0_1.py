#!/usr/bin/env python3
import json,time,urllib.request,urllib.error
from pathlib import Path

ENDPOINT="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_SQD_FIELD_SHAPE_CALIBRATION_RECEIPT_V0.1.json")
CONTROLS=[
 {"name":"kamino","program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
  "slot":230572965,"sig":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
  "prefix":"b1479abce2854a37","expected_account_counts":[16]},
 {"name":"save11","program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
  "slot":278496102,"sig":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
  "prefix":"11","expected_account_counts":[15]}
]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"; MAP={c:i for i,c in enumerate(ALPH)}
def b58decode(s):
    n=0
    for c in s:
        if c not in MAP: raise ValueError("bad base58")
        n=n*58+MAP[c]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def post(body):
    raw=json.dumps(body,separators=(",",":")).encode(); last=None
    for i in range(8):
        try:
            req=urllib.request.Request(ENDPOINT,data=raw,method="POST",headers={
             "Content-Type":"application/json","Accept":"application/x-ndjson,application/json",
             "User-Agent":"crypto-lab-dls-field-shape/0.1"})
            with urllib.request.urlopen(req,timeout=60) as resp:
                return int(resp.status),dict(resp.headers),resp.read().decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            txt=e.read().decode("utf-8","replace"); last={"http":e.code,"body":txt[:500]}
            if e.code in (429,529) or 500<=e.code<600:
                time.sleep(min(30,2**i)); continue
            return int(e.code),dict(e.headers),txt
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:400]}; time.sleep(min(30,2**i))
    raise RuntimeError(str(last))

rows=[]
for c in CONTROLS:
    body={
      "type":"solana","fromBlock":c["slot"],"toBlock":c["slot"],
      "fields":{
        "block":{"number":True,"timestamp":True},
        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
        "instruction":{"programId":True,"data":True,"accounts":True,"transactionIndex":True,
                       "instructionAddress":True,"isCommitted":True,"error":True}
      },
      "instructions":[{"programId":[c["program"]],"transaction":True}]
    }
    rec={"name":c["name"],"slot":c["slot"],"expected_signature":c["sig"]}
    try:
        st,h,txt=post(body); rec["http_status"]=st; rec["x_sqd_data_source"]=h.get("x-sqd-data-source")
        blocks=[json.loads(x) for x in txt.splitlines() if x.strip()] if st==200 else []
        matches=[]
        for b in blocks:
            txs=b.get("transactions") or []; txby={}
            for pos,tx in enumerate(txs):
                idx=tx.get("transactionIndex",tx.get("index",pos)); txby[idx]=tx
            for ix in b.get("instructions") or []:
                if ix.get("programId")!=c["program"]: continue
                try: dec=b58decode(ix.get("data") or "")
                except Exception: continue
                if not dec.startswith(bytes.fromhex(c["prefix"])): continue
                tx=txby.get(ix.get("transactionIndex"),{})
                if c["sig"] not in (tx.get("signatures") or []): continue
                matches.append({
                  "instructionAddress":ix.get("instructionAddress"),
                  "accounts":ix.get("accounts"),
                  "account_count":len(ix.get("accounts") or []) if isinstance(ix.get("accounts"),list) else None,
                  "data":ix.get("data"),"decoded_data_hex":dec.hex(),
                  "transactionErr":tx.get("err"),"isCommitted":ix.get("isCommitted"),"instructionError":ix.get("error")
                })
        rec["matches"]=matches
        rec["match_count"]=len(matches)
        rec["account_counts"]=[x.get("account_count") for x in matches]
        rec["shape_pass"]=bool(matches) and all(x.get("account_count") in c["expected_account_counts"] for x in matches)
        rec["success_semantics_pass"]=bool(matches) and all(x.get("transactionErr") is None and x.get("isCommitted") is True and x.get("instructionError") is None for x in matches)
    except Exception as e:
        rec.update(error=type(e).__name__,detail=str(e)[:1000],shape_pass=False,success_semantics_pass=False)
    rows.append(rec)

passed=all(r.get("http_status")==200 and r.get("shape_pass") and r.get("success_semantics_pass") for r in rows)
classification="SQD_FIELD_SHAPE_CALIBRATION_PASS" if passed else "SQD_FIELD_SHAPE_CALIBRATION_FAIL_CLOSED"
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "endpoint":ENDPOINT,"rows":rows,
 "firewall":{"prices":False,"balances":False,"token_balances":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="SQD_FIELD_SHAPE_CALIBRATION_PASS": raise SystemExit(2)
