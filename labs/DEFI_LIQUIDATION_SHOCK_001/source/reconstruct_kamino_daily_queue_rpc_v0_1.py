#!/usr/bin/env python3
import hashlib, json, time, urllib.request, urllib.error
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAM="KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
MAX_RETRIES=12
LIMIT=1000
OUTDIR=Path("labs/DEFI_LIQUIDATION_SHOCK_001")

CONTROL={
  "date":"2023-11-18",
  "start":1700265600,
  "end":1700352000,
  "newer":"5GjDCxV8pirvA3TFZcmCfBfjTy2zC37FLGUAqwwnyedkZq3p9b3mYHdH1EqztEHBraDagLZx1wJ4emQMTEGVFmnF",
  "older":"4kAsx7MhnmgqVNTTHbaAgRDaTbQqSJEhzo85FJQfMoN6oFVHMta837xjeHEGuGqmXSa4qAdZamFzLPjvgCFQd15J",
  "expected_rows":550,
  "expected_sha":"f94c0c6ae91bf74f9664d13a7e34a1e47c3285641dba95816be39062efe8c1ad"
}
TARGET={
  "date":"2023-11-19",
  "start":1700352000,
  "end":1700438400,
  "newer":"34PcMiHAnS2ydNGRmUTV129ms9BhgG2AGUgBN11G3bT14z1PqVjfZGRyrCwPH8zNamcJ8z8vh72pwJwx3WTaHSx4",
  "older":"5xPgHD26z25Q1baPZDQb2NnAmfMauoAgNzR3R9D8gH7TCAXFaWbw9ecHjdymKr5JBouahMGGp48kCN8gukECCiE4",
  "expected_rows":716,
  "expected_sha":"e9691dbe503ce8bbc5a54c321fbf560c0aba444303d3304a0f6f7b7cc1256400"
}

