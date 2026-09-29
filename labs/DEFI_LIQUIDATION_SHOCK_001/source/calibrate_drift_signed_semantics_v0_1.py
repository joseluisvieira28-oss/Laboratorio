#!/usr/bin/env python3
import base64, binascii, hashlib, json, struct, time, urllib.error, urllib.request
from pathlib import Path

STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
SRC=Path("drift_source/drift-202301.json")
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_JAN2023_SIGNED_FLOW_SEMANTICS_CALIBRATION_RECEIPT_V0.1.json")
DISC=hashlib.sha256(b"event:LiquidationRecord").digest()[:8]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def ak(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def rk(r): return hashlib.sha256((r["signature"]+"|"+ak(r["instructionAddress"])).encode()).hexdigest()

def b58encode(raw):
    n=int.from_bytes(raw,"big")
    s=""
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

def decode_payload(message):
    if not isinstance(message,str): return None
    s=message.strip()
    if s.startswith("Program data: "): s=s[len("Program data: "):].strip()
    try: raw=base64.b64decode(s,validate=True)
    except (binascii.Error,ValueError): return None
    if len(raw)<9 or raw[:8]!=DISC: return None
    r=Reader(raw); r.take(8)
    out={}
    out["ts"]=r.i64()
    out["liquidation_type"]=r.u8()
    out["user"]=r.pubkey()
    out["liquidator"]=r.pubkey()
    out["margin_requirement"]=r.u128()
    out["total_collateral"]=r.i128()
    out["margin_freed"]=r.u64()
    out["liquidation_id"]=r.u16()
    out["bankrupt"]=bool(r.u8())
    n=r.u32()
    if n>100000: raise ValueError("implausible_cancel_vec")
    out["canceled_order_ids"]=[r.u32() for _ in range(n)]
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
    out["liquidate_perp"]=lp
    out["decoded_prefix_bytes"]=r.o
    out["payload_size"]=len(raw)
    return out

def req(slot,retries=8):
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
      "User-Agent":"crypto-lab-dls-drift-signed-semantics/0.1"
    },method="POST")
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(q,timeout=120) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            raw=e.read()
            if e.code==429 or 500<=e.code<600:
                last={"http":e.code};time.sleep(min(45,2**i));continue
            return int(e.code),raw
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:200]};time.sleep(min(45,2**i))
    raise RuntimeError(f"transport_exhausted:{last}")

src=json.loads(SRC.read_text())
assert src["classification"]=="FIELD_ENRICHMENT_PARTITION_PASS"
rows=[r for r in src["enriched_rows"] if r.get("class")=="liquidate_perp"]
refs=sorted(rows,key=lambda r:(rk(r),r["signature"],ak(r["instructionAddress"])))[:3]
results=[]; contradictions=0; incomplete=0; nonzero=0

