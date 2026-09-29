#!/usr/bin/env python3
import argparse, base64, binascii, concurrent.futures, hashlib, json, struct, time, urllib.error, urllib.request
from collections import defaultdict
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
SRC=Path("drift_source/drift-202301.json")
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_JAN2023_REALIZED_SIGNED_FLOW_POPULATION_RECEIPT_V0.1.json")
DISC=hashlib.sha256(b"event:LiquidationRecord").digest()[:8]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
EARLY_NO_FLOW={
    "User has no base asset amount",
    "max_base_asset_amount_allowed_to_be_transferred == 0",
}

def canon(v): return json.dumps(v,separators=(",",":"),sort_keys=True)

def b58encode(raw):
    n=int.from_bytes(raw,"big"); s=""
    while n:
        n,rem=divmod(n,58); s=ALPH[rem]+s
    pad=0
    for b in raw:
        if b==0: pad+=1
        else: break
    return "1"*pad+(s or ("" if pad else "1"))

class Reader:
    def __init__(self,b): self.b=b; self.o=0
    def take(self,n):
        if self.o+n>len(self.b): raise ValueError("truncated")
        x=self.b[self.o:self.o+n]; self.o+=n; return x
    def u8(self): return self.take(1)[0]
    def u16(self): return struct.unpack("<H",self.take(2))[0]
    def u32(self): return struct.unpack("<I",self.take(4))[0]
    def u64(self): return struct.unpack("<Q",self.take(8))[0]
    def i64(self): return struct.unpack("<q",self.take(8))[0]
    def u128(self): return int.from_bytes(self.take(16),"little",signed=False)
    def i128(self): return int.from_bytes(self.take(16),"little",signed=True)
    def pubkey(self): return b58encode(self.take(32))

def decode_liquidation(message):
    if not isinstance(message,str): return None
    s=message.strip()
    if s.startswith("Program data: "): s=s[len("Program data: "):].strip()
    try: raw=base64.b64decode(s,validate=True)
    except (binascii.Error,ValueError): return None
    if len(raw)<9 or raw[:8]!=DISC: return None
    r=Reader(raw); r.take(8)
    ev={}
    ev["ts"]=r.i64()
    ev["liquidation_type"]=r.u8()
    ev["user"]=r.pubkey()
    ev["liquidator"]=r.pubkey()
    ev["margin_requirement"]=r.u128()
    ev["total_collateral"]=r.i128()
    ev["margin_freed"]=r.u64()
    ev["liquidation_id"]=r.u16()
    ev["bankrupt"]=bool(r.u8())
    n=r.u32()
    if n>100000: raise ValueError("implausible_cancel_vec")
    ev["canceled_order_ids"]=[r.u32() for _ in range(n)]
    lp={}
    lp["market_index"]=r.u16()
    lp["oracle_price"]=r.i64()
    lp["base_asset_amount"]=r.i64()
    lp["quote_asset_amount"]=r.i64()
    lp["lp_shares"]=r.u64()
    lp["fill_record_id"]=r.u64()
    lp["user_order_id"]=r.u32()
    lp["liquidator_order_id"]=r.u32()
    lp["liquidator_fee"]=r.u64()
    lp["if_fee"]=r.u64()
    ev["liquidate_perp"]=lp
    ev["decoded_prefix_bytes"]=r.o
    ev["payload_size"]=len(raw)
    return ev

def request_slot(slot,retries=9):
    body={"type":"solana","fromBlock":slot,"toBlock":slot,
      "fields":{
        "transaction":{"transactionIndex":True,"signatures":True,"err":True},
        "log":{"programId":True,"message":True,"kind":True,"transactionIndex":True,"instructionAddress":True}
      },
      "transactions":[{}],"logs":[{}]}
    data=json.dumps(body,separators=(",",":")).encode()
    q=urllib.request.Request(STREAM,data=data,headers={
      "Accept":"application/x-ndjson,application/json",
      "Content-Type":"application/json",
      "User-Agent":"crypto-lab-dls-drift-signed-population/0.1"
    },method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:
                status=int(r.status); raw=r.read()
                if status!=200: return {"slot":slot,"status":status,"raw":raw[:1000].decode("utf-8","replace")}
                sig_to_ti={}; logs_by_ti=defaultdict(list); schema_errors=[]
                for line in raw.decode("utf-8","replace").splitlines():
                    if not line.strip(): continue
                    b=json.loads(line)
                    for pos,tx in enumerate(b.get("transactions") or []):
                        idx=tx.get("transactionIndex",tx.get("index",pos))
                        sigs=tx.get("signatures") or []
                        if sigs and isinstance(sigs[0],str) and tx.get("err") is None:
                            if sigs[0] in sig_to_ti and sig_to_ti[sigs[0]]!=idx:
                                schema_errors.append("signature_multiple_transaction_indices:"+sigs[0])
                            sig_to_ti[sigs[0]]=idx
                    for lg in b.get("logs") or []:
                        ti=lg.get("transactionIndex")
                        if ti is not None: logs_by_ti[ti].append(lg)
                return {"slot":slot,"status":200,"sig_to_ti":sig_to_ti,"logs_by_ti":dict(logs_by_ti),"schema_errors":schema_errors}
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code}; time.sleep(min(45,1.5*(2**i))); continue
            return {"slot":slot,"status":int(e.code),"raw":raw[:1000].decode("utf-8","replace")}
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:250]}; time.sleep(min(45,1.5*(2**i)))
    return {"slot":slot,"status":None,"transport_exhausted":last}