def canon(rows):
    return json.dumps(rows,separators=(",",":"),sort_keys=True).encode()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def rpc(params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress","params":[PROGRAM,params]},separators=(",",":")).encode()
    last=None
    for attempt in range(MAX_RETRIES):
        req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-dls-daily-reconstruct/0.1"})
        try:
            with urllib.request.urlopen(req,timeout=60) as resp:
                raw=resp.read()
            obj=json.loads(raw)
            if obj.get("error"):
                last={"rpc_error":obj["error"]}
                time.sleep(min(45,2*(attempt+1)))
                continue
            rows=obj.get("result")
            if not isinstance(rows,list):
                last={"bad_result_type":type(rows).__name__}
                time.sleep(min(20,2*(attempt+1)))
                continue
            return rows
        except urllib.error.HTTPError as e:
            body=e.read() if hasattr(e,"read") else b""
            last={"http":e.code,"body":body[:300].decode("utf-8","replace")}
            if e.code in (429,500,502,503,504):
                time.sleep(min(45,2*(attempt+1)))
                continue
            break
        except Exception as e:
            last={"transport":repr(e)}
            time.sleep(min(45,2*(attempt+1)))
    raise RuntimeError(f"RPC_EXHAUSTED {last}")

def reconstruct(cfg):
    all_rows=[]
    before=cfg["newer"]
    page=0
    seen=set()
    while True:
        params={"before":before,"until":cfg["older"],"limit":LIMIT,"commitment":"finalized"}
        rows=rpc(params)
        page+=1
        if not rows:
            break
        for r in rows:
            if not isinstance(r,dict):
                raise RuntimeError(f"{cfg['date']} ROW_NOT_OBJECT")
            sig=r.get("signature")
            slot=r.get("slot")
            bt=r.get("blockTime")
            if not isinstance(sig,str) or not sig:
                raise RuntimeError(f"{cfg['date']} INVALID_SIGNATURE")
            if sig in (cfg["newer"],cfg["older"]):
                raise RuntimeError(f"{cfg['date']} ANCHOR_INCLUDED {sig}")
            if sig in seen:
                raise RuntimeError(f"{cfg['date']} DUPLICATE_SIGNATURE {sig}")
            if isinstance(slot,bool) or not isinstance(slot,int):
                raise RuntimeError(f"{cfg['date']} INVALID_SLOT {sig}")
            if isinstance(bt,bool) or not isinstance(bt,int):
                raise RuntimeError(f"{cfg['date']} NULL_OR_INVALID_BLOCKTIME {sig}")
            if not (cfg["start"] <= bt < cfg["end"]):
                raise RuntimeError(f"{cfg['date']} ROW_OUTSIDE_WINDOW sig={sig} blockTime={bt}")
            seen.add(sig)
            all_rows.append({"signature":sig,"slot":slot,"blockTime":bt,"err":r.get("err")})
        if len(rows)<LIMIT:
            break
        before=rows[-1]["signature"]
        if page>100:
            raise RuntimeError(f"{cfg['date']} PAGE_CAP_EXCEEDED")
        time.sleep(0.15)

    ordered=sorted(all_rows,key=lambda r:(r["blockTime"],r["slot"],r["signature"]))
    digest=sha(canon(ordered))
    return {
      "date":cfg["date"],
      "rows":ordered,
      "row_count":len(ordered),
      "queue_sha256":digest,
      "expected_rows":cfg["expected_rows"],
      "expected_sha256":cfg["expected_sha"],
      "count_match":len(ordered)==cfg["expected_rows"],
      "hash_match":digest==cfg["expected_sha"],
      "pages":page
    }

receipt={
 "schema_version":"0.1",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "program_id":PROGRAM,
 "classification":"KAMINO_DAILY_RPC_RECONSTRUCTION_CALIBRATION_FAIL_CLOSED",
 "transport":"official_public_solana_rpc_getSignaturesForAddress",
 "firewalls":{
   "liquidation_classification":False,"prices":False,"amounts":False,"returns":False,"pnl":False,
   "direction":False,"market_outcomes":False,"live_trading":False,"orders":False,"wallets":False,
   "exchange_mutation":False,"paid_source":False,"account_creation":False,"merge_main":False
 }
}

try:
    control=reconstruct(CONTROL)
    receipt["control"]={k:v for k,v in control.items() if k!="rows"}
    if not control["count_match"] or not control["hash_match"]:
        receipt["reason"]="control_count_or_hash_mismatch"
    else:
        target=reconstruct(TARGET)
        receipt["target"]={k:v for k,v in target.items() if k!="rows"}
        if target["count_match"] and target["hash_match"]:
            receipt["classification"]="KAMINO_DAILY_RPC_RECONSTRUCTION_CALIBRATION_PASS"
            queue={
              "schema_version":"0.1",
              "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
              "class_id":"KAMINO_V1",
              "program_id":PROGRAM,
              "discriminator":"b1479abce2854a37",
              "window":{"start":"2023-11-19T00:00:00Z","end":"2023-11-20T00:00:00Z","semantics":"half_open"},
              "source":{
                "method":"official_public_solana_rpc_getSignaturesForAddress",
                "newer_anchor":TARGET["newer"],"older_anchor":TARGET["older"],
                "manifest_expected_rows":TARGET["expected_rows"],
                "manifest_expected_sha256":TARGET["expected_sha"]
              },
              "queue_rows":target["row_count"],
              "queue_sha256":target["queue_sha256"],
              "rows":target["rows"],
              "firewalls":receipt["firewalls"]
            }
            OUTDIR.joinpath("KAMINO_V1_EVENT_CENSUS_2023_11_19_QUEUE_V0.1.json").write_text(json.dumps(queue,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        else:
            receipt["reason"]="target_count_or_hash_mismatch"
except Exception as e:
    receipt["classification"]="KAMINO_DAILY_RPC_RECONSTRUCTION_RPC_BLOCKED" if "RPC_EXHAUSTED" in str(e) else "KAMINO_DAILY_RPC_RECONSTRUCTION_CALIBRATION_FAIL_CLOSED"
    receipt["reason"]=type(e).__name__
    receipt["detail"]=str(e)[:1000]

OUTDIR.joinpath("KAMINO_DAILY_RPC_RECONSTRUCTION_CALIBRATION_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
if receipt["classification"]!="KAMINO_DAILY_RPC_RECONSTRUCTION_CALIBRATION_PASS":
    raise SystemExit(2)
