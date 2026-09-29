#!/usr/bin/env python3
import base64,binascii,collections,hashlib,json,struct,time,urllib.error,urllib.request
from pathlib import Path
STREAM="https://portal.sqd.dev/datasets/solana-mainnet/finalized-stream"
PROGRAM="dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
SRC=Path("drift_source/drift-202301.json")
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_JAN2023_REALIZED_SIGNED_FLOW_CENSUS_RECEIPT_V0.1.json")
DISC=hashlib.sha256(b"event:LiquidationRecord").digest()[:8]
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58(raw):
 n=int.from_bytes(raw,"big");s=""
 while n:n,r=divmod(n,58);s=ALPH[r]+s
 p=0
 for x in raw:
  if x==0:p+=1
  else:break
 return "1"*p+(s or ("" if p else "1"))
class R:
 def __init__(self,b):self.b=b;self.o=0
 def t(self,n):
  if self.o+n>len(self.b):raise ValueError("truncated")
  x=self.b[self.o:self.o+n];self.o+=n;return x
 def u8(self):return self.t(1)[0]
 def u16(self):return struct.unpack("<H",self.t(2))[0]
 def u32(self):return struct.unpack("<I",self.t(4))[0]
 def u64(self):return struct.unpack("<Q",self.t(8))[0]
 def i64(self):return struct.unpack("<q",self.t(8))[0]
 def u128(self):return int.from_bytes(self.t(16),"little")
 def i128(self):return int.from_bytes(self.t(16),"little",signed=True)
 def pk(self):return b58(self.t(32))
def dec(msg):
 if not isinstance(msg,str):return None
 s=msg.strip()
 if s.startswith("Program data: "):s=s[14:].strip()
 try:raw=base64.b64decode(s,validate=True)
 except (binascii.Error,ValueError):return None
 if len(raw)<9 or raw[:8]!=DISC:return None
 r=R(raw);r.t(8)
 e={"ts":r.i64(),"liquidation_type":r.u8(),"user":r.pk(),"liquidator":r.pk(),
 "margin_requirement":r.u128(),"total_collateral":r.i128(),"margin_freed":r.u64(),
 "liquidation_id":r.u16(),"bankrupt":bool(r.u8())}
 n=r.u32()
 if n>100000:raise ValueError("bad_vec")
 e["canceled_order_ids"]=[r.u32() for _ in range(n)]
 e["market_index"]=r.u16();e["oracle_price"]=r.i64();e["base_asset_amount"]=r.i64()
 e["quote_asset_amount"]=r.i64();e["lp_shares"]=r.u64();e["fill_record_id"]=r.u64()
 e["user_order_id"]=r.u32();e["liquidator_order_id"]=r.u32();e["liquidator_fee"]=r.u64();e["if_fee"]=r.u64()
 return e

def fetch(slot):
 body={"type":"solana","fromBlock":slot,"toBlock":slot,
 "fields":{"transaction":{"transactionIndex":True,"signatures":True,"err":True},
 "log":{"programId":True,"message":True,"kind":True,"transactionIndex":True,"instructionAddress":True}},
 "transactions":[{}],"logs":[{}]}
 data=json.dumps(body,separators=(",",":")).encode()
 for a in range(8):
  q=urllib.request.Request(STREAM,data=data,headers={"Accept":"application/x-ndjson,application/json","Content-Type":"application/json","User-Agent":"crypto-lab-dls-drift-realized-census/0.1"},method="POST")
  try:
   with urllib.request.urlopen(q,timeout=120) as z:return z.read().decode("utf-8","replace")
  except urllib.error.HTTPError as e:
   if e.code==429 or 500<=e.code<600:time.sleep(min(30,2**a));continue
   raise
  except Exception:
   time.sleep(min(30,2**a))
 raise RuntimeError("transport_exhausted")

