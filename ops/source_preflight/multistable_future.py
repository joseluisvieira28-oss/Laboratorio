"""Frozen-source preflight and optional future-only collection; no adjudicator."""
import argparse,json,math,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,"research/mexc_multistable_basis")
p="research/mexc_multistable_basis/forward_collector_v03.py"
assert subprocess.check_output(["git","hash-object",p],text=True).strip()=="e01a12c6794721981f6329b3c4c6473f7f968d24","FROZEN_COLLECTOR_IDENTITY_MISMATCH"
import forward_collector_v03 as m
now=datetime.now(timezone.utc);t=int(now.timestamp())//60*60
rows=[];errors=[]
for fn,symbol in [(m.spot_close,"USDCUSDT"),(m.spot_close,"USD1USDT")]+[(m.contract_close,s) for legs in m.ASSETS.values() for s in legs.values()]:
    try:
        px,ev=fn(symbol,t)
        if not math.isfinite(px) or px<=0:raise ValueError("INVALID_SOURCE_PRICE")
        rows.append({"symbol":symbol,"exact_close_utc":datetime.fromtimestamp(t,timezone.utc).isoformat(),"body_sha256":ev["body_sha256"],"http_status":ev["status_code"]})
    except Exception as e:errors.append({"symbol":symbol,"error_type":type(e).__name__,"error":str(e)})
try:
    meta,ev=m.contract_meta()
    rows.append({"metadata_bindings":len(meta),"body_sha256":ev["body_sha256"]})
except Exception as e:errors.append({"metadata_error_type":type(e).__name__,"error":str(e)})
report={"received_utc":now.isoformat(),"source_rows":rows,"errors":errors,"source_gate_pass":not errors and len(rows)==9,"economic_metrics_opened":False,"orders":False,"science_changed":False,"old_malformed_window_preserved":True,"readiness_parser_unchanged":True}
Path("evidence").mkdir(exist_ok=True);Path("evidence/MULTISTABLE_SOURCE_PREFLIGHT_2026-10-12.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,sort_keys=True))
ap=argparse.ArgumentParser();ap.add_argument("--collect-future",action="store_true");a=ap.parse_args()
if a.collect_future:
    if not report["source_gate_pass"]:raise SystemExit("SOURCE_BLOCKED_NO_FUTURE_CAPTURE")
    start="2026-10-12T10:15:00Z";end="2026-10-12T13:14:00Z"
    if datetime.now(timezone.utc)>=m.parse_iso(start):raise SystemExit("FUTURE_START_MISSED_NO_BACKFILL")
    subprocess.run([sys.executable,p,"--start",start,"--end",end,"--segment","2026-10-12_1015_1314_ops"],check=True)
