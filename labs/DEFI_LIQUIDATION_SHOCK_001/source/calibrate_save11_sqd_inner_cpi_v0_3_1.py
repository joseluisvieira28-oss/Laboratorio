#!/usr/bin/env python3
import json, time, urllib.request, urllib.error, datetime as dt
from pathlib import Path

ENDPOINT="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE11_SQD_INNER_CPI_CALIBRATION_RECEIPT_V0.3.1.json")
PROGRAM="So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"
EXPECTED_SIG="WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L"
EXPECTED_SLOT=278496102
EXPECTED_TIME="2024-07-19T19:30:52Z"
FROM=278496094
TO=278496110

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAP={c:i for i,c in enumerate(ALPH)}
def b58decode(s):
    n=0
    for ch in s:
        if ch not in MAP: raise ValueError("invalid base58")
        n=n*58+MAP[ch]
    raw=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    return b"\x00"*(len(s)-len(s.lstrip("1")))+raw

def request(body):
    raw=json.dumps(body,separators=(",",":")).encode()
    req=urllib.request.Request(ENDPOINT,data=raw,method="POST",headers={
      "Content-Type":"application/json",
      "Accept":"application/x-ndjson,application/json",
      "User-Agent":"crypto-lab-dls-save11-calibration/0.3.1"
    })
    last=None
    for i in range(6):
        try:
            with urllib.request.urlopen(req,timeout=60) as resp:
                return int(resp.status),dict(resp.headers),resp.read().decode("utf-8","replace")
        except urllib.error.HTTPError as e:
            txt=e.read().decode("utf-8","replace")
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code,"body":txt[:1000]}
                time.sleep(min(30,2**i)); continue
            return int(e.code),dict(e.headers),txt
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:500]}
            time.sleep(min(30,2**i))
    raise RuntimeError(str(last))

body={
 "type":"solana",
 "fromBlock":FROM,
 "toBlock":TO,
 "fields":{
   "block":{"number":True,"timestamp":True},
   "transaction":{"transactionIndex":True,"signatures":True,"err":True},
   "instruction":{"programId":True,"data":True,"transactionIndex":True,
                  "instructionAddress":True,"isCommitted":True,"error":True}
 },
 "instructions":[{"programId":[PROGRAM],"transaction":True}]
}

try:
    status,headers,txt=request(body)
    rows=[]
    if status==200:
        for line in txt.splitlines():
            if line.strip(): rows.append(json.loads(line))
    candidates=[]
    program_instruction_count=0
    for b in rows:
        hdr=b.get("header") or {}
        slot=hdr.get("number")
        t=hdr.get("timestamp")
        if isinstance(t,(int,float)):
            t=dt.datetime.fromtimestamp(t,dt.timezone.utc).isoformat().replace("+00:00","Z")
        txs=b.get("transactions") or []
        tx_by_idx={}
        for pos,tx in enumerate(txs):
            idx=tx.get("transactionIndex",tx.get("index",pos))
            tx_by_idx[idx]=tx
        for ix in b.get("instructions") or []:
            if ix.get("programId")!=PROGRAM: continue
            program_instruction_count+=1
            data=ix.get("data")
            try: dec=b58decode(data) if isinstance(data,str) else b""
            except Exception: dec=b""
            if not dec.startswith(b"\x11"): continue
            ti=ix.get("transactionIndex")
            tx=tx_by_idx.get(ti,{})
            candidates.append({
              "slot":slot,"timestamp":t,"programId":ix.get("programId"),
              "data":data,"decoded_prefix_hex":dec[:1].hex() if dec else None,
              "transactionIndex":ti,"instructionAddress":ix.get("instructionAddress"),
              "isCommitted":ix.get("isCommitted"),"instructionError":ix.get("error"),
              "signatures":tx.get("signatures") or [],"transactionErr":tx.get("err")
            })

    matches=[x for x in candidates if x["slot"]==EXPECTED_SLOT and EXPECTED_SIG in x["signatures"]]
    checks={
      "http_200":status==200,
      "expected_slot_found":any(x["slot"]==EXPECTED_SLOT for x in candidates),
      "expected_signature_found":any(EXPECTED_SIG in x["signatures"] for x in candidates),
      "exact_linked_match_count":len(matches),
      "program_exact":bool(matches) and all(x["programId"]==PROGRAM for x in matches),
      "prefix_exact":bool(matches) and all(x["decoded_prefix_hex"]=="11" for x in matches),
      "transaction_err_null":bool(matches) and all(x["transactionErr"] is None for x in matches),
      "instruction_committed_true":bool(matches) and all(x["isCommitted"] is True for x in matches),
      "instruction_error_null":bool(matches) and all(x["instructionError"] is None for x in matches),
      "instruction_address_present":bool(matches) and all(isinstance(x["instructionAddress"],list) and len(x["instructionAddress"])>0 for x in matches)
    }
    passed=all([
      checks["http_200"],checks["expected_slot_found"],checks["expected_signature_found"],
      checks["exact_linked_match_count"]>=1,checks["program_exact"],checks["prefix_exact"],
      checks["transaction_err_null"],checks["instruction_committed_true"],
      checks["instruction_error_null"],checks["instruction_address_present"]
    ])
    classification="SAVE11_SQD_INNER_CPI_CALIBRATION_PASS" if passed else (
      "SAVE11_SQD_INNER_CPI_CALIBRATION_BLOCKED" if status not in (200,) else "SOURCE_ANOMALY_FAIL_CLOSED"
    )
    rec={
      "schema_version":"0.3.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":classification,"endpoint":ENDPOINT,
      "http_status":status,"x_sqd_data_source":headers.get("x-sqd-data-source"),
      "program_instruction_count":program_instruction_count,
      "local_tag11_candidate_count":len(candidates),
      "checks":checks,"exact_matches":matches,
      "expected":{"slot":EXPECTED_SLOT,"signature":EXPECTED_SIG,"time":EXPECTED_TIME},
      "firewall":{"prices":False,"balances":False,"token_balances":False,"amounts":False,
                  "returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
                  "protected_market_outcomes_2025_2026":False,"live_trading":False,
                  "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
                  "account_creation":False,"merge_main":False}
    }
except Exception as e:
    rec={
      "schema_version":"0.3.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":"SAVE11_SQD_INNER_CPI_CALIBRATION_BLOCKED",
      "error":type(e).__name__,"detail":str(e)[:1000]
    }

OUT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(rec,indent=2,sort_keys=True))
