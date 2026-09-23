#!/usr/bin/env python3
import json, time, urllib.request, urllib.error
from pathlib import Path

ENDPOINT="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_SQD_BOUNDARY_CALIBRATION_RECEIPT_V0.3.json")

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}
def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid base58")
        n=n*58+MAP[ch]
    h=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    pad=len(s)-len(s.lstrip("1"))
    return b"\x00"*pad+h

controls=[
 {
  "name":"kamino",
  "program":"KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
  "filter_key":"d8","filter_value":"0xb1479abce2854a37",
  "prefix_hex":"b1479abce2854a37",
  "from":230572957,"to":230572973,
  "expected_slot":230572965,
  "expected_sig":"2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv",
  "expected_time":"2023-11-17T14:48:24Z"
 },
 {
  "name":"save11",
  "program":"So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",
  "filter_key":"d1","filter_value":"0x11",
  "prefix_hex":"11",
  "from":278496094,"to":278496110,
  "expected_slot":278496102,
  "expected_sig":"WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L",
  "expected_time":"2024-07-19T19:30:52Z"
 }
]

def post(body, retries=6):
    raw=json.dumps(body,separators=(",",":")).encode()
    req=urllib.request.Request(ENDPOINT,data=raw,headers={
      "Content-Type":"application/json",
      "Accept":"application/x-ndjson,application/json",
      "User-Agent":"crypto-lab-dls-source-calibration/0.3"
    },method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=60) as resp:
                txt=resp.read().decode("utf-8","replace")
                return int(resp.status), dict(resp.headers), txt
        except urllib.error.HTTPError as e:
            body=e.read().decode("utf-8","replace")
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code,"body":body[:1000]}
                time.sleep(min(30,2**i)); continue
            return int(e.code), dict(e.headers), body
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:500]}
            time.sleep(min(30,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

def norm_time(v):
    if isinstance(v,str):
        return v
    if isinstance(v,(int,float)):
        import datetime as dt
        return dt.datetime.fromtimestamp(v,dt.timezone.utc).isoformat().replace("+00:00","Z")
    return None

def collect(c):
    current=c["from"]
    all_blocks=[]
    request_count=0
    statuses=[]
    source_headers=[]
    while current<=c["to"]:
        filt={
          "programId":[c["program"]],
          c["filter_key"]:[c["filter_value"]],
          "transaction":True
        }
        body={
          "type":"solana",
          "fromBlock":current,
          "toBlock":c["to"],
          "fields":{
            "block":{"number":True,"timestamp":True},
            "transaction":{"transactionIndex":True,"signatures":True,"err":True},
            "instruction":{
              "programId":True,"data":True,"transactionIndex":True,
              "instructionAddress":True,"isCommitted":True,"error":True
            }
          },
          "instructions":[filt]
        }
        st,h,txt=post(body)
        request_count+=1
        statuses.append(st)
        source_headers.append(h.get("x-sqd-data-source"))
        if st==204:
            break
        if st!=200:
            return {
              "name":c["name"],"transport_ok":False,"http_statuses":statuses,
              "http_body":txt[:2000],"request_count":request_count,
              "source_headers":source_headers
            }
        lines=[x for x in txt.splitlines() if x.strip()]
        if not lines:
            # Empty successful response cannot prove completion; fail closed.
            return {
              "name":c["name"],"transport_ok":False,"reason":"empty_200_response",
              "http_statuses":statuses,"request_count":request_count,
              "source_headers":source_headers
            }
        batch=[]
        for line in lines:
            try: batch.append(json.loads(line))
            except Exception as e:
                return {
                  "name":c["name"],"transport_ok":False,
                  "reason":"ndjson_parse_error","detail":str(e),
                  "sample":line[:500]
                }
        all_blocks.extend(batch)
        last=None
        for b in batch:
            hdr=b.get("header") or {}
            num=hdr.get("number")
            if isinstance(num,int): last=num if last is None else max(last,num)
        if last is None:
            return {"name":c["name"],"transport_ok":False,"reason":"no_block_number"}
        if last<current:
            return {"name":c["name"],"transport_ok":False,"reason":"non_advancing_stream"}
        current=last+1

    candidates=[]
    for b in all_blocks:
        hdr=b.get("header") or {}
        slot=hdr.get("number")
        ts=norm_time(hdr.get("timestamp"))
        txs=b.get("transactions") or []
        tx_by_idx={}
        for pos,tx in enumerate(txs):
            idx=tx.get("transactionIndex",tx.get("index",pos))
            tx_by_idx[idx]=tx
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=c["program"]:
                continue
            data=ix.get("data")
            prefix_ok=False
            decoded_prefix=None
            try:
                dec=b58decode(data) if isinstance(data,str) else b""
                decoded_prefix=dec[:len(bytes.fromhex(c["prefix_hex"]))].hex()
                prefix_ok=dec.startswith(bytes.fromhex(c["prefix_hex"]))
            except Exception:
                pass
            ti=ix.get("transactionIndex")
            tx=tx_by_idx.get(ti,{})
            sigs=tx.get("signatures") or []
            candidates.append({
              "slot":slot,"timestamp":ts,"programId":ix.get("programId"),
              "data":data,"decoded_prefix_hex":decoded_prefix,"prefix_ok":prefix_ok,
              "transactionIndex":ti,"instructionAddress":ix.get("instructionAddress"),
              "isCommitted":ix.get("isCommitted"),"instructionError":ix.get("error"),
              "signatures":sigs,"transactionErr":tx.get("err")
            })

    match=[]
    for row in candidates:
        if row["slot"]==c["expected_slot"] and c["expected_sig"] in row["signatures"] and row["prefix_ok"]:
            match.append(row)

    checks={
      "expected_slot_found":any(x["slot"]==c["expected_slot"] for x in candidates),
      "expected_signature_found":any(c["expected_sig"] in x["signatures"] for x in candidates),
      "exact_linked_match_count":len(match),
      "program_exact":bool(match) and all(x["programId"]==c["program"] for x in match),
      "prefix_exact":bool(match) and all(x["prefix_ok"] for x in match),
      "transaction_err_null":bool(match) and all(x["transactionErr"] is None for x in match),
      "instruction_committed_true":bool(match) and all(x["isCommitted"] is True for x in match),
      "instruction_address_present":bool(match) and all(isinstance(x["instructionAddress"],list) and len(x["instructionAddress"])>0 for x in match)
    }
    passed=all([
      checks["expected_slot_found"],checks["expected_signature_found"],
      checks["exact_linked_match_count"]>=1,checks["program_exact"],checks["prefix_exact"],
      checks["transaction_err_null"],checks["instruction_committed_true"],
      checks["instruction_address_present"]
    ])
    return {
      "name":c["name"],"transport_ok":True,"passed":passed,
      "http_statuses":statuses,"request_count":request_count,
      "source_headers":source_headers,
      "expected":{"slot":c["expected_slot"],"signature":c["expected_sig"],"time":c["expected_time"]},
      "candidate_count":len(candidates),"checks":checks,
      "exact_matches":match,
      "all_candidates":candidates
    }

results=[]
for c in controls:
    print("CALIBRATE",c["name"],flush=True)
    try: results.append(collect(c))
    except Exception as e:
        results.append({"name":c["name"],"transport_ok":False,"reason":type(e).__name__,"detail":str(e)[:1000]})

pass_count=sum(1 for r in results if r.get("passed") is True)
transport_all=all(r.get("transport_ok") is True for r in results)
if pass_count==2:
    classification="SQD_BOUNDARY_CALIBRATION_PASS"
elif not transport_all:
    classification="SQD_BOUNDARY_CALIBRATION_BLOCKED"
elif pass_count==1:
    classification="SQD_BOUNDARY_CALIBRATION_PARTIAL"
else:
    classification="SOURCE_ANOMALY_FAIL_CLOSED"

receipt={
 "schema_version":"0.3","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,"endpoint":ENDPOINT,
 "controls":results,
 "firewall":{
  "prices":False,"token_balances":False,"balances":False,"amounts":False,
  "returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
  "protected_market_outcomes_2025_2026":False,"live_trading":False,
  "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
  "account_creation":False,"merge_main":False
 }
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({
 "classification":classification,
 "controls":[{"name":r.get("name"),"passed":r.get("passed"),"transport_ok":r.get("transport_ok"),
              "candidate_count":r.get("candidate_count"),"checks":r.get("checks"),"reason":r.get("reason")} for r in results]
},indent=2,sort_keys=True))