def process_ref(ref,slot_result):
    sem=ref.get("semantic_accounts") or {}
    market=(ref.get("market_identity") or {}).get("perp_market_index")
    rr={
      "signature":ref["signature"],"slot":ref["slot"],"timestamp":ref.get("timestamp"),
      "instructionAddress":ref["instructionAddress"],"canonical_market_index":market,
      "canonical_user":sem.get("liquidated_user"),"canonical_liquidator":sem.get("liquidator"),
      "status":"SOURCE_EVIDENCE_INCOMPLETE","direction_label":"SOURCE_EVIDENCE_INCOMPLETE",
      "evidence_reason":None,"decoded_liquidation_records":0,"bound_record_count":0,
      "signed_base_asset_amount":None,"transport_status":slot_result.get("status")
    }
    if slot_result.get("status")!=200:
        rr["evidence_reason"]="slot_transport_not_200"; return rr
    if slot_result.get("schema_errors"):
        rr["evidence_reason"]="slot_schema_conflict"; return rr
    ti=(slot_result.get("sig_to_ti") or {}).get(ref["signature"])
    if ti is None:
        rr["evidence_reason"]="exact_successful_transaction_not_found"; return rr
    rr["transactionIndex"]=ti
    logs=(slot_result.get("logs_by_ti") or {}).get(ti,[])
    drift_logs=[x for x in logs if x.get("programId")==PROGRAM]
    if any("truncated" in str(x.get("message","")).lower() for x in logs):
        rr["evidence_reason"]="transaction_logs_truncated"; return rr
    decoded=[]; decode_errors=[]
    for lg in drift_logs:
        try: ev=decode_liquidation(lg.get("message"))
        except Exception as e:
            decode_errors.append(type(e).__name__+":"+str(e)[:120]); continue
        if ev is None: continue
        decoded.append({"instructionAddress":lg.get("instructionAddress"),"kind":lg.get("kind"),"event":ev})
    rr["decoded_liquidation_records"]=len(decoded)
    bound=[]
    for item in decoded:
        ev=item["event"]; reasons=[]
        if ev.get("liquidation_type")!=0: reasons.append("not_liquidate_perp")
        if ev.get("user")!=rr["canonical_user"]: reasons.append("user_mismatch")
        if ev.get("liquidator")!=rr["canonical_liquidator"]: reasons.append("liquidator_mismatch")
        if (ev.get("liquidate_perp") or {}).get("market_index")!=market: reasons.append("market_index_mismatch")
        ia=item.get("instructionAddress")
        if ia is not None and ia!=ref["instructionAddress"]: reasons.append("instruction_address_mismatch")
        item["bind_reasons"]=reasons
        if not reasons: bound.append(item)
    rr["bound_record_count"]=len(bound)

    if len(bound)==1:
        lp=bound[0]["event"]["liquidate_perp"]; ba=lp["base_asset_amount"]
        rr["signed_base_asset_amount"]=ba
        rr["liquidation_id"]=bound[0]["event"]["liquidation_id"]
        rr["fill_record_id"]=lp["fill_record_id"]
        rr["lp_shares"]=lp["lp_shares"]
        if ba<0:
            rr["status"]="PROVEN_REALIZED"; rr["direction_label"]="SIGNED_SELL_PRESSURE_PROVEN"; rr["evidence_reason"]="bound_nonzero_liquidation_record"
        elif ba>0:
            rr["status"]="PROVEN_REALIZED"; rr["direction_label"]="SIGNED_BUY_PRESSURE_PROVEN"; rr["evidence_reason"]="bound_nonzero_liquidation_record"
        else:
            rr["status"]="PROVEN_NOT_REALIZED"; rr["direction_label"]="DIRECTION_AMBIGUOUS"; rr["evidence_reason"]="bound_zero_base_delta"
        return rr

    if len(bound)>1:
        signs={1 if x["event"]["liquidate_perp"]["base_asset_amount"]>0 else -1 if x["event"]["liquidate_perp"]["base_asset_amount"]<0 else 0 for x in bound}
        rr["status"]="CONTRADICTION" if 1 in signs and -1 in signs else "SOURCE_EVIDENCE_INCOMPLETE"
        rr["direction_label"]="SOURCE_EVIDENCE_INCOMPLETE"
        rr["evidence_reason"]="multiple_exact_bound_records"
        return rr

    messages={str(x.get("message","")) for x in drift_logs}
    matched=sorted(EARLY_NO_FLOW.intersection(messages))
    if matched:
        rr["status"]="PROVEN_NOT_REALIZED"; rr["direction_label"]="DIRECTION_AMBIGUOUS"
        rr["evidence_reason"]="explicit_historical_early_return:"+matched[0]
        return rr

    if decoded:
        rr["evidence_reason"]="liquidation_records_present_but_none_bind_exactly"
    elif decode_errors:
        rr["evidence_reason"]="target_event_decode_error"
        rr["decode_errors"]=decode_errors[:10]
    else:
        rr["evidence_reason"]="no_bound_liquidation_record_and_no_frozen_no_flow_log"
    return rr