for ref in refs:
    rr={
      "rank":rk(ref),"signature":ref["signature"],"slot":ref["slot"],
      "instructionAddress":ref["instructionAddress"],
      "canonical_market_index":(ref.get("market_identity") or {}).get("perp_market_index"),
      "canonical_user":(ref.get("semantic_accounts") or {}).get("liquidated_user"),
      "canonical_liquidator":(ref.get("semantic_accounts") or {}).get("liquidator"),
      "event_discriminator_hex":DISC.hex(),
      "classification":"SOURCE_EVIDENCE_INCOMPLETE",
      "bound_record_count":0,
      "decoded_liquidation_record_count":0,
      "identity_conflicts":[],
      "records":[]
    }
    st,raw=req(int(ref["slot"])); rr["http_status"]=st
    if st!=200:
        rr["transport_error"]=raw[:800].decode("utf-8","replace"); incomplete+=1; results.append(rr); continue
    ti=None; logs=[]
    for line in raw.decode("utf-8","replace").splitlines():
        if not line.strip(): continue
        b=json.loads(line)
        for pos,tx in enumerate(b.get("transactions") or []):
            idx=tx.get("transactionIndex",tx.get("index",pos))
            sigs=tx.get("signatures") or []
            if sigs and sigs[0]==ref["signature"] and tx.get("err") is None:
                if ti is not None and ti!=idx: rr["identity_conflicts"].append("signature_multiple_transaction_indices")
                ti=idx
        logs += b.get("logs") or []
    if ti is None:
        rr["identity_conflicts"].append("exact_transaction_not_found"); incomplete+=1; results.append(rr); continue
    rr["transactionIndex"]=ti
    for lg in logs:
        if lg.get("transactionIndex")!=ti or lg.get("programId")!=PROGRAM: continue
        try: ev=decode_payload(lg.get("message"))
        except Exception as e:
            rr.setdefault("decode_errors",[]).append(type(e).__name__+":"+str(e)[:120]); continue
        if ev is None: continue
        rr["decoded_liquidation_record_count"]+=1
        entry={"instructionAddress":lg.get("instructionAddress"),"kind":lg.get("kind"),"event":ev,"bind_reasons":[]}
        if ev["liquidation_type"]!=0: entry["bind_reasons"].append("not_liquidate_perp")
        if ev["user"]!=rr["canonical_user"]: entry["bind_reasons"].append("user_mismatch")
        if ev["liquidator"]!=rr["canonical_liquidator"]: entry["bind_reasons"].append("liquidator_mismatch")
        if ev["liquidate_perp"]["market_index"]!=rr["canonical_market_index"]: entry["bind_reasons"].append("market_index_mismatch")
        ia=lg.get("instructionAddress")
        if ia is not None and ia!=ref["instructionAddress"]: entry["bind_reasons"].append("instruction_address_mismatch")
        entry["bound"]=len(entry["bind_reasons"])==0
        rr["records"].append(entry)
    bound=[x for x in rr["records"] if x["bound"]]
    rr["bound_record_count"]=len(bound)
    if len(bound)!=1:
        if len(bound)>1:
            dirs={0 if x["event"]["liquidate_perp"]["base_asset_amount"]==0 else (1 if x["event"]["liquidate_perp"]["base_asset_amount"]>0 else -1) for x in bound}
            if 1 in dirs and -1 in dirs:
                contradictions+=1; rr["identity_conflicts"].append("opposite_signed_exact_records")
        incomplete+=1; results.append(rr); continue
    ba=bound[0]["event"]["liquidate_perp"]["base_asset_amount"]
    rr["signed_base_asset_amount"]=ba
    if ba<0:
        rr["classification"]="SIGNED_SELL_PRESSURE_PROVEN"; nonzero+=1
    elif ba>0:
        rr["classification"]="SIGNED_BUY_PRESSURE_PROVEN"; nonzero+=1
    else:
        rr["classification"]="DIRECTION_AMBIGUOUS"
    results.append(rr)

if any(r["identity_conflicts"] for r in results): contradictions += sum(1 for r in results if any(x=="opposite_signed_exact_records" for x in r["identity_conflicts"]))
passed=(len(results)==3 and incomplete==0 and contradictions==0 and nonzero>=1)
classification="DRIFT_SIGNED_SEMANTICS_3_OF_3_PASS" if passed else "DRIFT_SIGNED_SEMANTICS_CALIBRATION_BLOCKED"
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,
 "historical_source_repository_id":497045217,
 "historical_source_anchors":["099d7ac15260a2068738af36871bd384c93cade6","9a1a83029e995807efe9e15b8a77f59d100fd33b"],
 "event_discriminator_hex":DISC.hex(),
 "reference_count":len(results),"incomplete_count":incomplete,
 "contradiction_count":contradictions,"nonzero_signed_count":nonzero,
 "results":results,
 "firewall":{"prices":False,"returns":False,"pnl":False,"market_2025_opened":False,"market_2026_opened":False,
   "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":classification,"references":len(results),"incomplete":incomplete,
 "contradictions":contradictions,"nonzero_signed":nonzero,
 "labels":[r["classification"] for r in results],
 "signed_base":[r.get("signed_base_asset_amount") for r in results],
 "decoded_counts":[r["decoded_liquidation_record_count"] for r in results],
 "bound_counts":[r["bound_record_count"] for r in results]
},indent=2))
if not passed: raise SystemExit(2)