src=json.loads(SRC.read_text());assert src["classification"]=="FIELD_ENRICHMENT_PARTITION_PASS"
rows=[x for x in src["enriched_rows"] if x.get("class")=="liquidate_perp"]
by_slot=collections.defaultdict(list)
for x in rows:by_slot[int(x["slot"])].append(x)
out=[];query_failed=0
for ix,slot in enumerate(sorted(by_slot),1):
 try:raw=fetch(slot)
 except Exception as e:
  for x in by_slot[slot]:out.append({"signature":x["signature"],"slot":slot,"instructionAddress":x["instructionAddress"],"status":"SOURCE_EVIDENCE_INCOMPLETE","reason":"slot_query_failed","detail":str(e)[:200]})
  query_failed+=len(by_slot[slot]);continue
 txi={};logs=[]
 for line in raw.splitlines():
  if not line.strip():continue
  b=json.loads(line)
  for pos,t in enumerate(b.get("transactions") or []):
   sig=(t.get("signatures") or [None])[0]
   if sig:txi[sig]=(t.get("transactionIndex",t.get("index",pos)),t.get("err"))
  logs.extend(b.get("logs") or [])
 for x in by_slot[slot]:
  rec={"signature":x["signature"],"slot":slot,"instructionAddress":x["instructionAddress"],"canonical_market_index":(x.get("market_identity") or {}).get("perp_market_index"),"canonical_user":(x.get("semantic_accounts") or {}).get("liquidated_user"),"canonical_liquidator":(x.get("semantic_accounts") or {}).get("liquidator")}
  t=txi.get(x["signature"])
  if t is None or t[1] is not None:
   rec.update(status="SOURCE_EVIDENCE_INCOMPLETE",reason="exact_success_transaction_not_found");out.append(rec);continue
  ti=t[0];bound=[];opposite=False
  for lg in logs:
   if lg.get("transactionIndex")!=ti or lg.get("programId")!=PROGRAM:continue
   try:e=dec(lg.get("message"))
   except Exception:continue
   if e is None or e["liquidation_type"]!=0:continue
   if e["user"]!=rec["canonical_user"] or e["liquidator"]!=rec["canonical_liquidator"] or e["market_index"]!=rec["canonical_market_index"]:continue
   ia=lg.get("instructionAddress")
   if ia is not None and ia!=x["instructionAddress"]:continue
   bound.append({"instructionAddress":ia,"base_asset_amount":e["base_asset_amount"],"quote_asset_amount":e["quote_asset_amount"],"fill_record_id":e["fill_record_id"],"market_index":e["market_index"]})
  signs={1 if b["base_asset_amount"]>0 else -1 if b["base_asset_amount"]<0 else 0 for b in bound}
  if 1 in signs and -1 in signs:
   rec.update(status="CONTRADICTION",bound_records=bound);out.append(rec);continue
  if not bound:
   rec.update(status="NO_REALIZED_LIQUIDATION_RECORD");out.append(rec);continue
  if len(bound)>1:
   rec.update(status="SOURCE_EVIDENCE_INCOMPLETE",reason="multiple_exact_bound_records",bound_records=bound);out.append(rec);continue
  ba=bound[0]["base_asset_amount"]
  label="SIGNED_BUY_PRESSURE_PROVEN" if ba>0 else "SIGNED_SELL_PRESSURE_PROVEN" if ba<0 else "DIRECTION_AMBIGUOUS"
  rec.update(status=label,bound_record=bound[0]);out.append(rec)
 if ix%100==0:print(json.dumps({"slots_done":ix,"slots_total":len(by_slot),"rows_done":len(out)}),flush=True)

cnt=collections.Counter(x["status"] for x in out)
R=sum(cnt[k] for k in ["SIGNED_BUY_PRESSURE_PROVEN","SIGNED_SELL_PRESSURE_PROVEN","DIRECTION_AMBIGUOUS","SOURCE_EVIDENCE_INCOMPLETE","CONTRADICTION"])
I=cnt["SOURCE_EVIDENCE_INCOMPLETE"];D=cnt["SIGNED_BUY_PRESSURE_PROVEN"]+cnt["SIGNED_SELL_PRESSURE_PROVEN"];A=cnt["DIRECTION_AMBIGUOUS"];C=cnt["CONTRADICTION"]
coverage=(R-I)/R if R else 0.0;direction=D/(R-I) if R-I else 0.0
auth=R>0 and coverage>=.95 and direction>=.90 and C==0
classification="SIGNED_FLOW_SOURCE_PASS" if auth else ("SIGNED_FLOW_SOURCE_PARTIAL" if D>0 and C==0 else "SIGNED_FLOW_SOURCE_BLOCKED")
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","protocol":"drift","class":"liquidate_perp","interval":["2023-01-01T00:00:00Z","2023-02-01T00:00:00Z"],"classification":classification,"instruction_candidates":len(rows),"status_counts":dict(cnt),"realized_denominator":R,"source_non_incomplete":R-I,"direction_deterministic":D,"direction_ambiguous":A,"contradictions":C,"source_coverage":coverage,"direction_rate_non_incomplete":direction,"rows":out,"firewall":{"prices":False,"returns":False,"pnl":False,"market_2025_opened":False,"market_2026_opened":False,"live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","instruction_candidates","status_counts","realized_denominator","source_coverage","direction_rate_non_incomplete","contradictions"]},indent=2))
if classification!="SIGNED_FLOW_SOURCE_PASS":raise SystemExit(2)