ap=argparse.ArgumentParser(); ap.add_argument("--workers",type=int,default=16); args=ap.parse_args()
src=json.loads(SRC.read_text())
assert src["classification"]=="FIELD_ENRICHMENT_PARTITION_PASS"
refs=[r for r in src["enriched_rows"] if r.get("class")=="liquidate_perp"]
assert len(refs)==3179, f"frozen_population_mismatch:{len(refs)}"
unique_slots=sorted({int(r["slot"]) for r in refs})

slot_results={}
with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(request_slot,s):s for s in unique_slots}
    done=0
    for fut in concurrent.futures.as_completed(futs):
        s=futs[fut]
        try: slot_results[s]=fut.result()
        except Exception as e: slot_results[s]={"slot":s,"status":None,"transport_exhausted":{"error":type(e).__name__,"detail":str(e)[:250]}}
        done+=1
        if done%200==0: print(f"slot_progress {done}/{len(unique_slots)}",flush=True)

results=[process_ref(r,slot_results[int(r["slot"])]) for r in refs]
counts=defaultdict(int); labels=defaultdict(int); reasons=defaultdict(int)
for r in results:
    counts[r["status"]]+=1; labels[r["direction_label"]]+=1; reasons[r["evidence_reason"]]+=1
R=counts["PROVEN_REALIZED"]; I=counts["SOURCE_EVIDENCE_INCOMPLETE"]+counts["CONTRADICTION"]
B=labels["SIGNED_BUY_PRESSURE_PROVEN"]; S=labels["SIGNED_SELL_PRESSURE_PROVEN"]; C=counts["CONTRADICTION"]
coverage=(R/(R+I)) if (R+I)>0 else 0.0
direction=((B+S)/R) if R>0 else 0.0
authorized=R>0 and coverage>=0.95 and direction>=0.90 and C==0
classification="DRIFT_LIQUIDATE_PERP_SIGNED_FLOW_AUTHORIZED" if authorized else "DRIFT_LIQUIDATE_PERP_SIGNED_FLOW_PARTIAL"
hard_transport=sum(1 for x in slot_results.values() if x.get("status")!=200)
if R==0 and hard_transport==len(unique_slots):
    classification="DRIFT_LIQUIDATE_PERP_SIGNED_FLOW_BLOCKED"

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,"family":"drift/liquidate_perp",
 "source_artifact":{"run_id":36264543005,"artifact_id":10915721179,"name":"dls-field-enrichment-drift-drift-202301",
   "digest":"sha256:47c9f1af96c29c2c7ea80f2a167d27c932932f956ae8b650a5388cb9b14730c8"},
 "population_candidate_count":len(refs),"unique_slot_count":len(unique_slots),
 "slot_transport_non_200_count":hard_transport,
 "counts":dict(sorted(counts.items())),"labels":dict(sorted(labels.items())),"evidence_reasons":dict(sorted(reasons.items())),
 "metrics":{"proven_realized_R":R,"source_incomplete_or_contradiction_I":I,
   "conservative_source_coverage":coverage,"signed_buy_B":B,"signed_sell_S":S,
   "deterministic_directional_rate":direction,"contradictions_C":C},
 "thresholds":{"min_conservative_source_coverage":0.95,"min_deterministic_directional_rate":0.90,"contradictions_required":0},
 "historical_source_repository_id":497045217,
 "historical_source_anchors":["099d7ac15260a2068738af36871bd384c93cade6","9a1a83029e995807efe9e15b8a77f59d100fd33b"],
 "event_discriminator_hex":DISC.hex(),
 "results":sorted(results,key=lambda r:(r["timestamp"] or "",r["slot"],r["signature"])),
 "firewall":{"prices":False,"returns":False,"pnl":False,"market_2025_opened":False,"market_2026_opened":False,
   "future_market_direction":False,"live_trading":False,"orders":False,"wallets":False,
   "exchange_mutation":False,"merge_main":False,"post_outcome_tuning":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":classification,"population":len(refs),"unique_slots":len(unique_slots),
 "counts":dict(counts),"labels":dict(labels),
 "R":R,"I":I,"coverage":coverage,"directional_rate":direction,"contradictions":C,
 "slot_transport_non_200":hard_transport,
 "top_reasons":sorted(reasons.items(),key=lambda x:(-x[1],x[0]))[:12]
},indent=2))
if not authorized: raise SystemExit(2)
