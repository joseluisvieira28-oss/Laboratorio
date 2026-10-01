#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from datetime import datetime,timezone,timedelta

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
R=OUT/"MARGINFI_ORCA_IMPACT_V02_PREOUTCOME_RECEIPT.json"
C=OUT/"MARGINFI_ORCA_IMPACT_V02_PREOUTCOME_CASCADES.ndjson"

def find_one(root,needle):
 h=[p for p in Path(root).rglob("*") if p.is_file() and needle in p.name]
 return h[0] if len(h)==1 else None
def iso(s): return datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(timezone.utc)
def akey(x): return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(x): return str(x.get("signature"))+"|"+akey(x.get("instructionAddress"))

rec=find_one(args.source_root,"RECEIPT")
rows=find_one(args.source_root,"ROWS")
if not rec or not rows:
 R.write_text(json.dumps({"classification":"MARGINFI_ORCA_IMPACT_PREOUTCOME_SOURCE_BLOCKED","reason":"artifact_files_missing_or_ambiguous"},indent=2)+"\n");raise SystemExit(2)
sr=json.loads(rec.read_text())
if sr.get("classification")!="MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS":
 R.write_text(json.dumps({"classification":"MARGINFI_ORCA_IMPACT_PREOUTCOME_SOURCE_BLOCKED","source_classification":sr.get("classification")},indent=2)+"\n");raise SystemExit(2)

ev=[]
for line in rows.read_text().splitlines():
 if not line.strip(): continue
 x=json.loads(line)
 if x.get("classification")!="DIRECTION_PROVEN": continue
 if x.get("route_semantic")!="COLLATERAL_TO_LIABILITY_ORCA_PROVEN": continue
 t=iso(x["timestamp"])
 if datetime(2024,10,1,tzinfo=timezone.utc)<=t<datetime(2025,1,1,tzinfo=timezone.utc):
  ev.append({"t":t,"id":ident(x)})
ev.sort(key=lambda x:(x["t"],x["id"]))
cas=[]
for e in ev:
 if not cas or e["t"]>cas[-1]["last"]+timedelta(minutes=5):
  cas.append({"first":e["t"],"last":e["t"],"ids":[e["id"]]})
 else:
  cas[-1]["last"]=e["t"];cas[-1]["ids"].append(e["id"])
out=[]
for i,c in enumerate(cas,1):
 out.append({"cascade_id":f"orca-{i:05d}","first_event_time":c["first"].isoformat(),"last_event_time":c["last"].isoformat(),
             "source_event_count":len(c["ids"]),"member_identities":c["ids"]})
with C.open("w") as fh:
 for x in out: fh.write(json.dumps(x,separators=(",",":"),sort_keys=True)+"\n")
days=len({x["last_event_time"][:10] for x in out})
f1=sum(x["last_event_time"]<"2024-12-01T00:00:00+00:00" for x in out)
f2=len(out)-f1
g={"eligible_source_events":len(ev),"source_cascade_count":len(out),"distinct_utc_cascade_end_days":days,"F1_cascades":f1,"F2_cascades":f2}
checks={"eligible_ge_500":len(ev)>=500,"cascades_ge_100":len(out)>=100,"days_ge_20":days>=20,"F1_ge_60":f1>=60,"F2_ge_20":f2>=20}
cl="MARGINFI_ORCA_IMPACT_V02_PREOUTCOME_READY" if all(checks.values()) else "MARGINFI_ORCA_IMPACT_V02_PREOUTCOME_INSUFFICIENT_SAMPLE"
receipt={"schema_version":"0.1","classification":cl,"authority":"MARGINFI_ORCA_FORCED_FLOW_IMPACT_V0_2_CLEAN_PERIOD_FREEZE_2026-10-01.md",
         **g,"gates":checks,"market_outcomes_read":False,
         "firewall":{"prices":False,"ohlc":False,"returns":False,"pnl":False,"julsep_observed":True,
                     "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
                     "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}}
R.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
