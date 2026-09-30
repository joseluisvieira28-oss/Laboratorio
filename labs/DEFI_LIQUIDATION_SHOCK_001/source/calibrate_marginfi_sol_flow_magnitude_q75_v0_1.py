#!/usr/bin/env python3
import argparse,datetime as dt,hashlib,json,math
from pathlib import Path

SOL="So11111111111111111111111111111111111111112"
LINK_MIN=5

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
R=OUT/"MARGINFI_SOL_FLOW_MAGNITUDE_Q75_CALIBRATION_RECEIPT_V0.1.json"
C=OUT/"MARGINFI_SOL_FLOW_MAGNITUDE_Q75_CALIBRATION_CASCADES_V0.1.ndjson"

def find_one(root,name):
    h=sorted(Path(root).rglob(name));return h[0] if len(h)==1 else None
def parse(s):return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)
def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(x):return x["signature"]+"|"+addrkey(x["instructionAddress"])

rec=find_one(args.source_root,"MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_RECEIPT_V0.2.json")
rowsf=find_one(args.source_root,"MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_ROWS_V0.2.ndjson")
errs=[]
if rec is None or rowsf is None:errs.append("source_receipt_or_rows_missing_or_duplicate")
if errs:
    R.write_text(json.dumps({"classification":"MARGINFI_SOL_FLOW_MAGNITUDE_Q75_BLOCKED","errors":errs},indent=2)+"\n");raise SystemExit(2)
sr=json.loads(rec.read_text())
if sr.get("classification")!="MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_PASS":
    errs.append("febmar_source_not_pass")
rows=[json.loads(x) for x in rowsf.read_text().splitlines() if x.strip()]
eligible=[]
for r in rows:
    if r.get("classification")!="DIRECTION_PROVEN":continue
    if r.get("route_semantic")!="COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN":continue
    if r.get("asset_label")!="SIGNED_SELL_PRESSURE_PROVEN":continue
    if r.get("asset_mint")!=SOL or r.get("route_input_mint")!=SOL:continue
    evs=r.get("decoded_swap_events") or []
    if not evs:
        errs.append("missing_decoded_swap_events:"+ident(r));continue
    amt=evs[0].get("inputAmount")
    if not isinstance(amt,int) or amt<=0 or evs[0].get("inputMint")!=SOL:
        errs.append("invalid_realized_sol_input:"+ident(r));continue
    eligible.append({**r,"t":parse(r["timestamp"]),"realized_lamports":amt,"realized_sol":amt/1e9})
if errs:
    R.write_text(json.dumps({"classification":"MARGINFI_SOL_FLOW_MAGNITUDE_Q75_BLOCKED","errors":errs[:100]},indent=2)+"\n");raise SystemExit(2)
eligible.sort(key=lambda r:(r["t"],r["signature"],addrkey(r["instructionAddress"])))

casc=[]
for e in eligible:
    if not casc or e["t"]>casc[-1]["last"]+dt.timedelta(minutes=LINK_MIN):
        casc.append({"first":e["t"],"last":e["t"],"events":[e]})
    else:
        casc[-1]["events"].append(e);casc[-1]["last"]=e["t"]

out=[]
for i,c in enumerate(casc,1):
    lam=sum(x["realized_lamports"] for x in c["events"])
    out.append({"cascade_id":f"fm-mag-{i:05d}","first_event_time":c["first"].isoformat(),
                "last_event_time":c["last"].isoformat(),"source_event_count":len(c["events"]),
                "realized_lamports":lam,"realized_sol":lam/1e9,
                "member_identities":[ident(x) for x in c["events"]]})
with C.open("w") as fh:
    for x in out:fh.write(json.dumps(x,separators=(",",":"),sort_keys=True)+"\n")

vals=sorted(x["realized_lamports"] for x in out)
N=len(vals)
if N<=0:
    R.write_text(json.dumps({"classification":"MARGINFI_SOL_FLOW_MAGNITUDE_Q75_BLOCKED","errors":["cascade_count_zero"]},indent=2)+"\n");raise SystemExit(2)
rank=math.ceil(.75*N);thr=vals[rank-1]
selected=sum(1 for v in vals if v>=thr)
receipt={
 "schema_version":"0.1","lab_id":"DLS-MARGINFI-SOL-FLOW-MAGNITUDE-REVERSION-001",
 "classification":"MARGINFI_SOL_FLOW_MAGNITUDE_Q75_CALIBRATION_PASS",
 "authority":"MARGINFI_SOL_FLOW_MAGNITUDE_REVERSION_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md",
 "source_classification":sr.get("classification"),"eligible_source_event_count":len(eligible),
 "cascade_count":N,"quantile":0.75,"method":"nearest_rank_ceil","nearest_rank":rank,
 "threshold_lamports":thr,"threshold_sol":thr/1e9,"selected_at_or_above_count":selected,
 "selected_rate":selected/N,"cascade_rows_sha256":hashlib.sha256(C.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"returns":False,"pnl":False,"apr_jun_market_outcomes_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}
}
R.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
